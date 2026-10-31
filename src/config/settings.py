import urllib.parse
from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def clean_database_url(raw_url: Optional[str]) -> str:
    """Sanitize database URL against common formatting mistakes:
    - Strips surrounding single/double quotes and whitespace
    - Normalizes deprecated postgres:// scheme to postgresql://
    - Removes accidental bracket enclosures like [PASSWORD]
    - URL-encodes special characters (such as @ in password)
    """
    if not raw_url:
        return "sqlite:///./llm_judge.db"

    url = str(raw_url).strip().strip("'\"").strip()
    if not url:
        return "sqlite:///./llm_judge.db"

    # Normalize deprecated postgres:// prefix
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # For network URLs, clean credentials and authority
    if "://" in url:
        scheme, rest = url.split("://", 1)
        if scheme == "postgres":
            scheme = "postgresql"

        path_part = ""
        if "/" in rest:
            authority, path_part = rest.split("/", 1)
            path_part = "/" + path_part
        else:
            authority = rest

        if "@" in authority:
            user_info, host_port = authority.rsplit("@", 1)
            if ":" in user_info:
                user, pwd = user_info.split(":", 1)
                # Strip square brackets if copied like [YOUR-PASSWORD]
                if pwd.startswith("[") and pwd.endswith("]"):
                    pwd = pwd[1:-1]
                if user.startswith("[") and user.endswith("]"):
                    user = user[1:-1]
                # Decode first to avoid double-encoding %40, then quote safely
                decoded_pwd = urllib.parse.unquote(pwd)
                encoded_pwd = urllib.parse.quote(decoded_pwd, safe="")
                user_info = f"{user}:{encoded_pwd}"
            authority = f"{user_info}@{host_port}"

        url = f"{scheme}://{authority}{path_part}"

    return url


def get_async_database_url(raw_url: Optional[str]) -> str:
    """Convert any raw database URL into an async-compatible URL for SQLAlchemy + asyncpg / aiosqlite.
    - Handles sqlite:/// -> sqlite+aiosqlite:///
    - Normalizes postgresql://, postgres://, and postgresql+psycopg2:// to postgresql+asyncpg://
    - Replaces sslmode=require with ssl=require (required by asyncpg dialect)
    - Strips unsupported parameters like channel_binding
    """
    url = clean_database_url(raw_url)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    for prefix in ["postgresql+psycopg://", "postgresql+psycopg2://", "postgresql://", "postgres://"]:
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break

    if "postgresql+asyncpg://" in url:
        import re
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
        url = re.sub(r"[?&]channel_binding=[^&]+", "", url)
        if "?" not in url and "&" in url:
            url = url.replace("&", "?", 1)

    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env.lower() == "production":
            if (
                self.jwt_secret_key == "change-this-to-a-secure-random-secret-key-in-production"
                or len(self.jwt_secret_key) < 32
            ):
                raise ValueError(
                    "Production requires JWT_SECRET_KEY to be explicitly set to at least 32 characters."
                )
            if (
                self.encryption_secret_key == "change-this-to-a-secure-key-for-encrypting-user-api-keys"
                or len(self.encryption_secret_key) < 32
            ):
                raise ValueError(
                    "Production requires ENCRYPTION_SECRET_KEY to be explicitly set to at least 32 characters."
                )
            if self.cors_allowed_origins == "http://localhost:5173,http://127.0.0.1:5173":
                raise ValueError(
                    "Production requires CORS_ALLOWED_ORIGINS to be set to the deployed frontend origin(s)."
                )
        return self

    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    database_url: str = Field(default="sqlite:///./llm_judge.db", description="Database connection URL")

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> str:
        return clean_database_url(v)


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

    # Authentication & Security
    jwt_secret_key: str = Field(default="change-this-to-a-secure-random-secret-key-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, alias="JWT_EXPIRE_MINUTES")  # 7 days
    encryption_secret_key: str = Field(default="change-this-to-a-secure-key-for-encrypting-user-api-keys", alias="ENCRYPTION_SECRET_KEY")
    cors_allowed_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ALLOWED_ORIGINS")

    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")

    # Rate Limiting
    rate_limit_requests: int = Field(default=10, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: str = Field(default="minute", alias="RATE_LIMIT_WINDOW")


settings = Settings()
