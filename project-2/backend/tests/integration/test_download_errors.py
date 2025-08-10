import os
import uuid
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager


@pytest.fixture(scope="module")
def app_client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield app, c


def test_download_missing_file_path_404(app_client):
    app, client = app_client
    with app.app_context():
        dbm = DatabaseManager(db)
        v = dbm.create_video('NoPath', 'desc', 'input')
        vid = v.id
        # file_path remains None
        db.session.commit()
    rv = client.get(f'/api/videos/{vid}/download')
    assert rv.status_code == 404


def test_download_unknown_video_404(app_client):
    _, client = app_client
    rv = client.get(f'/api/videos/{uuid.uuid4()}/download')
    assert rv.status_code == 404 