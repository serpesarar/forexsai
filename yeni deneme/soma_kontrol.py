"""soma_kontrol.py — SOMA E2X3/E4X3 broker verisiyle geriye dönük ateşleme listesi (EMİR YOK, salt okuma).

Kullanım (kutuda): python soma_kontrol.py [gün=30]
Amaç: canlı kodun broker M1 (tick hacmi) ile ürettiği ateşlemeleri araştırmanın Dukascopy listesiyle kıyaslamak.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import config
import soma_e2x3_live as E2
import soma_e4x3_live as E4
import soma_motor as F


def _init(mt5) -> None:
    p = getattr(config, "MT5_TERMINAL_PATH", "")
    if not (mt5.initialize(p) if p else mt5.initialize()):
        raise SystemExit(f"MT5 initialize başarısız: {mt5.last_error()}")


def e2_liste(mt5, sym: str, gun: int, mdl: dict) -> list[str]:
    m1 = E2._arr(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, E2.FETCH_M1))
    s = E2.build_series(m1, E2._arr(mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, E2.FETCH_H1)))
    n = len(s["t"])
    bar = F.Bar(s["t"].astype(np.int64), s["o"], s["h"], s["l"], s["c"], np.zeros(n))
    M = F.Motor(bar, s["v"].astype(float))
    j = np.flatnonzero(bar.t >= bar.t[-1] - gun * 86400)
    e = pd.Series(bar.c).ewm(span=E2.EMA_Y, adjust=False).mean().to_numpy()
    y = np.where(bar.c[j] > e[j], 1, -1)
    sk = mdl["model"].predict_proba(M.ozellik(j, bar.c[j], y, bar.t[j] + 60)[mdl["oz"]].to_numpy(np.float32))[:, 1]
    ok = (sk >= mdl["esik"]) & (y > 0)
    ard = np.r_[False, np.diff(j) == 1]
    kenar = ok & ~(np.r_[False, ok[:-1]] & ard)
    return [str(pd.to_datetime(bar.t[j[i]] + 60, unit="s")) + f" skor={sk[i]:.3f}" for i in np.flatnonzero(kenar)]


def e4_liste(mt5, sym: str, gun: int) -> list[str]:
    r1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 1, 99_000)
    r4 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, 2000)
    rh = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 5000)
    m1, h4, h1 = E4._arr(r1), E4._arr(r4), E4._arr(rh)
    c = m1["c"]
    e_u, e_k = E4.ema(c, E4.EMA_UZUN), E4.ema(c, E4.EMA_KISA)
    gunk = (m1["t"] // 86400).astype(np.int64)
    out, gorulen = [], set()
    bas = m1["t"][-1] - gun * 86400
    for k in np.flatnonzero((m1["t"] >= bas) & (c > e_u) & (c > e_k)):
        if gunk[k] in gorulen or k < E4.FETCH_M1:
            continue
        w = slice(k - E4.FETCH_M1 + 1, k + 1)
        mm = {x: v[w] for x, v in m1.items()}
        hh4 = {x: v[E4.before_bucket(h4["t"], m1["t"][k], 4 * 3600)][-E4.FETCH_H:] for x, v in h4.items()}
        hh1 = {x: v[E4.before_bucket(h1["t"], m1["t"][k], 3600)][-E4.FETCH_H:] for x, v in h1.items()}
        s = E4.evaluate(mm, hh4, hh1)
        if s is not None:
            gorulen.add(gunk[k])
            out.append(f"{pd.to_datetime(m1['t'][k], unit='s')} (sunucu) close={s['close']} atr_h1={s['atr_h1']:.2f}")
    return out


def main() -> None:
    import MetaTrader5 as mt5
    gun = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    _init(mt5)
    mdl = E2.load_model()
    for rule, market in E2.MARKETS.items():
        sym = next((x for x in ({"NDX.INDX": ("NAS100", "USTEC", "US100")}.get(market, (market,))) if mt5.symbol_info(x)), None)
        print(f"== E2X3 {market} ({sym}) son {gun} gün ==")
        for ln in (e2_liste(mt5, sym, gun, mdl) if sym else []):
            print("  ", ln)
    print(f"== E4X3 XAUUSD son {gun} gün ==")
    for ln in e4_liste(mt5, "XAUUSD", gun):
        print("  ", ln)


if __name__ == "__main__":
    main()
