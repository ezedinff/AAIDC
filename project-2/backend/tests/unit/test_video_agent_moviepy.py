import os
import pytest

from agents.video_agent import VideoAgent  # type: ignore


class StubClip:
    def __init__(self, duration=1):
        self.duration = duration
        self._audio = None
    def with_duration(self, d):
        self.duration = d
        return self
    def with_audio(self, a):
        self._audio = a
        return self
    def write_videofile(self, path, fps=24, codec='libx264', audio_codec='aac'):
        # Create an empty file to simulate output
        with open(path, 'wb') as f:
            f.write(b'video')
    def close(self):
        pass


class StubAudio:
    def __init__(self, path):
        self.duration = 1


def test_video_agent_with_stub_moviepy(monkeypatch):
    va = VideoAgent()
    # Force non-mock path
    monkeypatch.setattr(va, 'mock_mode', False)

    # Patch module-level moviepy symbols in agents.video_agent
    import agents.video_agent as vamod
    monkeypatch.setattr(vamod, 'MOVIEPY_AVAILABLE', True)
    monkeypatch.setattr(vamod, 'ImageClip', lambda img: StubClip())
    monkeypatch.setattr(vamod, 'AudioFileClip', lambda p: StubAudio(p))
    monkeypatch.setattr(vamod, 'concatenate_videoclips', lambda clips, method='compose': StubClip())

    scenes = [
        {"caption_text": "cap1", "description": "desc1", "duration": 1},
        {"caption_text": "cap2", "description": "desc2", "duration": 1}
    ]
    audio_files = ["/tmp/a1.mp3", "/tmp/a2.mp3"]

    out = va.assemble_video(scenes, audio_files)
    assert out.endswith('.mp4')
    assert os.path.exists(out)
    # cleanup
    try:
        os.remove(out)
    except Exception:
        pass 