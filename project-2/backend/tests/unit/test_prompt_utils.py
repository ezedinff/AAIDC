import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from prompt_utils import prompt_manager  # type: ignore


def test_scene_generation_prompt_contains_input():
    p = prompt_manager.get_scene_generation_prompt('coffee video', scene_count=3, video_duration=30)
    assert isinstance(p, str) and 'coffee video' in p


def test_scene_critique_prompt_non_empty():
    scenes = [{"description": "d", "caption_text": "cap", "duration": 5}]
    p = prompt_manager.get_scene_critique_prompt(scenes)
    assert isinstance(p, str) and len(p) > 0


def test_audio_generation_prompt_non_empty():
    scene = {"description": "d", "caption_text": "cap", "duration": 5}
    p = prompt_manager.get_audio_generation_prompt(scene)
    assert isinstance(p, str) and len(p) > 0 