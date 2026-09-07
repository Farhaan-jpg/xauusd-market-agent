"""Google Gemini API Provider for Market Intelligence Synthesis."""
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

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI integration using direct REST endpoints with dynamic multi-model discovery and fallback."""

    def __init__(self):
        super().__init__(name="Google_Gemini")
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._cached_live_models: List[str] = []
        self._last_discovery_time: float = 0.0

    async def get_available_models(self) -> List[str]:
        """Fetches active models from Google Gemini API when an API key is present."""
        if not self.api_key:
            return [
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-flash-latest",
                "gemini-2.5-pro",
                "gemini-3.7-flash"
            ]

        now = time.time()
        if self._cached_live_models and (now - self._last_discovery_time < 600):
            return self._cached_live_models

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    models_data = res.json().get("models", [])
                    active = []
                    for m in models_data:
                        name = m.get("name", "").replace("models/", "").strip()
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods and "gemini" in name.lower():
                            active.append(name)
                    if active:
                        self._cached_live_models = active
                        self._last_discovery_time = now
                        logger.info(f"Gemini API dynamically returned {len(active)} active models.")
                        return active
        except Exception as e:
            logger.debug(f"Gemini get_available_models error: {e}")

        return [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-pro",
            "gemini-3.7-flash"
        ]

    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Candidate models with primary model first, followed by discovered/verified running models
        primary_clean = self.model.replace("models/", "").strip()
        candidate_models = [primary_clean]

        live_models = await self.get_available_models()
        for m in live_models:
            clean_m = m.replace("models/", "").strip()
            if clean_m not in candidate_models:
                candidate_models.append(clean_m)

        verified_fallbacks = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-pro",
            "gemini-3.7-flash"
        ]
        for vf in verified_fallbacks:
            if vf not in candidate_models:
                candidate_models.append(vf)

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
        for current_model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
            
            try:
                logger.info(f"Attempting Gemini synthesis via model '{current_model}'...")
                async with httpx.AsyncClient(timeout=min(settings.AI_TIMEOUT_SECONDS, 16)) as client:
                    response = await client.post(url, json=payload)

                if response.status_code == 200:
                    res_json = response.json()
                    candidates = res_json.get("candidates", [])
                    if not candidates:
                        logger.warning(f"No candidate parts returned from Gemini {current_model}.")
                        continue

                    raw_text = candidates[0]["content"]["parts"][0]["text"]
                    clean_json_str = self._clean_json(raw_text)
                    parsed = json.loads(clean_json_str)

                    # Validate with Pydantic schema
                    validated_output = AISynthesisOutput(**parsed)
                    logger.info(f"Gemini synthesis successfully generated via model '{current_model}'.")
                    return validated_output

                elif response.status_code == 429:
                    # Quota / Rate limit on this model -> immediately advance to next candidate model
                    logger.warning(f"Gemini model '{current_model}' hit 429 Quota/Rate Limit. Instantly switching to next fallback model...")
                    last_error = Exception(f"Gemini model '{current_model}' quota exceeded (429).")
                    continue

                elif response.status_code in [400, 404]:
                    # Model not supported in this region/key -> advance to next model
                    logger.warning(f"Gemini model '{current_model}' returned status {response.status_code}. Trying next model...")
                    last_error = Exception(f"Gemini model '{current_model}' not available ({response.status_code}).")
                    continue

                elif response.status_code == 503:
                    # Model overloaded -> advance to next model
                    logger.warning(f"Gemini model '{current_model}' returned 503 (high demand). Switching to next model...")
                    last_error = Exception(f"Gemini model '{current_model}' overloaded (503).")
                    continue

                else:
                    err_msg = f"Gemini API ({current_model}) returned status {response.status_code}: {response.text[:200]}"
                    logger.warning(err_msg)
                    last_error = Exception(err_msg)
                    continue

            except Exception as e:
                logger.warning(f"Gemini request exception on model '{current_model}': {e}")
                last_error = e
                continue

        raise last_error or Exception("All Gemini candidate models failed.")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if "{" in text and "}" in text:
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            text = text[start_idx:end_idx]
        return text
