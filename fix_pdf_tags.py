import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\checklist_pdf_template.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure company name tag is clean and on one line
content = content.replace(
    '<div style="font-weight: bold; color: #0d6efd; font-size: 24px;">{{ company.name|default:"Descartex"\n                        }}</div>',
    '<div style="font-weight: bold; color: #0d6efd; font-size: 24px;">{{ company.name|default:"Descartex" }}</div>'
)

# Alternative split pattern if the first one fails
content = content.replace(
    '{{ company.name|default:"Descartex"\n                        }}',
    '{{ company.name|default:"Descartex" }}'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Template tags fixed.")
