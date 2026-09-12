"""API routes for managing per-user LLM provider API keys."""

import ipaddress
import uuid
from typing import Dict, Optional, Any
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import UserApiKeyRecord
from src.api.routes.auth import get_current_user_required
from src.services.auth import encrypt_api_key, decrypt_api_key
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.mistral_provider import MistralProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.openrouter_provider import OpenRouterProvider
from src.providers.grok_provider import GrokProvider

router = APIRouter(prefix="/api/user/keys", tags=["User API Keys"])


class SaveKeysRequest(BaseModel):
    keys: Dict[str, Optional[str]] = Field(
        ...,
        description="Map of provider name to API key/URL (e.g. {'openai': 'sk-...', 'ollama': 'http://localhost:11434'})"
    )


class TestKeyRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None


def mask_api_key(key: str) -> str:
    """Mask key for safe display (e.g. 'sk-proj...a89f')."""
    if not key:
        return ""
    if key.startswith("http://") or key.startswith("https://"):
        return key  # Do not mask URLs
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def is_safe_ollama_url(url_str: str) -> bool:
    """Validate Ollama URL against SSRF attacks on cloud metadata and private link-local services."""
    try:
        parsed = urlparse(url_str.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Allow local development endpoints
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return True
        # Block cloud instance metadata IP literals
        if hostname == "169.254.169.254":
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_link_local or ip.is_multicast:
                return False
        except ValueError:
            # Hostname is a domain name
            if hostname.lower() in ("metadata.google.internal", "instance-data"):
                return False
        return True
    except Exception:
        return False


@router.get("")
async def get_user_keys(
    user=Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Retrieve all configured provider keys for the logged-in user (masked for security)."""
    records = db.query(UserApiKeyRecord).filter(UserApiKeyRecord.user_id == user.id).all()
    key_map = {r.provider: r.api_key for r in records}

    supported_providers = ["openai", "anthropic", "gemini", "deepseek", "mistral", "openrouter", "grok", "ollama"]
    result = {}
    for p in supported_providers:
        raw_stored = key_map.get(p)
        plain = decrypt_api_key(raw_stored) if raw_stored else None
        result[p] = {
            "provider": p,
            "is_set": bool(plain and plain.strip()),
            "masked_key": mask_api_key(plain) if plain else None,
            "updated_at": next((r.updated_at.isoformat() for r in records if r.provider == p and r.updated_at), None)
        }

    return {"success": True, "keys": result}


@router.post("")
async def save_user_keys(
    request: SaveKeysRequest,
    user=Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Save or update user API keys with encrypted storage at rest."""
    for provider, raw_key in request.keys.items():
        prov_clean = provider.strip().lower()
        rec = (
            db.query(UserApiKeyRecord)
            .filter(UserApiKeyRecord.user_id == user.id, UserApiKeyRecord.provider == prov_clean)
            .first()
        )

        if raw_key and raw_key.strip():
            key_clean = raw_key.strip()
            # If provider is ollama, validate URL
            if prov_clean == "ollama" and not is_safe_ollama_url(key_clean):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or restricted Ollama base URL."
                )

            encrypted_val = encrypt_api_key(key_clean)
            if not rec:
                rec = UserApiKeyRecord(
                    id=f"key-{uuid.uuid4().hex[:8]}",
                    user_id=user.id,
                    provider=prov_clean,
                    api_key=encrypted_val
                )
                db.add(rec)
            else:
                rec.api_key = encrypted_val
        else:
            # If empty string provided, remove saved key
            if rec:
                db.delete(rec)

    db.commit()
    return {"success": True, "message": "API keys updated and encrypted successfully."}


@router.post("/test")
async def test_key_connectivity(
    request: TestKeyRequest,
    user=Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Test connection with a given provider key."""
    provider = request.provider.strip().lower()
    key = request.api_key

    # If key not provided in test payload, lookup and decrypt from database
    if not key:
        rec = (
            db.query(UserApiKeyRecord)
            .filter(UserApiKeyRecord.user_id == user.id, UserApiKeyRecord.provider == provider)
            .first()
        )
        if rec:
            key = decrypt_api_key(rec.api_key)

    if not key and provider != "ollama":
        return {
            "success": False,
            "provider": provider,
            "message": f"No API key provided or saved for '{provider}'"
        }

    # Lightweight test by dispatching a minimal prompt
    try:
        if provider == "openai":
            prov_inst = OpenAIProvider(api_key=key)
            resp = await prov_inst.generate("gpt-4o-mini", "ping")
        elif provider == "anthropic":
            prov_inst = AnthropicProvider(api_key=key)
            resp = await prov_inst.generate("claude-3-5-haiku", "ping")
        elif provider == "gemini":
            prov_inst = GeminiProvider(api_key=key)
            resp = await prov_inst.generate("gemini-1.5-flash", "ping")
        elif provider == "deepseek":
            prov_inst = DeepSeekProvider(api_key=key)
            resp = await prov_inst.generate("deepseek-chat", "ping")
        elif provider == "mistral":
            prov_inst = MistralProvider(api_key=key)
            resp = await prov_inst.generate("mistral-small-latest", "ping")
        elif provider == "openrouter":
            prov_inst = OpenRouterProvider(api_key=key)
            resp = await prov_inst.generate("google/gemini-2.0-flash-lite:free", "ping")
        elif provider == "grok":
            prov_inst = GrokProvider(api_key=key)
            resp = await prov_inst.generate("grok-2-latest", "ping")
        elif provider == "ollama":
            ollama_url = key or "http://localhost:11434"
            if not is_safe_ollama_url(ollama_url):
                return {"success": False, "provider": "ollama", "message": "Restricted or unsafe Ollama URL."}
            prov_inst = OllamaProvider(base_url=ollama_url)
            healthy = await prov_inst.check_health()
            if healthy:
                return {"success": True, "provider": "ollama", "message": "Ollama service is reachable."}
            else:
                return {"success": False, "provider": "ollama", "message": "Cannot reach Ollama service."}
        else:
            return {"success": False, "provider": provider, "message": f"Unsupported provider '{provider}'."}

        if resp.success:
            return {"success": True, "provider": provider, "message": "Connection verified successfully!"}
        else:
            err_msg = resp.error.message if resp.error else "Unknown error"
            return {"success": False, "provider": provider, "message": err_msg}

    except Exception as exc:
        return {"success": False, "provider": provider, "message": str(exc)}

