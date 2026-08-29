from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    database_url: str = Field(default="sqlite:///./llm_judge.db", description="Database connection URL")

    # API Keys (loaded from environment or .env)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    mistral_api_key: Optional[str] = Field(default=None, alias="MISTRAL_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    grok_api_key: Optional[str] = Field(default=None, alias="GROK_API_KEY")
    xai_api_key: Optional[str] = Field(default=None, alias="XAI_API_KEY")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Timeouts & Limits
    generation_timeout_seconds: float = Field(default=60.0, alias="GENERATION_TIMEOUT_SECONDS")
    judge_timeout_seconds: float = Field(default=90.0, alias="JUDGE_TIMEOUT_SECONDS")
    min_selected_models: int = 1
    max_selected_models: int = Field(default=4, alias="MAX_SELECTED_MODELS")

    # Evaluation config
    default_judge_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", alias="DEFAULT_JUDGE_MODEL")
    position_swap_check: bool = Field(default=False, alias="POSITION_SWAP_CHECK")

    # Hugging Face Remote Qwen Judge (Space or Inference Endpoint)
    qwen_hf_api_url: Optional[str] = Field(default=None, alias="QWEN_HF_API_URL")
    qwen_hf_token: Optional[str] = Field(default=None, alias="QWEN_HF_TOKEN")


settings = Settings()
