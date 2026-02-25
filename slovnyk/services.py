from __future__ import annotations

import re
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from .models import Slovnyk, Slovo, Tlumachennia
from .ui import (
    format_dict_type,
    get_dictionaries,
    input_non_empty,
    input_int,
    input_int_optional,
    pick_id,
)

def dictionaries_list(session):
    rows = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    if not rows:
        print("Словників немає.")
        return
    print("\nСписок словників:")
    for r in rows:
        print(f"- ID {r.id}: {r.nazva} (тип: {format_dict_type(r.typ)}) | дата створення: {r.created_at}")


# === СТВОРЕННЯ СЛОВНИКА ===
def dictionary_create(session):
    nazva = input_non_empty("Назва словника: ")
    if nazva is None:
        return
    typ = input_non_empty("Тип (наприклад en-uk або uk-en): ")
    if typ is None:
        return
    s = Slovnyk(nazva=nazva, typ=typ)
    session.add(s)
    try:


        session.commit()
        print("Словник успішно створено.")
    except IntegrityError:
        session.rollback()
        print("Помилка: словник з такою назвою та типом вже існує.")




def dictionary_edit(session):
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print('Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.')
        return

    rows = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    sid = pick_id(rows, "Словники", ("nazva",))
    if sid is None:
        return
    obj = session.get(Slovnyk, sid)
    if not obj:
        print("Помилка: такого словника не існує.")
        return
    nazva = input_non_empty(f"Нова назва (зараз: {obj.nazva}): ")
    if nazva is None:
        return
    typ = input_non_empty(f"Новий тип (зараз: {obj.typ}): ")
    if typ is None:
        return
    obj.nazva = nazva
    obj.typ = typ
    try:
        session.commit()
        print("Словник успішно оновлено.")
    except IntegrityError:
        session.rollback()
        print("Помилка: словник з такою назвою та типом вже існує.")

def dictionary_delete(session):
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print('Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.')
        return

    rows = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    sid = pick_id(rows, "Словники", ("nazva",))
    if sid is None:
        return
    obj = session.get(Slovnyk, sid)
    if not obj:
        print("Помилка: такого словника не існує.")
        return
    confirm = input("Видалити dictionary_obj разом з усіма словами? (так/ні): ").strip().lower()
    if confirm != "tak":
        print("Скасовано.")
        return
    session.delete(obj)
    session.commit()
    print("Словник успішно видалено.")

def slova_list(session):
    # Список словників з бд.
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print('Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.')
        return

    dictionaries = session.execute(select(Slovnyk).order_by(Slovnyk.id)).scalars().all()
    if not dictionaries:
        print('Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.')
        return

    dictionaries = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    sid = pick_id(dictionaries, "Оберіть словник (Enter — назад)", ("nazva",))
    if sid is None:
        return
    d = session.get(Slovnyk, sid)
    if not d:
        print("Помилка: словник не знайдено.")
        return

# Список слів у вибраному словнику.
    stmt = (
        select(Slovo.id, Slovo.word, func.count(Tlumachennia.id).label("cnt"))
        .outerjoin(Tlumachennia, Tlumachennia.word_id == Slovo.id)
        .where(Slovo.dictionary_id == sid)
        .group_by(Slovo.id)
        .order_by(Slovo.word.asc())
    )
    rows = session.execute(stmt).all()
    if not rows:
        print("У словнику немає слів.")
        return
    print("\nСлова:")
    for wid, w, cnt in rows:
        print(f"- ID {wid}: {w}  (кількість тлумачень: {cnt})")



# нове слово. перше тлумачення.
def word_add(session):
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print('Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.')
        return

    dictionaries  = session.execute(select(Slovnyk).order_by(Slovnyk.id.desc())).scalars().all()
    sid = pick_id(dictionaries, "Оберіть словник (Enter — назад)", ("nazva",))
    if sid is None:
        return
    if not session.get(Slovnyk, sid):
        print("Помилка: словник не знайдено.")
        return

    word_text = input_non_empty("Слово або фраза (Enter — назад): ")
    meaning_1 = input_non_empty("Перше тлумачення (обов'язково): ")
    if meaning_1 is None:
        return

    obj = Slovo(dictionary_id=sid, word=word_text)
    obj.meanings.append(Tlumachennia(text=meaning_1))
    session.add(obj)
    try:
        session.commit()
        print("Слово успішно додано.")
    except IntegrityError:
        session.rollback()
        print("Помилка: таке слово вже існує у цьому словнику.")

