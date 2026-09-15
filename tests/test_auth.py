import uuid
import pytest
from starlette.testclient import TestClient
from src.api.main import app
from src.database.connection import init_db


from src.providers.registry import model_registry
from src.providers.mock_provider import MockProvider


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    model_registry.register_provider(MockProvider())


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_registration_and_validation(client):
    suffix = uuid.uuid4().hex[:6]
    username = f"evaluator_{suffix}"
    email = f"eval_{suffix}@evaluator.org"

    # Valid registration
    r = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "strongPassword123"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == username

    # Duplicate username
    r_dup_user = client.post("/api/auth/register", json={
        "username": username,
        "email": f"other_{suffix}@evaluator.org",
        "password": "strongPassword123"
    })
    assert r_dup_user.status_code == 400
    assert "already registered" in r_dup_user.json()["detail"]

    # Duplicate email
    r_dup_email = client.post("/api/auth/register", json={
        "username": f"other_usr_{suffix}",
        "email": email,
        "password": "strongPassword123"
    })
    assert r_dup_email.status_code == 400
    assert "already registered" in r_dup_email.json()["detail"]


def test_auth_login_and_me(client):
    suffix = uuid.uuid4().hex[:6]
    username = f"login_user_{suffix}"
    email = f"login_{suffix}@evaluator.org"

    # Register user
    client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "secretPassword"
    })

    # Login with username
    r_login = client.post("/api/auth/login", json={
        "username_or_email": username,
        "password": "secretPassword"
    })
    assert r_login.status_code == 200
    token = r_login.json()["token"]
    assert token

    # Login with email
    r_login_email = client.post("/api/auth/login", json={
        "username_or_email": email,
        "password": "secretPassword"
    })
    assert r_login_email.status_code == 200

    # Wrong password
    r_wrong = client.post("/api/auth/login", json={
        "username_or_email": username,
        "password": "wrongPassword"
    })
    assert r_wrong.status_code == 401

    # Protected me endpoint without token -> 401
    r_no_auth = client.get("/api/auth/me")
    assert r_no_auth.status_code == 401

    # Protected me endpoint with token -> 200
    r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    assert r_me.json()["user"]["username"] == username


def test_user_api_keys_management_and_masking(client):
    suffix = uuid.uuid4().hex[:6]
    username = f"keys_user_{suffix}"
    email = f"keys_{suffix}@evaluator.org"

    # Register and login user
    r_reg = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    assert r_reg.status_code == 200
    token = r_reg.json()["token"]

    # Initial keys check (all not set)
    r_get1 = client.get("/api/user/keys", headers={"Authorization": f"Bearer {token}"})
    assert r_get1.status_code == 200
    keys1 = r_get1.json()["keys"]
    assert keys1["openai"]["is_set"] is False

    # Save custom keys including openrouter and grok
    r_save = client.post("/api/user/keys", json={
        "keys": {
            "openai": "sk-proj-test1234567890abcdef",
            "gemini": "AIzaSyTestApiKey987654",
            "openrouter": "sk-or-v1-testopenrouter987654321",
            "grok": "xai-testgrokapikey123456789",
            "ollama": "http://127.0.0.1:11434"
        }
    }, headers={"Authorization": f"Bearer {token}"})
    assert r_save.status_code == 200

    # Retrieve keys and verify masking
    r_get2 = client.get("/api/user/keys", headers={"Authorization": f"Bearer {token}"})
    assert r_get2.status_code == 200
    keys2 = r_get2.json()["keys"]
    assert keys2["openai"]["is_set"] is True
    assert keys2["openai"]["masked_key"] == "sk-p...cdef"
    assert keys2["gemini"]["is_set"] is True
    assert keys2["gemini"]["masked_key"] == "AIza...7654"
    assert keys2["openrouter"]["is_set"] is True
    assert keys2["openrouter"]["masked_key"] == "sk-o...4321"
    assert keys2["grok"]["is_set"] is True
    assert keys2["grok"]["masked_key"] == "xai-...6789"
    assert keys2["ollama"]["is_set"] is True
    assert keys2["ollama"]["masked_key"] == "http://127.0.0.1:11434"

    # Test key endpoint
    r_test = client.post("/api/user/keys/test", json={
        "provider": "ollama",
        "api_key": "http://127.0.0.1:54321"  # dummy unreachable port
    }, headers={"Authorization": f"Bearer {token}"})
    assert r_test.status_code == 200
    assert r_test.json()["success"] is False


