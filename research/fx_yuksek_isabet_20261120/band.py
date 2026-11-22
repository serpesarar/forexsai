"""EK-5: resmî bant kurları (USDHKD, EURDKK) — PROTOCOL.md EK-5."""
import itertools
import json

import numpy as np
import pandas as pd

import core

META = {k: v["meta"] for k, v in json.loads((core.RES / "kutu_cek.json").read_text()).items() if isinstance(v, dict) and "meta" in v}
PIP = 0.0001
BASE_USD = {"USD": 1.0, "EUR": 1.16}


def load_h1(pair: str) -> pd.DataFrame:
    x = pd.read_csv(core.FX / f"{pair}_H1.csv.gz")
    x["srv"] = pd.to_datetime(x.t, unit="s")
    x["day"] = x.srv.dt.normalize()
    x["hr"] = x.srv.dt.hour
    pt = float(META[pair]["point"])
    sp = x.sp.astype(float) * pt / x.o * 1e4
    x["cost"] = 1.5 * sp + 7.0 / (100_000 * BASE_USD[pair[:3]]) * 1e4
    x["cap"] = np.arange(len(x)) + 10_000_000
    return x.reset_index(drop=True)


def swap_adj(x: pd.DataFrame, pair: str, t: pd.DataFrame) -> pd.DataFrame:
    if len(t) == 0:
        return t
    m = META[pair]
    pt = float(m["point"])
    days = x.day.values
    nd = np.array([len(np.unique(days[a:b + 1])) - 1 for a, b in zip(t.ei, t.xi)])
    wd = np.array([sum(1 for d in np.unique(days[a:b + 1])[1:] if pd.Timestamp(d).weekday() == 3) for a, b in zip(t.ei, t.xi)])
    sw = np.where(t.side > 0, m["swap_long"], m["swap_short"]) * pt / t.ep.values * 1e4 * (nd + 2 * wd)
    t = t.copy()
    t["swap"] = sw
    t["gross"] = t.gross + sw
    t["net"] = t.gross - t.cost
    t["R"] = t.net / t.sl_bp
    return t


def run_rule(pair, x, trig, side, tp, sl, hold):
    idx = np.where(trig)[0]
    if len(idx) == 0:
        return pd.DataFrame()
    t = core.run(x, idx, np.full(len(idx), side) if np.isscalar(side) else side[idx], tp[idx], sl[idx], np.full(len(idx), hold))
    return swap_adj(x, pair, t)


def main() -> None:
    out = []
    if "USDHKD" in META:
        x = load_h1("USDHKD")
        c = x.c.values
        for tpp, hold in itertools.product([20, 50], [24, 120]):
            t = run_rule("USDHKD", x, c >= 7.8450, -1, np.full(len(x), tpp * PIP), np.maximum(7.8530 - c, 5 * PIP), hold)
            t["rule"] = f"HK1 tp{tpp} h{hold}"; out.append(t)
            t = run_rule("USDHKD", x, c <= 7.7550, 1, np.full(len(x), tpp * PIP), np.maximum(c - 7.7470, 5 * PIP), hold)
            t["rule"] = f"HK2 tp{tpp} h{hold}"; out.append(t)
    if "EURDKK" in META:
        x = load_h1("EURDKK")
        dist = x.c.values - 7.46038
        for z, hold in itertools.product([30, 60], [24, 120]):
            trig = np.abs(dist) >= z * PIP
            side = -np.sign(dist).astype(int)
            t = run_rule("EURDKK", x, trig, side, np.abs(dist) / 2, 2 * np.abs(dist), hold)
            t["rule"] = f"DK1 z{z} h{hold}"; out.append(t)
    T = pd.concat([t for t in out if len(t)], ignore_index=True)
    T.to_parquet(core.RES / "trades_BAND.parquet")
    rows = []
    for r, g in T.groupby("rule"):
        g = g.sort_values("time")
        mid = g.time.min() + (g.time.max() - g.time.min()) / 2
        for nm, gg in (("KESIF", g[g.time < mid]), ("KOR", g[g.time >= mid])):
            ep = int((gg.time.diff().dt.days.fillna(99) > 7).sum())
            rows.append({"rule": r, "per": nm, "epizod": ep, "ilk": str(gg.time.min())[:10] if len(gg) else "", **core.summ(gg, boot=(nm == "KOR"))})
    pd.set_option("display.width", 250)
    R = pd.DataFrame(rows)
    R.to_csv(core.RES / "band.csv", index=False)
    print(R.drop(columns=[c for c in ("yari",) if c in R]).to_string(index=False))


if __name__ == "__main__":
    main()