def word_details(session):
    # список словників де саме шукати слово.
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print("Немає жодного словника. Спочатку створіть словник або імпортуйте демо-дані.")
        return

    did = pick_id(dictionaries, "Оберіть словник (Enter — назад)", ("nazva", "typ"))
    if did is None:
        return

    d = session.get(Slovnyk, did)
    if not d:
        print("Помилка: словник не знайдено.")
        return

    # слова словника, список, щоб було видно ID.
    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику поки немає слів.")
        return

    sid = pick_id(words, "Оберіть слово (Enter — назад)", ("word",))
    if sid is None:
        return

    s = session.get(Slovo, sid)
    if not s or s.dictionary_id != did:
        print("Помилка: слово не знайдено.")
        return

    print(f"\nID слова: {s.id}")
    print(f"Словник: {d.nazva} ({d.typ})")
    print(f"Слово: {s.word}")
    print("Тлумачення:")
    meanings = session.execute(
        select(Tlumachennia).where(Tlumachennia.word_id == s.id).order_by(Tlumachennia.id)
    ).scalars().all()

    if not meanings:
        print("  (Немає тлумачень)")
        return

    for t in meanings:
        print(f"  - {t.text}")

def meaning_add_to_word(session):
    dictionaries = get_dictionaries(session)
    if not dictionaries:
        print("Немає жодного словника.")
        return

    did = pick_id(dictionaries, "Оберіть словник (Enter — назад)", ("nazva", "typ"))
    if did is None:
        return

    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику немає слів.")
        return

    sid = pick_id(words, "Оберіть слово (Enter — назад)", ("word",))
    if sid is None:
        return

    s = session.get(Slovo, sid)
    if not s:
        print("Слово не знайдено.")
        return

    print("\nПоточні тлумачення:")
    meanings = session.execute(
        select(Tlumachennia).where(Tlumachennia.word_id == s.id).order_by(Tlumachennia.id)
    ).scalars().all()

    if meanings:
        for t in meanings:
            print(f"  - {t.text}")
    else:
        print("  (Немає тлумачень)")



    tekst = input_non_empty("Нове тлумачення (Enter — назад): ")
    if not tekst:
        return



    new_meaning = Tlumachennia(text=tekst, word_id=s.id)
    session.add(new_meaning)
    session.commit()

    print("Тлумачення додано успішно.")


def word_edit(session):
    """Редагування слова"""
    dictionaries = get_dictionaries(session)
    did = pick_id(dictionaries, "Оберіть словник (Enter — назад): ", ("nazva", "typ"))
    if did is None:
        return

    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику ще немає слів.")
        return

    wid = pick_id(words, "Оберіть слово для редагування (Enter — назад): ", ("word",))
    if wid is None:
        return

    word_obj = session.get(Slovo, wid)
    if not word_obj:
        print("Помилка: слово не знайдено.")
        return

    print(f"Поточне слово: {word_obj.word}")
    new_text = input_non_empty("Нове слово (Enter — назад): ", allow_blank=True)
    if new_text is None:
        return

    # перевірка на дублі у словнику
    exists = session.execute(
        select(Slovo)
        .where(Slovo.dictionary_id == did)
        .where(func.lower(Slovo.word) == new_text.lower())
        .where(Slovo.id != wid)
    ).scalars().first()

    if exists:
        print("Помилка: таке слово вже існує в цьому словнику.")
        return

    word_obj.word = new_text
    session.commit()
    print("Готово: слово відредаговано.")


def meaning_edit(session):
    """Редагування тлумачення слова."""
    dictionaries = get_dictionaries(session)
    did = pick_id(dictionaries, "Оберіть словник (Enter — назад): ", ("nazva", "typ"))
    if did is None:
        return

    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику ще немає слів.")
        return

    wid = pick_id(words, "Оберіть слово (Enter — назад): ", ("word",))
    if wid is None:
        return

    word_obj = session.get(Slovo, wid)
    if not word_obj:
        print("Помилка: слово не знайдено.")
        return

    meanings = session.execute(
        select(Tlumachennia).where(Tlumachennia.word_id == wid).order_by(Tlumachennia.id)
    ).scalars().all()

    if not meanings:
        print("Для цього слова ще немає тлумачень.")
        return

    print(f"Слово: {word_obj.word}")
    print("Поточні тлумачення:")
    for m in meanings:
        print(f"  ID {m.id}: {m.text}")

    mid = pick_id(meanings, "Оберіть тлумачення для редагування (Enter — назад): ", ("text",))
    if mid is None:
        return

    meaning_obj = session.get(Tlumachennia, mid)
    if not meaning_obj:
        print("Помилка: тлумачення не знайдено.")
        return

    print(f"Поточне тлумачення: {meaning_obj.text}")
    new_text = input_non_empty("Нове тлумачення (Enter — назад): ", allow_blank=True)
    if new_text is None:
        return

    # перевірка на дублікати тлумачень конкретного слова.
    exists = session.execute(
        select(Tlumachennia)
        .where(Tlumachennia.word_id == wid)
        .where(func.lower(Tlumachennia.text) == new_text.lower())
        .where(Tlumachennia.id != mid)
    ).scalars().first()

    if exists:
        print("Помилка: таке тлумачення вже існує для цього слова.")
        return

    meaning_obj.text = new_text
    session.commit()
    print("Готово: тлумачення відредаговано.")


