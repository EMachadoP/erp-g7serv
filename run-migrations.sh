#!/usr/bin/env bash
set -euo pipefail

echo "=== ENTRYPOINT: run-migrations.sh v2026-02-01-001 ==="
echo "PWD: $(pwd)"
echo "PORT=${PORT:-<empty>}"
echo "Python: $(python --version)"
echo "Listing /app:"
ls -la /app || true

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Migrations completed successfully!"
echo "Starting Gunicorn..."

# Use exec to replace the shell process with Gunicorn
exec gunicorn erp.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
