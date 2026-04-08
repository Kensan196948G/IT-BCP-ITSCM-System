"""API routes for monitoring, metrics, and health probes."""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

from apps.monitoring import health_checker, metrics_collector

router = APIRouter(tags=["monitoring"])


@router.get("/api/metrics", response_class=PlainTextResponse)
async def get_metrics() -> str:
    """Return application metrics in Prometheus exposition format."""
    m = metrics_collector.get_metrics()
    lines = [
        "# HELP itbcp_request_count Total number of HTTP requests",
        "# TYPE itbcp_request_count counter",
        f'itbcp_request_count {m["request_count"]}',
        "",
        "# HELP itbcp_request_duration_seconds Total request processing time",
        "# TYPE itbcp_request_duration_seconds counter",
        f'itbcp_request_duration_seconds {m["request_duration_seconds"]}',
        "",
        "# HELP itbcp_error_count Total number of error responses",
        "# TYPE itbcp_error_count counter",
        f'itbcp_error_count {m["error_count"]}',
        "",
        "# HELP itbcp_error_rate Ratio of error responses to total requests",
        "# TYPE itbcp_error_rate gauge",
        f'itbcp_error_rate {m["error_rate"]}',
        "",
        "# HELP itbcp_average_duration_seconds Average request duration",
        "# TYPE itbcp_average_duration_seconds gauge",
        f'itbcp_average_duration_seconds {m["average_duration_seconds"]}',
        "",
        "# HELP itbcp_active_incidents Number of active incidents",
        "# TYPE itbcp_active_incidents gauge",
        f'itbcp_active_incidents {m["active_incidents"]}',
        "",
        "# HELP itbcp_uptime_seconds Application uptime in seconds",
        "# TYPE itbcp_uptime_seconds gauge",
        f'itbcp_uptime_seconds {m["uptime_seconds"]}',
        "",
    ]
    return "\n".join(lines)


@router.get("/api/health/ready")
async def readiness_probe() -> JSONResponse:
    """Kubernetes-compatible readiness probe.

    Returns 200 when all dependencies are healthy, 503 otherwise so that
    Kubernetes stops routing traffic to a pod whose database or cache is down.
    """
    result = await health_checker.get_readiness()
    status_code = 200 if result["status"] == "ready" else 503
    return JSONResponse(content=result, status_code=status_code)


@router.get("/api/health/live")
async def liveness_probe() -> dict[str, Any]:
    """Kubernetes-compatible liveness probe."""
    return health_checker.get_liveness()


@router.get("/api/health/detailed")
async def detailed_health() -> dict[str, Any]:
    """Detailed health information including metrics and system resources."""
    readiness = await health_checker.get_readiness()
    details = metrics_collector.get_health_details()
    return {
        "status": readiness["status"],
        "checks": readiness["checks"],
        "metrics": details["metrics"],
        "system": details["system"],
    }
