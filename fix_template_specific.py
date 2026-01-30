import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import Contract, ContractTemplate

try:
    contract = Contract.objects.get(id=5)
    template = contract.template
    print(f"Contract 5 uses Template ID: {template.id}, Name: {template.name}")
    
    content = template.content
    
    # Check if placeholder exists
    if '{{NOME_SÍNDICO_OU_RESPONSÁVEL}}' in content:
        print("Placeholder ALREADY EXISTS in template.")
    else:
        print("Placeholder MISSING. Adding it now...")
        # Add it after NOME_CLIENTE for visibility
        if '{{NOME_CLIENTE}}' in content:
             content = content.replace('{{NOME_CLIENTE}}', '{{NOME_CLIENTE}}<br>Síndico/Responsável: {{NOME_SÍNDICO_OU_RESPONSÁVEL}}')
        else:
             content += '<br>Síndico/Responsável: {{NOME_SÍNDICO_OU_RESPONSÁVEL}}'
             
    # Check Signature Date
    if '{{DATA_ASSINATURA}}' in content:
        print("Signature Date placeholder ALREADY EXISTS.")
    else:
        print("Signature Date placeholder MISSING. Adding it...")
        content += '<br><br>Recife, {{DATA_ASSINATURA}}'
        
    template.content = content
    template.save()
    print("Template updated successfully.")
    
    # Verify
    template.refresh_from_db()
    print(f"Verification - Placeholder present: {'{{NOME_SÍNDICO_OU_RESPONSÁVEL}}' in template.content}")

except Contract.DoesNotExist:
    print("Contract 5 not found.")
