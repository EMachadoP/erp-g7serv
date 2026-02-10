import os
import re

def cleanup_templates(base_dir):
    stats = {'fixed': 0, 'errors': 0}
    for root, dirs, files in os.walk(base_dir):
        if '.git' in root or '.venv' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 1. Fix literal backslashes in attributes
                    # Replace class=\"...\" with class="..."
                    content = content.replace('\\"', '"')
                    
                    # 2. Merge multiline curly tags {{ ... }}
                    content = re.sub(r'\{\{([^}]*)\r?\n\s*([^}]*)\}\}', r'{{\1 \2}}', content)
                    content = re.sub(r'\{\{([^}]*)\r?\n\s*([^}]*)\}\}', r'{{\1 \2}}', content) # Run twice for safety
                    
                    # 3. Merge multiline percent tags {% ... %}
                    content = re.sub(r'\{%([^%}]*)\r?\n\s*([^%}]*)%\}', r'{%\1 \2%}', content)
                    content = re.sub(r'\{%([^%}]*)\r?\n\s*([^%}]*)%\}', r'{%\1 \2%}', content) # Run twice for safety

                    # 4. Final check for triple spaces or awkward gaps
                    content = re.sub(r' +', ' ', content)

                    if content != original_content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        stats['fixed'] += 1
                        print(f"FIXED: {path}")
                except Exception as e:
                    stats['errors'] += 1
                    print(f"ERROR: {path} - {e}")
    print(f"\nFinished: {stats['fixed']} files cleaned, {stats['errors']} errors.")

if __name__ == "__main__":
    cleanup_templates(os.getcwd())
