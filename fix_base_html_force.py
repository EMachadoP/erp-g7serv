
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\templates\base.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the incorrect blocks and their replacements
    
    # Block 1: Administrativo
    bad_admin = """{% if perms.comercial.view_person or perms.comercial.view_service or perms.estoque.view_product or
                perms.estoque.view_brand or perms.estoque.view_category or perms.auth.view_user or perms.auth.view_group
                %}"""
    good_admin = """{% if perms.comercial.view_person or perms.comercial.view_service or perms.estoque.view_product or perms.estoque.view_brand or perms.estoque.view_category or perms.auth.view_user or perms.auth.view_group %}"""
    
    # Block 2: Financeiro
    bad_fin = """{% if perms.financeiro.view_accountpayable or perms.financeiro.view_accountreceivable or
                perms.financeiro.view_receipt or perms.financeiro.view_budgetplan %}"""
    good_fin = """{% if perms.financeiro.view_accountpayable or perms.financeiro.view_accountreceivable or perms.financeiro.view_receipt or perms.financeiro.view_budgetplan %}"""

    new_content = content.replace(bad_admin, good_admin).replace(bad_fin, good_fin)

    if new_content == content:
        print("No changes needed or patterns not found.")
        # Debug: print what we found around the expected areas
        print("Surrounding text for Admin block:")
        start = content.find("Administrativo")
        print(content[start:start+300])
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")

except Exception as e:
    print(f"Error: {e}")
