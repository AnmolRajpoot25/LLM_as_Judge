import asyncio
import time
from typing import Optional, Dict, Any, Set
from src.providers.base import BaseProvider, ProviderResponse, ProviderError, GenerationConfig


class MockProvider(BaseProvider):
    """Mock LLM Provider for zero-cost testing and local validation."""

    def __init__(
        self,
        simulated_latencies: Optional[Dict[str, float]] = None,
        failing_models: Optional[Set[str]] = None,
        always_available: bool = True
    ):
        self._provider_name = "mock"
        self._simulated_latencies = simulated_latencies or {
            "model-a": 0.15,
            "model-b": 0.25,
            "model-c": 0.35,
            "model-d": 0.20,
        }
        self.failing_models: Set[str] = set(failing_models or [])
        self._always_available = always_available

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def is_available(self) -> bool:
        return self._always_available

    def set_failing_models(self, models: Set[str]) -> None:
        self.failing_models = set(models)

    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> ProviderResponse:
        start_time = time.perf_counter()
        clean_model = model_name.replace("mock:", "")

        # Simulate latency
        delay = self._simulated_latencies.get(clean_model, 0.2)
        await asyncio.sleep(delay)
        elapsed = time.perf_counter() - start_time

        # Check for simulated failures
        if clean_model in self.failing_models or "fail" in clean_model.lower():
            return ProviderResponse(
                success=False,
                model=clean_model,
                provider=self.provider_name,
                answer=None,
                latency_seconds=elapsed,
                error=ProviderError(
                    type="MockSimulatedFailure",
                    message=f"Simulated failure for mock model '{clean_model}'",
                    retryable=False
                )
            )

        # Generate realistic simulated answers based on model persona
        personas = {
            "model-a": (
                f"### High-Performance Architecture Overview\n\n"
                f"Regarding the problem: **{prompt.strip()}**\n\n"
                f"1. **Core Strategy**: Deploy a distributed microservices cluster with horizontally scalable stateless API gateways.\n"
                f"2. **Data Storage & Caching**: Implement multi-region PostgreSQL with read replicas, fronted by Redis clusters for hot keys (LRU cache policy, 99.9% hit rate target).\n"
                f"3. **Algorithmic Complexity**: O(1) key lookups using distributed consistent hashing with virtual nodes.\n"
                f"4. **High Availability**: Circuit breakers, rate limiting (token bucket algorithm), and zero-downtime rolling deployments."
            ),
            "model-b": (
                f"### System Implementation & Protocol\n\n"
                f"To address: **{prompt.strip()}**\n\n"
                f"Here is a comprehensive solution:\n"
                f"```python\n"
                f"class DistributedSolution:\n"
                f"    def __init__(self, capacity: int = 10_000):\n"
                f"        self.capacity = capacity\n"
                f"        self.cache = {{}}\n\n"
                f"    def process(self, query: str) -> dict:\n"
                f"        return {{'status': 'success', 'query': query, 'timestamp': time.time()}}\n"
                f"```\n"
                f"- **Scalability**: Decoupled asynchronous message brokers (Apache Kafka / RabbitMQ).\n"
                f"- **Fault Tolerance**: Leader election via Raft consensus and automated health probes."
            ),
            "model-c": (
                f"### Analytical Breakdown\n\n"
                f"Analysis for: **{prompt.strip()}**\n\n"
                f"We must consider throughput, consistency constraints (CAP theorem: AP vs CP), and storage estimation.\n"
                f"- **Write QPS**: ~10,000 writes/sec requiring distributed log-structured merge trees.\n"
                f"- **Read QPS**: ~100,000 reads/sec serviced directly from memory cache.\n"
                f"- **Edge Handling**: Graceful degradation under partition events and exponential backoff."
            ),
            "model-d": (
                f"### Balanced Enterprise Solution\n\n"
                f"Solution approach for: **{prompt.strip()}**\n\n"
                f"- **Architecture**: Clean layered design separating Presentation, Domain, and Data Access layers.\n"
                f"- **Security**: Strict mTLS, OAuth2 token validation, and encryption at rest using AES-256-GCM.\n"
                f"- **Monitoring**: OpenTelemetry tracing, Prometheus metrics collection, and alerting."
            )
        }

        answer = personas.get(
            clean_model,
            f"Mock response from {clean_model} for prompt: {prompt[:100]}..."
        )

        input_tokens = max(10, len(prompt.split()) * 2)
        output_tokens = max(25, len(answer.split()) * 2)

        return ProviderResponse(
            success=True,
            model=clean_model,
            provider=self.provider_name,
            answer=answer,
            latency_seconds=elapsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=0.0,
            raw_metadata={"mock": True, "clean_model": clean_model}
        )
