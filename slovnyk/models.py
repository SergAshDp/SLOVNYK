from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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

