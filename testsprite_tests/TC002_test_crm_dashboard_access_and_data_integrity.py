import requests

BASE_URL = "https://web-production-34bc.up.railway.app"
TIMEOUT = 30


def test_crm_dashboard_access_and_data_integrity():
    headers = {
        "Accept": "application/json",
    }

    # Test /comercial/ endpoint (CRM Dashboard)
    resp_comercial = requests.get(f"{BASE_URL}/comercial/", headers=headers, timeout=TIMEOUT)
    assert resp_comercial.status_code == 200, f"/comercial/ status code expected 200 but got {resp_comercial.status_code}"
    comercial_json = resp_comercial.json()
    # Check keys related to clients, quotations, contracts expected to be in the response
    assert any(
        key in comercial_json for key in ("clients", "quotations", "contracts")
    ), "CRM Dashboard response should contain client, quotation, or contract data keys"

    # Test /operacional/ endpoint (Field Service Dashboard)
    resp_operacional = requests.get(f"{BASE_URL}/operacional/", headers=headers, timeout=TIMEOUT)
    assert resp_operacional.status_code == 200, f"/operacional/ status code expected 200 but got {resp_operacional.status_code}"
    operacional_json = resp_operacional.json()
    # Validate response contains expected operational data keys
    assert isinstance(operacional_json, dict), "/operacional/ response should be a JSON object"

    # Test /ai/processar/ endpoint (AI message triage) - POST with a sample payload
    payload = {"message": "Status of client contract #1234?"}
    resp_ai = requests.post(f"{BASE_URL}/ai/processar/", headers={**headers, "Content-Type": "application/json"},
                            json=payload, timeout=TIMEOUT)
    assert resp_ai.status_code == 200, f"/ai/processar/ POST status 200 expected but got {resp_ai.status_code}"
    ai_resp_json = resp_ai.json()
    # Validate AI response contains a reply or processing outcome
    assert (
        "response" in ai_resp_json or "result" in ai_resp_json
    ), "/ai/processar/ response should contain 'response' or 'result' key"

    # Test /financeiro/ endpoint (Finance Dashboard) - Expecting redirect (status 3xx)
    resp_financeiro = requests.get(f"{BASE_URL}/financeiro/", headers=headers, timeout=TIMEOUT, allow_redirects=False)
    assert resp_financeiro.status_code in (301, 302, 303, 307, 308), f"/financeiro/ expected redirect status but got {resp_financeiro.status_code}"
    location = resp_financeiro.headers.get("Location")
    assert location, "/financeiro/ redirect response should contain 'Location' header"


test_crm_dashboard_access_and_data_integrity()