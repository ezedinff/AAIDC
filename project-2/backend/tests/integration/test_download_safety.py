import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager
from config import get_config  # type: ignore


@pytest.fixture(scope="module")
def app_client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield app, c


def test_download_invalid_path_rejected(app_client, monkeypatch):
    app, client = app_client
    with app.app_context():
        dbm = DatabaseManager(db)
        # Create a video with a malicious path
        v = dbm.create_video("Bad", "bad", "bad")
        vid = v.id
        outside_path = "/tmp/../../etc/passwd"
        v.file_path = outside_path
        db.session.commit()
    # Perform request outside app context
    rv = client.get(f"/api/videos/{vid}/download")
    assert rv.status_code == 400
    data = rv.get_json()
    assert data['success'] is False


def test_download_nonexistent_file_404(app_client):
    app, client = app_client
    cfg = get_config()
    outputs_dir = cfg['output_dir']
    with app.app_context():
        dbm = DatabaseManager(db)
        v = dbm.create_video("NoFile", "nofile", "nofile")
        vid = v.id
        v.file_path = os.path.join(outputs_dir, "does_not_exist.mp4")
        db.session.commit()
    # Perform request outside app context
    rv = client.get(f"/api/videos/{vid}/download")
    assert rv.status_code == 404 