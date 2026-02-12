web: (python manage.py migrate || echo 'Migration failed'); (python manage.py seed_importer || echo 'Seed failed'); gunicorn erp.wsgi:application --bind 0.0.0.0:$PORT
