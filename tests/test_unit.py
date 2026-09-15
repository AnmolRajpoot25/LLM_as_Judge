import pytest
import asyncio
from src.services.cost_calculator import CostCalculator
from src.services.generation_service import GenerationService, GenerationServiceError
from src.services.comparison_service import ComparisonService
from src.evaluation.pairwise import PairwiseEvaluator
from src.evaluation.ranking import RankingEngine
from src.providers.mock_provider import MockProvider
from src.providers.registry import ModelRegistry
from src.judge.model_loader import MockJudgeEvaluator


def test_cost_calculator():
    # Valid tokens
    cost = CostCalculator.calculate_cost("openai:gpt-4o", 1000, 2000)
    assert cost is not None
    # 1000/1M * 2.50 + 2000/1M * 10.00 = 0.0025 + 0.0200 = 0.0225
    assert cost == 0.0225

    # Missing tokens
    assert CostCalculator.calculate_cost("openai:gpt-4o", None, 100) is None
    assert CostCalculator.calculate_cost("openai:gpt-4o", 100, None) is None

    # Unknown model
    assert CostCalculator.calculate_cost("unknown:model", 100, 100) is None

    # Manual cost
    manual = CostCalculator.format_manual_cost()
    assert manual["estimated_cost"] is None
    assert manual["cost_source"] == "manual input"


def test_model_selection_validation():
    service = GenerationService()

    # 1 model rejected
    with pytest.raises(GenerationServiceError) as exc:
        service.validate_request(["mock:model-a"], "Valid prompt")
    assert "At least 2 models" in str(exc.value)

    # 5 models rejected
    with pytest.raises(GenerationServiceError) as exc:
        service.validate_request(
            ["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d", "extra:model"],
            "Valid prompt"
        )
    assert "At most 4 models" in str(exc.value)

    # Duplicate models rejected
    with pytest.raises(GenerationServiceError) as exc:
        service.validate_request(["mock:model-a", "mock:model-a"], "Valid prompt")
    assert "Duplicate models" in str(exc.value)

    # Empty prompt rejected
    with pytest.raises(GenerationServiceError) as exc:
        service.validate_request(["mock:model-a", "mock:model-b"], "   ")
    assert "Prompt cannot be empty" in str(exc.value)

    # 2, 3, 4 models accepted
    service.validate_request(["mock:model-a", "mock:model-b"], "Valid prompt")
    service.validate_request(["mock:model-a", "mock:model-b", "mock:model-c"], "Valid prompt")
    service.validate_request(["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d"], "Valid prompt")


@pytest.mark.asyncio
async def test_pairwise_combinations():
    evaluator = PairwiseEvaluator(judge=MockJudgeEvaluator())

    # 2 models -> 1 comparison
    answers_2 = [
        {"model_id": "m1", "model_name": "M1", "answer": "Answer 1 with detail."},
        {"model_id": "m2", "model_name": "M2", "answer": "Answer 2 with code."}
    ]
    res_2 = await evaluator.evaluate_all_pairs("Problem?", answers_2)
    assert res_2["total_comparisons"] == 1
    assert res_2["successful_comparisons"] == 1

    # 3 models -> 3 comparisons
    answers_3 = answers_2 + [{"model_id": "m3", "model_name": "M3", "answer": "Answer 3 with architecture."}]
    res_3 = await evaluator.evaluate_all_pairs("Problem?", answers_3)
    assert res_3["total_comparisons"] == 3
    assert res_3["successful_comparisons"] == 3

    # 4 models -> 6 comparisons
    answers_4 = answers_3 + [{"model_id": "m4", "model_name": "M4", "answer": "Answer 4 with breakdown."}]
    res_4 = await evaluator.evaluate_all_pairs("Problem?", answers_4)
    assert res_4["total_comparisons"] == 6
    assert res_4["successful_comparisons"] == 6


@pytest.mark.asyncio
async def test_position_swap_check():
    evaluator = PairwiseEvaluator(judge=MockJudgeEvaluator())
    answers = [
        {"model_id": "m1", "model_name": "M1", "answer": "Comprehensive code answer ```python print(1)```"},
        {"model_id": "m2", "model_name": "M2", "answer": "Short answer."}
    ]
    res = await evaluator.evaluate_all_pairs("Problem?", answers, position_swap_check=True)
    comp = res["comparisons"][0]
    assert comp["position_swap_check"] is not None
    assert comp["position_swap_check"]["executed"] is True
    assert "consistent" in comp["position_swap_check"]


