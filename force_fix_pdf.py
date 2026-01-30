import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\checklist_pdf_template.html'

if not os.path.exists(file_path):
    print("File not found")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Very aggressive replacement
old_tag = '{{ company.name|default:"G7 Serv"\n                        }}'
new_tag = '{{ company.name|default:"G7 Serv" }}'

if old_tag in content:
    content = content.replace(old_tag, new_tag)
    print("Found and replaced target tag.")
else:
    print("Target tag not found exactly. Trying regex-like replace...")
    import re
    content = re.sub(r'\{\{\s*company\.name\|default:"G7\s*Serv"\s*\}\}', '{{ company.name|default:"G7 Serv" }}', content, flags=re.MULTILINE | re.DOTALL)
    # Also check for the user's report `{{ mpany.name... }}`
    content = re.sub(r'\{\{\s*mpany\.name\|default:"G7\s*Serv"\s*\}\}', '{{ company.name|default:"G7 Serv" }}', content, flags=re.MULTILINE | re.DOTALL)

with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("File updated with newline normalization.")
