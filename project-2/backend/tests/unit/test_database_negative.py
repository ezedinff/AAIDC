import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager  # type: ignore


@pytest.fixture(scope="module")
def app_ctx():
    app = create_app()
    app.testing = True
    with app.app_context():
        yield app


def test_update_nonexistent_returns_false(app_ctx):
    dbm = DatabaseManager(db)
    ok = dbm.update_video_status('nonexistent', 'processing')
    assert ok is False


def test_get_progress_unknown_returns_empty(app_ctx):
    dbm = DatabaseManager(db)
    entries = dbm.get_video_progress('nonexistent')
    assert entries == [] 