"""Minimal schema migration entrypoint; Alembic can adopt this metadata later."""

from .database import Database
from .models import Base


def initialize_schema(database: Database) -> None:
    Base.metadata.create_all(database.engine)


def drop_schema_for_tests(database: Database) -> None:
    Base.metadata.drop_all(database.engine)
