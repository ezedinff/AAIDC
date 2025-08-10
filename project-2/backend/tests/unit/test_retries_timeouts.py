import os
import pytest

os.environ.setdefault("MOCK_MODE", "false")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from agents.scene_generator import SceneGeneratorAgent  # type: ignore
from agents.scene_critic import SceneCriticAgent  # type: ignore
from agents.audio_agent import AudioAgent  # type: ignore


class Flaky:
    def __init__(self, succeed_on=3):
        self.calls = 0
        self.succeed_on = succeed_on

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.calls < self.succeed_on:
            raise RuntimeError("temporary failure")
        # Minimal response mimic
        class Msg:
            content = "[ {\"description\": \"d\", \"caption_text\": \"adequate caption\", \"duration\": 5} ]"
        class Choice:
            message = Msg()
        class Resp:
            choices = [Choice()]
        return Resp()


def make_mock_chat(create_callable):
    class Cp:
        create = staticmethod(create_callable)
    class Ch:
        completions = Cp()
    class Client:
        chat = Ch()
    return Client()


def make_mock_tts(create_callable, chat_create_callable):
    class Speech:
        create = staticmethod(create_callable)
    class Audio:
        speech = Speech()
    class Cp:
        create = staticmethod(chat_create_callable)
    class Ch:
        completions = Cp()
    class Client:
        audio = Audio()
        chat = Ch()
    return Client()


def test_scene_generator_retries(monkeypatch):
    sg = SceneGeneratorAgent()
    flaky = Flaky(succeed_on=3)
    monkeypatch.setattr(sg, "mock_mode", False)
    monkeypatch.setattr(sg, "client", make_mock_chat(flaky))
    scenes = sg.generate_scenes("topic")
    assert isinstance(scenes, list) and len(scenes) >= 1
    assert flaky.calls >= 2


def test_scene_critic_retries(monkeypatch):
    sc = SceneCriticAgent()
    flaky = Flaky(succeed_on=3)
    monkeypatch.setattr(sc, "mock_mode", False)
    monkeypatch.setattr(sc, "client", make_mock_chat(flaky))
    improved = sc.improve_scenes([{ "description": "d", "caption_text": "adequate caption", "duration": 5 }])
    assert isinstance(improved, list) and len(improved) >= 1
    assert flaky.calls >= 2


def test_audio_agent_tts_retries(monkeypatch, tmp_path):
    aa = AudioAgent()
    monkeypatch.setattr(aa, "mock_mode", False)
    # chat completion returns narration immediately
    chat_resp = lambda **k: type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": "hello world"})()})]})()
    flaky_tts = Flaky(succeed_on=3)
    monkeypatch.setattr(aa, "client", make_mock_tts(flaky_tts, chat_resp))
    files = aa.generate_audio([{ "description": "d", "caption_text": "adequate caption", "duration": 1 }])
    assert len(files) == 1
    assert flaky_tts.calls >= 2 