def word_delete(session):
    """Видалення слова і усіх його тлумачень."""
    dictionaries = get_dictionaries(session)
    did = pick_id(dictionaries, "Оберіть словник (Enter — назад): ", ("nazva", "typ"))
    if did is None:
        return

    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику ще немає слів.")
        return

    wid = pick_id(words, "Оберіть слово для видалення (Enter — назад): ", ("word",))
    if wid is None:
        return

    word_obj = session.get(Slovo, wid)
    if not word_obj:
        print("Помилка: слово не знайдено.")
        return

    confirm = input_non_empty(f"Підтвердьте видалення слова «{word_obj.word}» (так/ні, Enter — назад): ", allow_blank=True)
    if confirm is None:
        return
    if confirm.strip().lower() not in ("так", "tак", "yes", "y", "1"):
        print("Скасовано.")
        return

    session.delete(word_obj)
    session.commit()
    print("Готово: слово видалено (разом із тлумаченнями).")


def meaning_delete(session):
    """Видалення одного тлумачення, якщо іх більше 1го"""
    dictionaries = get_dictionaries(session)
    did = pick_id(dictionaries, "Оберіть словник (Enter — назад): ", ("nazva", "typ"))
    if did is None:
        return

    words = session.execute(
        select(Slovo).where(Slovo.dictionary_id == did).order_by(Slovo.id)
    ).scalars().all()

    if not words:
        print("У цьому словнику ще немає слів.")
        return

    wid = pick_id(words, "Оберіть слово (Enter — назад): ", ("word",))
    if wid is None:
        return

    word_obj = session.get(Slovo, wid)
    if not word_obj:
        print("Помилка: слово не знайдено.")
        return

    meanings = session.execute(
        select(Tlumachennia).where(Tlumachennia.word_id == wid).order_by(Tlumachennia.id)
    ).scalars().all()

    if not meanings:
        print("Для цього слова ще немає тлумачень.")
        return

    if len(meanings) == 1:
        print("Не можна видалити останнє тлумачення для слова.")
        return

    print(f"Слово: {word_obj.word}")
    print("Тлумачення:")
    for m in meanings:
        print(f"  ID {m.id}: {m.text}")

    mid = pick_id(meanings, "Оберіть тлумачення для видалення (Enter — назад): ", ("text",))
    if mid is None:
        return

    meaning_obj = session.get(Tlumachennia, mid)
    if not meaning_obj:
        print("Помилка: тлумачення не знайдено.")
        return

    confirm = input_non_empty(f"Підтвердьте видалення тлумачення «{meaning_obj.text}» (так/ні, Enter — назад): ", allow_blank=True)
    if confirm is None:
        return
    if confirm.strip().lower() not in ("так", "tак", "yes", "y", "1"):
        print("Скасовано.")
        return

    count_now = session.execute(
        select(func.count(Tlumachennia.id)).where(Tlumachennia.word_id == wid)
    ).scalar_one()
    if count_now <= 1:
        print("Не можна видалити останнє тлумачення для слова.")
        return

    session.delete(meaning_obj)
    session.commit()
    print("Готово: тлумачення видалено.")

def search(session):
    q = input_non_empty("🔍 Пошук slova/frazy: ")
    if q is None:
        return
    stmt = (
        select(Slovnyk.nazva, Slovnyk.typ, Slovo.id, Slovo.word, Tlumachennia.id, Tlumachennia.text)
        .join(Slovo, Slovo.dictionary_id == Slovnyk.id)
        .join(Tlumachennia, Tlumachennia.word_id == Slovo.id)
        .where(Slovo.word.like(f"%{q}%"))
        .order_by(Slovnyk.id.desc(), Slovo.word.asc(), Tlumachennia.id.asc())
    )
    rows = session.execute(stmt).all()
    if not rows:
        print("Нічого не знайдено.")
        return

    print("\nРезультати:")
    current = None
    for dictionary_name, typ, word_id, word_text, tl_id, tl_txt in rows:
        key = (dictionary_name, typ, word_id, word_text)
        if key != current:
            current = key
            print(f"\n[{dictionary_name} ({typ})]  ID слова {word_id}: {word_text}")
        print(f"  - {tl_id}: {tl_txt}")


# Експорт у папку export/ у форматі JSON.
