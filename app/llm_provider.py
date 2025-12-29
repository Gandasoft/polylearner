"""
LLM Provider Interface
----------------------
Provides a unified interface for different LLM providers.
Supports: OpenAI, Anthropic, Ollama, and custom endpoints.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import os
import json

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """Generate text completion from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT models)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if not api_key or not api_key.startswith("sk-"):
            logger.error(f"Invalid OpenAI API key format. Key should start with 'sk-'. Got: {api_key[:10] if api_key else 'None'}...")
            return
        
        if api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info(f"OpenAI provider initialized with model: {model}")
            except ImportError:
                logger.error("OpenAI package not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check your API key.")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_mode and "gpt-4" in self.model:
                kwargs["response_format"] = {"type": "json_object"}
            
            logger.info(f"Calling OpenAI API with model {self.model}...")
            response = await self.client.chat.completions.create(**kwargs)
            logger.info(f"OpenAI API response received successfully")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {type(e).__name__}: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=api_key)
                logger.info(f"Anthropic provider initialized with model: {model}")
            except ImportError:
                logger.error("Anthropic package not installed. Install with: pip install anthropic")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self.client.messages.create(**kwargs)
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama local model provider"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        logger.info(f"Ollama provider initialized with model: {model} at {base_url}")
    
    def is_available(self) -> bool:
        # Check if Ollama is reachable
        try:
            import httpx
            import asyncio
            
            async def check():
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    return response.status_code == 200
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return True  # Assume available if we're in async context
            else:
                return loop.run_until_complete(check())
        except Exception:
            return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        try:
            import httpx
            
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if json_mode:
                payload["format"] = "json"
            
            # Increase timeout for local models which can be slower
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()
                
        except httpx.TimeoutException as e:
            logger.error(f"Ollama request timed out after 300s. Consider using a smaller model or reducing max_tokens. Error: {e}")
            raise RuntimeError("LLM request timed out. The model may be too slow for this request.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"LLM request failed with status {e.response.status_code}")
        except ImportError:
            logger.error("httpx package not installed. Install with: pip install httpx")
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {type(e).__name__}: {e}")
            raise


class CustomEndpointProvider(LLMProvider):
    """Custom API endpoint provider (OpenAI-compatible)"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, model: str = "default"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        logger.info(f"Custom endpoint provider initialized: {base_url}")
    
    def is_available(self) -> bool:
        return bool(self.base_url)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        try:
            import httpx
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            logger.error(f"Custom endpoint generation error: {e}")
            raise


def create_llm_provider(
    provider_type: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> Optional[LLMProvider]:
    """
    Factory function to create LLM providers.
    
    Args:
        provider_type: One of "openai", "anthropic", "ollama", "custom"
        api_key: API key for the provider (if required)
        model: Model name to use
        base_url: Base URL for custom/ollama providers
    
    Returns:
        LLMProvider instance or None if not available
    """
    provider_type = provider_type.lower()
    
    try:
        if provider_type == "openai":
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found in environment variables")
                return None
            if not api_key.startswith("sk-"):
                logger.error(f"Invalid OpenAI API key format. Must start with 'sk-'. Got: {api_key[:10]}...")
                return None
            model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
            logger.info(f"Creating OpenAI provider with model: {model}")
            return OpenAIProvider(api_key, model)
        
        elif provider_type == "anthropic":
            if not api_key:
                api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("Anthropic API key not provided")
                return None
            model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            return AnthropicProvider(api_key, model)
        
        elif provider_type == "ollama":
            base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
            return OllamaProvider(base_url, model)
        
        elif provider_type == "custom":
            if not base_url:
                base_url = os.getenv("CUSTOM_LLM_BASE_URL")
            if not base_url:
                logger.warning("Custom LLM base URL not provided")
                return None
            api_key = api_key or os.getenv("CUSTOM_LLM_API_KEY")
            model = model or os.getenv("CUSTOM_LLM_MODEL", "default")
            return CustomEndpointProvider(base_url, api_key, model)
        
        else:
            logger.error(f"Unknown provider type: {provider_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating LLM provider: {e}")
        return None


def get_default_provider() -> Optional[LLMProvider]:
    """
    Get the default LLM provider based on environment variables.
    Checks in order: OpenAI, Anthropic, Ollama, Custom
    """
    provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
    
    provider = create_llm_provider(provider_type)
    
    if provider and provider.is_available():
        logger.info(f"Using LLM provider: {provider_type}")
        return provider
    
    # Try fallback providers
    logger.warning(f"Primary provider {provider_type} not available, trying fallbacks...")
    
    for fallback_type in ["openai", "anthropic", "ollama"]:
        if fallback_type != provider_type:
            provider = create_llm_provider(fallback_type)
            if provider and provider.is_available():
                logger.info(f"Using fallback LLM provider: {fallback_type}")
                return provider
    
    logger.warning("No LLM provider available. Service will run with limited functionality.")
    return None
