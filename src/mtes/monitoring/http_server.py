"""Embeddable HTTP server for health and metrics endpoints."""

from collections.abc import Awaitable, Callable

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mtes.monitoring import metrics_registry as _metrics_registry  # noqa: F401 — register collectors
from mtes.monitoring.health_service import HealthService

RouteHandler = Callable[[Request], Awaitable[Response]]


def create_monitoring_app(health_service: HealthService) -> Starlette:
    """Create a Starlette app exposing GET /health and GET /metrics."""

    async def health_endpoint(request: Request) -> Response:
        del request
        payload = await health_service.build_health_response()
        return JSONResponse(payload)

    async def metrics_endpoint(request: Request) -> Response:
        del request
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return Starlette(
        routes=[
            Route("/health", endpoint=health_endpoint, methods=["GET"]),
            Route("/metrics", endpoint=metrics_endpoint, methods=["GET"]),
        ],
    )


async def serve_monitoring(
    health_service: HealthService,
    *,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Run uvicorn until process shutdown."""
    import uvicorn

    app = create_monitoring_app(health_service)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
