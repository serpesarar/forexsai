"""My AI Gold sinyali (2389616) — veri: işlem geçmişi + XAU 1m (Duka ≤ 2026-11-13, broker 1m sonrası; spread Duka yıl×saat medyanı)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
ARS = KOK.parent
HAM = Path.home() / "Downloads" / "2389616.history.csv"


def islemler() -> pd.DataFrame:
    d = pd.read_csv(HAM, sep=";", dtype=str)
    d.columns = ["t_ac", "tip", "lot", "sym", "px_ac", "sl", "tp", "t_kap", "px_kap", "kom", "swap", "kar", "yorum"]
    num = lambda s: pd.to_numeric(s.fillna("").str.replace(" ", "").str.replace(" ", ""), errors="coerce")  # noqa: E731
    for c in ("lot", "px_ac", "sl", "tp", "px_kap", "kom", "swap", "kar"):
        d[c] = num(d[c])
    x = d[d.tip.isin(["Buy", "Sell"])].copy()
    x["t_ac"] = pd.to_datetime(x.t_ac, format="%Y.%m.%d %H:%M:%S")
    x["t_kap"] = pd.to_datetime(x.t_kap, format="%Y.%m.%d %H:%M:%S")
    x["yon"] = np.where(x.tip == "Buy", 1, -1)
    x["net"] = x.kar.fillna(0) + x.kom.fillna(0) + x.swap.fillna(0)
    x["hareket"] = x.yon * (x.px_kap - x.px_ac)                       # $ (ons başına)
    x["tp_mesafe"] = x.yon * (x.tp - x.px_ac)
    x["sl_son_mesafe"] = x.yon * (x.sl - x.px_ac)                     # + ise stop kâr tarafına çekilmiş
    return x.sort_values("t_ac").reset_index(drop=True)


def xau_1m() -> pd.DataFrame:
    a = pd.read_parquet(ARS / "soma_cozum_20261122/data/xau_1m.parquet", columns=["t", "open", "high", "low", "close", "spr_bp"])
    a = a[a.t >= pd.Timestamp("2018-01-01", tz="UTC").timestamp()]
    b = pd.read_parquet(KOK / "data/xau_broker_1m_recent.parquet")
    b = b[b.t > a.t.max()].copy()
    z = pd.to_datetime(a.t, unit="s", utc=True)
    son = a[z >= pd.Timestamp("2026-08-01", tz="UTC")]
    med = son.groupby(pd.to_datetime(son.t, unit="s", utc=True).dt.hour).spr_bp.median()
    b["spr_bp"] = pd.to_datetime(b.t, unit="s", utc=True).dt.hour.map(med).fillna(son.spr_bp.median())
    d = pd.concat([a, b[["t", "open", "high", "low", "close", "spr_bp"]]]).sort_values("t").drop_duplicates("t").reset_index(drop=True)
    d["sp"] = d.spr_bp * d.open / 1e4
    assert d[["open", "high", "low", "close", "sp"]].notna().all().all(), "NaN (E154)"
    return d
