from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import DB_PATH
from .models import Base

# ПІДКЛЮЧЕННЯ ДО БАЗИ ДАНИХ
def make_engine():
    db_file = DB_PATH.resolve()
    return create_engine(f"sqlite:///{db_file.as_posix()}", echo=False, future=True)


def init_db(engine):
    Base.metadata.create_all(engine)


SessionLocal = sessionmaker(bind=make_engine(), autoflush=False, expire_on_commit=False, future=True)


SessionLocal = sessionmaker(bind=make_engine(), autoflush=False, expire_on_commit=False, future=True)
