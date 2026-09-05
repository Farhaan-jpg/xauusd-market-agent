"""CLI execution script to run a single one-shot Market Intelligence cycle."""
import asyncio
import json
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging import logger
from app.scheduler.orchestrator import IntelligenceOrchestrator

async def main():
    logger.info("Executing One-Shot XAUUSD Intelligence Cycle...")
    orchestrator = IntelligenceOrchestrator()
    await orchestrator.initialize()
    result = await orchestrator.run_cycle(force_report=True)
    
    print("\n" + "="*70)
    print("XAUUSD MARKET INTELLIGENCE RESULT")
    print("="*70)
    print(f"Price:        ${result['gold_price']:.2f}")
    print(f"Direction:    {result['direction']} ({result['score']:+.1f})")
    print(f"Confidence:   {result['confidence']:.0f}%")
    print(f"Provider:     {result['provider_used']}")
    print(f"Duration:     {result['cycle_duration_seconds']}s")
    print("="*70)
    print("Dominant Drivers:")
    for d in result['synthesis']['dominant_drivers']:
        print(f" • {d}")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
