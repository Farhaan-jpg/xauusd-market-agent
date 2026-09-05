"""Google Gemini API Provider for Market Intelligence Synthesis."""
import asyncio
import json
import re
import time
from typing import Any, Dict, Optional
import httpx
from app.ai.base import AISynthesisOutput, BaseAIProvider
from app.ai.prompts.prompts import SYSTEM_PROMPT, generate_synthesis_prompt
from app.config.settings import settings
from app.core.logging import logger

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI integration using direct REST endpoints with retry and validation."""

    def __init__(self):
        super().__init__(name="Google_Gemini")
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-2.5-flash"

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = generate_synthesis_prompt(structured_input)

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        last_error = None
        for attempt in range(1, settings.AI_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                    response = await client.post(url, json=payload)

                if response.status_code == 200:
                    res_json = response.json()
                    candidates = res_json.get("candidates", [])
                    if not candidates:
                        raise ValueError("No candidate responses returned from Gemini.")

                    raw_text = candidates[0]["content"]["parts"][0]["text"]
                    clean_json_str = self._clean_json(raw_text)
                    parsed = json.loads(clean_json_str)

                    # Validate with Pydantic
                    validated_output = AISynthesisOutput(**parsed)
                    return validated_output
                else:
                    err_msg = f"Gemini API returned status {response.status_code}: {response.text}"
                    logger.warning(f"Gemini attempt {attempt} failed: {err_msg}")
                    last_error = Exception(err_msg)

            except Exception as e:
                logger.warning(f"Gemini attempt {attempt} exception: {e}")
                last_error = e

            # Exponential backoff before retry
            if attempt < settings.AI_MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)

        raise last_error or Exception("Gemini synthesis failed after max retries.")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
