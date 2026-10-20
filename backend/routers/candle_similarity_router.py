"""Mum benzerlik (görsel eşleştirme) API'si.

  GET /api/candle-similarity/{symbol}?tf=1h&n=50&k=20 → son n mumun geçmişteki en benzer k eşi + sonrasında ne oldu
  GET /api/candle-similarity/reliability            → motorun geriye-dönük isabet karnesi (sembol × TF × n)
Bilgi amaçlıdır; sinyal üretmez, prediction_logs'a yazmaz.
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from services.candle_similarity_service import get_similarity, load_reliability

router = APIRouter(prefix="/api/candle-similarity", tags=["candle-similarity"])
logger = logging.getLogger(__name__)


@router.get("/reliability")
async def reliability():
    return load_reliability()


@router.get("/{symbol}")
async def similarity(
    symbol: str,
    tf: str = Query("1h", description="5m / 15m / 30m / 1h / 4h"),
    n: int = Query(50, ge=10, le=300, description="Eşleştirilecek son mum sayısı"),
    k: int = Query(20, ge=1, le=50, description="Döndürülecek eşleşme sayısı"),
):
    try:
        return await get_similarity(symbol, tf, n, k)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("candle-similarity failed %s %s n=%s", symbol, tf, n)
        raise HTTPException(status_code=500, detail=str(e))
