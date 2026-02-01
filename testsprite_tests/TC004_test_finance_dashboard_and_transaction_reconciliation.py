import requests

BASE_URL = "https://web-production-34bc.up.railway.app"
TIMEOUT = 30


def test_finance_dashboard_and_transaction_reconciliation():
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "ERP-G7Serv-TestClient/1.0"
    })

    # Verify CRM dashboard accessible and functional (/comercial/)
    resp_comercial = session.get(f"{BASE_URL}/comercial/", timeout=TIMEOUT, allow_redirects=True)
    assert resp_comercial.status_code == 200, f"/comercial/ expected 200 but got {resp_comercial.status_code}"
    assert "application/json" in resp_comercial.headers.get("Content-Type", ""), "/comercial/ did not return JSON"
    comercial_json = resp_comercial.json()
    # Basic structural checks (assuming dashboard JSON has keys like clients, quotations, contracts)
    assert isinstance(comercial_json, dict), "/comercial/ response not dict"
    assert any(key in comercial_json for key in ["clients", "quotations", "contracts"]), "/comercial/ missing expected keys"

    # Verify Operational dashboard accessible and functional (/operacional/)
    resp_operacional = session.get(f"{BASE_URL}/operacional/", timeout=TIMEOUT, allow_redirects=True)
    assert resp_operacional.status_code == 200, f"/operacional/ expected 200 but got {resp_operacional.status_code}"
    assert "application/json" in resp_operacional.headers.get("Content-Type", ""), "/operacional/ did not return JSON"
    operacional_json = resp_operacional.json()
    # Expect keys related to work orders or statuses
    assert isinstance(operacional_json, dict), "/operacional/ response not dict"
    assert any(key in operacional_json for key in ["work_orders", "statuses"]), "/operacional/ missing expected keys"

    # Verify AI message processing endpoint (/ai/processar/)
    ai_payload = {"message": "Check finance report status", "query_type": "status_inquiry"}
    resp_ai = session.post(f"{BASE_URL}/ai/processar/", json=ai_payload, timeout=TIMEOUT)
    assert resp_ai.status_code == 200, f"/ai/processar/ POST expected 200 but got {resp_ai.status_code}"
    resp_ai_json = resp_ai.json()
    assert isinstance(resp_ai_json, dict), "/ai/processar/ response not dict"
    assert "response" in resp_ai_json or "result" in resp_ai_json, "/ai/processar/ missing expected keys"

    # Verify Finance dashboard accessible and functional (/financeiro/) - redirect expected
    resp_financeiro = session.get(f"{BASE_URL}/financeiro/", timeout=TIMEOUT, allow_redirects=True)
    # It can redirect; final status code expected 200
    assert resp_financeiro.status_code == 200, f"/financeiro/ expected 200 but got {resp_financeiro.status_code}"
    # Check JSON response with finance-related keys
    assert "application/json" in resp_financeiro.headers.get("Content-Type", ""), "/financeiro/ did not return JSON"
    financeiro_json = resp_financeiro.json()
    assert isinstance(financeiro_json, dict), "/financeiro/ response not dict"
    expected_finance_keys = ["cash_flow", "accounts_payable", "accounts_receivable", "bank_statements"]
    assert any(key in financeiro_json for key in expected_finance_keys), "/financeiro/ missing finance keys"

    # Additional checks for reconciliation consistency if data present
    cash_flow = financeiro_json.get("cash_flow", {})
    accounts_payable = financeiro_json.get("accounts_payable", {})
    accounts_receivable = financeiro_json.get("accounts_receivable", {})
    bank_statements = financeiro_json.get("bank_statements", {})

    # Basic type checks
    assert isinstance(cash_flow, dict) or isinstance(cash_flow, list), "cash_flow should be dict or list"
    assert isinstance(accounts_payable, dict) or isinstance(accounts_payable, list), "accounts_payable should be dict or list"
    assert isinstance(accounts_receivable, dict) or isinstance(accounts_receivable, list), "accounts_receivable should be dict or list"
    assert isinstance(bank_statements, dict) or isinstance(bank_statements, list), "bank_statements should be dict or list"

    # If numeric totals available, verify that cash flow roughly equals payables + receivables reconciled with bank statements
    # This part is heuristic due to lack of schema specifics
    def sum_amounts(items):
        if isinstance(items, dict):
            items = items.values()
        total = 0
        for entry in items:
            if isinstance(entry, dict):
                amount = entry.get("amount") or entry.get("value") or 0
            else:
                amount = 0
            try:
                total += float(amount)
            except (ValueError, TypeError):
                continue
        return total

    total_payable = sum_amounts(accounts_payable)
    total_receivable = sum_amounts(accounts_receivable)
    total_bank = sum_amounts(bank_statements)
    total_cash_flow = sum_amounts(cash_flow)

    # Rough consistency checks (amounts can be zero or missing)
    assert abs(total_cash_flow - (total_receivable - total_payable)) < 1e-2 or total_cash_flow == 0, \
        "cash_flow total inconsistent with receivables minus payables"
    # Bank statements should be roughly consistent with cash flow
    assert abs(total_bank - total_cash_flow) < 1e-2 or total_bank == 0, "bank_statements total inconsistent with cash_flow"

    session.close()


test_finance_dashboard_and_transaction_reconciliation()