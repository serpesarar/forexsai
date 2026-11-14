"""NOM gölge modu koşucusu (karar desteği; emir açmaz).

  python backend/scripts/nom_shadow.py --once     # bir tahmin turu + olgunlaşan sonuçları doldur
  python backend/scripts/nom_shadow.py --loop     # NOM_SHADOW_INTERVAL_MIN (vars. 15) dakikada bir
  python backend/scripts/nom_shadow.py --fill     # yalnız sonuç doldur
Hedefler: NOM_SHADOW_TARGETS (vars. 15m:1x1,1h:1x1,1h:1.5x1,4h:1x1,4h:1.5x1.5,session:1x1).
Backend içinde aynı döngü: NOM_SHADOW_ENABLED=1 (main.py). İkisini aynı anda açma (upsert idempotent ama gereksiz).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from services.nom import live_data as LD  # noqa: E402
from services.nom import shadow as SH  # noqa: E402

def backfill(start_iso: str, end_iso: str, step_min: int = 60) -> int:
    """Model eğitim sonundan SONRAKİ dönemi örneklem dışı gölge kaydı olarak doldur (source='backfill_oos')."""
    import pandas as pd
    from services.nom import model_store as MS
    tu = pd.Timestamp(MS.load_bundle().meta['trained_until'], tz='UTC') + pd.Timedelta(days=1)
    t = max(pd.Timestamp(start_iso, tz='UTC'), tu)
    end = pd.Timestamp(end_iso, tz='UTC')
    n = 0
    while t <= end:
        if LD.market_open(t.timestamp()):
            n += SH.record_once(asof=t.timestamp(), source='backfill_oos')
        t += pd.Timedelta(minutes=step_min)
    return n


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '--once'
    if arg == '--loop':
        asyncio.run(SH.shadow_loop())
    elif arg == '--backfill':      # --backfill 2026-11-04 2026-11-13 [adım_dk]
        print('geri doldurulan', backfill(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 60))
        print('sonuç doldurulan', SH.fill_outcomes(limit=5000))
    elif arg == '--fill':
        print('sonuç doldurulan', SH.fill_outcomes())
    else:
        n = SH.record_once() if LD.market_open() else 0
        print('yazılan tahmin', n, '| sonuç doldurulan', SH.fill_outcomes())

