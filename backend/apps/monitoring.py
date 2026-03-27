"""Monitoring infrastructure: metrics collection and health checking."""

import time
from threading import Lock


class MetricsCollector:
    """Collects application metrics for monitoring and observability."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.request_count: int = 0
        self.request_duration_seconds: float = 0.0
        self.error_count: int = 0
        self.active_incidents_gauge: int = 0
        self._start_time = time.time()

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
    ) -> None:
        """Record a single request's metrics.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP response status code
            duration: Request duration in seconds
        """
        with self._lock:
            self.request_count += 1
            self.request_duration_seconds += duration
            if status_code >= 400:
                self.error_count += 1

    def get_metrics(self) -> dict:
        """Return current metrics as a dictionary."""
        with self._lock:
            avg_duration = self.request_duration_seconds / self.request_count if self.request_count > 0 else 0.0
            error_rate = self.error_count / self.request_count if self.request_count > 0 else 0.0
            return {
                "request_count": self.request_count,
                "request_duration_seconds": round(self.request_duration_seconds, 6),
                "error_count": self.error_count,
                "error_rate": round(error_rate, 4),
                "average_duration_seconds": round(avg_duration, 6),
                "active_incidents": self.active_incidents_gauge,
                "uptime_seconds": round(time.time() - self._start_time, 2),
            }

    def get_health_details(self) -> dict:
        """Return detailed health information including mock system metrics."""
        metrics = self.get_metrics()
        # Mock CPU/memory values for demonstration purposes
        cpu_usage = min(25.0 + (self.request_count % 50) * 0.5, 95.0)
        memory_usage = min(40.0 + (self.request_count % 30) * 0.3, 90.0)
        return {
            "metrics": metrics,
            "system": {
                "cpu_usage_percent": round(cpu_usage, 1),
                "memory_usage_percent": round(memory_usage, 1),
                "disk_usage_percent": 35.2,
            },
        }


class HealthChecker:
    """Performs health checks on application dependencies."""

    def check_database(self) -> dict:
        """Check database connectivity (mock: always OK)."""
        return {
            "name": "database",
            "status": "healthy",
            "latency_ms": 1.2,
        }

    def check_redis(self) -> dict:
        """Check Redis connectivity (mock: always OK)."""
        return {
            "name": "redis",
            "status": "healthy",
            "latency_ms": 0.5,
        }

    def check_all(self) -> list[dict]:
        """Check all components and return list of results."""
        return [
            self.check_database(),
            self.check_redis(),
        ]

    def get_readiness(self) -> dict:
        """Readiness probe: returns ok only when all dependencies are healthy."""
        checks = self.check_all()
        all_healthy = all(c["status"] == "healthy" for c in checks)
        return {
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
        }

    def get_liveness(self) -> dict:
        """Liveness probe: returns ok if the application process is alive."""
        return {
            "status": "alive",
        }


# Module-level singleton instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
