from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


def test_role_migration_backfills_nulls_and_rejects_invalid_roles():
    engine = create_engine("sqlite://")
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        config.attributes["connection"] = connection
        command.upgrade(config, "0001_initial_schema")
        connection.execute(
            text(
                "INSERT INTO users (name, email, password, role) "
                "VALUES ('Legacy', 'legacy@example.com', 'hash', NULL)"
            )
        )
        connection.commit()

        command.upgrade(config, "head")
        command.check(config)
        role = connection.execute(
            text("SELECT role FROM users WHERE email = 'legacy@example.com'")
        ).scalar_one()
        assert role == "user"

        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO users (name, email, password, role) "
                    "VALUES ('Invalid', 'invalid@example.com', 'hash', 'unknown')"
                )
            )
            connection.commit()
        connection.rollback()
    engine.dispose()
