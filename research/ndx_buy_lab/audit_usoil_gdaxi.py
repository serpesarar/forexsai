"""audit_usoil_gdaxi.py — USOIL ve GDAXI momentum filtresi doğrulamalarını yeniden ölç.

NDX'inki 3 saatlik saat kayması yüzünden SIZINTILI çıktı (audit_momo_validation.py).
`bot_router.py`'de kayıtlı diğer iki iddia AYNI kurguyu kullanıyordu:
  USOIL.FOREX:SELL  filtresiz TEST %71.4 → filtreli %96.6
  GDAXI.INDX:BUY    3/3 split +EV; bootstrap %99.9; placebo p=0.000
  USOIL.FOREX:BUY   3/3 split +EV; bootstrap %100

Bu script her scope'u İKİ saat ekseninde koşturur:
  A) KAYMIŞ  — barlara +offset uygulanmış hali (orijinal kurgunun gördüğü)
  B) DOĞRU   — candle_cache artık onarılmış gerçek UTC
ve aradaki farkı gösterir. Ayrıca sızıntının imzasını ölçer: kaymış eksende
filtre, girişten "sonraki" 3 saatin hareketini öngörüyor mu?

Geometriler botun gerçeği (config.ROBUST_SCOPES):
  USOIL: tp %1.04 / sl %1.49 (yüzde)   ·   GDAXI: tp 67 / sl 119 puan
"""
from __future__ import annotations

import ast
import json

import numpy as np
import pandas as pd

DATA = __import__("pathlib").Path(__file__).resolve().parent / "data"
RNG = np.random.default_rng(7)

SCOPES = {
    "USOIL.FOREX:SELL": dict(tag="usoil", direction="SELL", tp=1.04, sl=1.49, is_pct=True,
                             rules=[("M30_dist_ema20_atr", "<", 0.0),
                                    ("M30_macd_hist", "<", 0.0),
                                    ("H1_sar_dist_atr", "<", 0.0)], fric=0.03),
    "USOIL.FOREX:BUY":  dict(tag="usoil", direction="BUY", tp=1.04, sl=1.49, is_pct=True,
                             rules=[("M30_stoch_k", ">", 70.0),
                                    ("M30_dist_ema20_atr", ">", 0.8),
                                    ("H1_sar_dist_atr", ">", 0.0)], fric=0.03),
    "GDAXI.INDX:BUY":   dict(tag="gdaxi", direction="BUY", tp=67.0, sl=119.0, is_pct=False,
                             rules=[("M15_stoch_k", ">", 70.0),
                                    ("M15_dist_ema20_atr", ">", 0.8),
                                    ("H1_sar_dist_atr", ">", 0.0)], fric=1.0),
}
SHIFT_MIN = 180          # onarım öncesi broker kayması (ABD-yaz)


def _f(v):
    try:
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def passes(f: dict, rules) -> bool | None:
    for k, op, thr in rules:
        v = _f(f.get(k))
        if v is None:
            return None
        if op == ">" and not (v > thr):
            return False
        if op == "<" and not (v < thr):
            return False
    return True


def replay(bars, ts, t, direction, tp_d, sl_d, fric):
    i = np.searchsorted(ts, t, side="right")
    if i >= len(ts):
        return None
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = bars[i, 0] + sgn * fric
    tp_px, sl_px = entry + sgn * tp_d, entry - sgn * sl_d
    for j in range(i, min(len(ts), i + 1440)):
        hi, lo = bars[j, 1], bars[j, 2]
        if (lo <= sl_px) if direction == "BUY" else (hi >= sl_px):
            return 0
        if (hi >= tp_px) if direction == "BUY" else (lo <= tp_px):
            return 1
    return None


def day_boot_diff(d, B=3000):
    """Gün-bloklu bootstrap: ΔWR (geçen − kalan) güven aralığı."""
    days = d.day.unique()
    by = {x: d[d.day == x] for x in days}
    out = []
    for _ in range(B):
        pick = RNG.choice(days, size=len(days), replace=True)
        s = pd.concat([by[x] for x in pick])
        a, b = s[s.mp], s[~s.mp]
        if len(a) < 5 or len(b) < 5:
            continue
        out.append(a.outcome.mean() - b.outcome.mean())
    if not out:
        return np.nan, np.nan, np.nan
    o = np.array(out)
    return float(np.quantile(o, .05)), float(np.quantile(o, .95)), float((o > 0).mean())


