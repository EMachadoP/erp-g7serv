#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Migrations completed successfully!"
echo "Starting application: $*"

# Replace the shell with the real server process (PID 1)
exec "$@"
