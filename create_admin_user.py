import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin():
    username = 'admin'
    password = 'admin'
    email = 'admin@example.com'

    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"User '{username}' updated. Password set to '{password}'.")
    except User.DoesNotExist:
        User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' created with password '{password}'.")

if __name__ == '__main__':
    create_admin()
