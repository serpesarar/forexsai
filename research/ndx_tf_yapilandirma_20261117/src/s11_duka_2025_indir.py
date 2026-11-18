"""Adım 11 — Dukascopy USATECHIDXUSD 2025 günlük 1 dk BID mum dosyaları (herkese açık datafeed), kullanıcı onayıyla 2026-11-17.

Neden: ~/dukascopy_us100 2025 tik indirmesinde işlem saatlerinde 626 saat hiç tik yok (indirme hatası) → ana 2025 1 dk'sı
eksik, şüpheli fitillerin ~yarısı bu saatlerde. Dukascopy'nin KENDİ 1 dk mumları ayrıca indirilir; s03 bunları ana 1 dk ile
ortak dakikalarda birebir eşitlik dayatarak birleştirir. Kalıp: research/nom_20261113/src/duka_fetch.py (sıralı, yavaş;
paralel istek 503 verir). 404 → boş dosya (veri yok günü). Çıktı: out/duka_m1_2025/YYYYMMDD_BID.bi5 (git dışı).
"""
from __future__ import annotations

import datetime as D
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out/duka_m1_2025"
URL = "https://datafeed.dukascopy.com/datafeed/USATECHIDXUSD/{y}/{m:02d}/{d:02d}/BID_candles_min_1.bi5"
import os
PACE_S = float(os.getenv("DUKA_PACE_S", "4.0"))          # sunucu sık istekte engelliyor (ilk deneme 35 günde kesildi)
MAX_BLOCK_S = int(os.getenv("DUKA_MAX_BLOCK_S", "5400"))
FIXED_WAIT_S = int(os.getenv("DUKA_FIXED_WAIT_S", "0"))  # >0: 503'te sabit bekleme


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a, b = D.date(2025, 1, 1), D.date(2025, 12, 31)
    todo = []
    while a <= b:
        if a.weekday() != 5 and not (OUT / f"{a:%Y%m%d}_BID.bi5").exists():
            todo.append(a)
        a += D.timedelta(1)
    pri = OUT.parent / "duka_oncelik_2025.txt"  # eksik dakikalı DUKA mumlarının günleri önce
    if pri.exists():
        first = set(pri.read_text().split())
        todo.sort(key=lambda x: (f"{x:%Y%m%d}" not in first, x))
    print("todo", len(todo), flush=True)
    blocked, wait = 0, 60
    for i, x in enumerate(todo, 1):
        u = URL.format(y=x.year, m=x.month - 1, d=x.day)
        while True:
            try:
                data = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
                (OUT / f"{x:%Y%m%d}_BID.bi5").write_bytes(data)
                wait = 60
                break
            except urllib.error.HTTPError as ex:
                if ex.code == 404:
                    (OUT / f"{x:%Y%m%d}_BID.bi5").write_bytes(b"")
                    break
                code = ex.code
            except Exception as ex:  # noqa: BLE001 — ağ hatası: bekle, yeniden dene
                code = type(ex).__name__
            print(time.strftime("%H:%M:%S"), "blocked", code, x, "wait", wait, flush=True)
            w = FIXED_WAIT_S or wait
            time.sleep(w)
            blocked += w
            wait = min(wait * 2, 600)
            if blocked >= MAX_BLOCK_S:
                sys.exit(f"vazgeçildi; {i - 1} gün indi")
        if i % 50 == 0:
            print(time.strftime("%H:%M:%S"), "indi", i, "/", len(todo), flush=True)
        time.sleep(PACE_S)
    print("TAMAM", len(todo), flush=True)


if __name__ == "__main__":
    main()
