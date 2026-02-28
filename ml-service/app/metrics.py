"""
Prometheus metrics middleware and endpoint.

Exposes /metrics endpoint with standard HTTP metrics:
- request_count (Counter)
- request_latency (Histogram)
- model_prediction_latency (Histogram)
- active_requests (Gauge)
"""

import time
import logging
from typing import Callable
from functools import wraps

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

logger = logging.getLogger(__name__)


# =============================================================================
# SIMPLE METRICS COLLECTOR (No external dependencies)
# =============================================================================

class MetricsCollector:
    """
    Lightweight metrics collector compatible with Prometheus text format.
    
    Does not require prometheus_client library.
    For production, replace with prometheus_client for full functionality.
    """
    
    def __init__(self):
        self.request_count = {}       # {(method, path, status): count}
        self.request_latency_sum = {} # {(method, path): sum_ms}
        self.request_latency_count = {}
        self.prediction_count = 0
        self.prediction_latency_sum = 0.0
        self.prediction_latency_count = 0
        self.active_requests = 0
        self.startup_time = time.time()
    
    def record_request(self, method: str, path: str, status: int, latency_ms: float):
        """Record an HTTP request."""
        key = (method, path, status)
        self.request_count[key] = self.request_count.get(key, 0) + 1
        
        latency_key = (method, path)
        self.request_latency_sum[latency_key] = self.request_latency_sum.get(latency_key, 0) + latency_ms
        self.request_latency_count[latency_key] = self.request_latency_count.get(latency_key, 0) + 1
    
    def record_prediction(self, latency_ms: float):
        """Record a model prediction."""
        self.prediction_count += 1
        self.prediction_latency_sum += latency_ms
        self.prediction_latency_count += 1
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus text format metrics."""
        lines = []
        
        # Request count
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        for (method, path, status), count in self.request_count.items():
            path_label = path.replace('"', '\\"')
            lines.append(f'http_requests_total{{method="{method}",path="{path_label}",status="{status}"}} {count}')
        
        # Request latency
        lines.append("# HELP http_request_duration_ms HTTP request duration in milliseconds")
        lines.append("# TYPE http_request_duration_ms summary")
        for (method, path), total in self.request_latency_sum.items():
            count = self.request_latency_count[(method, path)]
            avg = total / count if count > 0 else 0
            path_label = path.replace('"', '\\"')
            lines.append(f'http_request_duration_ms_sum{{method="{method}",path="{path_label}"}} {total:.2f}')
            lines.append(f'http_request_duration_ms_count{{method="{method}",path="{path_label}"}} {count}')
        
        # Prediction metrics
        lines.append("# HELP model_predictions_total Total model predictions")
        lines.append("# TYPE model_predictions_total counter")
        lines.append(f"model_predictions_total {self.prediction_count}")
        
        lines.append("# HELP model_prediction_duration_ms Model prediction duration in milliseconds")
        lines.append("# TYPE model_prediction_duration_ms summary")
        lines.append(f"model_prediction_duration_ms_sum {self.prediction_latency_sum:.2f}")
        lines.append(f"model_prediction_duration_ms_count {self.prediction_latency_count}")
        
        if self.prediction_latency_count > 0:
            avg_latency = self.prediction_latency_sum / self.prediction_latency_count
            lines.append(f"model_prediction_duration_ms_avg {avg_latency:.2f}")
        
        # Active requests
        lines.append("# HELP http_requests_active Current active HTTP requests")
        lines.append("# TYPE http_requests_active gauge")
        lines.append(f"http_requests_active {self.active_requests}")
        
        # Uptime
        uptime_seconds = time.time() - self.startup_time
        lines.append("# HELP process_uptime_seconds Process uptime in seconds")
        lines.append("# TYPE process_uptime_seconds counter")
        lines.append(f"process_uptime_seconds {uptime_seconds:.2f}")
        
        return "\n".join(lines) + "\n"


# Global metrics collector
metrics_collector = MetricsCollector()


def record_prediction_metric(func: Callable) -> Callable:
    """Decorator to record prediction metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        latency = (time.perf_counter() - start) * 1000
        metrics_collector.record_prediction(latency)
        return result
    return wrapper


# =============================================================================
# METRICS MIDDLEWARE
# =============================================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""
    
    SKIP_PATHS = {"/metrics"}  # Don't record metrics endpoint itself
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Skip metrics endpoint
        if path in self.SKIP_PATHS:
            return await call_next(request)
        
        metrics_collector.active_requests += 1
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Normalize path for metrics (avoid high cardinality)
            normalized_path = self._normalize_path(path)
            metrics_collector.record_request(method, normalized_path, response.status_code, latency_ms)
            
            return response
        finally:
            metrics_collector.active_requests -= 1
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path to avoid high cardinality metrics."""
        # Keep only known paths, normalize unknown ones
        known_paths = {"/predict", "/health", "/reload-models", "/docs", "/redoc", "/openapi.json"}
        return path if path in known_paths else "/other"


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    metrics_text = metrics_collector.get_prometheus_metrics()
    return PlainTextResponse(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )
