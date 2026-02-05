import os

path = 'financeiro/templates/financeiro/account_receivable_list.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the specific lines reported in the error
content = content.replace("status_filter=='PENDING'", "status_filter == 'PENDING'")
content = content.replace("status_filter=='RECEIVED'", "status_filter == 'RECEIVED'")
content = content.replace("status_filter=='OVERDUE'", "status_filter == 'OVERDUE'")
content = content.replace("status_filter=='CANCELLED'", "status_filter == 'CANCELLED'")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax errors in template.")
