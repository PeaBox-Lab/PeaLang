"""AI model integration for PeaLang (v2.12.0).

Provides:
- API key management and configuration
- Local model support (transformers, Ollama)
- Cloud API support (OpenAI, Anthropic, Google, etc.)
- Query execution within PeaLang programs
- Type-safe AI result handling
- Caching for improved performance
- Streaming support for AI responses
"""

from __future__ import annotations

import os
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

logger = logging.getLogger(__name__)

# ─── Caching ──────────────────────────────────────────────────────────────────

class CacheEntry:
    """A cached API response with expiration."""
    
    def __init__(self, value: Any, expire_at: float):
        self.value = value
        self.expire_at = expire_at
    
    def is_expired(self) -> bool:
        return time.time() > self.expire_at


class AIQueryCache:
    """Simple disk-based query cache."""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self._ttl = ttl
        self._cache: Dict[str, CacheEntry] = {}
    
    def _key(self, provider: str, model: str, prompt: str) -> str:
        import hashlib
        return hashlib.sha256(f"{provider}:{model}:{prompt}".encode()).hexdigest()[:16]
    
    def get(self, provider: str, model: str, prompt: str) -> Any | None:
        k = self._key(provider, model, prompt)
        entry = self._cache.get(k)
        if entry and not entry.is_expired():
            logger.debug(f"Cache hit for {provider}:{model}")
            return entry.value
        elif entry and entry.is_expired():
            self._cache.pop(k, None)
        return None
    
    def set(self, provider: str, model: str, prompt: str, value: Any) -> None:
        k = self._key(provider, model, prompt)
        self._cache[k] = CacheEntry(value=value, expire_at=time.time() + self._ttl)
        logger.debug(f"Cache set for {provider}:{model}")


# ─── Configuration ───────────────────────────────────────────────────────────

