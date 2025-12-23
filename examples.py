import asyncio
import json
from typing import AsyncIterator

import numpy as np

from rhythm_detector_v2 import RhythmDetector, RhythmConfig


async def simulated_stream() -> AsyncIterator[float]:
    t = 0
    while t < 300:
        price = 100 + np.sin(2 * np.pi * (1 / 45) * t) + np.random.normal(scale=0.01)
        yield float(price)
        await asyncio.sleep(0.01)
        t += 1


def run_realtime_simulation() -> None:
    detector = RhythmDetector(RhythmConfig(window_seconds=300))
    for idx, price in enumerate(np.linspace(100, 101, 300)):
        detector.add_tick(price, timestamp=float(idx))
        if idx % 20 == 0:
            detector.detect_wave_pattern()
            print(detector.should_trade())


async def run_async_stream() -> None:
    detector = RhythmDetector(RhythmConfig(window_seconds=300))
    idx = 0
    async for price in simulated_stream():
        detector.add_tick(price, timestamp=float(idx))
        if idx % 15 == 0:
            state = detector.detect_wave_pattern()
            decision = detector.should_trade()
            print(json.dumps({"state": state, "decision": decision}, ensure_ascii=False))
        idx += 1


if __name__ == "__main__":
    run_realtime_simulation()
    asyncio.run(run_async_stream())
