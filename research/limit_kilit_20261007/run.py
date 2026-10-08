"""Ön-kayıt: PROTOCOL.md. Çalıştır (depo kökünden): python3 research/limit_kilit_20261007/run.py

A) girişten sonraki ters hareket dağılımı · B) X puan geri çekilme limiti · C) %f'de %L kâr kilidi.
Salt-okuma; sonuçlar results/ altına.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from scripts.islem_otopsi import align, build, cli, data  # noqa: E402
from scripts.islem_otopsi import settings as S  # noqa: E402
from scripts.islem_otopsi.features import make_ctx  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402

OUT = HERE / "results"
S08_CUTOFF = pd.Timestamp("2026-09-02T00:00:00Z")      # S08 raporunun gördüğü son tarih
XS, WINS = (10, 20, 30, 40), (30, 120)
FS, LS = (0.6, 0.7, 0.8, 0.9), (0.0, 0.1, 0.3, 0.5)
MAE_LEVELS = (10, 20, 30, 40)
MIN_RISK_PTS = 2 * max(XS)


def load() -> list[dict]:
    a = cli.parse_args(["--base-days", "200", "--no-vix"])
    now = data.utc_now()
    al, bars, fps, vix, _ = cli.load_everything(a, now)
    print("saat ekseni:", al.status, round(al.aligned_frac, 3), al.offset_counts)
    sbs = {k: SymbolBars(k, v) for k, v in bars.items() if len(v)}
    t, _ = build.build_table(al.trades, sbs, fps, vix, now)
    t["decision_id"] = align.assign_decisions(t)
    t = t.sort_values("entry_utc").drop_duplicates("decision_id")
    items = []
    for _, r in t.iterrows():
        c = make_ctx(r, sbs[r["symbol"]])
        if c is None or not (np.isfinite(c.risk) and np.isfinite(c.reward)) or c.i_exit < c.i_in0:
            continue
        items.append({"r": r, "c": c})
    half = pd.Series([x["r"]["entry_utc"] for x in items]).quantile(0.5)
    for x in items:
        x["half"] = "H1" if x["r"]["entry_utc"] < half else "H2"
        x["s08"] = "önce" if x["r"]["entry_utc"] < S08_CUTOFF else "sonra"
        x["base_R"] = simulate(x["c"].sb, x["c"].s, x["c"].entry, x["c"].i_in0, x["c"].risk, x["c"].reward, x["c"].spread)[0]
    return items


def _hl(c, j0: int, j1: int) -> tuple[np.ndarray, np.ndarray]:
    a = c.sb.a
    return a["high"][j0:j1], a["low"][j0:j1]


# ── A: ters hareket ──────────────────────────────────────────────────────────

def adverse_points(c, j1: int) -> float:
    hi, lo = _hl(c, c.i_in0, max(j1, c.i_in0))
    if not hi.size:
        return 0.0
    return float(c.entry - lo.min()) if c.s > 0 else float(hi.max() + c.spread - c.entry)


def part_a(items: list[dict]) -> pd.DataFrame:
    rows = []
    for x in items:
        c, r = x["c"], x["r"]
        if r["symbol"] != "NDX.INDX":
            continue
        rec = {"family": r["family"], "side": r["side"], "outcome": r["outcome"],
               "mae_trade": adverse_points(c, c.i_exit)}
        for m in (30, 60, 120):
            rec[f"mae_{m}"] = adverse_points(c, min(c.i_exit, c.sb.pos_at(c.t0 + pd.Timedelta(minutes=m))))
        rows.append(rec)
    return pd.DataFrame(rows)


# ── B: limit girişi ──────────────────────────────────────────────────────────

def limit_trade(c, X: float, win: int, fallback: str, geo: str) -> tuple[float, str]:
    """(puan K/Z, durum). durum: dolum | piyasa | atlandı."""
    a, s = c.sb.a, c.s
    jw = min(c.sb.pos_at(c.t0 + pd.Timedelta(minutes=win)), a["close"].size - 1)
    hi, lo = _hl(c, c.i_in0, jw)
    lim = c.entry - s * X
    hit = np.flatnonzero(lo + c.spread <= lim) if s > 0 else np.flatnonzero(hi >= lim)
    if hit.size:
        jf, fill, how = c.i_in0 + int(hit[0]), lim, "dolum"
    elif fallback == "piyasa":
        jf, fill, how = jw, float(a["open"][jw]) + (c.spread if s > 0 else 0.0), "piyasa"
    else:
        return 0.0, "atlandı"
    if geo == "mesafe":
        risk, reward = c.risk, c.reward
    else:
        risk, reward = s * (fill - c.sl0), s * (c.tp0 - fill)
    if risk <= 0:
        return 0.0, "atlandı"
    adj = 0.0 if s > 0 else c.spread
    adv_fill_bar = s * ((a["low"][jf] if s > 0 else a["high"][jf]) + adj - fill)
    if how == "dolum" and adv_fill_bar <= -risk:
        return -risk, how                                     # dolum barında SL (TP bu barda sayılmaz)
    R, _, _ = simulate(c.sb, s, fill, jf + (1 if how == "dolum" else 0), risk, reward, c.spread)
    return float(R * risk), how


def part_b(items: list[dict]) -> pd.DataFrame:
    rows = []
    for x in items:
        c, r = x["c"], x["r"]
        if r["symbol"] != "NDX.INDX" or c.risk < MIN_RISK_PTS:
            continue                                          # X, SL mesafesine yaklaşmasın (decider 20p stopları dışarıda)
        base = {"pid": r["pid"], "family": r["family"], "side": r["side"], "half": x["half"], "s08": x["s08"],
                "base_pts": x["base_R"] * c.risk, "base_tp": float(x["base_R"] > 0)}
        for X in XS:
            for w in WINS:
                for fb in ("atla", "piyasa"):
                    for geo in ("mesafe", "seviye"):
                        pts, how = limit_trade(c, X, w, fb, geo)
                        rows.append({**base, "X": X, "pencere": w, "dolmazsa": fb, "geo": geo, "pts": pts, "durum": how})
    return pd.DataFrame(rows)


# ── C: kâr kilidi ────────────────────────────────────────────────────────────

def lock_trade(c, f: float, L: float) -> float:
    a, s = c.sb.a, c.s
    j1 = min(c.i_in0 + S.REPLAY_MAX_HOLD_MIN, a["close"].size)
    hi, lo = _hl(c, c.i_in0, j1)
    if not hi.size:
        return np.nan
    adj = 0.0 if s > 0 else c.spread
    fav = s * ((hi if s > 0 else lo) + adj - c.entry) / c.risk
    adv = s * ((lo if s > 0 else hi) + adj - c.entry) / c.risk
    rr = c.reward / c.risk
    end = np.flatnonzero((adv <= -1.0) | (fav >= rr))
    k_end = end[0] if end.size else np.inf
    trig = np.flatnonzero(fav >= f * rr)
    k_t = trig[0] if trig.size else np.inf
    if k_end <= k_t:                                          # kilit devreye girmeden bitti
        if np.isinf(k_end):
            return float(s * (a["close"][j1 - 1] - c.entry) / c.risk)
        return -1.0 if adv[int(k_end)] <= -1.0 else rr
    k_t = int(k_t)
    after = np.flatnonzero((adv[k_t + 1:] <= L * rr) | (fav[k_t + 1:] >= rr))
    if not after.size:
        return float(s * (a["close"][j1 - 1] - c.entry) / c.risk)
    k = k_t + 1 + int(after[0])
    return L * rr if adv[k] <= L * rr else rr                # aynı bar → kilit (muhafazakâr)


def part_c(items: list[dict]) -> pd.DataFrame:
    rows = []
    for x in items:
        c, r = x["c"], x["r"]
        for f in FS:
            for L in LS:
                rows.append({"pid": r["pid"], "symbol": r["symbol"].split(".")[0], "side": r["side"],
                             "family": r["family"], "half": x["half"], "s08": x["s08"], "f": f, "L": L,
                             "base_R": x["base_R"], "R": lock_trade(c, f, L)})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    items = load()
    print("karar:", len(items), "NDX:", sum(x["r"]["symbol"] == "NDX.INDX" for x in items))
    pa, pb, pc = part_a(items), part_b(items), part_c(items)
    pa.to_csv(OUT / "a_ters_hareket.csv", index=False)
    pb.to_csv(OUT / "b_limit.csv", index=False)
    pc.to_csv(OUT / "c_kilit.csv", index=False)
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
