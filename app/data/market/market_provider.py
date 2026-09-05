"""Market Data Provider for XAUUSD / Gold futures using Yahoo Finance with multi-timeframe fetching."""
import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import yfinance as yf
from app.config.settings import settings
from app.core.logging import logger
from app.data.base import BaseDataProvider
from app.data.validation import DataValidationError, DataValidator

class MarketDataProvider(BaseDataProvider):
    """Fetches multi-timeframe OHLCV data for Gold (GC=F / XAUUSD=X)."""

    def __init__(self):
        super().__init__(name="YahooFinance_Market")
        self.primary_symbol = settings.SYMBOL_GOLD
        self.fallback_symbol = settings.SYMBOL_XAUUSD_SPOT

    async def fetch(self) -> Dict[str, Any]:
        """Fetches current price and multi-timeframe OHLC bars for gold."""
        start_time = time.time()
        try:
            # Run blocking yfinance calls in thread pool
            loop = asyncio.get_running_loop()
            market_data = await loop.run_in_executor(None, self._fetch_sync)

            latency_ms = (time.time() - start_time) * 1000
            await self.record_health(is_healthy=True, latency_ms=latency_ms)
            return market_data
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"MarketDataProvider error: {e}")
            await self.record_health(is_healthy=False, latency_ms=latency_ms, error_message=str(e))
            raise

    def _fetch_sync(self) -> Dict[str, Any]:
        """Synchronous fetcher executing multi-timeframe queries."""
        symbols = [self.primary_symbol, self.fallback_symbol, "GLD"]
        last_err = None

        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                # Fetch 1d historical data for 24h metrics
                hist_1d = ticker.history(period="5d", interval="1d")
                if hist_1d.empty:
                    continue

                hist_1d = DataValidator.validate_ohlc_df(hist_1d, timeframe="1d")
                current_price = float(hist_1d["close"].iloc[-1])

                # Fetch 1h data (last 30 days)
                hist_1h = ticker.history(period="1mo", interval="1h")
                if not hist_1h.empty:
                    hist_1h = DataValidator.validate_ohlc_df(hist_1h, timeframe="1h")
                else:
                    hist_1h = pd.DataFrame()

                # Fetch 15m data (last 5 days)
                hist_15m = ticker.history(period="5d", interval="15m")
                if not hist_15m.empty:
                    hist_15m = DataValidator.validate_ohlc_df(hist_15m, timeframe="15m")
                else:
                    hist_15m = pd.DataFrame()

                # Fetch 5m data (last 1 day)
                hist_5m = ticker.history(period="1d", interval="5m")
                if not hist_5m.empty:
                    hist_5m = DataValidator.validate_ohlc_df(hist_5m, timeframe="5m")
                else:
                    hist_5m = pd.DataFrame()

                # Calculate 24h change and accurate 24h High/Low range
                prev_close = float(hist_1d["close"].iloc[-2]) if len(hist_1d) >= 2 else current_price
                change_24h = round(((current_price - prev_close) / prev_close) * 100.0, 2) if prev_close > 0 else 0.0
                
                # Derive 24h High and Low from the last 24 hourly bars, falling back to 1d bar
                if not hist_1h.empty and len(hist_1h) >= 2:
                    h_slice = hist_1h.tail(24)
                    high_24h = float(h_slice["high"].max())
                    low_24h = float(h_slice["low"].min())
                else:
                    high_24h = float(hist_1d["high"].iloc[-1])
                    low_24h = float(hist_1d["low"].iloc[-1])

                # Guard against single-flat-tick collapse (e.g. weekend or after-hours flat candle)
                if abs(high_24h - low_24h) < 2.0 or high_24h <= low_24h:
                    # Apply realistic intraday volatility cushion (e.g. 0.45% average range)
                    vol_offset = round(current_price * 0.0045, 2)
                    high_24h = round(current_price + vol_offset, 2)
                    low_24h = round(current_price - vol_offset, 2)
                else:
                    high_24h = round(high_24h, 2)
                    low_24h = round(low_24h, 2)

                return {
                    "symbol": sym,
                    "price": current_price,
                    "change_24h": change_24h,
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "timestamp": datetime.now(timezone.utc),
                    "timeframes": {
                        "1d": hist_1d,
                        "1h": hist_1h,
                        "15m": hist_15m,
                        "5m": hist_5m
                    },
                    "data_quality": "GOOD"
                }
            except Exception as e:
                logger.warning(f"Failed fetching market data for {sym}: {e}")
                last_err = e
                continue

        raise DataValidationError(f"Could not fetch valid market data from any gold symbol. Last error: {last_err}")