def test_generate_compare_with_custom_api_keys(client):
    suffix = uuid.uuid4().hex[:6]
    username = f"gen_key_user_{suffix}"
    email = f"genkey_{suffix}@evaluator.org"

    # Register user
    r_reg = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    assert r_reg.status_code == 200
    token = r_reg.json()["token"]

    # Call generate-compare with user token and custom_api_keys
    r_gen = client.post("/api/generate-compare", json={
        "models": ["mock:model-a", "mock:model-b"],
        "prompt": "Explain database indexing with B-Trees.",
        "custom_api_keys": {
            "mock": "mock-key-custom"
        }
    }, headers={"Authorization": f"Bearer {token}"})

    assert r_gen.status_code == 200
    report = r_gen.json()
    assert report["mode"] == "GENERATE_AND_COMPARE"
    assert len(report["answers"]) == 2
    assert len(report["pairwise_comparisons"]) == 1


def test_authenticated_session_save_and_user_isolation(client):
    suffix1 = uuid.uuid4().hex[:6]
    suffix2 = uuid.uuid4().hex[:6]

    # User 1
    r1 = client.post("/api/auth/register", json={
        "username": f"user1_{suffix1}",
        "email": f"user1_{suffix1}@evaluator.org",
        "password": "password123"
    })
    token1 = r1.json()["token"]

    # User 2
    r2 = client.post("/api/auth/register", json={
        "username": f"user2_{suffix2}",
        "email": f"user2_{suffix2}@evaluator.org",
        "password": "password123"
    })
    token2 = r2.json()["token"]

    # User 1 runs a comparison and saves it
    cmp_res = client.post("/api/manual-compare", json={
        "problem": "Explain Python GIL",
        "answers": [
            {"model_name": "Ans A", "answer": "Global Interpreter Lock prevents concurrent execution."},
            {"model_name": "Ans B", "answer": "GIL is Python's garbage collector."}
        ]
    }, headers={"Authorization": f"Bearer {token1}"})
    assert cmp_res.status_code == 200
    rep1 = cmp_res.json()
    sid1 = rep1["session_id"]

    save_res = client.post(f"/api/sessions/{sid1}/save", json={
        "save_options": {"prompt": True, "answers": True},
        "session_data": rep1
    }, headers={"Authorization": f"Bearer {token1}"})
    assert save_res.status_code == 200

    # User 1 lists sessions -> sees their session
    list1 = client.get("/api/sessions", headers={"Authorization": f"Bearer {token1}"})
    assert list1.status_code == 200
    u1_ids = [s["session_id"] for s in list1.json()["data"]]
    assert sid1 in u1_ids

    # User 2 lists sessions -> does NOT see User 1's session
    list2 = client.get("/api/sessions", headers={"Authorization": f"Bearer {token2}"})
    assert list2.status_code == 200
    u2_ids = [s["session_id"] for s in list2.json()["data"]]
    assert sid1 not in u2_ids


def test_api_key_encryption_at_rest(client):
    from src.database.connection import SessionLocal
    from src.database.models import UserApiKeyRecord

    suffix = uuid.uuid4().hex[:6]
    r = client.post("/api/auth/register", json={
        "username": f"enc_user_{suffix}",
        "email": f"enc_{suffix}@evaluator.org",
        "password": "password123"
    })
    token = r.json()["token"]
    raw_secret = "sk-live-super-secret-key-12345678"

    # Save key via API
    r_save = client.post("/api/user/keys", json={
        "keys": {"openai": raw_secret}
    }, headers={"Authorization": f"Bearer {token}"})
    assert r_save.status_code == 200

    # Check database directly - must NOT be plaintext!
    db = SessionLocal()
    try:
        user_id = r.json()["user"]["id"]
        rec = db.query(UserApiKeyRecord).filter(
            UserApiKeyRecord.user_id == user_id,
            UserApiKeyRecord.provider == "openai"
        ).first()
        assert rec is not None
        assert rec.api_key.startswith("enc:")
        assert raw_secret not in rec.api_key  # Not stored in cleartext!
    finally:
        db.close()

