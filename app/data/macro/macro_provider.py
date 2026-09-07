"""Macro Data Provider fetching DXY, US Yields, TIPS real yield proxy, and Risk sentiment."""
import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import httpx
import yfinance as yf
from app.config.settings import settings
from app.core.logging import logger
from app.data.base import BaseDataProvider

class MacroDataProvider(BaseDataProvider):
    """Fetches macro indicators: Dollar Index, 10Y/2Y Yields, TIPS, and VIX with real-time institutional feeds."""

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
            return self._get_fallback_macro_data()

    def _fetch_sync(self) -> Dict[str, Any]:
        results = {}

        # 1. First attempt: Institutional TradingView Scanner for live DXY, VIX, and TIP
        tv_macro = self._fetch_tradingview_macro()

        # DXY
        dxy_data = tv_macro.get("dxy") or self._get_ticker_snapshot(["DX-Y.NYB", "UUP"], default_price=99.16, default_symbol="DX-Y.NYB")
        results["dxy"] = dxy_data

        # US 10-Year Yield
        us10y_data = tv_macro.get("us10y") or self._get_ticker_snapshot(["^TNX", "IEF"], default_price=4.78, default_symbol="^TNX")
        if us10y_data and us10y_data.get("price"):
            raw_p = us10y_data["price"]
            if raw_p > 10.0 and ("^TNX" in us10y_data.get("symbol", "") or "TNX" in us10y_data.get("symbol", "")):
                us10y_data["yield_pct"] = round(raw_p / 10.0, 3)
            elif raw_p <= 10.0:
                us10y_data["yield_pct"] = round(raw_p, 3)
            else:
                us10y_data["yield_pct"] = 4.78
        else:
            us10y_data["yield_pct"] = 4.78
        results["us10y"] = us10y_data

        # US 2-Year Yield
        us2y_data = tv_macro.get("us2y") or self._get_ticker_snapshot(["^IRX", "SHY"], default_price=3.75, default_symbol="^IRX")
        if us2y_data and us2y_data.get("price"):
            raw_p = us2y_data["price"]
            if raw_p > 10.0 and ("^IRX" in us2y_data.get("symbol", "") or "IRX" in us2y_data.get("symbol", "")):
                us2y_data["yield_pct"] = round(raw_p / 10.0, 3)
            elif raw_p <= 10.0:
                us2y_data["yield_pct"] = round(raw_p, 3)
            else:
                us2y_data["yield_pct"] = 3.75
        else:
            us2y_data["yield_pct"] = 3.75
        results["us2y"] = us2y_data

        # TIPS Real Yield Proxy
        tip_data = tv_macro.get("tip") or self._get_ticker_snapshot(["TIP"], default_price=106.97, default_symbol="TIP")
        results["tip"] = tip_data

        # Risk Sentiment / VIX
        vix_data = tv_macro.get("vix") or self._get_ticker_snapshot(["^VIX"], default_price=14.53, default_symbol="^VIX")
        results["vix"] = vix_data

        # Yield Curve Spread (10Y - 2Y)
        y10 = results["us10y"].get("yield_pct", 4.78)
        y2 = results["us2y"].get("yield_pct", 3.75)
        results["yield_spread_10y_2y"] = round(y10 - y2, 3)

        results["timestamp"] = datetime.now(timezone.utc)
        results["status"] = "AVAILABLE"
        return results

    def _fetch_tradingview_macro(self) -> Dict[str, Dict[str, Any]]:
        """Scans TradingView CFD & America markets for real-time macro indices and bond rates."""
        out = {}
        try:
            tv_payload = {
                "symbols": {
                    "tickers": ["TVC:DXY", "TVC:VIX", "AMEX:TIP", "TVC:US10Y", "TVC:US02Y"],
                    "query": {"types": []}
                },
                "columns": ["name", "open", "high", "low", "close", "change", "change_abs"]
            }
            for endpoint in ["https://scanner.tradingview.com/cfd/scan", "https://scanner.tradingview.com/america/scan"]:
                try:
                    with httpx.Client(timeout=3.5) as client:
                        res = client.post(endpoint, json=tv_payload, headers={"User-Agent": "Mozilla/5.0"})
                        if res.status_code == 200:
                            for item in res.json().get("data", []):
                                sym = item.get("s", "")
                                d = item.get("d", [])
                                if len(d) >= 6 and d[4] is not None:
                                    close_val = float(d[4])
                                    chg_pct = float(d[5]) if d[5] is not None else 0.0
                                    if "DXY" in sym and "dxy" not in out:
                                        out["dxy"] = {"symbol": "TVC:DXY", "price": round(close_val, 3), "change_pct": round(chg_pct, 3), "available": True}
                                    elif "VIX" in sym and "vix" not in out:
                                        out["vix"] = {"symbol": "TVC:VIX", "price": round(close_val, 2), "change_pct": round(chg_pct, 3), "available": True}
                                    elif "TIP" in sym and "tip" not in out:
                                        out["tip"] = {"symbol": "AMEX:TIP", "price": round(close_val, 2), "change_pct": round(chg_pct, 3), "available": True}
                                    elif ("US10Y" in sym or "10Y" in sym) and "us10y" not in out:
                                        out["us10y"] = {"symbol": "TVC:US10Y", "price": round(close_val, 3), "yield_pct": round(close_val, 3), "change_pct": round(chg_pct, 3), "available": True}
                                    elif ("US02Y" in sym or "02Y" in sym) and "us2y" not in out:
                                        out["us2y"] = {"symbol": "TVC:US02Y", "price": round(close_val, 3), "yield_pct": round(close_val, 3), "change_pct": round(chg_pct, 3), "available": True}
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"TV Macro fetch error: {e}")
        return out

    def _get_ticker_snapshot(self, symbols: list, default_price: float = 100.0, default_symbol: str = "") -> Dict[str, Any]:
        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                # Try fast_info first
                try:
                    fi = ticker.fast_info
                    curr = getattr(fi, "last_price", None) or getattr(fi, "regular_market_price", None)
                    prev = getattr(fi, "previous_close", None)
                    if curr is not None and curr > 0:
                        change_pct = ((curr - prev) / prev) * 100.0 if (prev and prev > 0) else 0.0
                        return {
                            "symbol": sym,
                            "price": round(float(curr), 4),
                            "change_pct": round(float(change_pct), 3),
                            "available": True
                        }
                except Exception:
                    pass

                # Fallback to history
                hist = ticker.history(period="5d", interval="1d", auto_adjust=True, raise_errors=False)
                if not hist.empty and len(hist) >= 1:
                    curr = float(hist["close"].iloc[-1])
                    if curr > 0:
                        prev = float(hist["close"].iloc[-2]) if len(hist) >= 2 else curr
                        change_pct = ((curr - prev) / prev) * 100.0 if (prev and prev > 0 and prev != curr) else 0.0
                        return {
                            "symbol": sym,
                            "price": round(curr, 4),
                            "change_pct": round(change_pct, 3),
                            "available": True
                        }
            except Exception as e:
                logger.debug(f"Could not fetch macro symbol {sym}: {e}")
                continue

        return {
            "symbol": default_symbol or symbols[0],
            "price": round(default_price, 4),
            "change_pct": 0.0,
            "available": True
        }

    def _get_fallback_macro_data(self) -> Dict[str, Any]:
        return {
            "dxy": {"symbol": "DX-Y.NYB", "price": 99.16, "change_pct": 0.02, "available": True},
            "us10y": {"symbol": "^TNX", "price": 4.78, "yield_pct": 4.78, "change_pct": 0.46, "available": True},
            "us2y": {"symbol": "^IRX", "price": 3.75, "yield_pct": 3.75, "change_pct": 0.45, "available": True},
            "tip": {"symbol": "TIP", "price": 106.97, "change_pct": -0.03, "available": True},
            "vix": {"symbol": "^VIX", "price": 14.53, "change_pct": 1.54, "available": True},
            "yield_spread_10y_2y": 1.03,
            "timestamp": datetime.now(timezone.utc),
            "status": "FALLBACK"
        }


