import os
import django
from django.template import Template, Context, TemplateSyntaxError
from django.conf import settings

# Setup minimal Django
if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
        }],
        INSTALLED_APPS=['django.contrib.humanize'], # Some templates might use it
    )
    django.setup()

def validate_template(path):
    print(f"Validating {path}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We need to simulate the environment a bit (extending base.html etc)
        # But we can just try to parse it. If it fails due to missing blocks or tags, we know it's a syntax issue.
        # However, Template(content) will fail if it uses tags not loaded.
        # A better way is to check the specific lines.
        
        # Let's try to parse it.
        Template(content)
        print("[OK] Template is valid.")
    except TemplateSyntaxError as e:
        print(f"[ERROR] TemplateSyntaxError: {e}")
    except Exception as e:
        print(f"[INFO] Other error (expected if base.html is missing): {e}")

if __name__ == "__main__":
    template_path = r"c:\Projetos\erp-g7serv\financeiro\templates\financeiro\financial_statement.html"
    if os.path.exists(template_path):
        validate_template(template_path)
    else:
        print(f"File not found: {template_path}")
