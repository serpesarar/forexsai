"""gece.py — "fitilli gece" motoru (PROTOCOL §2–5): gün başına giriş/çıkış fiyatları, yerel saate hizalı fitil mumları, etiketler,
ızgara, plasebo. Her besleme (t,o,h,l,c,sp; UTC açılış) ile çalışır.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/ndx_10y_1m_20261116/src", "research/fitil_zamanlama_20261118/src", "research/fitil_kesisim_20261118/src",
          "research/ndx_tf_yapilandirma_20261117/src"):
    sys.path.insert(0, str(ROOT / p))
import lib  # noqa: E402
import kesisim as KS  # noqa: E402

TFS = {"30m": 1800, "1h": 3600, "2h": 7200}
THRS = (0.35, 0.50, 0.75)
WS = {"3h": 3 * 3600, "6h": 6 * 3600, "12h": 12 * 3600}
ENTRIES = {"15:30": 930, "16:00": 960}
EXITS = {"04:00": 240, "09:30": 570, "16:00": 960}
KSG_REF = 900                    # 15:00
ESKI_END = date(2021, 10, 31)


def ndx_bars() -> pd.DataFrame:
    m = lib.load_m1()
    return pd.DataFrame({"t": m.t, "o": m.o, "h": m.h, "l": m.l, "c": m.c, "sp": m.spr})


def _local(d: pd.DataFrame, tz: str) -> pd.DataFrame:
    ts = pd.to_datetime(d.t, unit="s", utc=True).dt.tz_convert(tz)
    loc = (ts.dt.tz_localize(None) - pd.Timestamp("1970-01-01")).dt.total_seconds().astype(np.int64)
    return d.assign(day=ts.dt.date.values, mn=(ts.dt.hour * 60 + ts.dt.minute).values, loc=loc.values)


def day_prices(d: pd.DataFrame, tz: str, minutes: list[int], step: int) -> pd.DataFrame:
    """Gün × dakika açılış fiyatı ve spread (barın tam o dakikada açılması gerekir; 1m'de ≤ 5 dk tolerans)."""
    x = _local(d, tz)
    tol = 5 if step == 60 else 0
    out = {}
    for mn in minutes:
        sel = x[(x.mn >= mn) & (x.mn <= mn + tol)].groupby("day").first()
        out[f"o{mn}"] = sel.o
        out[f"s{mn}"] = sel.sp
        out[f"t{mn}"] = sel.t
    return pd.DataFrame(out).sort_index()


def wick_ends(d: pd.DataFrame, tz: str, sec: int, thr: float, step: int) -> np.ndarray:
    """Yerel saate hizalı sec'lik mumlar; alt fitil ≥ thr% ∧ üst ≤ alt/2 olanların kapanış zamanları (UTC)."""
    x = _local(d, tz)
    key = x["loc"].values - x["loc"].values % sec
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    o, c = x.o.values[st], x.c.values[en]
    h, l = np.maximum.reduceat(x.h.values, st), np.minimum.reduceat(x.l.values, st)
    bb, tt = np.minimum(o, c), np.maximum(o, c)
    lw, uw = (bb - l) / bb * 100, (h - tt) / tt * 100
    ok = (lw >= thr) & (uw <= 0.5 * lw)
    return np.sort(x.t.values[en][ok] + step).astype(np.int64)


def nights(dp: pd.DataFrame, entry: int, exit_: int, ksg_ref: int, valid_day=None) -> pd.DataFrame:
    """Gün başına gece işlemi: giriş entry açılışı (+spread), çıkış ertesi geçerli günün exit açılışı (bid), finansman."""
    days = [d for d in dp.index if d.weekday() < 5 and (valid_day is None or valid_day(d))]
    rows = []
    for i, d in enumerate(days[:-1]):
        r, nd = dp.loc[d], days[i + 1]
        oe, ok_, ox = r.get(f"o{entry}"), r.get(f"o{ksg_ref}"), dp.loc[nd].get(f"o{exit_}")
        if not (np.isfinite(oe) and np.isfinite(ox)):
            continue
        if exit_ >= 960 and exit_ <= entry:                      # ertesi gün 16:00
            pass
        px_in = oe + r[f"s{entry}"]
        nightsn = (nd - d).days
        net = (ox / px_in - 1) * 1e4 - lib.FIN_BP_PER_DAY * nightsn
        extra = 0.5 * (r[f"s{entry}"] + dp.loc[nd][f"s{exit_}"]) / px_in * 1e4
        rows.append({"d": d, "t_in": int(r[f"t{entry}"]), "ksg_ret": (oe / ok_ - 1) if np.isfinite(ok_) else np.nan,
                     "net_bp": net, "net_bp_s15": net - extra})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= ESKI_END, "ESKI", "YENI")
    return df


def tag(t_in: np.ndarray, ends: np.ndarray, w: int) -> np.ndarray:
    return np.searchsorted(ends, t_in, "right") > np.searchsorted(ends, t_in - w, "left")


def all_ends(d: pd.DataFrame, tz: str, step: int, shift_days: int = 0, rng: np.random.Generator | None = None) -> dict:
    out = {}
    for tfn, sec in TFS.items():
        for thr in THRS:
            e = wick_ends(d, tz, sec, thr, step)
            if rng is not None:
                k = rng.integers(1, 11, len(e)) * rng.choice([-1, 1], len(e))
                e = np.sort(e + k * 86400)
            out[(tfn, thr)] = e
    return out


def nyse_ok(d: date) -> bool:
    return not lib.nyse.is_holiday(d)
