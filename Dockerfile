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
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Copy and set execution permissions for the entrypoint script
RUN chmod +x /app/run-migrations.sh

# Ensure migrations, superuser creation, and server start run in sequence
CMD ["/app/run-migrations.sh"]
