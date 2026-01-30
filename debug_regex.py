import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from comercial.models import Contract

try:
    contract = Contract.objects.get(id=5)
    content = contract.template.content
    
    print(f"Checking Contract {contract.id}")
    
    # Find all occurrences of "Síndico/Responsável"
    indices = [m.start() for m in re.finditer(r'Síndico/Responsável', content)]
    
    print(f"Found {len(indices)} occurrences of 'Síndico/Responsável'")
    
    for i, idx in enumerate(indices):
        print(f"\n--- Occurrence {i+1} at index {idx} ---")
        # Grab a chunk around it
        chunk = content[idx:idx+100]
        print(f"Chunk: {repr(chunk)}")
        
        # Look for the placeholder in this chunk
        match = re.search(r'({{.*?}})', chunk)
        if match:
            placeholder = match.group(1)
            print(f"Found placeholder: '{placeholder}'")
            print(f"Hex dump: {' '.join('{:02x}'.format(ord(c)) for c in placeholder)}")
            
            # Test regex
            regex_pattern = r'{{NOME[_\s]S[IÍ]NDICO[_\s]OU[_\s]RESPONS[AÁ]VEL}}'
            if re.search(regex_pattern, placeholder, re.IGNORECASE):
                print("Regex MATCHES!")
            else:
                print("Regex DOES NOT match!")
        else:
            print("No placeholder found immediately after.")

except Contract.DoesNotExist:
    print("Contract 5 not found.")
