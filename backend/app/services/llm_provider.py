import os
import time
import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class ChatProvider(ABC):
    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate LLM response given a list of message dicts [{'role': '...', 'content': '...'}]"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider connection is reachable."""
        pass

class OllamaProvider(ChatProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.fallback_model = settings.OLLAMA_FALLBACK_MODEL

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Fast availability check first so users don't wait 45s if Ollama is off!
        if not await self.is_available():
            return self._heuristic_local_fallback(messages)

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": settings.OLLAMA_NUM_PREDICT
            }
        }
        
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    logger.info(
                        "Ollama completion ok | model=%s elapsed=%.1fs prompt_tokens=%s gen_tokens=%s",
                        self.model, time.perf_counter() - started,
                        data.get("prompt_eval_count"), data.get("eval_count")
                    )
                    return data.get("message", {}).get("content", "")

                # Attempt fallback model
                logger.warning(
                    "Ollama model %s returned HTTP %s; retrying with %s",
                    self.model, res.status_code, self.fallback_model
                )
                payload["model"] = self.fallback_model
                res_fb = await client.post(url, json=payload)
                if res_fb.status_code == 200:
                    return res_fb.json().get("message", {}).get("content", "")

                raise RuntimeError(f"Ollama returned HTTP {res.status_code}: {res.text}")
        except httpx.TimeoutException:
            # Silent fallbacks here previously looked like "Ollama is offline" even
            # when it was running fine and merely slow - always say which it was.
            logger.error(
                "Ollama timed out after %.1fs (limit %.0fs, model=%s). Raise OLLAMA_TIMEOUT "
                "or lower LLM_CONTEXT_MAX_CHUNKS/LLM_CONTEXT_CHUNK_WORDS.",
                time.perf_counter() - started, settings.OLLAMA_TIMEOUT, self.model
            )
            return self._heuristic_local_fallback(messages)
        except Exception as e:
            logger.error(
                "Ollama call failed after %.1fs (model=%s): %s",
                time.perf_counter() - started, self.model, e, exc_info=True
            )
            return self._heuristic_local_fallback(messages)


    def _heuristic_local_fallback(self, messages: List[Dict[str, str]]) -> str:
        user_msg = ""
        context = ""
        
        for m in messages:
            content = m.get("content", "")
            if "CONTEXT CHUNKS:" in content:
                context = content.split("CONTEXT CHUNKS:")[1]
                # The agent appends the question after the context; without this
                # the fallback echoes "USER QUESTION: ..." into the answer body.
                if "USER QUESTION:" in context:
                    context, trailing = context.split("USER QUESTION:", 1)
                    user_msg = user_msg or trailing.strip()
                context = context.strip()
            elif m.get("role") == "user" and not user_msg:
                user_msg = content

        if context:
            return (
                f"**Offline mode - retrieved transcript excerpts (no model reachable):**\n\n{context}\n\n"
                f"*These passages are returned verbatim from the knowledge base, not synthesised. Start Ollama or set a cloud API key in `.env` for a generated answer.*"
            )
        elif user_msg:
            return (
                f"I received your question: \"{user_msg}\".\n\n"
                f"I searched Lenny's Podcast transcripts. Running in offline mode (Ollama is not running locally). "
                f"To run with local AI models, please download Ollama and run `ollama pull llama3.1:8b`."
            )
        else:
            return "I searched Lenny's Podcast transcripts, but could not locate relevant coverage for your question."


class AnthropicProvider(ChatProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        system_prompt = ""
        formatted_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": formatted_messages,
            "system": system_prompt
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            if res.status_code != 200:
                raise RuntimeError(f"Anthropic API Error {res.status_code}: {res.text}")
            data = res.json()
            return data["content"][0]["text"]

class OpenAIProvider(ChatProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if res.status_code != 200:
                raise RuntimeError(f"OpenAI API Error {res.status_code}: {res.text}")
            data = res.json()
            return data["choices"][0]["message"]["content"]

class OpenRouterProvider(ChatProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
        self.model = model or settings.OPENROUTER_MODEL

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured in .env file.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Lenny Growth Assistant"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            if res.status_code != 200:
                data_err = res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text
                err_msg = data_err.get("error", {}).get("message", res.text) if isinstance(data_err, dict) else str(data_err)
                raise RuntimeError(f"OpenRouter API Error ({res.status_code}): {err_msg}")
            data = res.json()
            return data["choices"][0]["message"]["content"]

class GeminiProvider(ChatProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        system_instruction = None
        contents = []
        for m in messages:
            if m["role"] == "system":
                system_instruction = {"parts": [{"text": m["content"]}]}
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {"contents": contents}
        if system_instruction:
            payload["system_instruction"] = system_instruction

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                data_err = res.json() if res.headers.get("content-type", "").startswith("application/json") else res.text
                err_msg = data_err.get("error", {}).get("message", res.text) if isinstance(data_err, dict) else str(data_err)
                raise RuntimeError(f"Gemini API Error ({res.status_code}): {err_msg}")
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "No content returned from Gemini."

def get_provider(provider_name: str = None) -> ChatProvider:
    """
    Smart provider routing — logical UI names map to best available backend.

    Design intent (scalable key strategy):
      - "anthropic" = team's preferred cloud provider.
        • If GEMINI_API_KEY is set   → uses Gemini (dev's free key)
        • If OPENROUTER_API_KEY set  → uses OpenRouter (free tier)
        • Else                       → uses real Anthropic (team's key)
        So teams paste their ANTHROPIC_API_KEY and get Claude; devs paste
        their GEMINI_API_KEY into that same env slot and get Gemini — no
        code change needed.

      - "openai" = team's OpenAI preference.
        • If OPENROUTER_API_KEY set  → uses OpenRouter (free tier)
        • If GEMINI_API_KEY set      → uses Gemini
        • Else                       → uses real OpenAI (team's key)

      - "ollama"      → always local Ollama, no cloud keys needed
      - "openrouter"  → OpenRouter directly
      - "gemini"      → Google Gemini directly
    """
    name = (provider_name or settings.LLM_PROVIDER).lower().strip()

    if name == "anthropic":
        # Use best available key: Gemini (free) → OpenRouter (free) → real Anthropic
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            return GeminiProvider()
        elif settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY.strip()) > 5:
            return OpenRouterProvider()
        else:
            return AnthropicProvider()

    elif name == "openai":
        # Use best available key: OpenRouter (free) → Gemini (free) → real OpenAI
        if settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY.strip()) > 5:
            return OpenRouterProvider()
        elif settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            return GeminiProvider()
        else:
            return OpenAIProvider()

    elif name == "ollama":
        return OllamaProvider()

    elif name == "openrouter":
        return OpenRouterProvider()

    elif name == "gemini":
        return GeminiProvider()

    else:
        # Unknown / default → local Ollama (safe, no keys needed)
        return OllamaProvider()
