"""candle_cache ZAMAN EKSENİ DENETİMİ — hangi sembol/TF/gün kaymış?

Kök neden (2026-08-12 denetimi): MT5'in `copy_rates` `time` alanı broker SUNUCU
saatindedir (UTC+2/+3). Onu doğrudan UTC sanıp yazan her yol barları 2-3 saat
İLERİ etiketler. data_recorder 2026-07-28/31'de düzeltildi, 5m serisi Temmuz'da
MT5-otoriteli onarıldı — ama 1m'in Mayıs-2026 toplu-doldurma partisi
(bar aralığı 2026-02-11 → 05-07) onarılmadı.

Bu betik hasarı ÖLÇER (yazmaz):
  · Referans = 5m serisi (Temmuz onarımından geçti; ayrıca canlı bot loguyla
    doğrulandı: USOIL Donchian seviyeleri 17/19 birebir).
  · Her TF, 5m'e resample edilip gün gün kıyaslanır; en iyi kayma (0/±60/±120/
    ±180/±240 dk) ve artık hata raporlanır.
  · Ek çapa: gün içi hacim profili — endeks/emtia için ABD açılışı (13:30 UTC
    yaz / 14:30 kış) en yoğun saattir; 5m'in kendisi kaymışsa bu tepe kayar.

Çalıştırma: python backend/research/candle_time_audit.py [--json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakeout_miner as fm  # noqa: E402

SYMBOLS = ["NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"]
TFS = ["1m", "15m", "30m", "1h"]          # 5m referans
LAGS_MIN = [0, -60, -120, -180, -240, 60, 120, 180]
CLEAN_TOL = 0.6                            # gün bazında ort |fark| eşiği (fiyat birimi)
MIN_OVERLAP_FRAC = 0.35                    # gün başına beklenen barın en az bu oranı


def tf_minutes(tf: str) -> int:
    return {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}[tf]


def daily_offsets(ref5: pd.Series, other: pd.Series, tf: str) -> pd.DataFrame:
    """Gün gün: en iyi kayma (dk) + o kaymadaki ortalama mutlak fark."""
    step = max(tf_minutes(tf), 5)
    a = ref5.resample(f"{step}min").last()
    b = other.resample(f"{step}min").last()
    # eşik TF'e göre: 1h'te günde ~24 bar var, sabit 60 eşiği hepsini elerdi
    min_overlap = max(8, int(24 * 60 / step * MIN_OVERLAP_FRAC))
    rows = []
    for gun, sub in a.groupby(a.index.date):
        best = (None, np.inf)
        for lag in LAGS_MIN:
            shifted = b.shift(lag // step) if lag % step == 0 else None
            if shifted is None:
                continue
            j = pd.DataFrame({"a": sub, "b": shifted}).dropna()
            if len(j) < min_overlap:
                continue
            err = float((j.a - j.b).abs().mean())
            if err < best[1]:
                best = (lag, err)
        if best[0] is not None:
            rows.append({"gun": gun, "kayma_dk": best[0], "hata": round(best[1], 3)})
    return pd.DataFrame(rows)


def volume_anchor(df5: pd.DataFrame) -> pd.DataFrame:
    """Ay ay: en yüksek ortalama hacimli UTC saati (ABD açılışı çapası)."""
    d = df5.dropna(subset=["volume"]).copy()
    if d.empty:
        return pd.DataFrame()
    d["ay"] = d["ts"].dt.to_period("M").astype(str)
    d["saat"] = d["ts"].dt.hour
    g = d.groupby(["ay", "saat"])["volume"].mean().reset_index()
    top = g.sort_values("volume", ascending=False).groupby("ay").head(1)
    return top.sort_values("ay")[["ay", "saat", "volume"]]


def main() -> None:
    out: dict = {}
    for sym in SYMBOLS:
        print(f"\n{'='*70}\n{sym}\n{'='*70}", flush=True)
        df5 = fm.fetch_candles(sym, "5m")
        if df5.empty:
            print("  5m yok — atlandı"); continue
        ref = df5.set_index("ts").close
        print(f"  5m referans: {len(df5)} bar ({df5.ts.iloc[0]:%Y-%m-%d} → {df5.ts.iloc[-1]:%Y-%m-%d})")

        va = volume_anchor(df5)
        if not va.empty:
            saatler = va.tail(8).apply(lambda r: f"{r['ay']}:{int(r['saat']):02d}", axis=1).tolist()
            print(f"  hacim tepesi (UTC saat, son 8 ay): {' '.join(saatler)}")
            print("    → ABD açılışı beklenen tepe: yaz 13, kış 14 (±1). Sapma varsa 5m'in KENDİSİ kaymıştır.")

        sym_out = {"volume_peak": va.to_dict("records") if not va.empty else []}
        for tf in TFS:
            df = fm.fetch_candles(sym, tf)
            if df.empty or len(df) < 500:
                print(f"  {tf:<4}: veri yok/az ({len(df)})")
                continue
            d = daily_offsets(ref, df.set_index("ts").close, tf)
            if d.empty:
                print(f"  {tf:<4}: örtüşen gün yok")
                continue
            kirli = d[(d.kayma_dk != 0) | (d.hata > CLEAN_TOL)]
            print(f"  {tf:<4}: {len(d)} gün · kayma dağılımı "
                  f"{dict(d.kayma_dk.value_counts().sort_index())}")
            # kaymalı blokları aralık olarak özetle
            bad = d[d.kayma_dk != 0].sort_values("gun")
            if not bad.empty:
                blocks, start, prev, lag = [], None, None, None
                for _, r in bad.iterrows():
                    if start is None or r.kayma_dk != lag or (r.gun - prev).days > 4:
                        if start is not None:
                            blocks.append((start, prev, lag))
                        start, lag = r.gun, r.kayma_dk
                    prev = r.gun
                if start is not None:
                    blocks.append((start, prev, lag))
                for a, b, lg in blocks:
                    print(f"       ⚠ {a} → {b}  kayma {lg:+d} dk")
            temiz = d[(d.kayma_dk == 0) & (d.hata <= CLEAN_TOL)]
            print(f"       temiz gün: {len(temiz)}/{len(d)}  "
                  f"(kayma 0 ve hata ≤ {CLEAN_TOL})")
            sym_out[tf] = {"gun": len(d), "temiz": len(temiz),
                           "bloklar": [{"ilk": str(a), "son": str(b), "kayma_dk": int(lg)}
                                       for a, b, lg in (blocks if not bad.empty else [])]}
        out[sym] = sym_out

    if "--json" in sys.argv:
        p = Path(__file__).resolve().parent.parent / "data" / "candle_time_audit.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
        print(f"\nrapor: {p}")


if __name__ == "__main__":
    main()
