from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re

from sqlalchemy import select, func

from .config import EXPORT_DIR, INPUT_DIR
from .models import Slovnyk, Slovo, Tlumachennia
from .ui import ensure_export_dir, input_int, input_non_empty, input_text
from .reports import report_counts_by_dictionary
from .ui import run_menu, pick_id, format_dict_type
from .services import dictionaries_list, dictionary_create, dictionary_edit, dictionary_delete

def export_report_counts_json(session):
    ensure_export_dir()
    rows = report_counts_by_dictionary(session)
    data = [{"id": sid, "nazva": nazva, "typ": typ, "words_count": int(cnt)} for sid, nazva, typ, cnt in rows]
    path = EXPORT_DIR / "zvit_kilkist_sliv_u_slovnykakh.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nГотово: експорт у JSON -> {path}")


def export_dictionary_json(session):
    """ словники JSON файл"""
    ensure_export_dir()

    dictionaries = session.execute(select(Slovnyk).order_by(Slovnyk.id)).scalars().all()
    out = []

    for d in dictionaries:
        d_obj = {
            "id": d.id,
            "nazva": d.nazva,
            "typ": d.typ,
            "created_at": d.created_at.isoformat(sep=" ", timespec="seconds"),
            "slova": [],
        }

        words_sorted = sorted(d.words, key=lambda x: (x.word or "").lower())
        for w in words_sorted:
            meanings_sorted = sorted(w.meanings, key=lambda x: x.id)
            d_obj["slova"].append(
                {
                    "id": w.id,
                    "slovo": w.word,
                    "tlumachennia": [t.text for t in meanings_sorted],
                }
            )

        out.append(d_obj)

    path = EXPORT_DIR / "slovnyky_export.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово: експорт словників -> {path}")



def export_word_to_file(session):
    ensure_export_dir()
    word_id = input_int("ID слова: ")
    s = session.get(Slovo, word_id)
    if not s:
        print("Помилка: слово не знайдено.")
        return
    d = session.get(Slovnyk, s.dictionary_id)
    data = {
        "word_id": s.id,
        "слово": s.word,
        "dictionary_obj": d.nazva,
        "typ": d.typ,
        "тлумачення": [t.text for t in sorted(s.meanings, key=lambda x: x.id)],
    }
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in s.word[:40])
    path = EXPORT_DIR / f"слово_{s.id}_{safe_name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово: експорт слова -> {path}")


# Імпорт з JSON у базу даних.
def _get_or_create_dictionary(session, nazva: str, typ: str) -> Slovnyk:
    obj = session.execute(
        select(Slovnyk).where(Slovnyk.nazva == nazva, Slovnyk.typ == typ)
    ).scalar_one_or_none()
    if obj:
        return obj
    obj = Slovnyk(nazva=nazva, typ=typ)
    session.add(obj)
    session.flush()
    return obj


def _get_or_create_word(session, dictionary_id: int, word_text: str) -> Slovo:
    obj = session.execute(
        select(Slovo).where(Slovo.dictionary_id == dictionary_id, Slovo.word == word_text)
    ).scalar_one_or_none()
    if obj:
        return obj
    obj = Slovo(dictionary_id=dictionary_id, word=word_text)
    session.add(obj)
    session.flush()
    return obj


def _add_meaning_if_not_exists(session, word_id: int, tekst: str) -> bool:
    exists = session.execute(
        select(Tlumachennia.id).where(Tlumachennia.word_id == word_id, Tlumachennia.text == tekst)
    ).first()
    if exists:
        return False
    session.add(Tlumachennia(word_id=word_id, text=tekst))
    return True


def _safe_slug(text: str, max_len: int = 40) -> str:
    text = (text or "").strip().lower().replace(" ", "_")

    # груба транслітерація для українських літер для експорті словників у JSON, експорті одного слова у JSON, експорті звітів, формуванні автоматичних назв файлів
    map_ua = {
        "а":"a","б":"b","в":"v","г":"h","ґ":"g","д":"d","е":"e","є":"ie","ж":"zh","з":"z","и":"y","і":"i","ї":"i","й":"i",
        "к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"kh","ц":"ts","ч":"ch",
        "ш":"sh","щ":"shch","ь":"","ю":"iu","я":"ia",
    }
    tmp = []
    for ch in text:
        tmp.append(map_ua.get(ch, ch))
    text = "".join(tmp)

    # тільки лат і цифри
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_len] if text else "slovo"