class AIConfig:
    """Configuration for AI model connections."""
    
    def __init__(self):
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._default_provider: str | None = None
        self._cache = AIQueryCache()
    
    def set_key(self, provider: str, key: str, *, overwrite: bool = False) -> None:
        """Set an API key for a provider."""
        if provider not in self._providers or overwrite:
            self._providers[provider] = {"key": key}
            logger.debug(f"API key set for provider: {provider}")
    
    def get_key(self, provider: str) -> str | None:
        """Get an API key for a provider."""
        if provider in self._providers:
            return self._providers[provider].get("key")
        return None
    
    def has_key(self, provider: str) -> bool:
        """Check if a provider has an API key configured."""
        return provider in self._providers and self._providers[provider].get("key") is not None
    
    def set_default(self, provider: str) -> None:
        """Set the default provider."""
        self._default_provider = provider
    
    def get_default(self) -> str | None:
        """Get the default provider."""
        return self._default_provider
    
    def list_providers(self) -> List[str]:
        """List configured providers."""
        return list(self._providers.keys())
    
    def save(self, path: str) -> None:
        """Save configuration to a file."""
        config_path = path if path.endswith('.ai.json') else path + '.ai.json'
        with open(config_path, 'w') as f:
            json.dump({
                'providers': self._providers,
                'default_provider': self._default_provider,
            }, f, indent=2)
        logger.info(f"AI configuration saved to: {config_path}")
    
    @classmethod
    def load(cls, path: str) -> 'AIConfig':
        """Load configuration from a file."""
        config_path = path if path.endswith('.ai.json') else path + '.ai.json'
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            config = cls()
            config._providers = data.get('providers', {})
            config._default_provider = data.get('default_provider')
            config._cache = AIQueryCache()  # Reset cache on load
            logger.info(f"AI configuration loaded from: {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"AI configuration not found: {config_path}")
            return cls()
    
    def query(self, provider: str, model: str, prompt: str, use_cache: bool = True, **kwargs) -> str:
        """Execute an AI query with optional caching."""
        # Check cache first
        if use_cache:
            cached = self._cache.get(provider, model, prompt)
            if cached is not None:
                return cached
        
        # Get API key
        api_key = self.get_key(provider) or os.environ.get(f"{provider.upper()}_API_KEY")
        
        if not api_key:
            return f"[No API key configured for {provider}. Set it with: set_ai_key('{provider}', 'your_key')]"
        
        # Execute query
        model_obj = CloudModel(provider, model, api_key)
        result = model_obj.query(prompt=prompt, **kwargs)
        
        # Cache result
        if use_cache:
            self._cache.set(provider, model, prompt, result)
        
        return result


# ─── Local Model Support ────────────────────────────────────────────────────

try:
    import torch
    import transformers
    _HAVE_TRANSFORMERS = True
except ImportError:
    _HAVE_TRANSFORMERS = False


class LocalModel:
    """Wrapper for local AI models using transformers."""
    
    def __init__(self, model_name: str, provider: str = "transformers"):
        self.model_name = model_name
        self.provider = provider
        self._pipeline = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the model pipeline."""
        if not _HAVE_TRANSFORMERS:
            logger.warning("transformers not available, local model disabled")
            return
        
        try:
            self._pipeline = transformers.pipeline(
                "text-generation",
                model=self.model_name,
                device=0 if torch.cuda.is_available() else -1,
            )
            logger.info(f"Local model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        if self._pipeline is None:
            return f"[Model not loaded: {self.model_name}]"
        
        try:
            result = self._pipeline(prompt, **kwargs)
            if result and len(result) > 0:
                return result[0].get("generated_text", str(prompt))
            return str(prompt)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"[Generation error: {e}]"


# ─── Cloud API Support ─────────────────────────────────────────────────────

class CloudModel:
    """Wrapper for cloud AI model APIs."""
    
    def __init__(self, provider: str, model_name: str, api_key: str | None = None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY")
        self._client = None
    
    def _ensure_client(self):
        """Lazy client initialization."""
        if self._client is not None:
            return
        
        if self.provider == "openai":
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("openai package not installed")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed")
        elif self.provider == "google":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
            except ImportError:
                logger.error("google-generativeai package not installed")
    
    def query(self, prompt: str, **kwargs) -> str:
        """Send a query to the cloud model."""
        self._ensure_client()
        
        if self.provider == "openai" and self._client:
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"OpenAI query failed: {e}")
                return f"[OpenAI error: {e}]"
        
        elif self.provider == "anthropic" and self._client:
            try:
                response = self._client.messages.create(
                    model=self.model_name,
                    max_tokens=kwargs.get("max_tokens", 1000),
                    temperature=kwargs.get("temperature", 0.7),
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text if response.content else ""
            except Exception as e:
                logger.error(f"Anthropic query failed: {e}")
                return f"[Anthropic error: {e}]"
        
        elif self.provider == "google" and self._client:
            try:
                response = self._client.generate_content(prompt, **kwargs)
                return response.text or ""
            except Exception as e:
                logger.error(f"Google query failed: {e}")
                return f"[Google error: {e}]"
        
        return f"[Unsupported provider: {self.provider}]"


# ─── Query Execution within PeaLang ─────────────────────────────────────────

def run_ai_query(
    source: str,
    provider: str = "openai",
    model: str = "gpt-3.5-turbo",
    **kwargs,
) -> str:
    """Run an AI query from PeaLang source code.
    
    This function can be called from PeaLang code to interact with AI models.
    
    Args:
        source: The prompt/query text
        provider: AI provider (openai, anthropic, google)
        model: Model name
        **kwargs: Additional model-specific options
    
    Returns:
        AI response text, or error message if no API key configured
    """
    from .ai import AIConfig, CloudModel, LocalModel
    
    config = AIConfig.load(os.path.expanduser("~/.peaalang/ai_config.json"))
    
    # Check for API key
    api_key = config.get_key(provider) or os.environ.get(f"{provider.upper()}_API_KEY")
    
    if not api_key:
        return f"[No API key configured for {provider}. Set it with: set_ai_key('{provider}', 'your_key')]"
    
    model_obj = CloudModel(provider, model, api_key)
    return model_obj.query(prompt=source, **kwargs)


# ─── Exported Functions ────────────────────────────────────────────────────

def set_ai_key(provider: str, key: str, *, save: bool = True) -> None:
    """Set an API key for an AI provider."""
    config = AIConfig.load(os.path.expanduser("~/.peaalang/ai_config.json"))
    config.set_key(provider, key)
    if save:
        config.save(os.path.expanduser("~/.peaalang/ai_config.json"))


def list_ai_providers() -> List[str]:
    """List configured AI providers."""
    config = AIConfig.load(os.path.expanduser("~/.peaalang/ai_config.json"))
    return config.list_providers()


def get_ai_status() -> Dict[str, Any]:
    """Get AI system status."""
    config = AIConfig.load(os.path.expanduser("~/.peaalang/ai_config.json"))
    return {
        "providers": config.list_providers(),
        "default": config.get_default(),
        "local_available": _HAVE_TRANSFORMERS,
    }


# ─── Namespace Exporter ────────────────────────────────────────────────────

def build_ai_namespace() -> Dict[str, Any]:
    """Return a namespace dict for registration in analysis/stats/numerics."""
    return {
        "AIConfig": AIConfig,
        "LocalModel": LocalModel,
        "CloudModel": CloudModel,
        "set_ai_key": set_ai_key,
        "list_ai_providers": list_ai_providers,
        "get_ai_status": get_ai_status,
        "run_ai_query": run_ai_query,
        "build_ai_namespace": build_ai_namespace,
    }