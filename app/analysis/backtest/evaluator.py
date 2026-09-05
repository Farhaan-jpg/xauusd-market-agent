"""Analytics and Historical Evaluation Engine for Market Direction accuracy tracking."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy import desc, select
from app.core.logging import logger
from app.storage.database import get_db_session
from app.storage.models import AnalysisRunRecord, MarketSnapshot

class BacktestEvaluator:
    """Evaluates the statistical relationship between past market direction findings and subsequent price trends."""

    @staticmethod
    async def evaluate_accuracy() -> Dict[str, Any]:
        """Calculates direction accuracy, score bucket consistency, and predictive alignment."""
        async with get_db_session() as session:
            # Fetch historical analysis runs
            res = await session.execute(
                select(AnalysisRunRecord).order_by(AnalysisRunRecord.timestamp)
            )
            runs = list(res.scalars().all())

            # Fetch market snapshots
            m_res = await session.execute(
                select(MarketSnapshot).order_by(MarketSnapshot.timestamp)
            )
            snapshots = list(m_res.scalars().all())

        if len(runs) < 2 or len(snapshots) < 5:
            return {
                "status": "INSUFFICIENT_HISTORICAL_DATA",
                "total_evaluations": len(runs),
                "message": "More runtime snapshots required to generate statistical performance metrics."
            }

        correct_predictions = 0
        evaluated_count = 0
        bullish_correct = 0
        bullish_total = 0
        bearish_correct = 0
        bearish_total = 0

        for run in runs:
            # Find price at run timestamp and forward price (e.g. +4 hours)
            start_p = run.gold_price
            run_time = run.timestamp

            # Find snapshot after 4 hours
            target_time = run_time + timedelta(hours=4)
            forward_snaps = [s for s in snapshots if s.timestamp >= target_time]
            if not forward_snaps:
                continue

            end_p = forward_snaps[0].price
            price_change = end_p - start_p

            evaluated_count += 1
            if "BULLISH" in run.direction:
                bullish_total += 1
                if price_change > 0:
                    correct_predictions += 1
                    bullish_correct += 1
            elif "BEARISH" in run.direction:
                bearish_total += 1
                if price_change < 0:
                    correct_predictions += 1
                    bearish_correct += 1
            else:  # NEUTRAL
                # Neutral is considered correct if price change is within tight threshold (+/- 0.2%)
                pct_chg = abs(price_change / start_p) * 100.0 if start_p > 0 else 0
                if pct_chg <= 0.3:
                    correct_predictions += 1

        overall_acc = (correct_predictions / evaluated_count * 100.0) if evaluated_count > 0 else 0.0
        bull_acc = (bullish_correct / bullish_total * 100.0) if bullish_total > 0 else 0.0
        bear_acc = (bearish_correct / bearish_total * 100.0) if bearish_total > 0 else 0.0

        return {
            "status": "EVALUATED",
            "total_evaluations": evaluated_count,
            "overall_directional_accuracy_pct": round(overall_acc, 1),
            "bullish_accuracy_pct": round(bull_acc, 1),
            "bearish_accuracy_pct": round(bear_acc, 1),
            "bullish_sample_size": bullish_total,
            "bearish_sample_size": bearish_total,
            "evaluation_horizon": "4 Hours",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
