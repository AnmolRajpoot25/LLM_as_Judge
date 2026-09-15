import pytest
from starlette.testclient import TestClient
from src.api.main import app
from src.database.connection import init_db
from src.providers.registry import model_registry
from src.providers.mock_provider import MockProvider


@pytest.fixture(scope="module", autouse=True)
def setup_db_and_providers():
    init_db()
    # Register mock provider for fast zero-cost local automated testing
    mock_prov = MockProvider()
    model_registry.register_provider(mock_prov)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_and_health(client):
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["platform"] == "LLM-Judge"

    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"


def test_get_models(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert data["total"] >= 10

    # Verify mock demo models are REMOVED from catalog
    mock_ids = [m["id"] for m in data["models"] if m["provider"] == "mock"]
    assert len(mock_ids) == 0

    # Verify OpenRouter and Grok models are present
    providers = {m["provider"] for m in data["models"]}
    assert "openrouter" in providers
    assert "grok" in providers

    # Verify free tier openrouter models exist
    free_models = [m for m in data["models"] if "free" in m["id"].lower()]
    assert len(free_models) >= 3


def test_generate_compare_validation_errors(client):
    # 0 models -> 422
    r0 = client.post("/api/generate-compare", json={
        "models": [],
        "prompt": "Explain merge sort"
    })
    assert r0.status_code == 422

    # 5 models -> 422
    r5 = client.post("/api/generate-compare", json={
        "models": ["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d", "extra:model"],
        "prompt": "Explain merge sort"
    })
    assert r5.status_code == 422

    # Duplicate models -> 422
    r_dup = client.post("/api/generate-compare", json={
        "models": ["mock:model-a", "mock:model-a"],
        "prompt": "Explain merge sort"
    })
    assert r_dup.status_code == 422

    # Empty prompt -> 422
    r_empty = client.post("/api/generate-compare", json={
        "models": ["mock:model-a", "mock:model-b"],
        "prompt": "   "
    })
    assert r_empty.status_code == 422


def test_generate_single_model_execution(client):
    """Test generating output from a single model without pairwise judge comparison."""
    r = client.post("/api/generate-compare", json={
        "models": ["mock:model-a"],
        "prompt": "Explain quicksort in one sentence."
    })
    assert r.status_code == 200
    report = r.json()
    assert report["mode"] == "SINGLE_GENERATION"
    assert report["status"] == "COMPLETED"
    assert len(report["answers"]) == 1
    assert len(report["pairwise_comparisons"]) == 0
    assert len(report["rankings"]) == 1
    assert report["rankings"][0]["rank"] == 1
    assert report["rankings"][0]["model_id"] == "model-a"
    assert report["metrics"]["total_session_latency_seconds"] >= 0


def test_generate_compare_execution_2_models(client):
    r = client.post("/api/generate-compare", json={
        "models": ["mock:model-a", "mock:model-b"],
        "prompt": "Explain LRU cache eviction policy"
    })
    assert r.status_code == 200
    report = r.json()
    assert report["mode"] == "GENERATE_AND_COMPARE"
    assert report["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
    assert len(report["answers"]) == 2
    assert len(report["pairwise_comparisons"]) == 1
    assert len(report["rankings"]) == 2
    assert report["metrics"]["total_session_latency_seconds"] > 0


def test_manual_compare_execution(client):
    r = client.post("/api/manual-compare", json={
        "problem": "Write a python function to check prime numbers.",
        "answers": [
            {"model_name": "Solution A", "answer": "def is_prime(n):\n    return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5)+1))"},
            {"model_name": "Solution B", "answer": "def is_prime(n):\n    return n % 2 != 0"}
        ]
    })
    assert r.status_code == 200
    report = r.json()
    assert report["mode"] == "MANUAL_COMPARE"
    assert report["status"] == "COMPLETED"
    assert len(report["answers"]) == 2
    assert len(report["pairwise_comparisons"]) == 1
    assert len(report["rankings"]) == 2
    # Verify winner is Solution A (more accurate prime check)
    assert report["rankings"][0]["model_name"] == "Solution A"


def test_session_save_and_retrieve(client):
    # Run a manual compare first
    r = client.post("/api/manual-compare", json={
        "problem": "Explain CAP theorem",
        "answers": [
            {"model_name": "Candidate A", "answer": "CAP theorem states Consistency, Availability, Partition tolerance trade-offs."},
            {"model_name": "Candidate B", "answer": "CAP theorem is about caching and persistence."}
        ]
    })
    assert r.status_code == 200
    report = r.json()
    sess_id = report["session_id"]

    # Save session with custom options
    save_res = client.post(f"/api/sessions/{sess_id}/save", json={
        "save_options": {
            "prompt": True,
            "answers": True,
            "evaluations": True,
            "metrics": True,
            "raw_responses": False
        },
        "session_data": report
    })
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # Retrieve saved session
    get_res = client.get(f"/api/sessions/{sess_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()["data"]
    assert retrieved["session_id"] == sess_id
    assert retrieved["input"]["prompt"] == "Explain CAP theorem"
    assert len(retrieved["answers"]) == 2
    assert len(retrieved["pairwise_comparisons"]) == 1

    # List sessions
    list_res = client.get("/api/sessions")
    assert list_res.status_code == 200
    assert any(s["session_id"] == sess_id for s in list_res.json()["data"])