@pytest.mark.asyncio
async def test_partial_failures():
    # Setup registry with a failing model
    registry = ModelRegistry()
    mock_prov = MockProvider(failing_models={"model-c", "model-d"})
    registry.register_provider(mock_prov)

    gen_service = GenerationService(registry=registry)

    # 4 selected: 2 succeed, 2 fail -> has_sufficient_models True
    res = await gen_service.generate_answers(
        models=["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d"],
        prompt="Design a distributed cache"
    )
    assert res["successful_count"] == 2
    assert res["failed_count"] == 2
    assert res["has_sufficient_models"] is True

    # 4 selected: 3 fail, 1 succeed -> has_sufficient_models False
    mock_prov_3_fail = MockProvider(failing_models={"model-b", "model-c", "model-d"})
    registry.register_provider(mock_prov_3_fail)
    res_fail = await gen_service.generate_answers(
        models=["mock:model-a", "mock:model-b", "mock:model-c", "mock:model-d"],
        prompt="Design a distributed cache"
    )
    assert res_fail["successful_count"] == 1
    assert res_fail["has_sufficient_models"] is False
    assert res_fail["status"] == "INSUFFICIENT_SUCCESSFUL_MODELS"


def test_ranking_engine():
    # Simulated pairwise comparisons
    comparisons = [
        {
            "model_a": {"model_id": "m1", "name": "Model 1"},
            "model_b": {"model_id": "m2", "name": "Model 2"},
            "winner_model_id": "m1",
            "success": True,
            "judge_result": {
                "winner": "A",
                "scores": {
                    "A": {"correctness": 10, "relevance": 9, "completeness": 9, "reasoning": 10, "clarity": 9, "final_score": 9.6},
                    "B": {"correctness": 7, "relevance": 8, "completeness": 7, "reasoning": 7, "clarity": 8, "final_score": 7.3}
                }
            }
        },
        {
            "model_a": {"model_id": "m1", "name": "Model 1"},
            "model_b": {"model_id": "m3", "name": "Model 3"},
            "winner_model_id": "m1",
            "success": True,
            "judge_result": {
                "winner": "A",
                "scores": {
                    "A": {"correctness": 9, "relevance": 9, "completeness": 9, "reasoning": 9, "clarity": 9, "final_score": 9.0},
                    "B": {"correctness": 8, "relevance": 8, "completeness": 8, "reasoning": 8, "clarity": 8, "final_score": 8.0}
                }
            }
        },
        {
            "model_a": {"model_id": "m2", "name": "Model 2"},
            "model_b": {"model_id": "m3", "name": "Model 3"},
            "winner_model_id": "m3",
            "success": True,
            "judge_result": {
                "winner": "B",
                "scores": {
                    "A": {"correctness": 7, "relevance": 7, "completeness": 7, "reasoning": 7, "clarity": 7, "final_score": 7.0},
                    "B": {"correctness": 8, "relevance": 8, "completeness": 8, "reasoning": 8, "clarity": 8, "final_score": 8.0}
                }
            }
        }
    ]

    rankings = RankingEngine.rank_models(comparisons)
    assert len(rankings) == 3

    # Rank 1: m1 (2 wins, 0 losses, win_rate = 1.0)
    assert rankings[0]["model_id"] == "m1"
    assert rankings[0]["rank"] == 1
    assert rankings[0]["wins"] == 2
    assert rankings[0]["win_rate"] == 1.0
    assert rankings[0]["average_final_score"] == 9.3

    # Rank 2: m3 (1 win, 1 loss, win_rate = 0.5)
    assert rankings[1]["model_id"] == "m3"
    assert rankings[1]["rank"] == 2

    # Rank 3: m2 (0 wins, 2 losses, win_rate = 0.0)
    assert rankings[2]["model_id"] == "m2"
    assert rankings[2]["rank"] == 3


@pytest.mark.asyncio
async def test_comparison_service_manual_and_generate():
    service = ComparisonService(judge=MockJudgeEvaluator())

    # Mode 2: Manual Compare
    manual_report = await service.run_manual_compare(
        problem="Explain binary search complexity",
        answers=[
            {"model_name": "Candidate A", "answer": "Binary search is O(log n) because search space halves."},
            {"model_name": "Candidate B", "answer": "Binary search is O(n) in the worst case."}
        ]
    )
    assert manual_report["status"] == "COMPLETED"
    assert manual_report["mode"] == "MANUAL_COMPARE"
    assert len(manual_report["rankings"]) == 2
    assert len(manual_report["pairwise_comparisons"]) == 1

    # Mode 1: Generate and Compare with mock models
    gen_report = await service.run_generate_and_compare(
        models=["mock:model-a", "mock:model-b", "mock:model-c"],
        prompt="Design a distributed key-value store"
    )
    assert gen_report["status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS"]
    assert gen_report["mode"] == "GENERATE_AND_COMPARE"
    assert len(gen_report["rankings"]) == 3
    assert len(gen_report["pairwise_comparisons"]) == 3
    assert gen_report["metrics"]["total_session_latency_seconds"] > 0


