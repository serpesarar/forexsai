"""Saat ekseni doğrulaması — kanıtın ilk kapısı (defter E2/E5).

``bot_trades`` zamanları broker saatindedir ve DST ile +3 → +2 değişir. Sabit bir
kaymaya güvenmek yerine her işlem için aday kaymalar denenir: giriş VE çıkış
fiyatı, o dakikanın gerçek 1m mum aralığına (tolerans dahil) oturmalıdır.
Haftalık mod kayma kohortu belirler; tutarsız işlem dışlanır ve raporda listelenir.
Eşleşme oranı ``MIN_ALIGNED_FRAC`` altındaysa koşu DURUR (MISALIGNED).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import settings as S


@dataclass
class AlignResult:
    trades: pd.DataFrame
    status: str                       # ALIGNED | MISALIGNED | EMPTY
    aligned_frac: float
    offset_counts: dict = field(default_factory=dict)
    excluded: list = field(default_factory=list)


def price_tol(symbol: str, price: float) -> float:
    return S.PRICE_TOL.get(symbol, abs(price) * S.DEFAULT_PRICE_TOL_FRAC)


def _contains(bars: pd.DataFrame, ts: pd.Timestamp, price: float, tol: float) -> bool:
    pos = bars.index.get_indexer([ts.floor("min")])[0]
    if pos < 0:
        return False
    lo, hi = bars["low"].iat[pos], bars["high"].iat[pos]
    return bool(lo - tol <= price <= hi + tol)


def _has_bar(bars: pd.DataFrame, ts: pd.Timestamp) -> bool:
    return bars.index.get_indexer([ts.floor("min")])[0] >= 0


def score_offsets(row: pd.Series, bars: pd.DataFrame) -> dict[int, int]:
    """Aday kayma (saat) → eşleşen uç sayısı (0..2)."""
    tol = price_tol(row["symbol"], row["open_price"])
    out = {}
    for h in S.TRADE_OFFSET_CANDIDATES_H:
        d = pd.Timedelta(hours=h)
        out[h] = (int(_contains(bars, row["open_raw"] + d, row["open_price"], tol))
                  + int(_contains(bars, row["close_raw"] + d, row["close_price"], tol)))
    return out


def _weekly_mode(scores: pd.Series, weeks: pd.Series) -> dict:
    modes = {}
    for wk, idx in weeks.groupby(weeks).groups.items():
        tally = {h: 0 for h in S.TRADE_OFFSET_CANDIDATES_H}
        for i in idx:
            for h, sc in scores[i].items():
                tally[h] += sc == 2
        modes[wk] = max(tally, key=lambda h: (tally[h], -abs(h + 3)))
    return modes


def _choose(sc: dict, mode: int) -> tuple:
    if sc.get(mode, 0) >= 1:
        return mode, sc[mode], "mod" if sc[mode] == 2 else "kısmi"
    best = max(sc, key=lambda h: sc[h])
    if sc[best] == 2:
        return best, 2, "istisna"
    return None, sc.get(best, 0), "eşleşmedi"


def align_trades(trades: pd.DataFrame, bars: dict[str, pd.DataFrame]) -> AlignResult:
    """Her işleme gerçek UTC ``entry_utc``/``exit_utc`` atar."""
    if trades.empty:
        return AlignResult(trades, "EMPTY", 0.0)
    t = trades.copy()
    cover = t.apply(lambda r: r["symbol"] in bars and _has_any_bar(r, bars[r["symbol"]]), axis=1)
    no_bars = t.loc[~cover, "pid"].tolist()
    t = t[cover].reset_index(drop=True)
    if t.empty:
        return AlignResult(t, "EMPTY", 0.0, excluded=[(p, "mum yok") for p in no_bars])
    scores = t.apply(lambda r: score_offsets(r, bars[r["symbol"]]), axis=1)
    weeks = t["close_raw"].dt.strftime("%G-W%V")
    modes = _weekly_mode(scores, weeks)
    chosen = [_choose(scores[i], modes[weeks[i]]) for i in range(len(t))]
    t["offset_h"] = [c[0] for c in chosen]
    t["align_score"] = [c[1] for c in chosen]
    t["align_status"] = [c[2] for c in chosen]
    excluded = [(p, "mum yok") for p in no_bars]
    excluded += [(p, "fiyat hiçbir kaymada mumla eşleşmedi") for p in t.loc[t["offset_h"].isna(), "pid"]]
    ok = t["offset_h"].notna()
    frac = float((t["align_score"] == 2).mean())
    t = t[ok].copy()
    off = pd.to_timedelta(t["offset_h"].astype(float), unit="h")
    t["entry_utc"] = t["open_raw"] + off
    t["exit_utc"] = t["close_raw"] + off
    counts = {int(k): int(v) for k, v in t["offset_h"].value_counts().items()}
    status = "ALIGNED" if frac >= S.MIN_ALIGNED_FRAC else "MISALIGNED"
    return AlignResult(t.reset_index(drop=True), status, frac, counts, excluded)


def _has_any_bar(row: pd.Series, bars: pd.DataFrame) -> bool:
    return any(_has_bar(bars, row["open_raw"] + pd.Timedelta(hours=h)) for h in S.TRADE_OFFSET_CANDIDATES_H)


def assign_decisions(t: pd.DataFrame) -> pd.Series:
    """Aynı sembol+yön, ``DECISION_CLUSTER_MIN`` dk içinde açılan bacaklar → tek karar (E9)."""
    if t.empty:
        return pd.Series(dtype=int)
    order = t.sort_values("entry_utc")
    ids = np.zeros(len(order), dtype=int)
    last: dict = {}
    nid = 0
    gap = pd.Timedelta(minutes=S.DECISION_CLUSTER_MIN)
    for k, (_, r) in enumerate(order.iterrows()):
        key = (r["symbol"], r["direction"])
        prev = last.get(key)
        if prev is not None and r["entry_utc"] - prev[0] <= gap:
            ids[k] = prev[1]
        else:
            nid += 1
            ids[k] = nid
        last[key] = (r["entry_utc"], ids[k])
    return pd.Series(ids, index=order.index).reindex(t.index)
