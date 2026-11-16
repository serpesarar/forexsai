"""p23.py — PROTOCOL P2 (itki bacağı) + P3 (aşırı fitil reddi), RTH 09:45–15:30, 30 dk tutuş. Çıktı results/p23.json"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
HOLD = 30
PERIODS = {"KESIF": (date(2022, 1, 1), date(2023, 12, 31)), "TEST": (date(2024, 1, 1), date(2026, 12, 31)),
           "BAGIMSIZ": (date(2018, 1, 1), date(2021, 12, 31))}


def period(d: date) -> str:
    for k, (a, b) in PERIODS.items():
        if a <= d <= b:
            return k
    return "?"


def trade_bp(m1, j_entry: int, side: int, spr_mult: float = 1.0) -> float | None:
    """j_entry barının açılışında gir, HOLD dk sonra (aynı gün, ≤ 15:59) aç. Net bp (finansman yok, gün içi)."""
    t_out = m1.t[j_entry] + HOLD * 60
    k = int(np.searchsorted(m1.t, t_out))
    if k >= len(m1.t) or m1.t[k] - t_out > 300 or m1.d[k] != m1.d[j_entry]:
        return None
    si, so = m1.spr[j_entry] * spr_mult, m1.spr[k] * spr_mult
    if side > 0:
        pin, pout = m1.o[j_entry] + si, m1.o[k]
    else:
        pin, pout = m1.o[j_entry], m1.o[k] + so
    return side * (pout / pin - 1) * 1e4


def scan(m1) -> tuple[pd.DataFrame, pd.DataFrame]:
    o, h, l, c, m, d = m1.o, m1.h, m1.l, m1.c, m1.m, m1.d
    rng = h - l
    a60 = pd.Series(rng).rolling(60).mean().shift(1).values
    clv = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1), 0.5)
    green, red = (c > o) & (clv >= 0.7), (c < o) & (clv <= 0.3)
    uw, lw = h - np.maximum(o, c), np.minimum(o, c) - l
    rth = (m >= 570) & (m < 960)
    legs, wicks = [], []
    busy_leg = busy_wick = 0
    run_g = run_r = 0
    n = len(o)
    for j in range(61, n - 1):
        if not rth[j] or d[j] != d[j - 1]:
            run_g = run_r = 0
            continue
        run_g = run_g + 1 if green[j] else 0
        run_r = run_r + 1 if red[j] else 0
        ok_time = 585 <= m[j] <= 929 and np.isfinite(a60[j]) and a60[j] > 0
        if not ok_time:
            continue
        for run, side in ((run_g, 1), (run_r, -1)):
            if run >= 4 and j + 1 > busy_leg:
                s = j - run + 1
                move = (c[j] - o[s]) * side
                if move >= 4 * a60[j] and s - 30 >= 0 and d[s - 30] == d[j]:
                    s30 = (h[s - 30:s].max() - l[s - 30:s].min()) / a60[j]
                    legs.append({"j": j + 1, "side": side, "s30": s30, "move_a": move / a60[j], "run": run})
                    busy_leg = j + 1 + HOLD
                    run_g = run_r = 0
                    break
        for wk, side in ((uw[j], -1), (lw[j], 1)):
            if j + 1 > busy_wick and wk >= 6 * a60[j] and rng[j] > 0 and wk / rng[j] >= 0.6:
                wicks.append({"j": j + 1, "side": side, "wick_a": wk / a60[j]})
                busy_wick = j + 1 + HOLD
                break
    return pd.DataFrame(legs), pd.DataFrame(wicks)


def attach(m1, ev: pd.DataFrame, side_col: str) -> pd.DataFrame:
    rows = []
    for r in ev.itertuples():
        side = getattr(r, side_col)
        bp, bp15 = trade_bp(m1, r.j, side), trade_bp(m1, r.j, side, 1.5)
        if bp is None:
            continue
        dd = pd.Timestamp(m1.d[r.j]).date()
        rows.append({**r._asdict(), "trade_side": side, "bp": bp, "bp15": bp15, "d": dd, "per": period(dd), "minute": int(m1.m[r.j])})
    return pd.DataFrame(rows)


def placebo(m1, ev: pd.DataFrame, n_rep: int = 200, seed: int = 4) -> np.ndarray:
    """Aynı NY dakikası + aynı yön, aynı dönemde rastgele başka gün → ortalama bp dağılımı."""
    rng = np.random.default_rng(seed)
    day_start = {}
    dd = m1.d
    starts = np.r_[0, np.where(dd[1:] != dd[:-1])[0] + 1]
    for s in starts:
        day_start[pd.Timestamp(dd[s]).date()] = s
    days = np.array(sorted(day_start))
    out = []
    for _ in range(n_rep):
        vals = []
        for r in ev.itertuples():
            a, b = PERIODS[r.per]
            cand = days[(days >= a) & (days <= b)]
            dz = cand[rng.integers(0, len(cand))]
            j = m1.idx_from(lib.utc(dz, r.minute), 120)
            if j is None:
                continue
            v = trade_bp(m1, j, r.trade_side)
            if v is not None:
                vals.append(v)
        out.append(np.mean(vals) if vals else np.nan)
    return np.array(out)


def summarize(df: pd.DataFrame, m1) -> dict:
    out = {}
    for p in PERIODS:
        g = df[df.per == p]
        if len(g) < 5:
            out[p] = {"n": int(len(g))}
            continue
        mo = pd.to_datetime(g.d).dt.to_period("M").astype(str).values
        pl = placebo(m1, g, 100)
        out[p] = {"n": int(len(g)), "bp": float(g.bp.mean()), "bp15": float(g.bp15.mean()), "hit": float((g.bp > 0).mean()),
                  "P": lib.block_boot_p(g.bp.values, mo), "plasebo_ort": float(np.nanmean(pl)),
                  "plasebo_yuzdelik": float((pl < g.bp.mean()).mean())}
    out["gecti"] = bool(all(out[p].get("bp", -1) > 0 for p in PERIODS) and out["TEST"].get("P", 0) >= 0.9
                        and out["BAGIMSIZ"].get("P", 0) >= 0.9 and all(out[p].get("bp15", -1) > 0 for p in PERIODS)
                        and all(out[p].get("plasebo_yuzdelik", 0) >= 0.9 for p in ("TEST", "BAGIMSIZ")))
    return out


def main() -> None:
    m1 = lib.load_m1()
    legs, wicks = scan(m1)
    legs["d"] = [pd.Timestamp(m1.d[j]).date() for j in legs.j]
    legs["per"] = legs.d.map(period)
    edges = list(legs[legs.per == "KESIF"].s30.quantile([1 / 3, 2 / 3]))
    comp = legs[legs.s30 <= edges[0]].copy(); comp["dir"] = comp.side
    ext = legs[legs.s30 > edges[1]].copy(); ext["dir"] = -ext.side
    mid = legs[(legs.s30 > edges[0]) & (legs.s30 <= edges[1])].copy(); mid["dir"] = mid.side
    res = {"s30_esik": edges, "n_bacak": int(len(legs)), "n_fitil": int(len(wicks))}
    res["P2a_sikisma_devam"] = summarize(attach(m1, comp, "dir"), m1)
    res["P2b_uzama_ters"] = summarize(attach(m1, ext, "dir"), m1)
    res["P2_orta_devam_bilgi"] = summarize(attach(m1, mid, "dir"), m1)
    allc = legs.copy(); allc["dir"] = allc.side
    res["P2_tumu_devam_bilgi"] = summarize(attach(m1, allc, "dir"), m1)
    res["P3_fitil_ret"] = summarize(attach(m1, wicks, "side"), m1)
    OUT.mkdir(exist_ok=True)
    (OUT / "p23.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
