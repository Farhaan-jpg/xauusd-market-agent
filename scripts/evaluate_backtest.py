"""Evaluates historical predictive accuracy from stored snapshots."""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.backtest.evaluator import BacktestEvaluator
from app.storage.database import init_db

async def main():
    await init_db()
    result = await BacktestEvaluator.evaluate_accuracy()
    print("\n" + "="*60)
    print("HISTORICAL MARKET DIRECTION ACCURACY EVALUATION")
    print("="*60)
    print(json.dumps(result, indent=2))
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
