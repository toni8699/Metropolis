"""Gunicorn configuration for production (Metropolis Nexus backend)."""

from __future__ import annotations

import multiprocessing
import os

# Bind
_port = os.environ.get("PORT", "8080")
bind = f"0.0.0.0:{_port}"

# Gunicorn + UvicornWorker serves metropolis.asgi:app (FastAPI + Socket.IO).
_cpu = multiprocessing.cpu_count()
_default_workers = max(2, (_cpu * 2) + 1)
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
workers = int(os.environ.get("WEB_CONCURRENCY", str(_default_workers)))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

# Lifecycle
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "50"))

# Logging (stdout/stderr for container platforms)
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
capture_output = True
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ASGI app (FastAPI + Socket.IO) — see metropolis/asgi.py
wsgi_app = os.environ.get("GUNICORN_APP", "metropolis.asgi:app")

# Proxy headers (set to 1 behind ALB/nginx/Render)
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "127.0.0.1")
proxy_protocol = os.environ.get("GUNICORN_PROXY_PROTOCOL", "0") == "1"
