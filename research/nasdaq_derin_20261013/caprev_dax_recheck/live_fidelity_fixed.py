"""Canlı kod (yeni deneme/caprev_live.py saf fonksiyonları) ↔ DÜZELTİLMİŞ araştırma olayları.

(A) Gerçek-UTC barlar: canlı mantık düzeltilmiş kartın DAX olaylarını birebir üretiyor mu? (orijinal sadakat testi
    aynı hatalı veriyi iki tarafa da verdiği için ekseni sınamıyordu.)
(B) Canlı 'tek anlık broker ofseti' etkisi: bot 1500 H1 barın HEPSİNİ o anki ofsetle (tick.time − now) UTC'ye
    çevirir. Broker saati NY+7 olduğundan son ABD DST geçişinden ÖNCEKİ barlar ±60 dk kayar (Mart geçişi sonrası
    eski barlar 60 dk ERKEN, Kasım sonrası 60 dk GEÇ). Geçişten sonraki 35 takvim günü için bu kayma taklit edilir,
    tetik/pdl/stres/dvol kararı (A) ile karşılaştırılır.
Canlı koda ve bota DOKUNMAZ; yalnız saf fonksiyonları içe aktarır.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
sys.path.insert(0, str(ROOT / "yeni deneme")); sys.path.insert(0, str(ROOT / "research/ndx_gate_forge"))
import caprev_live as cl  # noqa: E402
from long_data import macro  # noqa: E402

HERE = Path(__file__).resolve().parent
PROF = cl.PROFILES["GDAXI.INDX"]
vix = macro().VIX_close.dropna()
HIST = {str(d.date()): float(v) for d, v in vix.items()}


def to_bars(df: pd.DataFrame) -> list[dict]:
    return [{"t": int(t.timestamp()), "open": o, "high": h, "low": l, "close": c}
            for t, o, h, l, c in zip(df.ts, df.open, df.high, df.low, df.close)]


def decide(bars: list[dict], today: date) -> dict | None:
    days = cl.rth_days(bars, PROF)
    ctx = cl.daily_context(days, today); v = cl.prev_day_vix(HIST, today)
    if ctx is None or ctx["pdl"] is None or not ctx["stress"] or v is None or v < cl.VIX_MIN:
        return None
    todays = [b for b in bars if cl.cs.to_local(b["t"], PROF["tz"])[0] == today]
    tr = cl.trigger(todays, PROF, today, ctx["pdl"])
    return None if tr is None else {"t": tr["t"], "pdl": ctx["pdl"], "dvol": ctx["dvol"]}


def us_switches(y0: int, y1: int) -> list[tuple[date, int]]:
    out = []
    for y in range(y0, y1 + 1):
        out.append((cl.cs._nth_weekday(y, 3, 6, 2), -60))   # Mart: eski barlar 60 dk erken görünür
        out.append((cl.cs._nth_weekday(y, 11, 6, 1), +60))  # Kasım: eski barlar 60 dk geç görünür
    return sorted(out)


if __name__ == "__main__":
    fx = pd.read_parquet(HERE / "data_fixed/dax_1h.parquet")
    fx = fx[fx.ts >= "2018-10-01"].reset_index(drop=True)
    bars = to_bars(fx)
    # (A) — tüm günler, gerçek UTC
    by_day: dict[date, list] = {}
    for b in bars:
        by_day.setdefault(cl.cs.to_local(b["t"], "EU")[0], []).append(b)
    days_all = cl.rth_days(bars, PROF)
    live = {}
    for today in sorted(by_day):
        if today < date(2019, 3, 1) or today.weekday() not in cl.TRADE_WEEKDAYS:
            continue
        ctx = cl.daily_context(days_all, today); v = cl.prev_day_vix(HIST, today)
        if ctx is None or ctx["pdl"] is None or not ctx["stress"] or v is None or v < cl.VIX_MIN:
            continue
        tr = cl.trigger(by_day[today], PROF, today, ctx["pdl"])
        if tr:
            live[today] = pd.Timestamp(tr["t"], unit="s", tz="UTC")
    tr = pd.read_csv(HERE / "results/trades_DAXfix.csv", parse_dates=["nyd", "trig_ts"])
    tr = tr[tr.m == "DAX"]
    card = {d.date(): t for d, t in zip(tr.nyd, tr.trig_ts)}
    both = set(live) & set(card)
    print(f"(A) düzeltilmiş kart {len(card)} olay, canlı kod {len(live)}, ortak gün {len(both)}, "
          f"aynı tetik barı {sum(live[d] == card[d] for d in both)}")
    print("    yalnız kartta:", sorted(set(card) - set(live)), " yalnız canlı:", sorted(set(live) - set(card)))
    # (B) — DST geçişi sonrası 35 gün, tek-ofset kayması taklidi
    diff, n_days, n_ev = [], 0, 0
    ts = fx.ts
    for sw, shift in us_switches(2019, 2026):
        sw_utc = pd.Timestamp(sw).tz_localize("UTC") + pd.Timedelta(hours=7)
        for k in range(1, 36):
            today = sw + timedelta(days=k)
            if today.weekday() not in cl.TRADE_WEEKDAYS or today < date(2019, 3, 1) or today > date(2026, 10, 1):
                continue
            lo = pd.Timestamp(today - timedelta(days=60)).tz_localize("UTC")
            hi = pd.Timestamp(today + timedelta(days=1)).tz_localize("UTC")
            w = fx[(ts >= lo) & (ts < hi)].copy()
            if w.empty:
                continue
            m = w.ts < sw_utc
            w.loc[m, "ts"] = w.ts[m] + pd.Timedelta(minutes=shift)
            a = decide(to_bars(fx[(ts >= lo) & (ts < hi)]), today)
            b = decide(to_bars(w), today)
            n_days += 1
            if a or b:
                n_ev += 1
            if (a is None) != (b is None) or (a and b and (a["t"] != b["t"] or abs(a["pdl"] - b["pdl"]) > 1e-6)):
                diff.append({"gun": today, "gecis": sw, "kayma": shift,
                             "dogru": None if a is None else (pd.Timestamp(a["t"], unit="s", tz="UTC").tz_convert("Europe/Berlin").strftime("%H:%M"), round(a["pdl"], 1)),
                             "canli_tek_ofset": None if b is None else (pd.Timestamp(b["t"], unit="s", tz="UTC").tz_convert("Europe/Berlin").strftime("%H:%M"), round(b["pdl"], 1))})
            elif a and b and abs(a["dvol"] - b["dvol"]) > 1e-9:
                diff.append({"gun": today, "gecis": sw, "kayma": shift, "dogru": ("dvol", round(a["dvol"], 5)),
                             "canli_tek_ofset": ("dvol", round(b["dvol"], 5))})
    print(f"(B) geçiş sonrası 35 gün içinde {n_days} işlem günü, {n_ev} günde (en az bir tarafta) olay; farklı karar/dvol:")
    print(pd.DataFrame(diff).to_string(index=False) if diff else "    yok")
