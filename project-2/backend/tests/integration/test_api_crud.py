import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager
from config import get_config  # type: ignore


@pytest.fixture(scope="module")
def client_app():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield app, c


def test_get_videos_and_not_found(client_app):
    app, client = client_app
    rv = client.get('/api/videos')
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

    # Not found
    rv = client.get('/api/videos/does-not-exist')
    assert rv.status_code == 404


def test_delete_video_success_and_not_found(client_app):
    app, client = client_app
    cfg = get_config()
    outputs = cfg['output_dir']
    os.makedirs(outputs, exist_ok=True)

    with app.app_context():
        dbm = DatabaseManager(db)
        v = dbm.create_video('Del', 'Del', 'Del')
        vid = v.id
        # create dummy file to delete
        fpath = os.path.join(outputs, 'to_delete.mp4')
        with open(fpath, 'wb') as f:
            f.write(b'X')
        v.file_path = fpath
        db.session.commit()

    rv = client.delete(f'/api/videos/{vid}')
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

    # subsequent delete should be 404
    rv = client.delete(f'/api/videos/{vid}')
    assert rv.status_code == 404


def test_progress_endpoint(client_app):
    app, client = client_app
    with app.app_context():
        dbm = DatabaseManager(db)
        v = dbm.create_video('Prog', 'Prog', 'Prog')
        vid = v.id
        dbm.add_progress_entry(vid, 'initialization', 'started', 'msg')
    rv = client.get(f'/api/videos/{vid}/progress')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] is True
    assert isinstance(data['progress'], list)
    assert len(data['progress']) >= 1 