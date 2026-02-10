import os, re
def fix_templates(file_list):
    for path in file_list:
        try:
            with open(path, "r", encoding="utf-8") as f: content = f.read()
            new = re.sub(r"class=\"table(?!\s+table-premium)([^\\\"]*)\"", r"class=\"table table-premium\1\"", content)
            new = re.sub(r"data-bs-toggle=\"dropdown\"(?!\s+data-bs-boundary)", r"data-bs-toggle=\"dropdown\" data-bs-boundary=\"viewport\"", new)
            if content != new:
                with open(path, "w", encoding="utf-8") as f: f.write(new)
                print(f"FIXED: {path}")
            else:
                print(f"SKIPPED: {path}")
        except Exception as e: print(f"ERROR: {path} - {e}")

files = [
    r"comercial\templates\comercial\billing_group_list.html",
    r"comercial\templates\comercial\budget_list.html",
    r"comercial\templates\comercial\client_list.html",
    r"comercial\templates\comercial\contract_list.html",
    r"comercial\templates\comercial\contract_template_list.html",
    r"comercial\templates\comercial\service_list.html",
    r"core\templates\core\email_template_list.html",
    r"core\templates\core\profile_list.html",
    r"core\templates\core\technician_list.html",
    r"core\templates\core\user_list.html",
    r"estoque\templates\estoque\brand_list.html",
    r"estoque\templates\estoque\category_list.html",
    r"estoque\templates\estoque\inventory_list.html",
    r"estoque\templates\estoque\location_list.html",
    r"estoque\templates\estoque\movement_list.html",
    r"estoque\templates\estoque\product_list.html",
    r"faturamento\templates\faturamento\nota_entrada_list.html",
    r"financeiro\templates\financeiro\account_payable_list.html",
    r"financeiro\templates\financeiro\account_receivable_list.html",
    r"financeiro\templates\financeiro\cash_account_list.html",
    r"financeiro\templates\financeiro\cost_center_list.html",
    r"financeiro\templates\financeiro\financial_category_list.html",
    r"financeiro\templates\financeiro\receipt_list.html",
    r"nfse_nacional\templates\nfse_nacional\empresa_list.html",
    r"nfse_nacional\templates\nfse_nacional\nfse_list.html",
    r"operacional\templates\operacional\service_order_list.html"
]
fix_templates(files)
