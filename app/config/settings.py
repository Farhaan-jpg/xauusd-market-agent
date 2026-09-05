"""Central application configuration using Pydantic Settings."""
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # General & Server Settings
    APP_NAME: str = "XAUUSD AI Market Intelligence & Liquidity Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    TIMEZONE: str = "Asia/Kolkata"

    # AI Configuration (Optional keys - fallback to deterministic if empty)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.7-flash"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "deepseek/deepseek-r1:free,meta-llama/llama-3.3-70b-instruct:free,google/gemini-2.0-flash-exp:free"
    AI_PRIORITY: str = "gemini_first"  # 'gemini_first', 'openrouter_first', 'deterministic_only'
    AI_TIMEOUT_SECONDS: int = 25
    AI_MAX_RETRIES: int = 3

    # Telegram Bot Configuration (Optional keys)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ALERTS_ENABLED: bool = True
    ALERT_COOLDOWN_MINUTES: int = 30
    DIRECTION_CHANGE_THRESHOLD_SCORE: int = 15

    # Data Provider Symbols
    SYMBOL_GOLD: str = "GC=F"
    SYMBOL_XAUUSD_SPOT: str = "XAUUSD=X"
    SYMBOL_DXY: str = "DX-Y.NYB"
    SYMBOL_US10Y: str = "^TNX"
    SYMBOL_US2Y: str = "^IRX"
    SYMBOL_TIPS: str = "TIP"

    # Optional External API Keys
    FRED_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None

    # Intervals (Seconds) & Schedule Controls
    ANALYSIS_INTERVAL_SECONDS: int = 180
    MARKET_DATA_INTERVAL_SECONDS: int = 60
    NEWS_FETCH_INTERVAL_SECONDS: int = 180
    ECONOMIC_FETCH_INTERVAL_SECONDS: int = 300
    PAUSE_ON_WEEKENDS: bool = True

    # Liquidity Engine Parameters
    LIQUIDITY_TOLERANCE_PIPS: float = 1.5
    EVIDENCE_CONFLICT_PENALTY: int = 20
    MIN_TOUCH_COUNT_CLUSTER: int = 2

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/xauusd_agent.db"

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def has_openrouter(self) -> bool:
        return bool(self.OPENROUTER_API_KEY and self.OPENROUTER_API_KEY.strip())

    @property
    def has_telegram(self) -> bool:
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID and self.TELEGRAM_BOT_TOKEN.strip() and self.TELEGRAM_CHAT_ID.strip())

    def update_runtime_config(self, updates: dict) -> None:
        """Dynamically updates configuration in memory."""
        for k, v in updates.items():
            if hasattr(self, k) and v is not None:
                # Type cast appropriately
                curr_val = getattr(self, k)
                if isinstance(curr_val, bool):
                    setattr(self, k, bool(v))
                elif isinstance(curr_val, int):
                    setattr(self, k, int(v))
                elif isinstance(curr_val, float):
                    setattr(self, k, float(v))
                else:
                    setattr(self, k, str(v).strip())

settings = Settings()
