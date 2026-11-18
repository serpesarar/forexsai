"""fz.py — büyük alt fitil tetikleri, 5m/TF giriş zamanlamaları (Z0–Z6) ve çok-çıkışlı değerlendirici (PROTOCOL §2–4).

Sızıntı ilkesi: her karar kapanmış mumla (tend); giriş karar anından SONRA açılan ilk yol barında; TP/SL yolu giriş barından.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/vw_dip_20261117/src"))
import vw  # noqa: E402  (lib, veri, next_day_16, duka_path_stable, NY)
import veri  # noqa: E402
import lib  # noqa: E402

NY = vw.NY
THR, UW = 0.50, 0.5
TPS = (1.0, 2.0, 3.0)
TIMES = ("1h", "4h", "D1_16")
STOPS = ("Sa", "Sb")
TYPES = ("Z0", "Z1", "Z2", "Z3", "Z4", "Z5", "Z6")
MIN_RISK = 0.0005
NQ_SPREAD = 0.25


# ═══════════════════════════ veri ═══════════════════════════

def path_ndx() -> veri.PathBars:
    return vw.duka_path_stable()


def path_dax() -> veri.PathBars:
    src = ROOT / "research/fibo_altin_bolge_20261116/cache"
    raw = pd.read_parquet(src / "DAX_1m_raw.parquet", columns=["t"]).sort_values("t").drop_duplicates("t")
    z = np.load(src / "DAX_1m.npz")
    return veri.PathBars(raw.t.values.astype(np.int64), z["o"], z["h"], z["l"], z["c"], z["spr"].astype(float), 60, "DAX_1m")


def path_nq() -> veri.PathBars:
    d = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/NQ_kalibre.parquet").sort_values("t").drop_duplicates("t")
    return veri.PathBars(d.t.values.astype(np.int64), d.open.values, d.high.values, d.low.values, d.close.values,
                         np.full(len(d), NQ_SPREAD), 300, "NQ_5m")


def agg(p: veri.PathBars, sec: int) -> pd.DataFrame:
    """Yol barlarından sec saniyelik mum (UTC tabanı; NY ofseti tam saat → 5m/1h NY ile hizalı). tend = son yol barının kapanışı."""
    key = p.t - p.t % sec
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    return pd.DataFrame({"t": key[st], "open": p.o[st], "high": np.maximum.reduceat(p.h, st), "low": np.minimum.reduceat(p.l, st),
                         "close": p.c[en], "tend": p.t[en] + p.step})


def tf_bars(p: veri.PathBars, tf: str) -> pd.DataFrame:
    if tf == "1h":
        b = agg(p, 3600)
    else:
        q = veri.build_15m(p) if p.step < 900 else veri.build_15m(p)
        b = veri.build_210m(q)[["t", "open", "high", "low", "close", "tend"]]
    return veri.add_wicks(b.reset_index(drop=True))


# ═══════════════════════════ tetik ve girişler ═══════════════════════════

def trigger_mask(b: pd.DataFrame, atr_k: float | None = None) -> np.ndarray:
    """Tetik: alt fitil ≥ %0,50 (kullanıcı) ya da Tur Z3'te alt fitil ≥ atr_k × ATR14 (önceki 14 mum, tetik mumu hariç); üst ≤ alt/2."""
    uw_ok = b.uw_pct.values <= UW * b.lw_pct.values
    if atr_k is None:
        return (b.lw_pct.values >= THR) & uw_ok
    pc = b.close.shift(1)
    tr = np.maximum(b.high - b.low, np.maximum((b.high - pc).abs(), (b.low - pc).abs()))
    atr = tr.rolling(14, min_periods=14).mean().shift(1).values
    lw_abs = np.minimum(b.open.values, b.close.values) - b.low.values
    return (lw_abs >= atr_k * atr) & uw_ok & np.isfinite(atr)


