"""NOM gölge (paper) modu — her SHADOW_INTERVAL_MIN dakikada tahmin üret + `nom_predictions`'a yaz;
ufku dolan tahminlerin sonucunu (eğitimdeki AYNI etiket fonksiyonuyla) aynı satıra yaz.

Sızıntı: tahmin karar anında, sonuç bilinmeden yazılır; sonuç yalnız t_end geçtikten sonra, yalnız giriş barı ve
sonrası 1m barlarla hesaplanır. Emir açmaz; prediction_logs'a yazmaz. Fail-open: hata yalnız loglanır.

Çalıştırma: backend içinde `NOM_SHADOW_ENABLED=1` (main.py döngüsü) veya `python backend/scripts/nom_shadow.py --loop`.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import engine as NOM
from . import labels as LB
from . import live_data as LD

logger = logging.getLogger(__name__)
SHADOW_INTERVAL_MIN = int(os.getenv('NOM_SHADOW_INTERVAL_MIN', '15'))
SHADOW_TARGETS = [x.split(':') for x in os.getenv('NOM_SHADOW_TARGETS',
                  '15m:1x1,1h:1x1,1h:1.5x1,4h:1x1,4h:1.5x1.5,session:1x1').split(',')]
TABLE = 'nom_predictions'
NY = 'America/New_York'
# Faz 0 koruyucu spread modeli (NY saati → puan) = max(Dukascopy 2025, Pepperstone MT5) — etiketle aynı
SPREAD_NY_HOUR = {h: (1.5 if 9 <= h <= 17 else 3.41) for h in range(24)}
SPREAD_NY_HOUR.update({9: 1.46, 10: 1.4, 11: 1.404, 12: 1.405, 13: 1.394, 14: 1.395, 15: 1.405})


def _db():
    from database.supabase_client import get_supabase_client
    return get_supabase_client()


def _t_end(t_dec: int, hz: str) -> int:
    if hz != 'session':
        return t_dec + LB.HORIZONS[hz]['minutes'] * 60
    from . import nyse_calendar as CAL
    ny = pd.Timestamp(t_dec, unit='s', tz='UTC').tz_convert(NY)
    day0 = int(ny.normalize().tz_convert('UTC').timestamp())
    return day0 + CAL.cash_close_minutes(ny.date()) * 60


def record_once(now: float | None = None, asof: float | None = None, source: str | None = None) -> int:
    """asof verilirse o anın yeniden oynatması yazılır (geri doldurma; yalnız model eğitim sonundan SONRAKİ anlar
    örneklem dışıdır — çağıran sorumlu)."""
    db = _db()
    if db is None:
        return 0
    n = 0
    for hz, gk in SHADOW_TARGETS:
        try:
            r = NOM.predict(hz, gk, now=now) if asof is None else NOM.predict(hz, gk, asof=asof)
        except Exception as e:  # noqa: BLE001
            logger.warning('NOM gölge tahmin hatası %s %s: %s', hz, gk, e)
            continue
        if not r.get('tahmin'):
            continue
        t_dec = int(pd.Timestamp(r['veri']['son_bar_kapanis_utc']).timestamp())
        L, S = r['tahmin']['long'], r['tahmin']['short']
        atr_tf = LB.HORIZONS[hz]['atr_tf']
        row = {'t_dec': r['veri']['son_bar_kapanis_utc'], 'horizon': hz, 'geometry': r['geometri'],
               'model_version': r['model']['surum'], 'price': r['baglam']['fiyat'],
               'atr': r['atr_birimleri'][atr_tf],
               't_end': pd.Timestamp(_t_end(t_dec, hz), unit='s', tz='UTC').isoformat(),
               'p_long_tp': L['p_tp_once'], 'p_long_sl': L['p_sl_once'], 'p_long_to': L['p_zaman_asimi'],
               'exp_r_long': L['beklenen_r'], 'p_short_tp': S['p_tp_once'], 'p_short_sl': S['p_sl_once'],
               'p_short_to': S['p_zaman_asimi'], 'exp_r_short': S['beklenen_r'], 'status': r['durum'],
               'feature_summary': {'long_neden': [x['metin'] for x in L['neden']],
                                   'short_neden': [x['metin'] for x in S['neden']],
                                   'rejim': r['baglam']['rejim'], 'seans': r['baglam']['seans'],
                                   'vix': r['baglam']['vix']},
               'source': source or os.getenv('NOM_SHADOW_SOURCE', 'shadow')}
        try:
            res = db.table(TABLE).upsert(row, on_conflict='t_dec,horizon,geometry,model_version')   # sarmalayıcı hemen çalıştırır
            if isinstance(res, dict) and res.get('error'):
                raise RuntimeError(res['error'])
            n += 1
        except Exception as e:  # noqa: BLE001
            logger.warning('NOM gölge yazım hatası: %s', e)
    return n


def fill_outcomes(now: float | None = None, limit: int = 500) -> int:
    """Ufku dolmuş, sonucu boş satırları çöz (eğitimle aynı label_batch; ATR = karar anındaki kayıt)."""
    db = _db()
    if db is None:
        return 0
    now = now or time.time()
    res = (db.table(TABLE).select('id,t_dec,t_end,horizon,geometry,atr').is_('outcome_filled_at', 'null')
           .lt('t_end', datetime.fromtimestamp(now - 120, tz=timezone.utc).isoformat()).order('t_dec').limit(limit).execute())
    rows = getattr(res, 'data', None) or (res.get('data') if isinstance(res, dict) else None) or []
    if not rows:
        return 0
    b = LD.load_bars()
    h = pd.to_datetime(b.t, unit='s', utc=True).dt.tz_convert(NY).dt.hour.to_numpy()
    spr = np.array([SPREAD_NY_HOUR[x] for x in h])
    path = LB.Path1m(t=b.t.to_numpy(), o=b.open.to_numpy(), h=b.high.to_numpy(), l=b.low.to_numpy(),
                     c=b.close.to_numpy(), spr=spr)
    pos = {int(v): i for i, v in enumerate(b.t.to_numpy())}
    n = 0
    for r in rows:
        t_dec = int(pd.Timestamp(r['t_dec']).timestamp())
        t_end = int(pd.Timestamp(r['t_end']).timestamp())
        i0 = pos.get(t_dec)
        upd = {'outcome_filled_at': datetime.now(timezone.utc).isoformat()}
        if i0 is None or not r.get('atr'):
            upd |= {'outcome_long_cls': -1, 'outcome_short_cls': -1}
        else:
            tp, sl = (float(x) for x in r['geometry'].split('x'))
            d = LB.label_batch(path, np.array([i0]), np.array([float(r['atr'])]), np.array([t_end]), geoms=((tp, sl),),
                               expected_min=np.array([(t_end - t_dec) / 60.0]))
            gk = LB.geom_key(tp, sl)
            for side in ('long', 'short'):
                c = int(d[(side, gk, 'cls')][0])
                upd[f'outcome_{side}_cls'] = c
                rv = float(d[(side, gk, 'r')][0])
                upd[f'outcome_{side}_r'] = None if np.isnan(rv) else rv
        try:
            # DİKKAT: proje sarmalayıcısında update() ANINDA çalışır → filtre ÖNCE eklenmeli (aksi hâlde tüm tablo)
            res = db.table(TABLE).eq('id', r['id']).update(upd)
            if isinstance(res, dict) and res.get('error'):
                raise RuntimeError(res['error'])
            n += 1
        except Exception as e:  # noqa: BLE001
            logger.warning('NOM sonuç yazım hatası: %s', e)
    return n


async def shadow_loop() -> None:
    while True:
        try:
            if LD.market_open():
                await asyncio.to_thread(record_once)
            await asyncio.to_thread(fill_outcomes)
        except Exception as e:  # noqa: BLE001
            logger.warning('NOM gölge döngüsü: %s', e)
        await asyncio.sleep(SHADOW_INTERVAL_MIN * 60)
