# СЛОВНИК — курсова робота SQLite + SQLAlchemy
# Cловники, пошук, звіти, слова та тлумачення у базі даних.
# Файли тільки для експорту/імпорту JSON (папки export та input).

"""
SLOVNYK
Ver: 2.53
BD: SQLite (SQLAlchemy)
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import re

from sqlalchemy import (
    create_engine, String, Integer, DateTime, ForeignKey,
    UniqueConstraint, select, func
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)
from sqlalchemy.exc import IntegrityError

PROJECT_NAME = "SLOVNYK"
VERSION = "2.53"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "input"
EXPORT_DIR = BASE_DIR / "export"

# для зберігання файлів бази даних, якщо вона ще не існує.
DATA_DIR.mkdir(parents=True, exist_ok=True)
# для імпорту JSON-файлів.
INPUT_DIR.mkdir(parents=True, exist_ok=True)
# для збереження результатів експорту у JSON.
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Шлях до файлу SQLite-бази даних.
DB_PATH = DATA_DIR / "dictionary_obj.db"
class Base(DeclarativeBase):

    pass


# таблиці словників у базі даних.
class Slovnyk(Base):
    __tablename__ = "dictionaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nazva: Mapped[str] = mapped_column(String, nullable=False)
    typ: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    # Один dictionary_obj може мати багато слів
    words: Mapped[list["Slovo"]] = relationship(
        back_populates="dictionary",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("nazva", "typ", name="uq_dictionary_nazva_typ"),
    )


class Slovo(Base):
    """
    Сутність "word". Слово належить до конкретного словника і має быльше ныж 1+ тлумачень.
    """
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dictionary_id: Mapped[int] = mapped_column(ForeignKey("dictionaries.id", ondelete="CASCADE"), nullable=False)
    word: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    dictionary: Mapped[Slovnyk] = relationship(back_populates="words")
    meanings: Mapped[list["Tlumachennia"]] = relationship(
        back_populates="word_obj",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("dictionary_id", "word", name="uq_word_dictionary_word"),
    )


class Tlumachennia(Base):
    """
    Сутність "тлумачення" Варіант перекладу/пояснення для слова.
    """
    __tablename__ = "meanings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    word_obj: Mapped[Slovo] = relationship(back_populates="meanings")

    __table_args__ = (
        UniqueConstraint("word_id", "text", name="uq_meaning_word_text"),
    )



# ПІДКЛЮЧЕННЯ ДО БАЗИ ДАНИХ
def make_engine():
    db_file = DB_PATH.resolve()
    return create_engine(f"sqlite:///{db_file.as_posix()}", echo=False, future=True)


def init_db(engine):
    Base.metadata.create_all(engine)


SessionLocal = sessionmaker(bind=make_engine(), autoflush=False, expire_on_commit=False, future=True)


def format_dict_type(typ_value: str) -> str:

    if not typ_value:
        return ""
    v = typ_value.strip().lower()
    mapping = {
        "en-uk": "англійсько-український",
        "uk-en": "українсько-англійський",
        "en-ua": "англійсько-український",
        "ua-en": "українсько-англійський",
    }
    return mapping.get(v, typ_value)


def ensure_export_dir():
# Папка export для експорту у JSON.
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def safe_input(prompt: str) -> str | None:
    """  Ctrl+C щоб не було помилок по завершенню скрипта!!!!!!!!!!!!    """
    try:
        return input(prompt)
    except KeyboardInterrupt:
        return None


def input_text(prompt: str) -> str | None:
    s_raw = safe_input(prompt)
    if s_raw is None:
        return None
    s = s_raw.strip()
    if s == "":
        return None
    return s


def input_int_optional(prompt: str) -> int | None:
    while True:
        s_raw = safe_input(prompt)
        if s_raw is None:
            return None
        s = s_raw.strip()
        if s == "":
            return None
        if s.isdigit() and int(s) > 0:
            return int(s)
        print("Помилка: введіть додатне ціле число.")


def input_int_required(prompt: str) -> int:
    while True:
        s_raw = safe_input(prompt)
        if s_raw is None:
            print("Помилка: введення перервано.")
            continue
        s = s_raw.strip()
        if s.isdigit() and int(s) > 0:
            return int(s)
        print("Помилка: введіть додатне ціле число.")


def input_non_empty(prompt: str, allow_blank: bool = False):
    while True:
        s = input_text(prompt)
        if s is None:
            # Enter або Ctrl+C
            if allow_blank:
                return None
            print("Помилка: рядок не може бути порожнім.")
            continue
        return s





def input_int(prompt: str, allow_blank: bool = False):
    if allow_blank:
        return input_int_optional(prompt)
    return input_int_required(prompt)




def get_dictionaries(session):
    """ список словників з бази даних"""
    return session.execute(select(Slovnyk).order_by(Slovnyk.id)).scalars().all()
def press_enter():
    return


def pick_id(rows, title="Оберіть", label_fields=("nazva", "word")):
    """ список записів і ввод ID."""
    rows = list(rows)
    if not rows:
        print("Дані відсутні.")
        return None

    print("\n" + title)
    for r in rows:
        label = ""
        for f in label_fields:
            if hasattr(r, f):
                label = getattr(r, f) or ""
                break
        print(f"  {r.id}) {label}")
    print("  0) ↩️ Назад")

    val = input_int_optional("Введіть ID: ")
    if val is None or val == 0:
        return None
    return val

def run_menu(title: str, items: list[tuple[str, str, callable]], show_back: bool = True):
    while True:
        print(f"\n=== {title} ===")
        for key, label, _ in items:
            print(f"{key}) {label}")
        if show_back:
            print("0) ↩️ Назад")

        valid = {k for k, _, _ in items} | ({"0"} if show_back else set())
        ch_raw = safe_input("Оберіть: ")
        if ch_raw is None:
            return
        ch = ch_raw.strip()
        if ch == "":
            if show_back:
                return
            else:
                continue
        if show_back and ch == "0":
            return
        if ch not in valid:
            print("Помилка: невірний пункт меню.")
            continue

        for key, _, handler in items:
            if key == ch:
                handler()
                break


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
def report_counts_by_dictionary(session):
    stmt = (
        select(Slovnyk.id, Slovnyk.nazva, Slovnyk.typ, func.count(Slovo.id).label("words_count"))
        .outerjoin(Slovo, Slovo.dictionary_id == Slovnyk.id)
        .group_by(Slovnyk.id)
        .order_by(func.count(Slovo.id).desc(), Slovnyk.id.desc())
    )
    rows = session.execute(stmt).all()
    print("\n📊 Звіт: кількість слів у словниках")
    for sid, nazva, typ, cnt in rows:
        print(f"- ID {sid}: {nazva} (тип: {format_dict_type(typ)}) → кількість слів: {cnt}")
    return rows


def report_top_words_by_meanings(session, limit=10):
    stmt = (
        select(Slovo.id, Slovo.word, Slovnyk.nazva, Slovnyk.typ, func.count(Tlumachennia.id).label("mc"))
        .join(Slovnyk, Slovnyk.id == Slovo.dictionary_id)
        .join(Tlumachennia, Tlumachennia.word_id == Slovo.id)
        .group_by(Slovo.id)
        .order_by(func.count(Tlumachennia.id).desc(), Slovo.id.desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    print(f"\n📊 Звіт: топ-{limit} слів за кількістю тлумачень")
    for wid, w, nazva, typ, mc in rows:
        print(f"- ID слова {wid}: {w}  [{nazva} {typ}] -> {mc}")
    return rows


def report_recent_words(session, limit=10):
    stmt = (
        select(Slovo.id, Slovo.word, Slovo.created_at, Slovnyk.nazva, Slovnyk.typ)
        .join(Slovnyk, Slovnyk.id == Slovo.dictionary_id)
        .order_by(Slovo.id.desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    print(f"\n📊 Звіт: останні {limit} додані слова")
    for wid, w, created_at, nazva, typ in rows:
        print(f"- ID {wid}: {w}  [{nazva} | {format_dict_type(typ)}]  дата додавання: {created_at}")
    return rows


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


def menu_slovnykyy(session):
    items = [
        ("1", "📋 Список словників", lambda: slovnyky_list(session)),
        ("2", "➕ Створити словник", lambda: slovnyk_create(session)),
        ("3", "✏️ Редагувати словник", lambda: slovnyk_edit(session)),
        ("4", "🗑️ Видалити словник", lambda: slovnyk_delete(session)),
    ]
    run_menu("📚 Меню: Словники", items)


def menu_slova(session):
    items = [
        ("1", "📋 Список слів у словнику", lambda: slova_list(session)),
        ("2", "➕ Додати слово (+1 тлумачення)", lambda: word_add(session)),
        ("3", "👁️ Перегляд слова (деталі)", lambda: word_details(session)),
        ("4", "➕ Додати тлумачення до слова", lambda: meaning_add_to_word(session)),
        ("5", "✏️ Редагувати слово", lambda: word_edit(session)),
        ("6", "✏️ Редагувати тлумачення", lambda: meaning_edit(session)),
        ("7", "🗑️ Видалити слово", lambda: word_delete(session)),
        ("8", "🗑️ Видалити тлумачення", lambda: meaning_delete(session)),
    ]
    run_menu("📝 Меню: Слова і тлумачення", items)


def menu_reports(session):

    def report_top():
        limit = input_int("Кількість (наприклад 10): ", allow_blank=True)
        if limit is None:
            return
        report_top_words_by_meanings(session, limit=limit)

    def report_recent():
        limit = input_int("Кількість (наприклад 10): ", allow_blank=True)
        if limit is None:
            return
        report_recent_words(session, limit=limit)

    items = [
        ("1", "📊 Звіт: кількість слів у словниках (на екрані)", lambda: report_counts_by_dictionary(session)),
        ("2", "🏆 Звіт: топ слів за кількістю тлумачень (на екрані)", report_top),
        ("3", "🕒 Звіт: останні додані слова (на екрані)", report_recent),
        ("4", "📤 Експорт звіту №1 у форматі JSON", lambda: export_report_counts_json(session)),
        ("5", "📤 Експорт усіх словників у форматі JSON", lambda: export_dictionary_json(session)),
        ("6", "📤 Експорт одного слова у форматі JSON", lambda: export_one_word_to_json(session)),
        ("7", "📥 Імпорт з JSON у базу даних", lambda: import_from_json(session)),
    ]
    run_menu("📊 Меню: Звіти / експорт / імпорт", items)

def main():
    engine = make_engine()
    init_db(engine)
    ensure_export_dir()

    print(f"{PROJECT_NAME} v{VERSION}")

    with SessionLocal() as session:
        items = [
            ("1", "📖 Словники (CRUD)", lambda: menu_slovnykyy(session)),
            ("2", "📝 Слова і тлумачення (CRUD)", lambda: menu_slova(session)),
            ("3", "🔍 Пошук", lambda: search(session)),
            ("4", "📊 Звіти / експорт / імпорт", lambda: menu_reports(session)),
            ("9", "🚪 Вихід", lambda: (_ for _ in ()).throw(SystemExit())),
        ]
        run_menu("📚 ГОЛОВНЕ МЕНЮ", items, show_back=False)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        print("До побачення! 👋")
    except KeyboardInterrupt:
        print("\nРоботу перервано користувачем. До побачення! 👋")
