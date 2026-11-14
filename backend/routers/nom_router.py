"""NASDAQ Olasılık Motoru (NOM) API'si — karar desteği, OTOMATİK İŞLEM AÇMAZ.

  GET /api/probability/nasdaq?horizon=1h&geometry=1.5x1.0   (takma ad: GET /probability/nasdaq)
      → LONG/SHORT P(TP önce)/P(SL önce)/P(zaman aşımı), beklenen R, WF bandı, bağlam, SHAP nedenleri, durum
  GET /api/probability/nasdaq/meta          → etkin model sürümü, hedef başına kanıt durumu ve eşik
  GET /api/probability/nasdaq/calibration   → canlı kalibrasyon (nom_predictions) + WF referans bandı
  GET /api/probability/nasdaq/drift         → özellik PSI kayması + kalibrasyon bozulması uyarısı
Araştırma: research/nom_20261113/ (FAZ_0…9 raporları, PROTOCOL.md).
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query

from services.nom import engine as NOM
from services.nom import model_store as MS

logger = logging.getLogger(__name__)
router = APIRouter(tags=['nom'])
HZ_PATTERN = '^(15m|1h|4h|session)$'


def _asof(v: str | None) -> float | None:
    if not v:
        return None
    try:
        import pandas as pd
        if v.replace('.', '').isdigit():
            return float(v)
        ts = pd.Timestamp(v)
        ts = ts.tz_localize('UTC') if ts.tzinfo is None else ts.tz_convert('UTC')
        return float(ts.timestamp())
    except Exception as e:  # noqa: BLE001
        raise ValueError(f'asof biçimi ISO tarih veya epoch olmalı: {v}') from e


async def _predict(horizon: str, geometry: str, asof: str | None = None) -> dict:
    try:
        a = _asof(asof)
        if a is None:
            return await asyncio.to_thread(NOM.predict, horizon, geometry)
        return await asyncio.to_thread(NOM.predict, horizon, geometry, None, None, None, None, a)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f'model paketi yok: {e}') from e
    except Exception as e:  # noqa: BLE001
        logger.exception('NOM tahmin hatası')
        raise HTTPException(status_code=500, detail=f'NOM hatası: {e}') from e


@router.get('/api/probability/nasdaq')
async def probability_nasdaq(horizon: str = Query('1h', pattern=HZ_PATTERN),
                             geometry: str = Query('1.5x1.0', max_length=12),
                             asof: str | None = Query(None, max_length=40, description='yeniden oynatma anı (ISO/epoch)')):
    return await _predict(horizon, geometry, asof)


@router.get('/probability/nasdaq', include_in_schema=False)
async def probability_nasdaq_alias(horizon: str = Query('1h', pattern=HZ_PATTERN),
                                   geometry: str = Query('1.5x1.0', max_length=12), asof: str | None = Query(None)):
    return await _predict(horizon, geometry, asof)


@router.get('/api/probability/nasdaq/meta')
async def nom_meta():
    try:
        b = MS.load_bundle()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    t = {k: {kk: v.get(kk) for kk in ('proven', 'dev_passes', 'rule', 'threshold', 'base_p_tp', 'base_ev_r',
                                       'final_ev_r', 'final_bss')} for k, v in b.meta['targets'].items()}
    return {'surum': b.version, 'egitim_sonu': b.meta.get('trained_until'), 'veri': b.meta.get('data_version'),
            'olusturma': b.meta.get('created'), 'hedefler': t}


@router.get('/api/probability/nasdaq/calibration')
async def nom_calibration(horizon: str = Query('1h', pattern=HZ_PATTERN), geometry: str = Query('1.5x1.0'),
                          days: int = Query(56, ge=1, le=365),
                          source: str | None = Query(None, pattern='^(shadow|backfill_oos)$')):
    from services.nom import calibration as CB
    try:
        return await asyncio.to_thread(CB.live_report, horizon, NOM.norm_geometry(geometry), days, source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get('/api/probability/nasdaq/drift')
async def nom_drift(horizon: str = Query('1h', pattern=HZ_PATTERN), geometry: str = Query('1x1')):
    from services.nom import drift as DR
    return await asyncio.to_thread(DR.report, horizon, NOM.norm_geometry(geometry))
