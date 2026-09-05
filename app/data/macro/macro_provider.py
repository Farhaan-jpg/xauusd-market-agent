"""Macro Data Provider fetching DXY, US Yields, TIPS real yield proxy, and Risk sentiment."""
import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional
import yfinance as yf
from app.config.settings import settings
from app.core.logging import logger
from app.data.base import BaseDataProvider

class MacroDataProvider(BaseDataProvider):
    """Fetches macro indicators: Dollar Index, 10Y/2Y Yields, TIPS, and VIX."""

    def __init__(self):
        super().__init__(name="Macro_Provider")

    async def fetch(self) -> Dict[str, Any]:
        start_time = time.time()
        try:
            loop = asyncio.get_running_loop()
            macro_data = await loop.run_in_executor(None, self._fetch_sync)
            latency_ms = (time.time() - start_time) * 1000
            await self.record_health(is_healthy=True, latency_ms=latency_ms)
            return macro_data
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"MacroDataProvider error: {e}")
            await self.record_health(is_healthy=False, latency_ms=latency_ms, error_message=str(e))
            # Return safe default structure on error
            return self._get_fallback_macro_data()

    def _fetch_sync(self) -> Dict[str, Any]:
        results = {}

        # 1. DXY / US Dollar Index
        dxy_data = self._get_ticker_snapshot(["DX-Y.NYB", "UUP", "USDX"])
        results["dxy"] = dxy_data

        # 2. US 10-Year Yield (^TNX is yield * 10, e.g. 43.50 = 4.35%)
        us10y_data = self._get_ticker_snapshot(["^TNX", "IEF"])
        if us10y_data and us10y_data.get("price") and us10y_data["price"] > 10.0 and "^TNX" in us10y_data.get("symbol", ""):
            us10y_data["yield_pct"] = us10y_data["price"] / 10.0
        else:
            us10y_data["yield_pct"] = us10y_data.get("price", 0.0)
        results["us10y"] = us10y_data

        # 3. US 2-Year Yield (^IRX 13-week bill / 2Y proxy)
        us2y_data = self._get_ticker_snapshot(["^IRX", "SHY"])
        if us2y_data and us2y_data.get("price") and us2y_data["price"] > 10.0 and "^IRX" in us2y_data.get("symbol", ""):
            us2y_data["yield_pct"] = us2y_data["price"] / 10.0
        else:
            us2y_data["yield_pct"] = us2y_data.get("price", 0.0)
        results["us2y"] = us2y_data

        # 4. TIPS Real Yield Proxy (TIP ETF)
        tip_data = self._get_ticker_snapshot(["TIP"])
        results["tip"] = tip_data

        # 5. Risk Sentiment / VIX
        vix_data = self._get_ticker_snapshot(["^VIX"])
        results["vix"] = vix_data

        # Yield Curve Spread (10Y - 2Y)
        y10 = results["us10y"].get("yield_pct", 0.0)
        y2 = results["us2y"].get("yield_pct", 0.0)
        results["yield_spread_10y_2y"] = round(y10 - y2, 3)

        results["timestamp"] = datetime.now(timezone.utc)
        results["status"] = "AVAILABLE"
        return results

    def _get_ticker_snapshot(self, symbols: list) -> Dict[str, Any]:
        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="5d", interval="1d")
                if not hist.empty and len(hist) >= 1:
                    curr = float(hist["close"].iloc[-1])
                    prev = float(hist["close"].iloc[-2]) if len(hist) >= 2 else curr
                    change_pct = ((curr - prev) / prev) * 100.0 if prev > 0 else 0.0
                    return {
                        "symbol": sym,
                        "price": round(curr, 4),
                        "change_pct": round(change_pct, 3),
                        "available": True
                    }
            except Exception as e:
                logger.debug(f"Could not fetch macro symbol {sym}: {e}")
                continue

        return {"symbol": symbols[0], "price": 0.0, "change_pct": 0.0, "available": False}

    def _get_fallback_macro_data(self) -> Dict[str, Any]:
        return {
            "dxy": {"symbol": "DX-Y.NYB", "price": 104.0, "change_pct": 0.0, "available": False},
            "us10y": {"symbol": "^TNX", "price": 4.2, "yield_pct": 4.2, "change_pct": 0.0, "available": False},
            "us2y": {"symbol": "^IRX", "price": 4.1, "yield_pct": 4.1, "change_pct": 0.0, "available": False},
            "tip": {"symbol": "TIP", "price": 107.0, "change_pct": 0.0, "available": False},
            "vix": {"symbol": "^VIX", "price": 15.0, "change_pct": 0.0, "available": False},
            "yield_spread_10y_2y": 0.1,
            "timestamp": datetime.now(timezone.utc),
            "status": "FALLBACK"
        }
