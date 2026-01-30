
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\faturamento\templates\faturamento\nota_entrada_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The exact strings from the error log (again)
    replacements = {
        "{% if status_filter=='IMPORTADA' %}": "{% if status_filter == 'IMPORTADA' %}",
        "{% if status_filter=='LANCADA' %}": "{% if status_filter == 'LANCADA' %}",
        "{% if status_filter=='CANCELADA' %}": "{% if status_filter == 'CANCELADA' %}"
    }

    new_content = content
    changes_made = 0
    for old, new in replacements.items():
        if old in new_content:
            new_content = new_content.replace(old, new)
            changes_made += 1

    if changes_made > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"File updated successfully. {changes_made} replacements made.")
    else:
        print("No matching patterns found.")

except Exception as e:
    print(f"Error: {e}")
