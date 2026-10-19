from uuid import uuid4

from app.services.auth import create_access_token, verify_password
from conftest import login


def register(client, email="customer@example.com", **extra):
    return client.post("/api/auth/register", json={
        "email": email, "password": "TestPassword123!", **extra})


def test_registration_login_and_logout(anonymous_client):
    client = anonymous_client
    response = register(client)
    assert response.status_code == 201
    assert response.json()["role"] == "user" and "password_hash" not in response.json()
    record = client.app.state.users.by_email("customer@example.com")
    assert record["password_hash"] != "TestPassword123!"
    assert verify_password("TestPassword123!", record["password_hash"])
    assert login(client, "customer@example.com", "wrong-password").status_code == 401
    response = login(client, "customer@example.com")
    assert response.status_code == 200
    access_cookie = next(value for value in response.headers.get_list("set-cookie") if value.startswith("access_token="))
    assert "HttpOnly" in access_cookie and "SameSite=lax" in access_cookie
    assert "access_token" not in response.json()
    assert client.get("/api/auth/me").json()["email"] == "customer@example.com"
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_anonymous_requests_are_blocked(anonymous_client):
    client = anonymous_client
    missing = str(uuid4())
    for method, path in [
        ("GET", "/api/documents"), ("POST", "/api/documents"),
        ("DELETE", f"/api/documents/{missing}"),
        ("POST", "/api/chat"), ("POST", "/api/retrieve"),
        ("GET", f"/api/documents/{missing}/source"),
        ("GET", f"/api/documents/{missing}/chunks/{missing}")
    ]:
        assert client.request(method, path).status_code == 401
    assert client.get("/admin", follow_redirects=False).status_code == 303
    assert client.get(f"/sources/{missing}/{missing}", follow_redirects=False).status_code == 303
    assert client.get("/login").status_code == 200


def test_user_can_chat_and_read_sources_but_cannot_manage_documents(client):
    document = client.post("/api/documents", files={"file": ("policy.txt", b"NovaFiber has no data cap.")}).json()["document"]
    assert client.post("/api/auth/logout").status_code == 204
    assert register(client).status_code == 201
    assert login(client, "customer@example.com").status_code == 200
    response = client.post("/api/chat", json={"question": "Is there a data cap?"})
    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert client.get(source["passage_url"]).status_code == 200
    assert client.get(source["source_url"]).status_code == 200
    assert client.get(f"/api/documents/{document['document_id']}/chunks/{source['chunk_id']}").status_code == 200
    assert client.get("/api/documents").status_code == 403
    assert client.post("/api/documents", files={"file": ("other.txt", b"Other policy.")}).status_code == 403
    assert client.delete(f"/api/documents/{document['document_id']}").status_code == 403
    assert client.post("/api/retrieve", json={"question": "data cap"}).status_code == 403
    assert client.get("/admin").status_code == 403


def test_registration_cannot_choose_admin_and_duplicate_email_is_rejected(anonymous_client):
    assert register(anonymous_client, role="admin").status_code == 422
    assert register(anonymous_client).status_code == 201
    assert register(anonymous_client, email="CUSTOMER@example.com").status_code == 409
    assert anonymous_client.post("/api/auth/login", headers={"Origin": "https://other.example"},
        json={"email": "customer@example.com", "password": "TestPassword123!"}).status_code == 403


def test_csrf_is_required_for_authenticated_changes(client):
    csrf = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/chat", json={"question": "policy"}).status_code == 403
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.post("/api/chat", headers={"X-CSRF-Token": csrf, "Origin": "https://other.example"},
                       json={"question": "policy"}).status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    assert client.post("/api/chat", json={"question": "policy"}).status_code == 200


def test_expired_and_invalid_tokens_are_rejected(client):
    user = client.app.state.users.by_email("admin@example.com")
    expired = create_access_token(user["user_id"], client.app.state.settings.jwt_secret, "csrf", expires_minutes=-1)
    client.cookies.set("access_token", expired, domain="testserver.local", path="/")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("access_token", "invalid-token", domain="testserver.local", path="/")
    assert client.get("/api/auth/me").status_code == 401
