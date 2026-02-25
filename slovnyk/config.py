from __future__ import annotations

from pathlib import Path

PROJECT_NAME = "SLOVNYK"
VERSION = "3.18"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "input"
EXPORT_DIR = BASE_DIR / "export"

# для зберігання файлів бази даних, якщо вона ще не існує.
DATA_DIR.mkdir(parents=True, exist_ok=True)
# для імпорту JSON-файлів.
INPUT_DIR.mkdir(parents=True, exist_ok=True)
# для збереження результатів експорту у JSON.
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Шлях до файлу БД.
DB_PATH = DATA_DIR / "dictionary_obj.db"
