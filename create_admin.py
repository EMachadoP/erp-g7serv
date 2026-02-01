import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Pega os dados das variáveis de ambiente do Railway
username = os.getenv('ADMIN_USERNAME', 'admin')
email = os.getenv('ADMIN_EMAIL', 'admin@g7serv.com.br')
password = os.getenv('ADMIN_PASSWORD', 'G7Serv2026!')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superusuário '{username}' criado com sucesso!")
else:
    print(f"Superusuário '{username}' já existe.")
