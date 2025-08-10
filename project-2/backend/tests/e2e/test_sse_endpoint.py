import os
import time
import pytest
import requests
from sseclient import SSEClient

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore


@pytest.fixture(scope="module")
def base_url():
    # Launch app in a background thread using Flask built-in server is complex; instead, we hit test client
    # SSE requires a real HTTP server; skip if not available
    # We'll try to use environment variable API_URL if provided
    return os.getenv('TEST_API_URL', 'http://localhost:5000')


def test_sse_stream_smoke(base_url):
    # If server not running, skip
    try:
        r = requests.get(f"{base_url}/api/health", timeout=1)
        if r.status_code != 200:
            pytest.skip("API server not running for SSE test")
    except Exception:
        pytest.skip("API server not running for SSE test")

    # Create video via real server
    payload = {
        "title": "SSE Test",
        "description": "Testing SSE",
        "user_input": "Generate a mock video"
    }
    resp = requests.post(f"{base_url}/api/videos", json=payload, timeout=5)
    assert resp.status_code == 201
    vid = resp.json()['video']['id']

    # Connect to SSE
    resp = requests.get(f"{base_url}/api/videos/{vid}/events", stream=True, timeout=30)
    events = SSEClient(resp)
    count = 0
    for evt in events.events():
        if not evt.data:
            continue
        count += 1
        # Stop after a few events to keep test short
        if count >= 3:
            break
    assert count >= 1 