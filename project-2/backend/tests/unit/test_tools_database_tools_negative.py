import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from tools.database_tools import save_scene_progress, get_video_context  # type: ignore


@pytest.fixture(scope="module")
def app_ctx():
    app = create_app()
    app.testing = True
    with app.app_context():
        yield app


def test_save_scene_progress_not_found(app_ctx):
    res = save_scene_progress.invoke({"video_id": "unknown", "scenes": [], "step": "raw_scenes"})
    assert 'not found' in res.lower()


def test_get_video_context_unknown(app_ctx):
    ctx = get_video_context.invoke({"video_id": "unknown"})
    assert ctx == {} 