def export_one_word_to_json(session):
    """ Експорт одне слово і тлумачення у JSON     """
    ensure_export_dir()

    # 1)вибір словника
    dictionaries = session.execute(select(Slovnyk).order_by(Slovnyk.id)).scalars().all()
    if not dictionaries:
        print("Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.")
        return

    print("\nОберіть словник:")
    for d in dictionaries:
        print(f"  ID {d.id}: {d.nazva} ({d.typ})")

    sid = input_int("Введіть ID словника (Enter — назад): ", allow_blank=True)
    if sid is None:
        return

    dictionary_obj = session.get(Slovnyk, sid)
    if not dictionary_obj:
        print("Помилка: словник не знайдено.")
        return

    # 2) вибір слова
    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == dictionary_obj.id).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику немає слів.")
        return

    print("\nОберіть слово:")
    for w in words:
        print(f"  ID {w.id}: {w.word} (тлумачень: {len(w.meanings)})")

    wid = input_int("Введіть ID слова (Enter — назад): ", allow_blank=True)
    if wid is None:
        return

    word_obj = session.get(Slovo, wid)
    if not word_obj or word_obj.dictionary_id != dictionary_obj.id:
        print("Помилка: слово не знайдено у вибраному словнику.")
        return

    payload = {
        "dictionary": {
            "id": dictionary_obj.id,
            "nazva": dictionary_obj.nazva,
            "typ": dictionary_obj.typ,
        },
        "word": {
            "id": word_obj.id,
            "slovo": word_obj.word,
            "tlumachennia": [m.text for m in sorted(word_obj.meanings, key=lambda x: x.id)],
        },
        "exported_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }

    slug = _safe_slug(word_obj.word)
    path = EXPORT_DIR / f"slovo_{word_obj.id}_{slug}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово: експорт слова у JSON -> {path}")


def import_from_json(session):
    """    Імпорт словника з JSON у бд."""
    print("\n📥 ІМПОРТ З JSON У БАЗУ ДАНИХ")


    default_demo = INPUT_DIR / "demo_import.json"
    if default_demo.exists():
        print(f"Підказка: демо-файл лежить тут: {default_demo}")

    path_str = input("Введіть шлях до JSON-файлу (або натисніть Enter для демо): ").strip()

    if not path_str:
        if not default_demo.exists():
            print("Помилка: демо-файл не знайдено у папці input/.")
            return
        path = default_demo
    else:
        path = Path(path_str)

    if path.exists() and path.is_dir():
        json_files = sorted(path.glob("*.json"))
        if not json_files:
            print("Помилка: у вказаній папці немає жодного JSON-файлу.")
            return
        path = json_files[0]
        print(f"Знайдено файл: {path}")

    # Перевірка чи є файл
    if not path.exists():
        print("Помилка: файл не знайдено. Перевірте шлях.")
        return

    if path.suffix.lower() != ".json":
        print("Помилка: файл має бути у форматі .json")
        return

    # Читання файлу
    try:
        raw = path.read_text(encoding="utf-8")
    except PermissionError:
        print("Помилка: немає доступу до файлу. Перевірте права або виберіть інший файл.")
        return
    except Exception as e:
        print(f"Помилка читання файлу: {e}")
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Помилка: невірний формат JSON (файл не читається як JSON).")
        return
    dictionaries_data = None

    if isinstance(data, dict) and isinstance(data.get("dictionaries"), list):
        dictionaries_data = data["dictionaries"]
    elif isinstance(data, dict) and isinstance(data.get("словники"), list):
        dictionaries_data = data["словники"]
    elif isinstance(data, list):
        dictionaries_data = data
    elif isinstance(data, dict) and "nazva" in data and "typ" in data:
        dictionaries_data = [data]

    if dictionaries_data is None:
        print("Помилка: JSON має містити 1 словник або список словників.")
        return


    normalized = []
    for dct in dictionaries_data:
        if not isinstance(dct, dict) or "nazva" not in dct or "typ" not in dct:
            print("Помилка: кожен словник у JSON має містити поля 'nazva' та 'typ'.")
            return

        words_list = dct.get("slova")
        if words_list is None:
            words_list = dct.get("слова")
        if words_list is None:
            words_list = []

        if not isinstance(words_list, list):
            print("Помилка: поле 'slova' (або 'слова') має бути списком.")
            return

        normalized.append({"nazva": dct["nazva"], "typ": dct["typ"], "slova": words_list})

    # сохранение в БД
    try:
        try:
            session.rollback()
        except Exception:
            pass

        for dct in normalized:
            dictionary_obj = _get_or_create_dictionary(session, dct["nazva"], dct["typ"])

            for w in dct["slova"]:
                if not isinstance(w, dict):
                    continue

                word_text = (w.get("slovo") or w.get("word") or "").strip()
                if not word_text:
                    continue

                word = _get_or_create_word(session, dictionary_obj.id, word_text)

                meanings_list = w.get("tlumachennia")
                if meanings_list is None:
                    meanings_list = w.get("meanings")
                if meanings_list is None:
                    meanings_list = []

                if not isinstance(meanings_list, list):
                    meanings_list = [meanings_list]

                for meaning in meanings_list:
                    mtxt = str(meaning).strip()
                    if mtxt:
                        _add_meaning_if_not_exists(session, word.id, mtxt)

        session.commit()
        print("Готово: імпорт завершено ✅")
    except Exception as e:
        session.rollback()
        print(f"Помилка під час імпорту: {e}")

