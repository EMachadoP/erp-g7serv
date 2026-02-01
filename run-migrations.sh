#!/bin/sh
set -eu

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking for superuser creation..."
python create_admin.py

echo "Migrations and admin check completed successfully!"
echo "Starting Gunicorn on port ${PORT:-8000}..."

# Use exec to replace the shell process with Gunicorn (PID 1)
exec gunicorn erp.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
