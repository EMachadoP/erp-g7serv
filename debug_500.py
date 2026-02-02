import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from core.views import profile_create

def debug_view():
    rf = RequestFactory()
    request = rf.get('/perfis/novo/')
    
    # Get or create an admin user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("Creating temporary superuser...")
        user = User.objects.create_superuser('debug_admin', 'debug@example.com', 'pwd123')
    
    request.user = user
    
    # Mock messages and session
    setattr(request, '_messages', FallbackStorage(request))
    from django.contrib.sessions.middleware import SessionMiddleware
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

    print(f"Testing profile_create view for user: {request.user}")
    try:
        response = profile_create(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Successfully rendered 200")
            # Verify context or content
            if hasattr(response, 'context_data'):
                print(f"Context keys: {response.context_data.keys()}")
            
            # Since it's a TemplateResponse (from render), we might need to render it
            if hasattr(response, 'render'):
                response.render()
            
            if "Permissões de Acesso" in str(response.content):
                print("Found 'Permissões de Acesso' in content!")
            else:
                print("WARNING: Expected content not found in rendered output")
                # print(response.content[:500])
        else:
            print(f"Unexpected status code: {response.status_code}")
            if hasattr(response, 'url'):
                print(f"Redirect URL: {response.url}")
    except Exception as e:
        print("\n!!! ERROR CAPTURED !!!\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_view()
