"""SC — Dukascopy XAUUSD 1m indirici (kilitli KASA 2010–2017 BID + tüm yıllar için ASK örneklemi).

Neden:
- KASA dönemi 2010–2017 bu projede HİÇ kullanılmadı (fibo/kopya çalışmaları 2018+). Strateji iterasyonları onu görmez.
- Mevcut XAU 1m'de ASK yalnız 2025 Çarşambaları → 2018 spread'i 2025 medyan $'ıyla dolduruluyordu (altın 1.300 $ iken bp maliyeti
  ~2,5× şişik). Her yılın her Çarşambası ASK indirilir → yıl × UTC saat spread modeli (sc_veri.spread_modeli).

2018-01 → 2026-11 BID günleri fibo klasöründen (salt okunur) kullanılır, yeniden indirilmez.
Kullanım: .venv/bin/python -I research/soma_cozum_20261122/src/sc_duka.py [indir|kontrol]
"""
from __future__ import annotations

import datetime as dt
import http.client
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
CH = KOK / "data" / "chunks" / "XAU"
FIBO_CH = KOK.parents[0] / "fibo_altin_bolge_20261116" / "data" / "chunks" / "XAU"
FEED = "XAUUSD"
BID_ARALIK = (dt.date(2010, 1, 1), dt.date(2017, 12, 31))
ASK_ARALIK = (dt.date(2010, 1, 1), dt.date(2026, 11, 13))
ISCI = int(os.getenv("DUKA_WORKERS", "12"))
BEKLE_S = float(os.getenv("DUKA_PACE_S", "0.3"))
MAKS_DENEME = 5

_TL = threading.local()


def gunler(a: dt.date, b: dt.date):
    while a <= b:
        if a.weekday() != 5:  # Cumartesi verisi yok
            yield a
        a += dt.timedelta(1)


def _baglanti() -> http.client.HTTPSConnection:
    c = getattr(_TL, "c", None)
    if c is None:
        c = _TL.c = http.client.HTTPSConnection("datafeed.dukascopy.com", timeout=180)
    return c


def _al(d: dt.date, taraf: str) -> bool:
    hedef = CH / f"{d:%Y%m%d}_{taraf}.bi5"
    yol = f"/datafeed/{FEED}/{d:%Y}/{d.month - 1:02d}/{d:%d}/{taraf}_candles_min_1.bi5"
    bekle = 20
    for _ in range(MAKS_DENEME):
        try:
            c = _baglanti()
            c.request("GET", yol, headers={"User-Agent": "Mozilla/5.0", "Connection": "keep-alive"})
            r = c.getresponse()
            govde = r.read()
            if r.status in (200, 404):
                tmp = hedef.with_suffix(".tmp")
                tmp.write_bytes(govde if r.status == 200 else b"")
                tmp.rename(hedef)  # atomik: yarım dosya kalmaz
                time.sleep(BEKLE_S)
                return True
            kod = r.status
        except Exception as e:  # noqa: BLE001 — ağ hatası: bağlantıyı yenile, yeniden dene
            kod = type(e).__name__
            try:
                _TL.c.close()
            except Exception:  # noqa: BLE001
                pass
            _TL.c = None
        print(time.strftime("%H:%M:%S"), "engel", kod, d, taraf, "bekle", bekle, flush=True)
        time.sleep(bekle)
        bekle = min(bekle * 2, 120)
    return False


def yapilacaklar() -> list[tuple[dt.date, str]]:
    isler = [(d, "ASK") for d in gunler(*ASK_ARALIK) if d.weekday() == 2]  # önce ASK: spread modeli tüm dönemleri etkiler
    isler += [(d, "BID") for d in gunler(*BID_ARALIK)]
    return [x for x in isler if not (CH / f"{x[0]:%Y%m%d}_{x[1]}.bi5").exists()]


def guncel() -> None:
    """İleri gölge için 2026-11-14 → dün BID (+ Çarşamba ASK). fibo cache 2026-11-13'te bitiyor."""
    CH.mkdir(parents=True, exist_ok=True)
    dun = dt.date.today() - dt.timedelta(days=1)
    isler = [(d, "BID") for d in gunler(dt.date(2026, 11, 14), dun)]
    isler += [(d, "ASK") for d in gunler(dt.date(2026, 11, 14), dun) if d.weekday() == 2]
    # son iki gün yeniden çekilir (yarım gün verisi olabilir)
    isler = [x for x in isler if not (CH / f"{x[0]:%Y%m%d}_{x[1]}.bi5").exists() or x[0] >= dun - dt.timedelta(days=1)]
    with ThreadPoolExecutor(4) as ex:
        print("guncel", sum(ex.map(lambda x: _al(*x), isler)), "/", len(isler), flush=True)


def indir() -> None:
    CH.mkdir(parents=True, exist_ok=True)
    for tur in range(3):
        isler = yapilacaklar()
        print("tur", tur, "kalan", len(isler), flush=True)
        if not isler:
            break
        bitti = 0
        with ThreadPoolExecutor(ISCI) as ex:
            for _ in ex.map(lambda x: _al(*x), isler):
                bitti += 1
                if bitti % 100 == 0:
                    print(time.strftime("%H:%M:%S"), bitti, "/", len(isler), flush=True)
    print("İNDİRME BİTTİ, kalan", len(yapilacaklar()), flush=True)


def kontrol() -> None:
    bos = [f.name for f in sorted(CH.glob("*.bi5")) if f.stat().st_size == 0 and f.name.endswith("BID.bi5")
           and dt.date(int(f.name[:4]), int(f.name[4:6]), int(f.name[6:8])).weekday() < 5]
    print("dosya", len(list(CH.glob("*.bi5"))), "kalan", len(yapilacaklar()), "boş hafta içi BID", len(bos), bos[:20])


if __name__ == "__main__":
    {"indir": indir, "kontrol": kontrol, "guncel": guncel}[sys.argv[1] if len(sys.argv) > 1 else "indir"]()
