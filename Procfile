web: (python manage.py migrate || echo 'Migration failed'); python create_admin.py; gunicorn erp.wsgi:application --bind 0.0.0.0:$PORT
