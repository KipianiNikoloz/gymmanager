import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_metrics_endpoint(client: AsyncClient) -> None:
    # Trigger a request to generate metrics
    await client.get("/health")
    response = await client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


async def test_metrics_records_error_path(client: AsyncClient) -> None:
    await client.get("/does-not-exist")  # generate 404
    response = await client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'status_code="404"' in body