def test_database_selective_persistence():
    from src.database import init_db, SessionLocal, SessionRepository

    init_db()
    db = SessionLocal()
    repo = SessionRepository(db)

    test_data = {
        "session_id": "test-sess-001",
        "mode": "GENERATE_AND_COMPARE",
        "status": "COMPLETED",
        "input": {"prompt": "What is Raft consensus?", "system_prompt": None},
        "answers": [
            {"model_id": "m1", "model_name": "M1", "provider": "mock", "answer": "Raft is consensus algorithm", "latency_seconds": 1.2, "input_tokens": 10, "output_tokens": 20, "estimated_cost": 0.001, "success": True},
            {"model_id": "m2", "model_name": "M2", "provider": "mock", "answer": "Raft uses leader election", "latency_seconds": 1.5, "input_tokens": 10, "output_tokens": 25, "estimated_cost": 0.001, "success": True}
        ],
        "pairwise_comparisons": [
            {
                "comparison_id": "cmp-test-1",
                "model_a": {"model_id": "m1", "name": "M1"},
                "model_b": {"model_id": "m2", "name": "M2"},
                "winner_model_id": "m1",
                "success": True,
                "judge_latency": 0.8,
                "judge_result": {
                    "winner": "A",
                    "scores": {
                        "A": {"correctness": 9, "relevance": 9, "completeness": 9, "reasoning": 9, "clarity": 9, "final_score": 9.0},
                        "B": {"correctness": 8, "relevance": 8, "completeness": 8, "reasoning": 8, "clarity": 8, "final_score": 8.0}
                    },
                    "confidence": 0.75,
                    "reason": "Good"
                },
                "raw_judge_response": '{"A": ...}'
            }
        ],
        "rankings": [{"rank": 1, "model_id": "m1"}],
        "metrics": {"total_session_latency_seconds": 2.5}
    }

    # Selective save: only prompt and answers, NOT evaluations, NOT metrics
    save_opts = {"prompt": True, "answers": True, "evaluations": False, "metrics": False, "raw_responses": False}
    repo.save_session("test-sess-001", test_data, save_opts)

    retrieved = repo.get_session("test-sess-001")
    assert retrieved is not None
    assert retrieved["input"]["prompt"] == "What is Raft consensus?"
    assert len(retrieved["answers"]) == 2
    # Evaluations were not saved:
    assert len(retrieved["pairwise_comparisons"]) == 0
    # Metrics were not saved:
    assert retrieved["metrics"] == {}

    # List sessions should contain this session
    sessions_list = repo.list_sessions()
    assert any(s["session_id"] == "test-sess-001" for s in sessions_list)
    db.close()


@pytest.mark.asyncio
async def test_real_providers_graceful_missing_key():
    from src.providers.openai_provider import OpenAIProvider
    from src.providers.anthropic_provider import AnthropicProvider
    from src.providers.gemini_provider import GeminiProvider
    from src.providers.deepseek_provider import DeepSeekProvider
    from src.providers.mistral_provider import MistralProvider
    from src.providers.ollama_provider import OllamaProvider

    # OpenAI missing key
    oa = OpenAIProvider(api_key="")
    res_oa = await oa.generate("gpt-4o", "Hello")
    assert res_oa.success is False
    assert res_oa.error.type == "ConfigurationError"
    assert "OPENAI_API_KEY" in res_oa.error.message

    # Anthropic missing key
    anth = AnthropicProvider(api_key="")
    res_anth = await anth.generate("claude-3-5-sonnet", "Hello")
    assert res_anth.success is False
    assert res_anth.error.type == "ConfigurationError"

    # Gemini missing key
    gem = GeminiProvider(api_key="")
    res_gem = await gem.generate("gemini-1.5-flash", "Hello")
    assert res_gem.success is False
    assert res_gem.error.type == "ConfigurationError"

    # DeepSeek missing key
    ds = DeepSeekProvider(api_key="")
    res_ds = await ds.generate("deepseek-chat", "Hello")
    assert res_ds.success is False
    assert res_ds.error.type == "ConfigurationError"

    # Mistral missing key
    mis = MistralProvider(api_key="")
    res_mis = await mis.generate("mistral-small-latest", "Hello")
    assert res_mis.success is False
    assert res_mis.error.type == "ConfigurationError"

    # Ollama unavailable host
    ollama = OllamaProvider(base_url="http://127.0.0.1:54321")
    res_ollama = await ollama.generate("qwen2.5:7b", "Hello")
    assert res_ollama.success is False
    assert res_ollama.error.type in ["ConnectionRefusedError", "ConnectError"]


