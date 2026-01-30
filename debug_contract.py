import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import Contract
from comercial.views import replace_contract_variables

# Get the latest contract (or specific one if known, assuming ID 5 from context)
try:
    contract = Contract.objects.get(id=5)
    print(f"Contract ID: {contract.id}")
    print(f"Client: {contract.client.name}")
    print(f"Responsible Name: '{contract.client.responsible_name}'")
    
    template_content = contract.template.content
    print(f"\nTemplate Content Length: {len(template_content)}")
    
    # Find the placeholder in the raw content
    match = re.search(r'(.{0,50}{{.*?NOME.*?}}.{0,50})', template_content, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"\nFound placeholder context:\n{match.group(1)!r}")
    else:
        print("\nPlaceholder {{NOME...}} NOT found in template content!")
        
    # Test replacement
    new_content = replace_contract_variables(template_content, contract)
    
    # Check if replaced
    if contract.client.responsible_name in new_content:
        print(f"\nSUCCESS: Responsible name '{contract.client.responsible_name}' found in processed content.")
    else:
        print(f"\nFAILURE: Responsible name '{contract.client.responsible_name}' NOT found in processed content.")
        
    # Check Signature Date
    print(f"\nSignature Date Logic Check:")
    if '{{DATA_ASSINATURA}}' in template_content:
        print("{{DATA_ASSINATURA}} is present in template.")
    else:
        print("{{DATA_ASSINATURA}} is NOT present in template.")
        
    if '__________________' in new_content:
        print("Placeholder line '__________________' found in processed content.")
    else:
        print("Placeholder line '__________________' NOT found in processed content.")

except Contract.DoesNotExist:
    print("Contract ID 5 not found. Trying latest...")
    contract = Contract.objects.last()
    if contract:
        print(f"Using latest Contract ID: {contract.id}")
        # ... repeat logic or just fail if needed ...
    else:
        print("No contracts found.")
