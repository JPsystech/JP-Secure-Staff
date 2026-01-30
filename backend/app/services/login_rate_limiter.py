"""
Simple in-memory rate limiter for /api/v1/auth/login.
Per IP: max 10 attempts per 5 minutes. Returns 429 when exceeded.
"""
import time
import threading
from collections import defaultdict

# (ip -> list of attempt timestamps)
_attempts: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()
WINDOW_SECONDS = 300  # 5 minutes
MAX_ATTEMPTS = 10


def is_rate_limited(ip: str) -> bool:
    """True if this IP has exceeded the limit."""
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        _attempts[ip] = [t for t in _attempts[ip] if t > cutoff]
        if len(_attempts[ip]) >= MAX_ATTEMPTS:
            return True
        _attempts[ip].append(now)
    return False


def get_client_ip(request) -> str:
    """Get client IP from request."""
    if hasattr(request, "client") and request.client:
        host = request.client.host
    else:
        host = "unknown"
    forwarded = getattr(request, "headers", None) and request.headers.get("X-Forwarded-For")
    if forwarded:
        host = forwarded.split(",")[0].strip()
    return host or "unknown"
