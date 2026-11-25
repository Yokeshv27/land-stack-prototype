"""Keep tests independent of the developer's local demo database."""
from pathlib import Path
import pytest
from database import database


@pytest.fixture(autouse=True)
def isolated_sqlite_database(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB", Path(tmp_path) / "land_stack_test.db")
