"""OpenRouter AI Provider for secondary fallback synthesis."""
import asyncio
import json
from typing import Any, Dict, List
import httpx
from app.ai.base import AISynthesisOutput, BaseAIProvider
from app.ai.prompts.prompts import SYSTEM_PROMPT, generate_synthesis_prompt
from app.config.settings import settings
from app.core.logging import logger

class OpenRouterProvider(BaseAIProvider):
    """OpenRouter integration with dynamic multi-model fallback across active free and low-cost models."""

    def __init__(self):
        super().__init__(name="OpenRouter")
        self.api_key = settings.OPENROUTER_API_KEY
        configured_models = [m.strip() for m in settings.OPENROUTER_MODEL.split(",") if m.strip()]
        
        # Live verified free models and popular high-efficiency fallbacks
        fallback_models = [
            "openrouter/free",
            "google/gemma-4-31b-it:free",
            "google/gemma-4-26b-a4b-it:free",
            "nvidia/nemotron-3.5-lightning:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "minimax/minimax-m3:free",
            "z-ai/glm-5.2:free",
            "liquid/lfm-2.5-2.6b:free",
            "inclusionai/ling-3.0-flash-fin:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "deepseek/deepseek-r1",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini"
        ]
        for fm in fallback_models:
            if fm not in configured_models:
                configured_models.append(fm)
        self.models = configured_models

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        prompt = generate_synthesis_prompt(structured_input)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Farhaan-jpg/xauusd-market-agent",
            "X-Title": "XAUUSD Market Intelligence Agent",
            "Content-Type": "application/json"
        }

        last_error = None
        for model in self.models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }

            try:
                logger.info(f"Trying OpenRouter model '{model}'...")
                async with httpx.AsyncClient(timeout=min(settings.AI_TIMEOUT_SECONDS, 15)) as client:
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
                elif response.status_code == 404:
                    logger.warning(f"OpenRouter model '{model}' not found / unavailable (404). Trying next model...")
                elif response.status_code == 402:
                    logger.warning(f"OpenRouter model '{model}' requires more credits (402). Trying next model...")
                elif response.status_code == 429:
                    logger.warning(f"OpenRouter model '{model}' hit rate limit (429). Trying next model...")
                else:
                    logger.warning(f"OpenRouter model '{model}' failed ({response.status_code}): {response.text[:200]}")
            except Exception as e:
                logger.warning(f"OpenRouter model '{model}' exception: {e}")
                last_error = e

        raise last_error or Exception("All OpenRouter candidate models failed.")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
