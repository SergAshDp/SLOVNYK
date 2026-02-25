from __future__ import annotations

from .config import EXPORT_DIR
from sqlalchemy import select
from .models import Slovnyk

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


