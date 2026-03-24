from __future__ import annotations

import asyncio
import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.ais_oil_collector import AISOilCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    collector = AISOilCollector()
    await collector.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
