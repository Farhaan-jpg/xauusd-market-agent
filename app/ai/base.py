"""Pydantic schemas and abstract base class for AI Providers."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AISynthesisOutput(BaseModel):
    """Strict schema for AI Market Intelligence output."""
    direction: str = Field(description="BULLISH, BEARISH, NEUTRAL, STRONGLY BULLISH, STRONGLY BEARISH, or INSUFFICIENT DATA")
    score: float = Field(ge=-100.0, le=100.0, description="Directional score from -100 to +100")
    confidence: float = Field(ge=0.0, le=100.0, description="Confidence score from 0 to 100")
    dominant_drivers: List[str] = Field(default_factory=list, description="Top 2-3 primary factors shaping the market")
    supporting_factors: List[str] = Field(default_factory=list, description="Factors supporting the direction")
    contradicting_factors: List[str] = Field(default_factory=list, description="Conflicting or opposing factors")
    liquidity_summary: List[str] = Field(default_factory=list, description="Key overhead and underlying liquidity zones")
    macro_summary: str = Field(description="Contextual synthesis of DXY, Treasury Yields, and Fed policy")
    news_summary: str = Field(description="Contextual synthesis of recent news and geopolitical developments")
    risk_factors: str = Field(description="Key tail risks and upcoming volatility triggers")
    data_quality: str = Field(default="GOOD", description="Assessment of input data reliability")

class BaseAIProvider(ABC):
    """Interface for AI Providers (Gemini, OpenRouter, Deterministic)."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def synthesize(self, structured_input: Dict[str, Any]) -> AISynthesisOutput:
        """Takes validated deterministic data and returns validated structured synthesis."""
        pass