def entries(p: veri.PathBars, tf: str, atr_k: float | None = None) -> pd.DataFrame:
    b = tf_bars(p, tf)
    b5 = agg(p, 300)
    t5, o5, h5, l5, c5, te5 = (b5[k].values for k in ("t", "open", "high", "low", "close", "tend"))
    trig = np.flatnonzero(trigger_mask(b, atr_k))
    out = []
    for k in trig:
        r = b.iloc[k]
        tc = int(r.tend)
        stopA = float(r.low) * (1 - 0.001)
        base = {"tf": tf, "trig_t": int(r.t), "low": float(r.low), "stopA": stopA, "k": atr_k if atr_k is not None else 0.0}
        out.append({**base, "typ": "Z0", "t_sig": tc, "stopB": stopA, "sig_close": float(r.close)})
        k0 = int(np.searchsorted(t5, tc))                       # t_c'den sonra açılan ilk 5m
        inside = np.flatnonzero((t5 >= int(r.t)) & (t5 < tc))
        last5_hi = float(h5[inside[-1]]) if inside.size else np.inf

        def add(typ: str, j: int) -> None:
            seg = l5[k0:j + 1]
            sb = float(seg.min()) * (1 - 0.0005) if seg.size else stopA
            out.append({**base, "typ": typ, "t_sig": int(te5[j]), "stopB": sb, "sig_close": float(c5[j])})

        if k0 + 1 < len(t5) and t5[k0] - tc < 6 * 3600:
            if c5[k0] > o5[k0]:
                add("Z1", k0)
                if c5[k0 + 1] > o5[k0 + 1]:
                    add("Z2", k0 + 1)
            for j in range(k0, min(k0 + 12, len(t5))):
                if c5[j] > last5_hi:
                    add("Z3", j)
                    break
            red = next((j for j in range(k0, min(k0 + 24, len(t5))) if c5[j] < o5[j]), None)
            if red is not None:
                for j in range(red + 1, min(k0 + 24, len(t5))):
                    if c5[j] > h5[red]:
                        add("Z4", j)
                        break
        if k + 1 < len(b) and int(b.t.iloc[k + 1]) - int(r.t) < 2 * 86400:
            nx = b.iloc[k + 1]
            if nx.close > nx.open and nx.close > r.close:
                out.append({**base, "typ": "Z5", "t_sig": int(nx.tend), "stopB": min(stopA, float(nx.low) * (1 - 0.0005)),
                            "sig_close": float(nx.close)})
            if nx.close > r.high:
                out.append({**base, "typ": "Z6", "t_sig": int(nx.tend), "stopB": min(stopA, float(nx.low) * (1 - 0.0005)),
                            "sig_close": float(nx.close)})
    e = pd.DataFrame(out)
    e["d"] = [datetime.fromtimestamp(int(t), NY).date() for t in e.t_sig]
    return e


def add_context(e: pd.DataFrame, kesif_end=pd.Timestamp("2021-10-31").date()) -> pd.DataFrame:
    e["vix"] = e.d.map(lib.vix_prev_map(sorted(set(e.d))))
    e["era"] = np.where(e.d <= kesif_end, "KESIF", "TEST")
    return e


# ═══════════════════════════ değerlendirici ═══════════════════════════

def _ends(t0: int) -> dict[str, int]:
    return {"1h": t0 + 3600, "4h": t0 + 4 * 3600, "D1_16": vw.next_day_16(t0)}


def evaluate(p: veri.PathBars, t_sig: int, stops: tuple[float, float], sig_close: float | None = None,
             stop_pcts: tuple[float, float] | None = None) -> tuple[np.ndarray, int] | None:
    """Dönüş: (arr[len(STOPS), len(TPS), len(TIMES), 4] = R, R15, bp, t_out), t_in."""
    i = int(np.searchsorted(p.t, t_sig))
    if i >= len(p.t) or p.t[i] - t_sig > 4 * 86400:
        return None
    opt = sig_close is not None
    spi = 0.0 if opt else float(p.spr[i])
    ask = (sig_close if opt else float(p.o[i])) + spi
    t0 = int(p.t[i])
    ends = _ends(t0)
    jmax = min(max(int(np.searchsorted(p.t, max(ends.values()))), i + 1), len(p.t))
    lo, hi, op = p.l[i:jmax], p.h[i:jmax], p.o[i:jmax]
    cm = np.maximum.accumulate(hi)
    out = np.full((len(STOPS), len(TPS), len(TIMES), 4), np.nan)
    d0 = datetime.fromtimestamp(t0, NY).date()
    for s_, st in enumerate(stops):
        if stop_pcts is not None:
            st = ask * (1 - stop_pcts[s_])
        st = min(st, ask * (1 - MIN_RISK))
        risk = ask - st
        if risk <= 0:
            continue
        hs = np.flatnonzero(lo <= st)
        js = int(hs[0]) if hs.size else 10 ** 9
        rb = risk / ask * 1e4
        for b_, tn in enumerate(TIMES):
            jT = int(np.searchsorted(p.t[i:jmax], ends[tn]))
            for a_, k in enumerate(TPS):
                tp = ask + k * risk
                jt = int(np.searchsorted(cm, tp))
                if js < jT and js <= jt:
                    j, px = js, min(st, float(op[js]))
                elif jt < jT:
                    j, px = jt, max(tp, float(op[jt]))
                else:
                    g = i + jT
                    if g < len(p.t) and p.t[g] - ends[tn] <= 4 * 86400:
                        j, px = jT, float(p.o[g])
                    else:
                        j, px = jT - 1, float(p.c[i + jT - 1])
                g = min(i + j, len(p.t) - 1)
                nights = (datetime.fromtimestamp(int(p.t[g]), NY).date() - d0).days
                net = (px / ask - 1) * 1e4 - lib.FIN_BP_PER_DAY * max(0, nights)
                extra = 0.5 * (spi + float(p.spr[g])) / ask * 1e4
                out[s_, a_, b_] = (net / rb, (net - extra) / rb, net, p.t[g] + (p.step if j < jT else 0))
    return out, t0


