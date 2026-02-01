FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies for signxml (lxml), psycopg2, and xhtml2pdf
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libffi-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    pkg-config \
    libcairo2-dev \
    libxml2-dev \
    libxslt-dev \
    libxmlsec1-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Copy and set execution permissions for the entrypoint script
RUN chmod +x /app/run-migrations.sh

# Ensure migrations, superuser creation, and server start run in sequence (One-line failsafe)
CMD ["bash", "-lc", "python manage.py migrate --noinput && python create_admin.py && exec gunicorn erp.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -"]
