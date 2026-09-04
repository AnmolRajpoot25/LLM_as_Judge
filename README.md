# LLM-Judge: Production LLM Comparison & Evaluation Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-Qwen%20Judge-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)

**LLM-Judge** is an enterprise-grade LLM comparison and evaluation platform. It enables concurrent multi-model benchmarking (2 to 4 models simultaneously) across two distinct modes using exhaustive pairwise comparisons evaluated by a local fine-tuned/quantized **Qwen** model.

---

## Key Capabilities

### 1. Two Operational Modes
- **Mode 1: Generate & Compare**: Select 2 to 4 models (OpenAI, Anthropic, Gemini, DeepSeek, Mistral, Ollama, or built-in Mocks). The platform queries all providers concurrently, records latency, extracts input/output tokens, computes financial API cost, and feeds the answers into pairwise evaluation.
- **Mode 2: Compare Existing Answers**: Paste 2 to 4 candidate model answers directly. The platform bypasses external generation, performs pairwise judge evaluation, and calculates complete criteria scorecards without incurring generation costs.

### 2. Pairwise Architecture & Position Bias Mitigation
- Evaluates $N$ models via $N(N - 1) / 2$ unique pairwise battles ($2 \to 1$, $3 \to 3$, $4 \to 6$) using `itertools.combinations`.
- Evaluates candidates under 5 weighted criteria:
  - **Correctness (40%)**
  - **Relevance (20%)**
  - **Completeness (15%)**
  - **Reasoning (15%)**
  - **Clarity (10%)**
- Optional **Position Bias Mitigation** (`position_swap_check`): Evaluates $A$ vs $B$ followed by $B$ vs $A$ to verify consistency.

### 3. Clean Provider Abstraction Layer
- Uniform `BaseProvider` interface returning normalized `ProviderResponse` objects.
- Supported providers:
  - **Mock Provider** (zero-cost testing with simulated latency, tokens, and fail modes)
  - **OpenAI** (GPT-4o, GPT-4o Mini, GPT-4.1)
  - **Anthropic** (Claude 3.5 Sonnet, Claude 3.5 Haiku)
  - **Google Gemini** (Gemini 1.5 Pro, Flash, 2.0 Flash)
  - **DeepSeek** (V3, R1)
  - **Mistral** (Mistral Large, Mistral Small)
  - **Ollama** (local offline models: Qwen 2.5, Llama 3.1, DeepSeek R1)
- Never crashes on missing API keys or provider outages; returns structured `ConfigurationError` and continues with remaining models.

### 4. Resilient Partial Failure Handling
- If 4 models are requested and 3 succeed: continues evaluation with 3 models ($3$ comparisons).
- If 2 succeed: continues evaluation with 2 models ($1$ comparison).
- If $< 2$ succeed: safely halts with `INSUFFICIENT_SUCCESSFUL_MODELS` and detailed diagnostics.

### 5. Standard Competition Ranking & Metrics
- Ranks models using **Standard Competition Ranking** (1224 ranking) with documented tie-breaking priority:
  1. Win Rate (descending)
  2. Total Wins (descending)
  3. Average Final Score (descending)
  4. Average Correctness (descending)
  5. Successful Evaluations (descending)
- Tracks per-model latency, judge latency, wall-clock session duration, and token usage.

### 6. User-Controlled Selective Persistence
- Built on SQLAlchemy with SQLite (PostgreSQL ready).
- Save only what you choose: `prompt`, `answers`, `evaluations`, `metrics`, or `raw_responses`.
- Enforces strict relational integrity without orphaned foreign keys.

---

## System Architecture

```
LLM-Judge/
├── src/
│   ├── judge/
│   │   ├── evaluator.py       # Validated Qwen JudgeEvaluator (untouched)
│   │   ├── prompts.py         # Judge system prompts & rubrics (untouched)
│   │   └── model_loader.py    # JudgeManager, GPU inference lock, MockJudgeEvaluator
│   ├── providers/
│   │   ├── base.py            # BaseProvider, ProviderResponse, GenerationConfig
│   │   ├── mock_provider.py   # Mock provider for testing
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── mistral_provider.py
│   │   ├── ollama_provider.py
│   │   └── registry.py        # ModelRegistry catalog
│   ├── services/
│   │   ├── cost_calculator.py # Centralized pricing calculations
│   │   ├── generation_service.py # Concurrent async generation & partial failure policy
│   │   └── comparison_service.py # End-to-end Mode 1 and Mode 2 pipeline orchestrator
│   ├── evaluation/
│   │   ├── pairwise.py        # Combinations generator & pairwise judge runner
│   │   ├── ranking.py         # RankingEngine (standard competition ranking)
│   │   ├── metrics.py         # MetricsTracker (latencies, tokens, costs)
│   │   └── report_generator.py # Final evaluation report generator
│   ├── database/
│   │   ├── connection.py      # Engine, session factory & SQLite connection
│   │   ├── models.py          # Session, Prompt, ModelResponse, PairwiseComparison, EvaluationResult
│   │   └── repository.py      # SessionRepository with selective saving
│   ├── api/
│   │   ├── main.py            # FastAPI application with CORS & lifespan
│   │   ├── dependencies.py    # Dependency injection
│   │   ├── routes/            # models, generate, compare, sessions
│   │   └── schemas/           # Pydantic request & response validation
│   └── config/
│       ├── settings.py        # Pydantic Settings (.env loader)
│       └── pricing.py         # Centralized pricing table
├── frontend/                  # React + TypeScript + Vite web app
├── tests/                     # 20 automated unit, API, and E2E integration tests
├── requirements.txt
└── .env.example
```

---

## Quickstart Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/AnmolRajpoot25/LLM_as_Judge.git
cd LLM_as_Judge

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

Copy `.env.example` to `.env` and provide your API keys (optional for mock testing):

```bash
cp .env.example .env
```

```ini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=...
MISTRAL_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Run Backend & Frontend

In Terminal 1 (FastAPI Backend):
```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

In Terminal 2 (React Frontend):
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running the Automated Test Suite

Run all 20 tests (unit, API, database, and live integration):
```bash
python -m pytest tests/ -v
```

---

## GPU & Google Colab Deployment

When running on a GPU-enabled server (e.g., Google Colab Tesla T4 with 4-bit Qwen):

```python
from src.judge.model_loader import judge_manager

# Load Qwen model with 4-bit quantization
judge = judge_manager.load_qwen_judge(
    model_name="Qwen/Qwen2.5-7B-Instruct",
    max_new_tokens=300,
    max_retries=1
)
```

The system automatically serializes inference through `judge_manager.lock` to prevent concurrent GPU execution and eliminate CUDA Out-Of-Memory (OOM) errors.

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/models` | List all configured models, availability, and pricing |
| `POST` | `/api/generate-compare` | Run concurrent generation & pairwise evaluation (Mode 1) |
| `POST` | `/api/manual-compare` | Evaluate user-supplied answers pairwise (Mode 2) |
| `POST` | `/api/sessions/{session_id}/save` | Selectively persist session components to SQLite |
| `GET` | `/api/sessions/{session_id}` | Retrieve full details of a saved session |
| `GET` | `/api/sessions` | List saved sessions history |
| `GET` | `/api/health` | Service health status |
