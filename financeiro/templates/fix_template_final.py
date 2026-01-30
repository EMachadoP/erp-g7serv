
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\financeiro\templates\financeiro\account_payable_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacements for bad syntax (missing spaces around ==)
    # Also manual fix for the split line 22/23
    
    # 1. The Supplier Options Split - Handling the specific split logic
    bad_supplier_split = """{% if request.GET.supplier==s.id|stringformat:"i" %}selected{% endif
                            %}>"""
    good_supplier_split = """{% if request.GET.supplier == s.id|stringformat:"i" %}selected{% endif %}>"""
    
    if bad_supplier_split in content:
        content = content.replace(bad_supplier_split, good_supplier_split)
        print("Fixed split supplier tag.")

    # 2. Generic Replacements for missing spaces
    replacements = {
        "request.GET.supplier==s.id": "request.GET.supplier == s.id",
        "status_filter=='PENDING'": "status_filter == 'PENDING'",
        "status_filter=='PAID'": "status_filter == 'PAID'",
        "status_filter=='OVERDUE'": "status_filter == 'OVERDUE'",
        "status_filter=='CANCELLED'": "status_filter == 'CANCELLED'",
    }
    
    count = 0
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            count += 1
            
    # 3. Fix potential split line for Cancelled if it exists (Step 1180 didn't show it split but line 34 looked wrapped)
    bad_cancelled_split = """{% if status_filter=='CANCELLED' %}selected{% endif %}>Canceladas
                        </option>"""
    good_cancelled_split = """{% if status_filter == 'CANCELLED' %}selected{% endif %}>Canceladas</option>"""
    
    if bad_cancelled_split in content:
        content = content.replace(bad_cancelled_split, good_cancelled_split)
        print("Fixed split cancelled option.")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Fixed {count} generic syntax errors.")

except Exception as e:
    print(f"Error: {e}")
