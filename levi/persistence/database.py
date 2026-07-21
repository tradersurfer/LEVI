"""SQLAlchemy engine/session setup, disabled unless explicitly configured."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True)
class Database:
    engine: Engine
    sessions: sessionmaker[Session]


def persistence_enabled() -> bool:
    return os.getenv("LEVI_PERSISTENCE_ENABLED", "false").lower() == "true"


def create_database(url: str | None = None) -> Database:
    resolved = url or os.getenv("DATABASE_URL")
    if not resolved:
        raise RuntimeError("database persistence is not configured")
    engine = create_engine(resolved, pool_pre_ping=True)
    return Database(engine, sessionmaker(engine, expire_on_commit=False))


@contextmanager
def session_scope(database: Database) -> Iterator[Session]:
    session = database.sessions()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
