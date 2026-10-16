from collections import defaultdict

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