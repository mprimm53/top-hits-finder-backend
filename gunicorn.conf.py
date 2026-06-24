# Gunicorn auto-loads ./gunicorn.conf.py regardless of the start command,
# so these settings apply even if Render's dashboard "Start Command" is just
# `gunicorn app:app` (which overrides the Procfile). Billboard scrapes are slow,
# so the default 30s worker timeout kills the request — raise it.
timeout = 120
workers = 2
graceful_timeout = 120