def menu_dictionaries(session):

    def act_list():
        dictionaries_list(session)

    def act_create():
        dictionary_create(session)

    def act_edit():
        dictionary_edit(session)

    def act_delete():
        dictionary_delete(session)

    items = [
        ("1", "📋 Список словників", act_list),
        ("2", "➕ Створити dictionary_obj", act_create),
        ("3", "✏️ Редагувати dictionary_obj", act_edit),
        ("4", "🗑️ Видалити dictionary_obj", act_delete),
    ]
    run_menu("📚 Меню: Словники", items)



def slovnyky_list(session):
    """ список всех словників.  """
    rows = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    if not rows:
        print("У базі ще немає словників.")
        return []
    print("\n📚 Словники:")
    for d in rows:
        print(f"- ID {d.id}: {d.nazva} (тип: {format_dict_type(d.typ)})")
    return rows


def slovnyk_create(session):

    nazva = input_non_empty("Назва словника (Enter — назад): ")
    if nazva is None:
        return
    typ = input_non_empty("Тип словника (наприклад en-uk або uk-en) (Enter — назад): ", allow_blank=True)
    if typ is None:
        return

    exists = session.execute(
        select(Slovnyk).where(Slovnyk.nazva == nazva, Slovnyk.typ == typ)
    ).scalar_one_or_none()
    if exists:
        print("Помилка: такий словник з цією назвою і типом вже існує.")
        return

    d = Slovnyk(nazva=nazva, typ=typ)
    session.add(d)
    session.commit()
    print(f"✅ Створив словник: ID {d.id}")


def slovnyk_edit(session):
    rows = slovnyky_list(session)
    if not rows:
        return
    sid = pick_id(rows, "Оберіть словник (Enter — назад): ", ("nazva", "typ"))
    if sid is None:
        return
    d = session.get(Slovnyk, sid)
    if not d:
        print("Помилка: словник не знайдено.")
        return

    new_nazva = input_non_empty(f"Нова назва (зараз: {d.nazva}) (Enter — залишити): ", allow_blank=True)
    if new_nazva is None:
        new_nazva = d.nazva
    new_typ = input_non_empty(f"Новий тип (зараз: {d.typ}) (Enter — залишити): ", allow_blank=True)
    if new_typ is None:
        new_typ = d.typ

    exists = session.execute(
        select(Slovnyk).where(Slovnyk.nazva == new_nazva, Slovnyk.typ == new_typ, Slovnyk.id != d.id)
    ).scalar_one_or_none()
    if exists:
        print("Помилка: такий словник з цією назвою і типом вже існує.")
        return

    d.nazva = new_nazva
    d.typ = new_typ
    session.commit()
    print("✅ Оновив словник.")


def slovnyk_delete(session):
    rows = slovnyky_list(session)
    if not rows:
        return
    sid = pick_id(rows, "Оберіть словник для видалення (Enter — назад): ", ("nazva", "typ"))
    if sid is None:
        return
    d = session.get(Slovnyk, sid)
    if not d:
        print("Помилка: словник не знайдено.")
        return

    confirm = input(f"Точно видалити словник '{d.nazva}'? (так/ні): ").strip().lower()
    if confirm not in ("так", "т", "yes", "y"):
        print("Скасовано.")
        return

    session.delete(d)
    session.commit()
    print("✅ Видалив словник.")


