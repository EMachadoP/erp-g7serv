#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Migrations completed successfully!"
echo "Starting Gunicorn..."

# Use exec to replace the shell process with Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 \
    --access-logfile - --error-logfile - erp.wsgi:application
