"""USOIL BREAKOUT scope — dürüst otopsi + giriş filtresi laboratuvarı (MT5 KUTUSUNDA çalışır).

NEDEN: 2026-08-06'da canlıya alınan USOIL_BREAKOUT scope'u (Donchian48 kırılımı +
5m EMA200 hizası, TP=SL=1.0×ATR) canlıda 19 işlemde WR %26.3 / −895$ verdi.
Araştırma raporu TEST'te %58.8 WR vaat ediyordu. Bu betik farkın nereden geldiğini
GERÇEK broker verisiyle (MT5 M5 + M1) ölçer ve giriş filtresi arar.

Sızıntı garantileri:
  * Karar yalnız SON KAPALI 5m bardan (botun check_usoil_breakout'u birebir).
  * Giriş = bar kapanışından sonraki İLK M1 barın açılışı + SPREAD (ask'ten alım).
  * Çözümleme M1 (bid) barlarıyla; aynı barda TP+SL → konservatif KAYIP.
  * Eşik araması yalnız TRAIN diliminde; TEST'e hiç bakılmadan dondurulur.

Çalıştırma (kutuda):  python backend/research/usoil_breakout_lab.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

CACHE = Path(__file__).resolve().parent / "_usoil_cache"
SYMBOL = "SpotCrude"
N_DON, N_EMA, N_ATR = 48, 200, 14
DAYS = 420
TRAIN_FRAC = 0.70
MAX_HOLD_MIN = 24 * 60
SERVER_UTC_OFFSET = 3           # broker sunucu saati = UTC+3


# ── veri ────────────────────────────────────────────────────────────────────

def fetch(tf_name: str, days: int) -> np.ndarray:
    """MT5'ten aylık dilimlerle bar çek (tek seferde büyük istek terminali çökertiyor)."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{SYMBOL}_{tf_name}_{days}.npy"
    if f.exists():
        return np.load(f, allow_pickle=False)
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"mt5.initialize() basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYMBOL, True)
    tf = {"M5": mt5.TIMEFRAME_M5, "M1": mt5.TIMEFRAME_M1}[tf_name]
    end = datetime.now() + timedelta(days=1)
    chunks = []
    for k in range(days // 20 + 1):
        b = end - timedelta(days=20 * k)
        a = b - timedelta(days=20)
        r = mt5.copy_rates_range(SYMBOL, tf, a, b)
        if r is not None and len(r):
            chunks.append(np.array([(int(x["time"]), float(x["open"]), float(x["high"]),
                                     float(x["low"]), float(x["close"]), float(x["tick_volume"]))
                                    for x in r]))
        print(f"  {tf_name} dilim {k}: {0 if r is None else len(r)}", flush=True)
    if not chunks:
        raise SystemExit(f"{tf_name} verisi alınamadı")
    arr = np.vstack(chunks)
    arr = arr[np.argsort(arr[:, 0])]
    _, uniq = np.unique(arr[:, 0], return_index=True)
    arr = arr[np.sort(uniq)]
    np.save(f, arr)
    return arr


def get_spread() -> float:
    import MetaTrader5 as mt5
    mt5.initialize()
    i = mt5.symbol_info(SYMBOL)
    return round(i.spread * i.point, 5) if i else 0.028


# ── göstergeler (bot ile aynı tanımlar) ─────────────────────────────────────

def ema(x: np.ndarray, span: int) -> np.ndarray:
    k = 2.0 / (span + 1)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = x[i] * k + out[i - 1] * (1 - k)
    return out


def roll(fn, x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    from numpy.lib.stride_tricks import sliding_window_view
    out[n - 1:] = fn(sliding_window_view(x, n), axis=-1)
    return out


def rma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    a = 1.0 / n
    acc = np.nanmean(x[:n])
    out[n - 1] = acc
    for i in range(n, len(x)):
        acc = x[i] * a + acc * (1 - a)
        out[i] = acc
    return out


def indicators(o, h, l, c, v):
    tr = np.full(len(c), np.nan)
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    atr = roll(np.mean, tr, N_ATR)                       # bot: düz TR ortalaması
    up = np.diff(h, prepend=h[0])
    dn = -np.diff(l, prepend=l[0])
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr0 = np.nan_to_num(tr, nan=0.0)
    atr_r = rma(tr0, N_ATR)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = 100 * rma(plus, N_ATR) / atr_r
        mdi = 100 * rma(minus, N_ATR) / atr_r
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = rma(np.nan_to_num(dx), N_ATR)
    d = np.diff(c, prepend=c[0])
    gain = rma(np.where(d > 0, d, 0.0), 14)
    loss = rma(np.where(d < 0, -d, 0.0), 14)
    with np.errstate(invalid="ignore", divide="ignore"):
        rsi = 100 - 100 / (1 + gain / loss)
    return dict(atr=atr, adx=adx, rsi=np.nan_to_num(rsi, nan=50.0),
                ema200=ema(c, N_EMA), ema20=ema(c, 20), ema50=ema(c, 50),
                don_hi=roll(np.max, h, N_DON), don_lo=roll(np.min, l, N_DON),
                vol_ma=roll(np.mean, v, 20), atr_slow=roll(np.mean, tr, 100))


# ── olaylar ─────────────────────────────────────────────────────────────────

FEATS = ["overshoot", "bar_range", "body", "upper_wick", "ext_ema20", "ext_ema50",
         "ext_ema200", "run12", "run36", "don_width", "day_pos", "rsi", "adx",
         "vol_ratio", "atr_pct", "atr_ratio", "bars_since_prev", "hour_utc", "dow"]


def build_events(m5: np.ndarray) -> list[dict]:
    t, o, h, l, c, v = (m5[:, i] for i in range(6))
    ind = indicators(o, h, l, c, v)
    atr, e200 = ind["atr"], ind["ema200"]
    day_id = (t + SERVER_UTC_OFFSET * 3600) // 86400
    ev, prev_i = [], None
    for i in range(N_EMA + N_DON + 5, len(c)):
        lvl, lvl_prev = ind["don_hi"][i - 1], ind["don_hi"][i - 2]
        if not (c[i] > lvl and c[i - 1] <= lvl_prev and c[i] > e200[i]):
            continue
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        m = day_id[:i + 1] == day_id[i]
        dh, dl = h[:i + 1][m].max(), l[:i + 1][m].min()
        rng = max(dh - dl, 1e-9)
        utc_h = int(((t[i] % 86400) // 3600 - SERVER_UTC_OFFSET) % 24)
        ev.append(dict(
            i=int(i), t=float(t[i]), level=float(lvl), close=float(c[i]), atr=float(a),
            overshoot=(c[i] - lvl) / a,
            bar_range=(h[i] - l[i]) / a,
            body=(c[i] - o[i]) / a,
            upper_wick=(h[i] - c[i]) / a,
            ext_ema20=(c[i] - ind["ema20"][i]) / a,
            ext_ema50=(c[i] - ind["ema50"][i]) / a,
            ext_ema200=(c[i] - e200[i]) / a,
            run12=(c[i] - c[i - 12]) / a,
            run36=(c[i] - c[i - 36]) / a,
            don_width=(lvl - ind["don_lo"][i - 1]) / a,
            day_pos=(c[i] - dl) / rng,
            rsi=float(ind["rsi"][i]),
            adx=float(ind["adx"][i]),
            vol_ratio=float(v[i] / ind["vol_ma"][i]) if ind["vol_ma"][i] > 0 else np.nan,
            atr_pct=float(a / c[i] * 100),
            atr_ratio=float(a / ind["atr_slow"][i]) if ind["atr_slow"][i] > 0 else np.nan,
            bars_since_prev=float(i - prev_i) if prev_i else 999.0,
            hour_utc=float(utc_h),
            dow=float(datetime.utcfromtimestamp(t[i] - SERVER_UTC_OFFSET * 3600).weekday()),
        ))
        prev_i = i
    return ev


def resolve(ev: list[dict], m1: np.ndarray, spread: float,
            tp_atr=1.0, sl_atr=1.0, be_trail=False) -> list[dict]:
    t1, o1, h1, l1 = m1[:, 0], m1[:, 1], m1[:, 2], m1[:, 3]
    out = []
    for e in ev:
        close_t = e["t"] + 300
        k = int(np.searchsorted(t1, close_t))
        if k >= len(t1) or t1[k] - close_t > 600:      # M1 boşluğu → atla
            continue
        entry = o1[k] + spread
        tp, sl = entry + tp_atr * e["atr"], entry - sl_atr * e["atr"]
        r = dict(e)
        r["entry"] = entry
        r["slip_atr"] = (entry - e["close"]) / e["atr"]
        hi, lo = h1[k:k + MAX_HOLD_MIN], l1[k:k + MAX_HOLD_MIN]
        unit = sl_atr * e["atr"]              # 1R mesafesi
        cur_sl, runner, peak = sl, False, entry
        exit_R, mins = None, None
        for j in range(len(hi)):
            hit_sl = lo[j] <= cur_sl
            hit_tp = (not runner) and hi[j] >= tp
            if hit_sl and hit_tp:                        # aynı bar → konservatif KAYIP
                exit_R, mins = (cur_sl - entry) / unit, j + 1
                break
            if hit_sl:
                exit_R, mins = (cur_sl - entry) / unit, j + 1
                break
            if hit_tp:
                if not be_trail:                         # sabit TP → çık
                    exit_R, mins = tp_atr / sl_atr, j + 1
                    break
                runner = True                            # TP kaldır, koşturmaya geç
                cur_sl = max(cur_sl, tp - unit)
            if runner:                                   # trail SL'i bar SONUNDA güncelle
                peak = max(peak, hi[j])
                cur_sl = max(cur_sl, peak - unit)
        if exit_R is None:
            continue
        r["win"] = 1 if exit_R > 0 else 0
        r["hold_min"] = mins
        r["R"] = exit_R
        out.append(r)
    return out


# ── değerlendirme ───────────────────────────────────────────────────────────

def stat(rows: list[dict]) -> str:
    if not rows:
        return "n=0"
    n = len(rows)
    w = sum(r["win"] for r in rows)
    R = sum(r["R"] for r in rows)
    return f"n={n:>4} WR={100*w/n:5.1f}% ortR={R/n:+.3f} topR={R:+7.1f}"


def wilson_low(w: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = w / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (c - m) / d


def bucket_report(rows: list[dict], feat: str, q=5) -> str:
    vals = np.array([r[feat] for r in rows], dtype=float)
    ok = np.isfinite(vals)
    rows = [r for r, m in zip(rows, ok) if m]
    vals = vals[ok]
    if len(rows) < 50:
        return f"  {feat}: yetersiz"
    edges = np.quantile(vals, np.linspace(0, 1, q + 1))
    parts = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = [r for r, v in zip(rows, vals) if (a <= v <= b if b == edges[-1] else a <= v < b)]
        if sel:
            parts.append(f"[{a:+.2f},{b:+.2f}) n={len(sel):>3} WR={100*np.mean([s['win'] for s in sel]):4.1f}%")
    return f"  {feat:<15}" + " | ".join(parts)


def main():
    print(f"=== USOIL BREAKOUT LAB — {datetime.now():%Y-%m-%d %H:%M} ===", flush=True)
    m5 = fetch("M5", DAYS)
    m1 = fetch("M1", DAYS)
    spread = get_spread()
    print(f"M5={len(m5)} bar  M1={len(m1)} bar  spread={spread}", flush=True)
    print(f"M5 aralık: {datetime.utcfromtimestamp(m5[0,0])} → {datetime.utcfromtimestamp(m5[-1,0])} (sunucu saati)")

    ev = build_events(m5)
    print(f"\nham olay: {len(ev)}", flush=True)
    base = resolve(ev, m1, spread)
    print(f"çözülen : {len(base)}")
    print(f"\n[TABAN — botun bugünkü kuralı, TP=SL=1.0×ATR, spread dahil]\n  {stat(base)}")
    print(f"  ort. giriş kayması (ATR): {np.mean([r['slip_atr'] for r in base]):+.3f}"
          f"  medyan tutuş: {np.median([r['hold_min'] for r in base]):.0f} dk")

    # spread'siz karşılaştırma — kaybın ne kadarı sürtünme?
    nofric = resolve(ev, m1, 0.0)
    print(f"  [spread=0 varsayımı]      {stat(nofric)}   ← rapor bu dünyada ölçmüştü")

    # yönetim (BE+koştur) etkisi
    mgmt = resolve(ev, m1, spread, be_trail=True)
    print(f"  [BE1R+koştur yönetimi]    {stat(mgmt)}")

    # yıl-ay dökümü
    print("\n[AYLIK]")
    months = {}
    for r in base:
        key = datetime.utcfromtimestamp(r["t"] - SERVER_UTC_OFFSET * 3600).strftime("%Y-%m")
        months.setdefault(key, []).append(r)
    for k in sorted(months):
        print(f"  {k}  {stat(months[k])}")

    # train/test bölünmesi
    base.sort(key=lambda r: r["t"])
    cut = int(len(base) * TRAIN_FRAC)
    tr, te = base[:cut], base[cut:]
    print(f"\n[BÖLÜNME] train {datetime.utcfromtimestamp(tr[0]['t']):%Y-%m-%d}→"
          f"{datetime.utcfromtimestamp(tr[-1]['t']):%Y-%m-%d} {stat(tr)}")
    print(f"          test  {datetime.utcfromtimestamp(te[0]['t']):%Y-%m-%d}→"
          f"{datetime.utcfromtimestamp(te[-1]['t']):%Y-%m-%d} {stat(te)}")

    print("\n[TRAIN — özellik kovaları (yalnız train!)]")
    for f in FEATS:
        print(bucket_report(tr, f))

    # tek eşikli filtre taraması (yalnız train'de seçilir)
    print("\n[FİLTRE TARAMASI — eşik TRAIN'de seçilir, TEST kör]")
    cands = []
    for f in FEATS:
        vals = np.array([r[f] for r in tr if np.isfinite(r[f])], dtype=float)
        if len(vals) < 100:
            continue
        for q in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
            thr = float(np.quantile(vals, q))
            for op in ("<=", ">="):
                sel = [r for r in tr if np.isfinite(r[f]) and (r[f] <= thr if op == "<=" else r[f] >= thr)]
                if len(sel) < 60:
                    continue
                w = sum(s["win"] for s in sel)
                cands.append(dict(feat=f, op=op, thr=thr, n=len(sel),
                                  wr=100 * w / len(sel), r=np.mean([s["R"] for s in sel]),
                                  lo=wilson_low(w, len(sel))))
    cands.sort(key=lambda d: -d["lo"])
    print(f"  {'özellik':<16}{'op':<3}{'eşik':>8}{'n':>6}{'trainWR':>9}{'ortR':>8}{'wilson':>8}   → TEST")
    seen = set()
    top = []
    for cd in cands:
        if cd["feat"] in seen:
            continue
        seen.add(cd["feat"])
        sel = [r for r in te if np.isfinite(r[cd["feat"]]) and
               (r[cd["feat"]] <= cd["thr"] if cd["op"] == "<=" else r[cd["feat"]] >= cd["thr"])]
        cd["test"] = stat(sel)
        top.append(cd)
        print(f"  {cd['feat']:<16}{cd['op']:<3}{cd['thr']:>8.2f}{cd['n']:>6}{cd['wr']:>8.1f}%"
              f"{cd['r']:>+8.3f}{cd['lo']:>8.3f}   → {cd['test']}")
        if len(top) >= 10:
            break

    json.dump({"baseline": stat(base), "n": len(base),
               "top": [{k: (v if not isinstance(v, float) else round(v, 4)) for k, v in c.items()} for c in top]},
              open(CACHE / "lab_summary.json", "w"), indent=1)
    print("\nBITTI")


if __name__ == "__main__":
    sys.exit(main())