def run_axis(bars_df, sig, sc, label):
    ts = bars_df["ts"].values
    arr = bars_df[["open", "high", "low", "close"]].to_numpy()
    rows = []
    for r in sig.itertuples(index=False):
        i = np.searchsorted(ts, np.datetime64(r.ts), side="right")
        if i >= len(ts):
            continue
        px = arr[i, 0]
        tp_d = px * sc["tp"] / 100 if sc["is_pct"] else sc["tp"]
        sl_d = px * sc["sl"] / 100 if sc["is_pct"] else sc["sl"]
        o = replay(arr, ts, np.datetime64(r.ts), sc["direction"], tp_d, sl_d, sc["fric"])
        if o is None:
            continue
        rows.append(dict(ts=r.ts, mp=r.mp, outcome=o,
                         day=pd.Timestamp(r.ts).tz_convert("UTC").date()))
    d = pd.DataFrame(rows)
    if d.empty or d.mp.nunique() < 2:
        print(f"     {label}: yetersiz veri (n={len(d)})"); return None
    a, b = d[d.mp], d[~d.mp]
    lo, hi, p = day_boot_diff(d)
    print(f"     {label}")
    print(f"        filtresiz n={len(d):4d} WR={d.outcome.mean()*100:5.1f}%  |  "
          f"GEÇEN n={len(a):4d} WR={a.outcome.mean()*100:5.1f}%  |  "
          f"KALAN n={len(b):4d} WR={b.outcome.mean()*100:5.1f}%")
    print(f"        ΔWR = {(a.outcome.mean()-b.outcome.mean())*100:+5.1f} puan   "
          f"gün-bloklu %90 GA [{lo*100:+.1f}, {hi*100:+.1f}]  P(Δ>0)={p*100:.1f}%")
    return d


def leak_probe(bars_df, sig, label):
    """Kaymış eksende filtre, girişten SONRAKİ 180 dk'yı 'biliyor' mu?"""
    ts = bars_df["ts"].values
    px = bars_df["close"].to_numpy()
    rows = []
    for r in sig.itertuples(index=False):
        i = np.searchsorted(ts, np.datetime64(r.ts), side="right")
        if i + 180 >= len(px):
            continue
        rows.append(dict(mp=r.mp, fwd=(px[i + 180] - px[i]) / px[i] * 100))
    d = pd.DataFrame(rows)
    if d.empty or d.mp.nunique() < 2:
        return
    a, b = d[d.mp], d[~d.mp]
    print(f"        [{label}] girişten sonraki 180dk: GEÇEN {a.fwd.mean():+.3f}%  "
          f"KALAN {b.fwd.mean():+.3f}%  fark {a.fwd.mean()-b.fwd.mean():+.3f}%")


def main():
    cache = {}
    for scope, sc in SCOPES.items():
        tag = sc["tag"]
        if tag not in cache:
            b = pd.read_csv(DATA / f"bars_1m_{tag}.csv", parse_dates=["ts"])
            b["ts"] = pd.to_datetime(b["ts"], utc=True)
            b = b.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
            s = pd.read_csv(DATA / f"signals_{tag}.csv")
            s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
            def _parse(v):
                if isinstance(v, dict):
                    return v
                if not isinstance(v, str) or not v.startswith("{"):
                    return {}
                try:
                    return json.loads(v)          # gerçek JSON
                except Exception:
                    try:
                        return ast.literal_eval(v)  # python dict repr (CSV yazımı)
                    except Exception:
                        return {}
            s["fac"] = s["factors"].apply(_parse)
            cache[tag] = (b, s)
        bars, sigs = cache[tag]
        sig = sigs[(sigs.model_type.isin(["pulse1", "pulse2", "pulse3"]))
                   & (sigs.ml_direction == sc["direction"])].copy()
        sig["mp"] = sig["fac"].apply(lambda f: passes(f, sc["rules"]))
        sig = sig[sig.mp.notna()].copy()
        sig["mp"] = sig["mp"].astype(bool)
        print(f"\n══════ {scope} ══════")
        print(f"   factors taşıyan sinyal: {len(sig)} "
              f"(filtre geçen %{sig.mp.mean()*100:.0f})")
        if len(sig) < 60:
            print("   → n yetersiz, ölçüm yapılmadı"); continue
        shifted = bars.copy()
        shifted["ts"] = shifted["ts"] + pd.Timedelta(minutes=SHIFT_MIN)
        run_axis(shifted, sig, sc, "A) KAYMIŞ eksen (orijinal kurgunun gördüğü)")
        leak_probe(shifted, sig, "sızıntı imzası")
        run_axis(bars, sig, sc, "B) DOĞRU eksen (onarılmış candle_cache)")
        leak_probe(bars, sig, "doğru eksen")


if __name__ == "__main__":
    main()
