#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Migrations completed successfully!"
echo "Starting Gunicorn on port ${PORT:-8000}..."

# Use exec to replace the shell process with Gunicorn
exec gunicorn erp.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
