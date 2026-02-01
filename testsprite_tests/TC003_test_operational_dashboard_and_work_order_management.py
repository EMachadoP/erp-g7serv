import requests
import uuid

BASE_URL = "https://web-production-34bc.up.railway.app"
TIMEOUT = 30
HEADERS = {
    "Content-Type": "application/json"
}

def test_operational_dashboard_and_work_order_management():
    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Verify access to /operacional/ dashboard (GET)
    resp_dashboard = session.get(f"{BASE_URL}/operacional/", timeout=TIMEOUT)
    assert resp_dashboard.status_code == 200, f"Expected 200 OK for /operacional/, got {resp_dashboard.status_code}"

    # 2. Create a client under /comercial/clientes/ to link OS (POST)
    client_payload = {
        "name": f"Test Client {uuid.uuid4()}",
        "type": "individual",
        "document": "12345678900",
        "email": "testclient@example.com",
        "phone": "+5511999999999",
        "address": "123 Test St."
    }
    resp_client = session.post(f"{BASE_URL}/comercial/clientes/", json=client_payload, timeout=TIMEOUT)
    assert resp_client.status_code == 201, f"Expected 201 Created for /comercial/clientes/, got {resp_client.status_code}"
    client_id = resp_client.json().get("id")
    assert client_id is not None, "Client creation response missing id"

    try:
        # 3. Create a work order (OS) linked to client (POST)
        os_payload = {
            "client_id": client_id,
            "description": "Test Work Order",
            "status": "pending"  # initial state as per core goals
        }
        resp_os_create = session.post(f"{BASE_URL}/operacional/os/", json=os_payload, timeout=TIMEOUT)
        assert resp_os_create.status_code == 201, f"Expected 201 Created for /operacional/os/, got {resp_os_create.status_code}"
        os_data = resp_os_create.json()
        os_id = os_data.get("id")
        assert os_id is not None, "Work order creation response missing id"
        assert os_data.get("status") == "pending", f"Expected work order initial status 'pending', got {os_data.get('status')}"

        # 4. Transition state: pending -> in_progress (PUT)
        update_state_payload = {"status": "in_progress"}
        resp_update_state = session.put(f"{BASE_URL}/operacional/os/{os_id}/", json=update_state_payload, timeout=TIMEOUT)
        assert resp_update_state.status_code == 200, f"Expected 200 OK updating OS status, got {resp_update_state.status_code}"
        updated_os = resp_update_state.json()
        assert updated_os.get("status") == "in_progress", f"Expected OS status 'in_progress', got {updated_os.get('status')}"

        # 5. Record geolocation on check-in (PATCH)
        geolocation_checkin = {
            "check_in_location": {
                "lat": -23.55052,
                "lng": -46.633308
            },
            "check_in_time": "2026-01-31T10:00:00Z"
        }
        resp_checkin = session.patch(f"{BASE_URL}/operacional/os/{os_id}/", json=geolocation_checkin, timeout=TIMEOUT)
        assert resp_checkin.status_code == 200, f"Expected 200 OK for geolocation check-in, got {resp_checkin.status_code}"
        os_after_checkin = resp_checkin.json()
        assert "check_in_location" in os_after_checkin, "check_in_location missing after check-in update"
        assert os_after_checkin.get("check_in_location") == geolocation_checkin["check_in_location"], "check_in_location data mismatch"

        # 6. Validate checklist on check-in (PATCH)
        checklist_checkin = {
            "checklist": {
                "safety_gear": True,
                "equipment_checked": True,
                "client_informed": True
            }
        }
        resp_checklist_in = session.patch(f"{BASE_URL}/operacional/os/{os_id}/", json=checklist_checkin, timeout=TIMEOUT)
        assert resp_checklist_in.status_code == 200, f"Expected 200 OK for checklist update on check-in, got {resp_checklist_in.status_code}"
        os_after_checklist_in = resp_checklist_in.json()
        assert os_after_checklist_in.get("checklist") == checklist_checkin["checklist"], "Checklist data mismatch on check-in"

        # 7. Transition state: in_progress -> completed (PUT)
        resp_update_state_done = session.put(f"{BASE_URL}/operacional/os/{os_id}/", json={"status": "completed"}, timeout=TIMEOUT)
        assert resp_update_state_done.status_code == 200, f"Expected 200 OK updating OS status to completed, got {resp_update_state_done.status_code}"
        os_done = resp_update_state_done.json()
        assert os_done.get("status") == "completed", f"Expected OS status 'completed', got {os_done.get('status')}"

        # 8. Record geolocation on check-out (PATCH)
        geolocation_checkout = {
            "check_out_location": {
                "lat": -23.55100,
                "lng": -46.634000
            },
            "check_out_time": "2026-01-31T12:00:00Z"
        }
        resp_checkout = session.patch(f"{BASE_URL}/operacional/os/{os_id}/", json=geolocation_checkout, timeout=TIMEOUT)
        assert resp_checkout.status_code == 200, f"Expected 200 OK for geolocation check-out, got {resp_checkout.status_code}"
        os_after_checkout = resp_checkout.json()
        assert "check_out_location" in os_after_checkout, "check_out_location missing after check-out update"
        assert os_after_checkout.get("check_out_location") == geolocation_checkout["check_out_location"], "check_out_location data mismatch"

        # 9. Validate checklist on check-out (PATCH)
        checklist_checkout = {
            "checklist": {
                "work_reported": True,
                "client_signature": True,
                "equipment_cleaned": True
            }
        }
        resp_checklist_out = session.patch(f"{BASE_URL}/operacional/os/{os_id}/", json=checklist_checkout, timeout=TIMEOUT)
        assert resp_checklist_out.status_code == 200, f"Expected 200 OK for checklist update on check-out, got {resp_checklist_out.status_code}"
        os_after_checklist_out = resp_checklist_out.json()
        assert os_after_checklist_out.get("checklist") == checklist_checkout["checklist"], "Checklist data mismatch on check-out"

    finally:
        # Cleanup: delete created work order and client resources
        if 'os_id' in locals():
            session.delete(f"{BASE_URL}/operacional/os/{os_id}/", timeout=TIMEOUT)
        if client_id:
            session.delete(f"{BASE_URL}/comercial/clientes/{client_id}/", timeout=TIMEOUT)

    # 10. Verify redirects for /comercial/, /financeiro/, and /ai/processar/

    # /comercial/ dashboard GET
    resp_comercial = session.get(f"{BASE_URL}/comercial/", allow_redirects=False, timeout=TIMEOUT)
    assert resp_comercial.status_code in (200, 302), f"Unexpected status for /comercial/: {resp_comercial.status_code}"
    if resp_comercial.status_code == 302:
        assert "location" in resp_comercial.headers, "Redirect missing Location header for /comercial/"

    # /financeiro/ dashboard GET
    resp_financeiro = session.get(f"{BASE_URL}/financeiro/", allow_redirects=False, timeout=TIMEOUT)
    assert resp_financeiro.status_code in (200, 302), f"Unexpected status for /financeiro/: {resp_financeiro.status_code}"
    if resp_financeiro.status_code == 302:
        assert "location" in resp_financeiro.headers, "Redirect missing Location header for /financeiro/"

    # /ai/processar/ POST: test minimal valid payload and check for valid response
    ai_payload = {"message": "Status update request"}
    resp_ai = session.post(f"{BASE_URL}/ai/processar/", json=ai_payload, timeout=TIMEOUT)
    assert resp_ai.status_code == 200, f"Expected 200 OK for AI processing, got {resp_ai.status_code}"
    ai_response_json = resp_ai.json()
    assert isinstance(ai_response_json, dict), "AI response is not a JSON object"
    assert "response" in ai_response_json or "status" in ai_response_json, "AI response missing expected keys"


test_operational_dashboard_and_work_order_management()