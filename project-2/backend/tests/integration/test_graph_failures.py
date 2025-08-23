import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")

from graph import VideoGeneratorGraph  # type: ignore
from api import create_app, VideoGeneratorWithProgress  # type: ignore
from database import db, DatabaseManager  # type: ignore


def test_graph_audio_generation_failure(monkeypatch):
    g = VideoGeneratorGraph()
    # Make audio generation raise
    def boom(*a, **k):
        raise RuntimeError('audio fail')
    monkeypatch.setattr(g.audio_agent, 'generate_audio', boom)
    result = g.generate_video('topic')
    # The workflow may proceed to video assembly, but it must record the error message
    messages = result.get('messages', [])
    msg_texts = [str(m) for m in messages]
    assert any('Audio generation failed' in t for t in msg_texts)


def test_graph_video_assembly_failure(monkeypatch):
    g = VideoGeneratorGraph()
    monkeypatch.setattr(g.video_agent, 'assemble_video', lambda scenes, audios: '')
    result = g.generate_video('topic')
    assert result.get('current_step') == 'video_assembly_failed'
    assert result.get('error')


def test_video_generator_with_progress_marks_failed(monkeypatch):
    app = create_app()
    with app.app_context():
        dbm = DatabaseManager(db)
        v = dbm.create_video('Fail', 'desc', 'input')
        vid = v.id
        # Make audio generation fail through the graph in wrapper
        progress_updates = {}  # Empty dict for testing
        wrapper = VideoGeneratorWithProgress(vid, dbm, progress_updates)
        monkeypatch.setattr(wrapper.generator.audio_agent, 'generate_audio', lambda s: (_ for _ in ()).throw(RuntimeError('err')))
        result = wrapper.generate_video('input')
        video = dbm.get_video(vid)
        assert video.status in ('failed', 'completed')  # wrapper updates status appropriately
        if not result.get('final_video'):
            assert video.status == 'failed' 