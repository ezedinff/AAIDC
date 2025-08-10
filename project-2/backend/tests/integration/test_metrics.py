import os
import pytest

os.environ.setdefault("MOCK_MODE", "true")
from api import create_app  # type: ignore


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_metrics(client):
    rv = client.get('/api/metrics')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] is True
    assert 'counts' in data
    assert isinstance(data['counts'], dict) 