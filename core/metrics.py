from collections import defaultdict
from prometheus_client import Counter, Gauge, Histogram

_metrics = defaultdict(int)

def increment(metric_name, **labels):
    _metrics[metric_name] += 1

    key = metric_name

    if labels:
        labels_str = "_".join(f"{k}:{v}" for k, v in labels.items())
        key = f"{metric_name} | {labels_str}"
        _metrics[key] += 1

def get_metrics():
    return dict(_metrics)


http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method"],
)

http_requests_errors_total = Counter(
    "http_requests_errors_total",
    "Total number of requests with error status codes",
    ["method", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)