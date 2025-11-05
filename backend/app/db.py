from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_URL = "sqlite+pysqlite:///:memory:"
DATABASE_URL = os.getenv("NEXUS_DATABASE_URL", DEFAULT_DB_URL)

is_sqlite = DATABASE_URL.startswith("sqlite")
uses_memory = is_sqlite and ":memory:" in DATABASE_URL

if uses_memory:
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args=connect_args,
        poolclass=StaticPool,
    )
else:
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


__all__ = ["engine", "init_db", "get_session"]
