"""Yalnız Evrim Paneli router'ını ayağa kaldıran hafif test app'i.

main.py tüm arka plan döngülerini (MT5 redis, scheduler, signal lifecycle)
başlatır — panel doğrulaması için gereksiz ve prod DB'ye yazar. Bu app yalnız
okuma yapan /api/evolution/* uçlarını sunar.

    python3 backend/scripts/evolution_test_app.py     # :8010
"""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND.parent / ".env")
load_dotenv(BACKEND / ".env")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routers.evolution_router import router as evolution_router  # noqa: E402

app = FastAPI(title="ForexSAI — Evrim Paneli (test)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
app.include_router(evolution_router)


@app.get("/health")
async def health():
    return {"ok": True, "app": "evolution-test"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8010")), log_level="info")
