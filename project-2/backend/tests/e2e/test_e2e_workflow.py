import os
import time
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_create_to_complete_and_download(client):
    # Create video
    payload = {
        "title": "E2E",
        "description": "End to end test",
        "user_input": "Create a short mock video"
    }
    rv = client.post('/api/videos', json=payload)
    assert rv.status_code == 201
    vid = rv.get_json()['video']['id']

    # Poll for completion
    deadline = time.time() + 15
    status = None
    while time.time() < deadline:
        rv = client.get(f'/api/videos/{vid}')
        assert rv.status_code == 200
        data = rv.get_json()['video']
        status = data['status']
        if status == 'completed':
            break
        time.sleep(0.3)
    assert status == 'completed'

    # Progress entries exist
    rv = client.get(f'/api/videos/{vid}/progress')
    assert rv.status_code == 200
    progress = rv.get_json()['progress']
    assert isinstance(progress, list)
    assert len(progress) >= 1

    # Download works
    rv = client.get(f'/api/videos/{vid}/download')
    assert rv.status_code == 200
    assert rv.mimetype == 'video/mp4' 