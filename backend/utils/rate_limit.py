"""
rate_limit.py
=============
A tiny in-memory, per-IP sliding-window rate limiter.

Why: an unauthenticated scoring endpoint is a cheap denial-of-service target.
This is intentionally simple (a dict of timestamps) because the project runs
locally. In production, use Redis or a reverse-proxy limiter.
"""

import time
from collections import defaultdict, deque
from functools import wraps

from flask import request, jsonify

from backend.config import RATE_LIMIT_PER_MINUTE

_WINDOW_SECONDS = 60
_HITS = defaultdict(deque)


def _client_ip():
    """
    Best-effort client IP.

    NOTE: X-Forwarded-For is trivially spoofable and is only honoured here
    because the app runs behind a trusted local proxy in development.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit(limit_per_minute=None):
    """Decorator that returns HTTP 429 when the per-IP limit is exceeded."""
    limit = limit_per_minute or RATE_LIMIT_PER_MINUTE

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip = _client_ip()
            now = time.time()
            bucket = _HITS[ip]

            while bucket and now - bucket[0] > _WINDOW_SECONDS:
                bucket.popleft()

            if len(bucket) >= limit:
                response = jsonify({
                    "error": "rate_limited",
                    "message": "Too many requests. Please slow down and try again shortly.",
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(_WINDOW_SECONDS)
                return response

            bucket.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def reset_rate_limits():
    """Clear all buckets (used by tests)."""
    _HITS.clear()