def evaluate_all(p: veri.PathBars, e: pd.DataFrame, optimistic: bool = False, shift: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    for n, r in enumerate(e.itertuples()):
        ts = int(r.t_sig + (shift[n] if shift is not None else 0))
        pcts = None
        if shift is not None:
            i = min(int(np.searchsorted(p.t, int(r.t_sig))), len(p.t) - 1)
            ref = float(p.o[i]) + float(p.spr[i])
            pcts = (max(MIN_RISK, (ref - r.stopA) / ref), max(MIN_RISK, (ref - r.stopB) / ref))
        res = evaluate(p, ts, (r.stopA, r.stopB), sig_close=(r.sig_close if optimistic else None), stop_pcts=pcts)
        if res is None:
            continue
        arr, t0 = res
        for s_, sn in enumerate(STOPS):
            for a_, k in enumerate(TPS):
                for b_, tn in enumerate(TIMES):
                    v = arr[s_, a_, b_]
                    if np.isfinite(v[0]):
                        rows.append((n, sn, k, tn, v[0], v[1], v[2], t0, int(v[3])))
    return pd.DataFrame(rows, columns=["e", "stop", "tp", "time", "R", "R15", "bp", "t_in", "t_out"])


# ═══════════════════════════ Tur Z2: yön tersi (SAT), ayna zamanlamalar ═══════════════════════════

def entries_short(p: veri.PathBars, tf: str) -> pd.DataFrame:
    """Aynı tetik (büyük alt fitil); ayna girişler SAT: Z1 ilk 5m kırmızı, Z2 iki kırmızı, Z3 son 5m dibinin altında kapanış,
    Z4 ilk yeşilden sonra onun dibinin altında kapanış, Z5 sonraki TF kırmızı ve tetik kapanışının altında, Z6 tetik dibinin altında.
    Stop Sa = tetik tepesi + %0,10; Sb = t_c–giriş arası 5m tepeleri + %0,05."""
    b = tf_bars(p, tf)
    b5 = agg(p, 300)
    t5, o5, h5, l5, c5, te5 = (b5[k].values for k in ("t", "open", "high", "low", "close", "tend"))
    trig = np.flatnonzero((b.lw_pct.values >= THR) & (b.uw_pct.values <= UW * b.lw_pct.values))
    out = []
    for k in trig:
        r = b.iloc[k]
        tc = int(r.tend)
        stopA = float(r.high) * (1 + 0.001)
        base = {"tf": tf, "trig_t": int(r.t), "stopA": stopA}
        out.append({**base, "typ": "Z0", "t_sig": tc, "stopB": stopA, "sig_close": float(r.close)})
        k0 = int(np.searchsorted(t5, tc))
        inside = np.flatnonzero((t5 >= int(r.t)) & (t5 < tc))
        last5_lo = float(l5[inside[-1]]) if inside.size else -np.inf

        def add(typ: str, j: int) -> None:
            seg = h5[k0:j + 1]
            sb = float(seg.max()) * (1 + 0.0005) if seg.size else stopA
            out.append({**base, "typ": typ, "t_sig": int(te5[j]), "stopB": sb, "sig_close": float(c5[j])})

        if k0 + 1 < len(t5) and t5[k0] - tc < 6 * 3600:
            if c5[k0] < o5[k0]:
                add("Z1", k0)
                if c5[k0 + 1] < o5[k0 + 1]:
                    add("Z2", k0 + 1)
            for j in range(k0, min(k0 + 12, len(t5))):
                if c5[j] < last5_lo:
                    add("Z3", j)
                    break
            grn = next((j for j in range(k0, min(k0 + 24, len(t5))) if c5[j] > o5[j]), None)
            if grn is not None:
                for j in range(grn + 1, min(k0 + 24, len(t5))):
                    if c5[j] < l5[grn]:
                        add("Z4", j)
                        break
        if k + 1 < len(b) and int(b.t.iloc[k + 1]) - int(r.t) < 2 * 86400:
            nx = b.iloc[k + 1]
            if nx.close < nx.open and nx.close < r.close:
                out.append({**base, "typ": "Z5", "t_sig": int(nx.tend), "stopB": max(stopA, float(nx.high) * (1 + 0.0005)),
                            "sig_close": float(nx.close)})
            if nx.close < r.low:
                out.append({**base, "typ": "Z6", "t_sig": int(nx.tend), "stopB": max(stopA, float(nx.high) * (1 + 0.0005)),
                            "sig_close": float(nx.close)})
    e = pd.DataFrame(out)
    e["d"] = [datetime.fromtimestamp(int(t), NY).date() for t in e.t_sig]
    return e


def evaluate_short(p: veri.PathBars, t_sig: int, stops: tuple[float, float], sig_close: float | None = None,
                   stop_pcts: tuple[float, float] | None = None) -> tuple[np.ndarray, int] | None:
    """SAT: giriş bid; stop ask tepesi ≥ stop; TP ask dibi ≤ tp; çıkış ask. Gecelik finansman kısa tarafta yok sayıldı (lib ile aynı)."""
    i = int(np.searchsorted(p.t, t_sig))
    if i >= len(p.t) or p.t[i] - t_sig > 4 * 86400:
        return None
    opt = sig_close is not None
    bid = sig_close if opt else float(p.o[i])
    t0 = int(p.t[i])
    ends = _ends(t0)
    jmax = min(max(int(np.searchsorted(p.t, max(ends.values()))), i + 1), len(p.t))
    sp = np.zeros(jmax - i) if opt else p.spr[i:jmax]
    ahi, alo, aop = p.h[i:jmax] + sp, p.l[i:jmax] + sp, p.o[i:jmax] + sp
    cmin = np.minimum.accumulate(alo)
    out = np.full((len(STOPS), len(TPS), len(TIMES), 4), np.nan)
    for s_, st in enumerate(stops):
        if stop_pcts is not None:
            st = bid * (1 + stop_pcts[s_])
        st = max(st, bid * (1 + MIN_RISK))
        risk = st - bid
        hs = np.flatnonzero(ahi >= st)
        js = int(hs[0]) if hs.size else 10 ** 9
        rb = risk / bid * 1e4
        for b_, tn in enumerate(TIMES):
            jT = int(np.searchsorted(p.t[i:jmax], ends[tn]))
            for a_, k in enumerate(TPS):
                tp = bid - k * risk
                jt = int(np.searchsorted(-cmin, -tp))
                if js < jT and js <= jt:
                    j, px = js, max(st, float(aop[js]))
                elif jt < jT:
                    j, px = jt, min(tp, float(aop[jt]))
                else:
                    g = i + jT
                    if g < len(p.t) and p.t[g] - ends[tn] <= 4 * 86400:
                        j, px = jT, float(p.o[g]) + (0.0 if opt else float(p.spr[g]))
                    else:
                        j, px = jT - 1, float(p.c[i + jT - 1]) + (0.0 if opt else float(p.spr[i + jT - 1]))
                g = min(i + j, len(p.t) - 1)
                net = -(px / bid - 1) * 1e4
                extra = 0.5 * (float(p.spr[i]) + float(p.spr[g])) / bid * 1e4 if not opt else 0.0
                out[s_, a_, b_] = (net / rb, (net - extra) / rb, net, p.t[g] + (p.step if j < jT else 0))
    return out, t0


def evaluate_all_short(p: veri.PathBars, e: pd.DataFrame, optimistic: bool = False, shift: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    for n, r in enumerate(e.itertuples()):
        ts = int(r.t_sig + (shift[n] if shift is not None else 0))
        pcts = None
        if shift is not None:
            i = min(int(np.searchsorted(p.t, int(r.t_sig))), len(p.t) - 1)
            ref = float(p.o[i])
            pcts = (max(MIN_RISK, (r.stopA - ref) / ref), max(MIN_RISK, (r.stopB - ref) / ref))
        res = evaluate_short(p, ts, (r.stopA, r.stopB), sig_close=(r.sig_close if optimistic else None), stop_pcts=pcts)
        if res is None:
            continue
        arr, t0 = res
        for s_, sn in enumerate(STOPS):
            for a_, k in enumerate(TPS):
                for b_, tn in enumerate(TIMES):
                    v = arr[s_, a_, b_]
                    if np.isfinite(v[0]):
                        rows.append((n, sn, k, tn, v[0], v[1], v[2], t0, int(v[3])))
    return pd.DataFrame(rows, columns=["e", "stop", "tp", "time", "R", "R15", "bp", "t_in", "t_out"])
