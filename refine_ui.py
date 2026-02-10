import os
import re

def refine_ui_bulk(file_list):
    stats = {'fixed': 0, 'errors': 0}
    for path in file_list:
        if not os.path.exists(path):
            print(f"NOT FOUND: {path}")
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new = content
            # 1. Remove bg-light from thead if it's interfering with table-premium
            new = re.sub(r'<thead class="bg-light">', '<thead>', new)
            
            # 2. Add shadow-sm and py-2 to dropdowns
            new = re.sub(r'class="dropdown-menu dropdown-menu-end"', 'class="dropdown-menu dropdown-menu-end shadow-sm"', new)
            new = re.sub(r'class="dropdown-item"', 'class="dropdown-item py-2"', new)
            
            # 3. Standardize Ações button style if it uses gears or white buttons
            new = re.sub(r'btn-white border shadow-sm', 'btn-sm btn-outline-secondary', new)
            new = re.sub(r'<i class="bi bi-gear-fill[^>]*></i>', 'Ações', new)

            if content != new:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
                stats['fixed'] += 1
                print(f"REFINED: {path}")
            else:
                print(f"SKIPPED: {path}")
        except Exception as e:
            stats['errors'] += 1
            print(f"ERROR: {path} - {e}")
    print(f"\nDone: {stats['fixed']} fixed, {stats['errors']} errors.")

if __name__ == "__main__":
    # List of important templates to refine
    files = [
        r'comercial\templates\comercial\client_list.html',
        r'estoque\templates\estoque\product_list.html',
        r'financeiro\templates\financeiro\account_receivable_list.html',
        r'financeiro\templates\financeiro\account_payable_list.html',
        r'comercial\templates\comercial\budget_list.html',
        r'comercial\templates\comercial\billing_group_list.html'
    ]
    refine_ui_bulk(files)
