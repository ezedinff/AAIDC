import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore
from database import db, DatabaseManager
from tools.database_tools import save_scene_progress, search_similar_videos, log_progress_event, get_video_context  # type: ignore


@pytest.fixture(scope="module")
def app_ctx():
    app = create_app()
    app.testing = True
    with app.app_context():
        yield app


def test_database_tools_flow(app_ctx):
    dbm = DatabaseManager(db)
    v = dbm.create_video('Tools', 'Tools Description', 'topic tools test')
    vid = v.id

    # save scenes raw and improved
    raw = [{"description": "d1", "caption_text": "caption one", "duration": 5}]
    res1 = save_scene_progress.invoke({"video_id": vid, "scenes": raw, "step": "raw_scenes"})
    assert 'Successfully saved' in res1

    improved = [{"description": "d1 improved", "caption_text": "caption one better", "duration": 5}]
    res2 = save_scene_progress.invoke({"video_id": vid, "scenes": improved, "step": "improved_scenes"})
    assert 'Successfully saved' in res2

    # search similar videos
    similar = search_similar_videos.invoke({"topic": "tools topic", "limit": 5})
    assert isinstance(similar, list)

    # log event
    res3 = log_progress_event.invoke({"video_id": vid, "step": "x", "status": "started", "message": "msg"})
    assert 'Logged' in res3

    # get context
    ctx = get_video_context.invoke({"video_id": vid})
    assert ctx.get('title') == 'Tools' 