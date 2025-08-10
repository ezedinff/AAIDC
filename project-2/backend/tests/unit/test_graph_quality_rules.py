import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from graph import VideoGeneratorGraph  # type: ignore


def make_scenes(captions):
    return [
        {"description": f"desc {i}", "caption_text": cap, "duration": 5}
        for i, cap in enumerate(captions)
    ]


def test_quality_rejects_short_and_long_captions():
    g = VideoGeneratorGraph()
    # Too short
    scenes = make_scenes(["short", "adequate caption text"])
    assert g._evaluate_scenes_quality(scenes, retry_count=0) is False
    # Too long
    long_cap = "x" * 200
    scenes = make_scenes([long_cap, "adequate caption text"])
    assert g._evaluate_scenes_quality(scenes, retry_count=0) is False


def test_quality_variety_rule():
    g = VideoGeneratorGraph()
    scenes = make_scenes(["repeat", "repeat", "repeat", "repeat"])
    assert g._evaluate_scenes_quality(scenes, retry_count=0) is False


def test_quality_accepts_after_retry():
    g = VideoGeneratorGraph()
    scenes = make_scenes(["adequate content here", "another adequate caption"])
    assert g._evaluate_scenes_quality(scenes, retry_count=1) is True 