import requests

BASE_URL = "https://web-production-34bc.up.railway.app"
TIMEOUT = 30

def test_admin_login_access_control():
    # Attempt unauthenticated GET request to /admin/
    admin_url = f"{BASE_URL}/admin/"
    try:
        response = requests.get(admin_url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /admin/ failed: {e}"

    # We expect a redirect to login page (HTTP 302) or HTTP 200 login page but restricted
    # Django admin usually redirects to /admin/login/ if not authenticated
    # Accept either 200 or 302 but check if unauthenticated access does not show admin dashboard content
    assert response.status_code in (200, 302), f"Unexpected status code {response.status_code} for unauthenticated access"

    # If redirected, verify Location header points to login page
    if response.status_code == 302:
        location = response.headers.get("Location", "")
        assert location.endswith("/admin/login/?next=/admin/") or "/admin/login" in location, \
            f"Redirect location expected to be login page but was {location}"
    else:
        # 200 might be login page HTML, check that it contains login form but not admin content
        content = response.text.lower()
        assert ("login" in content or "username" in content) and "csrfmiddlewaretoken" in content, \
            "Unauthenticated access to /admin/ should show login page"

    # Attempt authorized access by logging in and then accessing /admin/
    # Since no credentials are given, try to authenticate with invalid and valid attempts if possible
    # This test only verifies access restriction and logging: simulate login attempt with invalid credentials
    login_url = f"{BASE_URL}/admin/login/"
    login_data = {
        "username": "invalid_user",
        "password": "wrong_password",
        "csrfmiddlewaretoken": None  # Will fetch from login page
    }

    session = requests.Session()

    # Fetch login page first to get csrf token
    try:
        login_page = session.get(login_url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /admin/login/ failed: {e}"

    assert login_page.status_code == 200, f"Expected 200 OK for login page, got {login_page.status_code}"

    # Extract csrfmiddlewaretoken from login page HTML
    import re
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
    assert match, "CSRF token not found on login page"
    csrf_token = match.group(1)
    login_data["csrfmiddlewaretoken"] = csrf_token

    headers = {
        "Referer": login_url
    }

    try:
        post_response = session.post(login_url, data=login_data, headers=headers, timeout=TIMEOUT, allow_redirects=False)
    except requests.RequestException as e:
        assert False, f"Login POST request failed: {e}"

    # Validate response implies failed login (should be 200 with form showing errors or redirect to login again)
    assert post_response.status_code in (200, 302), f"Unexpected status code after login attempt: {post_response.status_code}"

    if post_response.status_code == 302:
        # Redirect back to login page (login failure)
        location = post_response.headers.get("Location", "")
        assert "/admin/login/" in location, f"Expected redirect to login page after failed login but got {location}"
    else:
        # Response page after failed login should contain error message
        assert "please enter the correct username and password" in post_response.text.lower() or \
               "error" in post_response.text.lower(), "Expected login error message after failed login"

    # Confirm that after failed login, access to /admin/ is still restricted
    try:
        admin_resp_after_login = session.get(admin_url, timeout=TIMEOUT, allow_redirects=False)
    except requests.RequestException as e:
        assert False, f"Request to /admin/ after login attempt failed: {e}"
    assert admin_resp_after_login.status_code in (302, 200), \
        f"Expected 302 redirect or 200 on /admin/ access after failed login, got {admin_resp_after_login.status_code}"

    if admin_resp_after_login.status_code == 302:
        loc = admin_resp_after_login.headers.get("Location", "")
        assert loc.endswith("/admin/login/?next=/admin/") or "/admin/login" in loc, \
            f"Access to /admin/ after failed login must redirect to login page, got {loc}"
    else:
        # 200 may be login page again showing form
        content2 = admin_resp_after_login.text.lower()
        assert ("login" in content2 or "username" in content2) and "csrfmiddlewaretoken" in content2, \
            "Access to /admin/ after failed login should show login page"

test_admin_login_access_control()