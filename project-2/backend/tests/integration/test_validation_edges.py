import os
import pytest

os.environ.setdefault("MOCK_MODE", "false")

from api import create_app  # type: ignore


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_user_input_too_long(client):
    payload = {
        "title": "T",
        "description": "D",
        "user_input": "x" * 4001
    }
    rv = client.post('/api/videos', json=payload)
    assert rv.status_code == 400


def test_max_lengths_ok(client, monkeypatch):
    # Mock LLM moderation to not flag anything for deterministic 201
    import api as api_module
    monkeypatch.setattr(api_module, "_llm_moderation_flagged", lambda text: False)
    payload = {
        "title": "x" * 255,
        "description": "y" * 2000,
        "user_input": "z" * 4000
    }
    rv = client.post('/api/videos', json=payload)
    assert rv.status_code == 201


def test_bad_json_payload(client):
    rv = client.post('/api/videos', data="not-json", headers={"Content-Type": "text/plain"})
    assert rv.status_code in (400, 415) 