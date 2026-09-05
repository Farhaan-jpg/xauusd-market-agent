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
    """OpenRouter integration with multi-model fallback."""

    def __init__(self):
        super().__init__(name="OpenRouter")
        self.api_key = settings.OPENROUTER_API_KEY
        self.models = [m.strip() for m in settings.OPENROUTER_MODEL.split(",") if m.strip()]

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        prompt = generate_synthesis_prompt(structured_input)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/xauusd-market-agent",
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
                "response_format": {"type": "json_object"}
            }

            try:
                async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                    response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    res_json = response.json()
                    choices = res_json.get("choices", [])
                    if choices:
                        raw_content = choices[0]["message"]["content"]
                        clean_str = self._clean_json(raw_content)
                        parsed = json.loads(clean_str)
                        return AISynthesisOutput(**parsed)
                else:
                    logger.warning(f"OpenRouter model {model} failed ({response.status_code}): {response.text}")
            except Exception as e:
                logger.warning(f"OpenRouter model {model} error: {e}")
                last_error = e

        raise last_error or Exception("All OpenRouter models failed.")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
