import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


def test_e2e_live_models_catalog():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        res = client.get("/api/models")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 19
        model_ids = [m["id"] for m in data["models"]]
        assert "mock:model-a" in model_ids
        assert "mock:model-b" in model_ids
        assert "mock:model-c" in model_ids
        assert "mock:model-d" in model_ids


def test_e2e_live_mode1_generate_3_models():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "models": ["mock:model-a", "mock:model-b", "mock:model-c"],
            "prompt": "Design a high-throughput distributed event streaming platform.",
            "system_prompt": "You are a senior distributed systems architect.",
            "generation_config": {"temperature": 0.5, "max_tokens": 1024},
            "position_swap_check": False
        }
        res = client.post("/api/generate-compare", json=payload)
        assert res.status_code == 200
        report = res.json()
        assert report["mode"] == "GENERATE_AND_COMPARE"
        assert report["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
        # 3 models -> 3 comparisons
        assert len(report["answers"]) == 3
        assert len(report["pairwise_comparisons"]) == 3
        assert len(report["rankings"]) == 3
        assert report["metrics"]["total_session_latency_seconds"] > 0
        assert report["metrics"]["generation"]["successful_models"] == 3


def test_e2e_live_mode1_generate_4_models():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "models": ["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d"],
            "prompt": "Implement consistent hashing algorithm with virtual nodes in Python.",
            "position_swap_check": False
        }
        res = client.post("/api/generate-compare", json=payload)
        assert res.status_code == 200
        report = res.json()
        # 4 models -> 6 comparisons
        assert len(report["answers"]) == 4
        assert len(report["pairwise_comparisons"]) == 6
        assert len(report["rankings"]) == 4
        assert report["rankings"][0]["rank"] == 1


def test_e2e_live_mode2_manual_compare_4_answers():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "problem": "Explain ACID properties in database management systems.",
            "answers": [
                {"model_name": "GPT-4.1", "answer": "Atomicity ensures all-or-nothing transactions. Consistency maintains invariants. Isolation prevents concurrency anomalies. Durability guarantees committed data survives crashes."},
                {"model_name": "Claude Sonnet", "answer": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Essential for relational transactional databases."},
                {"model_name": "Gemini Pro", "answer": "Atomicity, Consistency, Isolation, Durability. Implemented using write-ahead logs and MVCC."},
                {"model_name": "DeepSeek R1", "answer": "ACID properties govern database transactions ensuring correctness under failure and concurrent execution."}
            ],
            "position_swap_check": True
        }
        res = client.post("/api/manual-compare", json=payload)
        assert res.status_code == 200
        report = res.json()
        assert report["mode"] == "MANUAL_COMPARE"
        assert len(report["answers"]) == 4
        # 4 models -> 6 comparisons
        assert len(report["pairwise_comparisons"]) == 6
        assert len(report["rankings"]) == 4
        # Verify position swap check was executed
        assert report["pairwise_comparisons"][0]["position_swap_check"]["executed"] is True


def test_e2e_live_selective_save_and_history():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Run manual compare
        compare_payload = {
            "problem": "What is the time complexity of QuickSort average and worst case?",
            "answers": [
                {"model_name": "Candidate Alpha", "answer": "QuickSort average case is O(n log n). Worst case is O(n^2) when pivot selection is poor."},
                {"model_name": "Candidate Beta", "answer": "QuickSort is always O(n log n)."}
            ]
        }
        comp_res = client.post("/api/manual-compare", json=compare_payload)
        report = comp_res.json()
        session_id = report["session_id"]

        # Save selectively (save prompt, answers, evaluations; omit raw responses)
        save_payload = {
            "save_options": {
                "prompt": True,
                "answers": True,
                "evaluations": True,
                "metrics": True,
                "raw_responses": False
            },
            "session_data": report
        }
        save_res = client.post(f"/api/sessions/{session_id}/save", json=save_payload)
        assert save_res.status_code == 200
        assert save_res.json()["success"] is True

        # Retrieve saved session
        get_res = client.get(f"/api/sessions/{session_id}")
        assert get_res.status_code == 200
        saved_data = get_res.json()["data"]
        assert saved_data["session_id"] == session_id
        assert saved_data["input"]["prompt"] == compare_payload["problem"]
        assert len(saved_data["answers"]) == 2
        assert len(saved_data["pairwise_comparisons"]) == 1

        # Check list sessions includes it
        list_res = client.get("/api/sessions")
        assert list_res.status_code == 200
        all_sessions = list_res.json()["data"]
        assert any(s["session_id"] == session_id for s in all_sessions)
