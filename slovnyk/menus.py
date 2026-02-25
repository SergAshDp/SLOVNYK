from __future__ import annotations

from .ui import run_menu, input_int
from .services import (
    dictionaries_list, dictionary_create, dictionary_edit, dictionary_delete,
    slova_list, word_add, word_details, meaning_add_to_word,
    word_edit, meaning_edit, word_delete, meaning_delete,
    search
)
from .reports import (
    report_counts_by_dictionary, report_top_words_by_meanings, report_recent_words
)
from .io_json import (
    export_report_counts_json, export_dictionary_json, export_word_to_file,
    export_one_word_to_json, import_from_json
)


slovnyky_list = dictionaries_list
slovnyk_create = dictionary_create
slovnyk_edit = dictionary_edit
slovnyk_delete = dictionary_delete

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

