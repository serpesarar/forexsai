"""Broker XAUUSD 1m barlarını UTC eksenine düzeltir ve önbelleğe yazar.

Zaman ekseni kuralı (satır bazlı, created_at ile ÖLÇÜLEREK):
  * lag = created_at − candle_time.  Kaydedici barı kapanıştan ~1-2 dk sonra yazar.
  * lag < −60 dk  → etiket broker sunucu saatinde (UTC+3, 2026-07-28 onarımı öncesi) → −3 saat.
  * lag ≥ −60 dk  → etiket UTC (canlı onarılmış kayıt veya sonradan UTC ile doldurulmuş).
  * −60 < lag < 0 dk → etiket güvenilmez (bar kapanmadan yazılmış görünüyor; çoğu günlük açılışta
    kaydedicinin offset ölçümünün sapması) → atılır (~360 satır).
  * 2026-07-28 18:00–21:00 etiketleri: fixbars.py bu pencereyi tümden atıyordu; burada satır bazlı
    bakıldı — hepsinin lag'i −178 (gerçek 15:00–18:00'de yazılmış kaymış satırlar, süreklilik
    17:59→18:00 etiketinde kesintisiz) → kaydırılarak KORUNUR. Gerçek 18:00–21:00 verisi kayıp (boşluk).
  * Düzeltme sonrası aynı UTC dakikasında iki satır kalırsa UTC-etiketli olan (lag≥−60) tercih edilir.
Doğrulama (bkz. 03 çıktısı): journal OPEN fiyatı ile düzeltilmiş 1m kapanışı arasındaki medyan mutlak fark
offset 0'da en küçük olmalı; ±60/±180 dk'da büyümeli.
Çıktı: data/xau_1m_utc.csv.gz  (t_utc, open, high, low, close, volume) — BID barları (MT5 varsayılanı)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SHIFT = pd.Timedelta(hours=3)
LAG_BROKER_MIN = -60.0
AMBIG_A = pd.Timestamp("2026-07-28 18:00", tz="UTC")
AMBIG_B = pd.Timestamp("2026-07-28 21:00", tz="UTC")


def build() -> pd.DataFrame:
    d = pd.read_csv(HERE / "data" / "xau_1m_raw.csv")
    d["ct"] = pd.to_datetime(d.candle_time, utc=True, format="ISO8601")
    d["ca"] = pd.to_datetime(d.created_at, utc=True, format="ISO8601")
    d["lag"] = (d.ca - d.ct).dt.total_seconds() / 60
    bad = (d.lag > LAG_BROKER_MIN) & (d.lag < 0)
    d = d[~bad].copy()
    broker = d.lag <= LAG_BROKER_MIN
    d["t_utc"] = d.ct.where(~broker, d.ct - SHIFT)
    d["pref"] = (~broker).astype(int)
    d = d.sort_values(["t_utc", "pref"]).drop_duplicates("t_utc", keep="last")
    print(f"satır {len(d)} | broker-etiketli düzeltilen {int(broker.sum())} | güvenilmez etiket atılan {int(bad.sum())}")
    return d[["t_utc", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def validate(bars: pd.DataFrame) -> None:
    rows = [json.loads(l) for l in open(HERE / "data" / "journal_xau_raw.jsonl")]
    pts = [(pd.Timestamp(r["ts"]), r["raw"]["trade"]["entry_price"]) for r in rows
           if (r["raw"].get("decision") or {}).get("action") == "OPEN"]
    s = bars.set_index("t_utc").close
    for off in (-180, -60, 0, 60, 180):
        diffs = []
        for ts, px in pts:
            t = (ts + pd.Timedelta(minutes=off)).floor("min")
            if t in s.index:
                diffs.append(abs(s[t] - px))
        print(f"  offset {off:+4d} dk: medyan |close−journal_price| = {np.median(diffs):.3f} (n={len(diffs)})")
    # gap kontrolü: art arda barlar arası açılış≈önceki kapanış
    b = bars.copy(); b["gap"] = b.t_utc.diff().dt.total_seconds() / 60
    j = (b.open - b.close.shift()).abs()
    print("  1-dk ardışık barlarda |open−prev close| medyan:", round(float(j[b.gap == 1].median()), 3),
          "| p99:", round(float(j[b.gap == 1].quantile(.99)), 3))
    hr = b.assign(rng=b.high - b.low, h=b.t_utc.dt.hour).groupby("h").rng.mean()
    print("  en oynak saat (UTC):", int(hr.idxmax()), "→ ABD açılışı/veri 12-14 UTC olmalı")


if __name__ == "__main__":
    bars = build()
    validate(bars)
    out = HERE / "data" / "xau_1m_utc.csv.gz"
    bars.to_csv(out, index=False)
    print("yazıldı", out, bars.t_utc.min(), "→", bars.t_utc.max())
