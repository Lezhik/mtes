"""Unit tests for monitoring HTTP endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from mtes.monitoring.health_service import HealthService, StaticEvolutionSnapshotProvider
from mtes.monitoring.http_server import create_monitoring_app
from mtes.shared.types import EvolutionStatus


@pytest.fixture
def health_service() -> HealthService:
    mongo_client = MagicMock()
    mongo_client.ping = AsyncMock(return_value=True)
    return HealthService(
        mongo_client=mongo_client,
        evolution_provider=StaticEvolutionSnapshotProvider(
            evolution_status=EvolutionStatus.RUNNING,
            queue_depth=4,
            active_workers=1,
        ),
    )


def test_health_endpoint_returns_json(health_service: HealthService) -> None:
    app = create_monitoring_app(health_service)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["evolution_status"] == "RUNNING"
    assert body["queue_depth"] == 4


def test_metrics_endpoint_returns_prometheus_text(health_service: HealthService) -> None:
    app = create_monitoring_app(health_service)
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "mtes_generation_total" in response.text
