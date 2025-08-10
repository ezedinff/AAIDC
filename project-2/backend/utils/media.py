import os
import subprocess


def compute_duration_from_file(file_path: str) -> float:
    """Try to read video duration from the actual file using ffprobe (ffmpeg).
    Returns duration in seconds, or 0.0 if unavailable.
    """
    try:
        if os.path.exists(file_path):
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                try:
                    duration = float(result.stdout.strip())
                    return duration
                except ValueError:
                    pass
    except Exception:
        pass
    return 0.0 