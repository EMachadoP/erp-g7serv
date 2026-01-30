import os
import re

def collapse_tags(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # regex to find {{ ... }} and {% ... %} that span multiple lines
    def collapse_match(match):
        inner = match.group(1)
        # Collapse all whitespace/newlines into a single space
        collapsed = ' '.join(inner.split())
        start = match.group(0)[:2] # {{ or {%
        end = match.group(0)[-2:]   # }} or %}
        return f"{start} {collapsed} {end}"

    # Handle {{ ... }}
    content = re.sub(r'\{\{(.*?)\}\}', collapse_match, content, flags=re.DOTALL)
    # Handle {% ... %}
    content = re.sub(r'\{\%(.*?)\%\}', collapse_match, content, flags=re.DOTALL)
    
    if content != original_content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS: Collapsed tags in {path}")
    else:
        print(f"NO CHANGE: {path}")

files_to_fix = [
    r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\service_order_list.html",
    r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\operational_dashboard.html"
]

for f in files_to_fix:
    collapse_tags(f)
