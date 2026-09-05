"""Abstract base class for all external data providers with error handling and health tracking."""
from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Optional
from app.core.logging import logger
from app.storage.repository import Repository

class BaseDataProvider(ABC):
    """Base interface for all market, macro, news, and calendar data providers."""

    def __init__(self, name: str):
        self.name = name

    async def record_health(self, is_healthy: bool, latency_ms: float = 0.0, error_message: str = "") -> None:
        """Records health metric in the repository database."""
        try:
            await Repository.update_provider_health(
                provider_name=self.name,
                is_healthy=is_healthy,
                latency_ms=latency_ms,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to record provider health for {self.name}: {e}")

    @abstractmethod
    async def fetch(self) -> Any:
        """Fetch data from the provider source."""
        pass
