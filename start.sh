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

# Start gunicorn
echo "Starting Gunicorn..."
exec gunicorn mooibanana_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --worker-class sync \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile -