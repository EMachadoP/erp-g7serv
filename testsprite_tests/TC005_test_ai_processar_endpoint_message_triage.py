import requests

BASE_URL = "https://web-production-34bc.up.railway.app"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_ai_processar_endpoint_message_triage():
    url = f"{BASE_URL}/ai/processar/"
    payloads = [
        # Sample message triage input
        {"message": "Request status update for order #12345"},
        # Sample AI status query
        {"message": "What is the current status of my service order?"},
        # Sample message expecting routing response
        {"message": "Please route this message to the finance department."},
    ]
    for payload in payloads:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException as e:
            assert False, f"Request to /ai/processar/ failed: {e}"
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        try:
            resp_json = response.json()
        except ValueError:
            assert False, "Response is not valid JSON"
        assert "result" in resp_json or "status" in resp_json or "route" in resp_json, \
            "Response JSON must contain 'result', 'status', or 'route' key"
        # Validate that the response content is a non-empty string/value
        if "result" in resp_json:
            assert isinstance(resp_json["result"], str) and resp_json["result"].strip() != "", "Invalid 'result' content"
        if "status" in resp_json:
            assert isinstance(resp_json["status"], str) and resp_json["status"].strip() != "", "Invalid 'status' value"
        if "route" in resp_json:
            assert isinstance(resp_json["route"], str) and resp_json["route"].strip() != "", "Invalid 'route' content"

test_ai_processar_endpoint_message_triage()
