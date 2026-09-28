import httpx
from hindsight_client import Hindsight
from backend.config import settings


def test_hindsight_health():
    """Smoke test to verify GET /health returns HTTP 200 from Hindsight API."""
    health_url = f"{settings.hindsight_base_url.rstrip('/')}/health"
    response = httpx.get(health_url, timeout=5.0)
    assert response.status_code == 200, f"Expected 200 from {health_url}, got {response.status_code}"


def test_hindsight_client_instantiation():
    """Smoke test to verify hindsight_client.Hindsight imports and instantiates properly."""
    client = Hindsight(base_url=settings.hindsight_base_url)
    assert client is not None
    assert isinstance(client, Hindsight)
