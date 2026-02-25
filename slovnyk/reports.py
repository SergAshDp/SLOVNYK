from __future__ import annotations

from sqlalchemy import select, func

from .models import Slovnyk, Slovo, Tlumachennia
from .ui import format_dict_type

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


