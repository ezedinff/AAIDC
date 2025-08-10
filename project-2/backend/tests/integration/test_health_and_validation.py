import os
import json
import pytest

# Ensure mock mode for tests
os.environ.setdefault("MOCK_MODE", "true")

from api import create_app  # type: ignore

@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_health_ok(client):
    rv = client.get("/api/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["success"] is True
    assert "checks" in data


def test_validation_errors(client):
    # Missing fields
    rv = client.post("/api/videos", json={})
    assert rv.status_code == 400

    # Too long title
    long_title = "x" * 300
    rv = client.post(
        "/api/videos",
        json={
            "title": long_title,
            "description": "ok",
            "user_input": "ok",
        },
    )
    assert rv.status_code == 400


def test_create_video_mock_mode(client):
    payload = {
        "title": "Test",
        "description": "A simple test",
        "user_input": "Create a mock video"
    }
    rv = client.post("/api/videos", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["success"] is True
    video = data["video"]
    assert video["status"] in ("pending", "processing")
    assert video["id"] 