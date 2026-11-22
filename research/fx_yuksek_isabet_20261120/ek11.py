"""EK-11: zorunlu akış takvimi (gotobi / ay sonu fiksi / FOMC öncesi) × yüksek isabet geometrisi, Pepperstone H1 2010→ (PROTOCOL.md EK-11)."""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
import pandas as pd

import core

USD_BASKET = {"EURUSD": +1, "GBPUSD": +1, "AUDUSD": +1, "USDJPY": -1, "USDCHF": -1, "USDCAD": -1}
FAM = {"A": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"], "B": list(USD_BASKET), "C": list(USD_BASKET)}
GEO = list(itertools.product([0.25, 0.5, 1.0], [1.0, 2.0, 4.0, 100.0]))
DOSE_Q, DOSE_N = 0.67, 250
_C: dict = {}


def per(t: pd.Timestamp) -> str:
    return "KESIF" if t.year <= 2017 else ("TEST" if t.year <= 2021 else "KOR")


def h1(pair: str) -> pd.DataFrame:
    if pair in _C:
        return _C[pair]
    x = pd.read_csv(core.FX / f"{pair}_H1.csv.gz")
    x["srv"] = pd.to_datetime(x.t, unit="s")
    et = x.srv - pd.Timedelta(hours=core.SRV_MINUS_ET_H)
    x["utc"] = et.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dt.tz_localize(None)
    x = x.dropna(subset=["utc"]).drop_duplicates("utc").reset_index(drop=True)
    x["hr"] = x.srv.dt.hour
    sp = (x.sp.astype(float) * core.point(pair) / x.o * 1e4).where(x.sp > 0)
    sp = sp.fillna(sp.groupby([x.utc.dt.year, x.hr]).transform("median")).fillna(sp.median())
    sh = (core.TS.get(pair) or {}).get("saat") or {}
    tick = x.hr.map(lambda h: sh.get(str(h), [0.0])[0]).astype(float)
    x["cost"] = np.fmax(sp.values, tick.values) + core.comm_bp(pair)
    pc = x.c.shift(1)
    tr = np.maximum(x.h - x.l, np.maximum((x.h - pc).abs(), (x.l - pc).abs()))
    x["atr"] = tr.rolling(14).mean()
    x["cap"] = np.arange(len(x)) + 10**9
    x["day"] = x.utc.dt.normalize()
    _C[pair] = x
    return x


def loc(d: pd.Timestamp, hh: int, tz: str) -> pd.Timestamp:
    return pd.Timestamp(d.year, d.month, d.day, hh, tz=tz).tz_convert("UTC").tz_localize(None)


def windows(fam: str, cal: pd.DataFrame) -> list[tuple]:
    """(gün, olay mı, giriş utc, bitiş utc, itme penceresi (a,b) veya None, yön kuralı)."""
    out = []
    fdow = set(cal.d[cal.fomc].dt.dayofweek)
    for r in cal.itertuples():
        d = r.d
        if fam == "A":
            if not r.jbd:
                continue
            out.append((d, bool(r.gotobi), d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=6), (d - pd.Timedelta(hours=1), d + pd.Timedelta(hours=1))))
        elif fam == "B":
            out.append((d, bool(r.ay_sonu), loc(d, 16, "Europe/London"), loc(d, 20, "Europe/London"), (loc(d, 10, "Europe/London"), loc(d, 16, "Europe/London"))))
        else:
            if not (r.fomc or d.dayofweek in fdow):
                continue
            p = d - pd.offsets.BDay(1)
            out.append((d, bool(r.fomc), loc(p, 18, "America/New_York"), loc(d, 14, "America/New_York"), None))
    return out


def signals(fam: str, pair: str, W: list[tuple]) -> pd.DataFrame:
    x = h1(pair)
    pos = pd.Series(np.arange(len(x)), index=x.utc.values)
    rows = []
    for d, ev, t_in, t_out, pw in W:
        if t_in not in pos.index or t_out not in pos.index:
            continue
        i, j = int(pos[t_in]), int(pos[t_out])
        if j <= i or i < 15:
            continue
        push = np.nan
        if pw is not None:
            if pw[0] not in pos.index:
                continue
            push = np.log(x.o.values[i] / x.o.values[int(pos[pw[0]])]) * 1e4
        rows.append((d, ev, i, j, push))
    s = pd.DataFrame(rows, columns=["d", "ev", "i", "j", "push"])
    if fam == "A":
        s["side"] = -1
        s["ok"] = s.push > 0
    elif fam == "B":
        s["side"] = -np.sign(s.push).astype(int)
        s["ok"] = s.push.abs() > 0
    else:
        s["side"] = USD_BASKET[pair]
        s["ok"] = True
    if fam in "AB":   # doz: önceki 250 iş günü |itme| 67. yüzdelik (yalnız geçmiş, tüm günler)
        a = s.push.abs() if fam == "B" else s.push.clip(lower=0).where(s.push > 0)
        thr = a.rolling(DOSE_N, min_periods=120).quantile(DOSE_Q).shift(1)
        s["dose"] = s.push.abs() > thr
    else:
        s["dose"] = True
    s["U"] = x.atr.values[s.i - 1] * np.sqrt(s.j - s.i)
    s = s[s.ok & (s.side != 0) & s.U.notna()].reset_index(drop=True)
    return s


def trades(fam: str, cal: pd.DataFrame) -> pd.DataFrame:
    W = windows(fam, cal)
    out = []
    for pair in FAM[fam]:
        x = h1(pair)
        s = signals(fam, pair, W)
        for dose in ([False, True] if fam in "AB" else [False]):
            ss = s[s.dose] if dose else s
            for gi, (tpk, slk) in enumerate(GEO):
                for ev in (True, False):
                    g = ss[ss.ev == ev]
                    if len(g) == 0:
                        continue
                    t = core.run(x, (g.i - 1).values, g.side.values, tpk * g.U.values, slk * g.U.values, (g.j - g.i).values)
                    if len(t) == 0:
                        continue
                    t["time"] = x.utc.values[t.ei.values]
                    t["day"] = x.day.values[t.ei.values]
                    t["fam"], t["pair"], t["ev"] = fam, pair, ev
                    t["cell"] = f"{fam}|D{int(dose)}|tp{tpk}|sl{slk}"
                    out.append(t)
        print(fam, pair, flush=True)
    T = pd.concat(out, ignore_index=True)
    T["per"] = [per(pd.Timestamp(v)) for v in T.time.values]
    return T


def main() -> None:
    cal = pd.read_csv(core.RES / "takvim11.csv", parse_dates=["d"])
    T = pd.concat([trades(f, cal) for f in "ABC"], ignore_index=True)
    T.to_parquet(core.RES / "trades_EK11.parquet")
    E = T[T.ev & (T.per == "KESIF")]
    H = pd.DataFrame([{"cell": c, **core.summ(g)} for c, g in E.groupby("cell")])
    H.to_csv(core.RES / "kesif_EK11.csv", index=False)
    pd.set_option("display.width", 250)
    print(H.sort_values(["cell"]).to_string(index=False))


if __name__ == "__main__":
    main()
