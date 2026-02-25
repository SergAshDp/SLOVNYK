# СЛОВНИК — курсова робота SQLite + SQLAlchemy
# Cловники, пошук, звіти, слова та тлумачення у базі даних.
# Файли тільки для експорту/імпорту JSON (папки export та input).

"""
SLOVNYK
Ver: 3.18
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


from slovnyk.db import SessionLocal, init_db, make_engine
from slovnyk.ui import run_menu
from slovnyk.menus import menu_slovnykyy, menu_slova, menu_reports, search

def main():
    engine = make_engine()
    init_db(engine)
    with SessionLocal() as session:
        items = [
            ("1", "📚 Словники (CRUD)", lambda: menu_slovnykyy(session)),
            ("2", "📝 Слова і тлумачення (CRUD)", lambda: menu_slova(session)),
            ("3", "🔎 Пошук", lambda: search(session)),
            ("4", "📊 Звіти / експорт / імпорт", lambda: menu_reports(session)),
            ("9", "🚪 Вихід", lambda: (_ for _ in ()).throw(SystemExit())),
        ]
        run_menu("📗 ГОЛОВНЕ МЕНЮ", items, show_back=False)

if __name__ == "__main__":
    main()
