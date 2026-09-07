"""OpenRouter AI Provider with real-time dynamic model discovery and fallback."""
import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base import AISynthesisOutput, BaseAIProvider
from app.ai.prompts.prompts import SYSTEM_PROMPT, generate_synthesis_prompt
from app.config.settings import settings
from app.core.logging import logger

class OpenRouterProvider(BaseAIProvider):
    """OpenRouter integration with dynamic model discovery across verified active free and low-cost models."""

    def __init__(self):
        super().__init__(name="OpenRouter")
        self.api_key = settings.OPENROUTER_API_KEY
        self.models = [m.strip() for m in settings.OPENROUTER_MODEL.split(",") if m.strip()]
        self._cached_live_models: List[str] = []
        self._last_discovery_time: float = 0.0

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetches all currently available OpenRouter models, tagging free ones."""
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get("https://openrouter.ai/api/v1/models", headers={"User-Agent": "Mozilla/5.0"})
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    models_list = []
                    for m in data:
                        mid = m.get("id", "")
                        pricing = m.get("pricing", {})
                        is_free = ":free" in mid or (pricing.get("prompt") == "0" and pricing.get("completion") == "0")
                        models_list.append({
                            "id": mid,
                            "name": m.get("name", mid),
                            "is_free": is_free,
                            "context_length": m.get("context_length", 4096)
                        })
                    return models_list
        except Exception as e:
            logger.debug(f"OpenRouter get_available_models error: {e}")
        return []

    async def fetch_live_free_models(self) -> List[str]:
        """Discovers and caches active free models from OpenRouter."""
        now = time.time()
        if self._cached_live_models and (now - self._last_discovery_time < 600):
            return self._cached_live_models

        live_free: List[str] = []
        try:
            models_data = await self.get_available_models()
            for m in models_data:
                if m.get("is_free") and m.get("id"):
                    live_free.append(m["id"])
            if live_free:
                self._cached_live_models = live_free
                self._last_discovery_time = now
                logger.info(f"OpenRouter dynamically discovered {len(live_free)} live free models.")
        except Exception as e:
            logger.debug(f"OpenRouter dynamic free models error: {e}")

        return live_free or [
            "inclusionai/ling-3.0-flash-fin:free",
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "minimax/minimax-m3:free",
            "z-ai/glm-5.2:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "openrouter/free"
        ]

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        prompt = generate_synthesis_prompt(structured_input)

        # Build prioritized list: User configured models first, then dynamic live free models, then popular fallbacks
        live_free = await self.fetch_live_free_models()
        candidate_models = []

        for m in self.models:
            clean = m.strip()
            if clean and clean not in candidate_models:
                candidate_models.append(clean)

        for fm in live_free:
            if fm not in candidate_models:
                candidate_models.append(fm)

        popular_fallbacks = [
            "deepseek/deepseek-r1",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini"
        ]
        for pf in popular_fallbacks:
            if pf not in candidate_models:
                candidate_models.append(pf)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Farhaan-jpg/xauusd-market-agent",
            "X-Title": "XAUUSD Market Intelligence Agent",
            "Content-Type": "application/json"
        }

        last_error = None
        for model in candidate_models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"}
            }

            try:
                logger.info(f"Trying OpenRouter model '{model}'...")
                async with httpx.AsyncClient(timeout=min(settings.AI_TIMEOUT_SECONDS, 16)) as client:
                    response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    res_json = response.json()
                    choices = res_json.get("choices", [])
                    if choices:
                        raw_content = choices[0]["message"]["content"]
                        clean_str = self._clean_json(raw_content)
                        parsed = json.loads(clean_str)
                        logger.info(f"OpenRouter synthesis successfully generated via model '{model}'.")
                        return AISynthesisOutput(**parsed)
                elif response.status_code in [404, 400]:
                    logger.warning(f"OpenRouter model '{model}' not found / unsupported ({response.status_code}). Switching to next model...")
                    continue
                elif response.status_code == 402:
                    logger.warning(f"OpenRouter model '{model}' requires credits (402). Switching to next free model...")
                    continue
                elif response.status_code == 429:
                    logger.warning(f"OpenRouter model '{model}' hit rate limit (429). Switching to next model...")
                    continue
                else:
                    logger.warning(f"OpenRouter model '{model}' status {response.status_code}: {response.text[:150]}")
            except Exception as e:
                logger.warning(f"OpenRouter model '{model}' exception: {e}")
                last_error = e

        raise last_error or Exception("All OpenRouter candidate models failed.")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        # Strip reasoning model think tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        # If surrounded by text, find first { and last }
        if "{" in text and "}" in text:
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            text = text[start_idx:end_idx]
        return text
