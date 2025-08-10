import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager


@pytest.fixture(scope="module")
def app_ctx():
    app = create_app()
    app.testing = True
    with app.app_context():
        yield app


def test_database_crud(app_ctx):
    dbm = DatabaseManager(db)
    v = dbm.create_video("Title", "Desc", "Input")
    assert v.id

    fetched = dbm.get_video(v.id)
    assert fetched is not None
    assert fetched.title == "Title"

    # status update
    ok = dbm.update_video_status(v.id, 'processing', 'initializing', 5)
    assert ok
    fetched = dbm.get_video(v.id)
    assert fetched.status == 'processing'
    assert fetched.current_step == 'initializing'
    assert fetched.progress_percent == 5

    # progress entry
    entry = dbm.add_progress_entry(v.id, 'initialization', 'started', 'msg')
    assert entry.id is not None

    # result update
    ok = dbm.update_video_result(v.id, file_path=os.path.join(os.getcwd(), 'outputs', 'fake.mp4'), duration=12.3)
    assert ok
    fetched = dbm.get_video(v.id)
    assert fetched.status == 'completed'
    assert fetched.duration == 12.3

    # progress list
    entries = dbm.get_video_progress(v.id)
    assert isinstance(entries, list)
    assert len(entries) >= 1 