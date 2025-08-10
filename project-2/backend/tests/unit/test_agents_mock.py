import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from agents.scene_generator import SceneGeneratorAgent  # type: ignore
from agents.scene_critic import SceneCriticAgent  # type: ignore
from agents.audio_agent import AudioAgent  # type: ignore
from agents.video_agent import VideoAgent  # type: ignore
from config import get_config  # type: ignore


def test_scene_generator_mock():
    sg = SceneGeneratorAgent()
    scenes = sg.generate_scenes("make a video")
    assert isinstance(scenes, list)
    assert len(scenes) > 0
    for s in scenes:
        assert 'caption_text' in s and 'description' in s and 'duration' in s


def test_scene_critic_mock():
    sg = SceneGeneratorAgent()
    sc = SceneCriticAgent()
    scenes = sg.generate_scenes("mock")
    improved = sc.improve_scenes(scenes)
    assert improved == scenes


def test_audio_agent_mock(tmp_path):
    cfg = get_config()
    # Point temp dir to tmp_path for this test to avoid pollution
    os.makedirs(cfg['temp_dir'], exist_ok=True)
    aa = AudioAgent()
    scenes = [{"caption_text": "hello world", "description": "desc", "duration": 2}]
    files = aa.generate_audio(scenes)
    assert len(files) == 1
    assert os.path.exists(files[0])


def test_video_agent_mock():
    va = VideoAgent()
    scenes = [{"caption_text": "hello world", "description": "desc", "duration": 1}]
    files = [""]
    out = va.assemble_video(scenes, files)
    assert out.endswith('.mp4')
    assert os.path.exists(out) 