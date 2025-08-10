import os
import pytest

# Ensure non-mock for moderation path
os.environ.setdefault("MOCK_MODE", "false")

from api import create_app  # type: ignore
import api as api_module  # type: ignore


@pytest.fixture(scope="module")
def client():
    api_module.config['mock_mode'] = False
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_moderation_blocks_when_llm_flags(client, monkeypatch):
    monkeypatch.setenv("MODERATION_USE_LLM", "true")
    import api as api_module
    monkeypatch.setattr(api_module, "_llm_moderation_flagged", lambda text: True)
    rv = client.post('/api/videos', json={
        "title":"Violence topic","description":"Some illegal stuff","user_input":"Discuss hate and illegal topics"
    })
    assert rv.status_code == 422


def test_moderation_allows_when_llm_disabled(client, monkeypatch):
    monkeypatch.setenv("MODERATION_USE_LLM", "true")  # env won’t matter after mock
    import api as api_module
    monkeypatch.setattr(api_module, "_llm_moderation_flagged", lambda text: False)
    rv = client.post('/api/videos', json={
        "title":"Violence topic","description":"Some illegal stuff","user_input":"Discuss hate and illegal topics"
    })
    assert rv.status_code == 201