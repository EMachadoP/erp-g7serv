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
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Run migrations and start gunicorn
# Note: Using sh -c to allow multiple commands
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 erp.wsgi:application"]
