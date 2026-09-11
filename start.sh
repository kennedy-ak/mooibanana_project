#!/bin/bash

# Exit on any error
set -e

echo "Starting Django application..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# --- Gunicorn tuning -------------------------------------------------------
# Worker count: set WEB_CONCURRENCY to pin an exact number (recommended once you
# know the box's RAM). Otherwise auto = (2 x CPU cores) + 1, capped at 8 so a
# high-core VPS doesn't spawn dozens of ~200MB workers and run out of memory.
# Keep Gunicorn in the foreground: this script is the ExecStart of the systemd
# service (and the container CMD), so systemd / Docker owns supervision + logs.
if [ -n "${WEB_CONCURRENCY}" ]; then
    WORKERS="${WEB_CONCURRENCY}"
else
    WORKERS=$(( $(nproc) * 2 + 1 ))
    [ "${WORKERS}" -gt 8 ] && WORKERS=8
fi
PORT="${PORT:-8080}"

echo "Starting Gunicorn on 0.0.0.0:${PORT} with ${WORKERS} workers..."
exec gunicorn mooibanana_project.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --worker-class sync \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile -
