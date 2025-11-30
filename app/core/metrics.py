from __future__ import annotations

import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def _get_path_template(request: Request) -> str:
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path  # type: ignore[return-value]
    return request.url.path


def register_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
        start_time = time.perf_counter()
        response: Optional[Response] = None
        status_code = "500"
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            duration = time.perf_counter() - start_time
            path = _get_path_template(request)
            method = request.method
            HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status_code=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, path=path, status_code=status_code
            ).observe(duration)

    @app.get("/metrics")
    async def metrics() -> Response:
        data = generate_latest()
        return PlainTextResponse(content=data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
