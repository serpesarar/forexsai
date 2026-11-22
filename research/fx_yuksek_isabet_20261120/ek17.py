"""EK-17: saat × önceki hareket kural madencisi (PROTOCOL.md EK-17). Argüman: ana | plasebo_yon | plasebo_saat"""
import itertools, json, sys
import numpy as np, pandas as pd
import core, ek11

MODE = sys.argv[1] if len(sys.argv) > 1 else "ana"
BLOCK = "blok" in MODE
BLOCKS = {"ASYA": range(0, 7), "LON": range(7, 12), "NY": range(12, 17), "GEC": range(17, 22)}
TPK = 0.25 if BLOCK else 0.5
HOURS = list(range(24))
LS, QS, HS = [1, 4, 8], [1.0, 2.0], [2, 4, 8]


def prep(pair):
    x = ek11.h1(pair).copy()
    sd = x.srv.dt.normalize()
    ok = (x.hr < 23).values
    idx = np.arange(len(x))
    x["cap"] = pd.Series(np.where(ok, idx, -1)).groupby(sd.values).transform("max").values
    x["uh"] = x.utc.dt.hour
    return x


def summ_fast(net, day, cost, gross):
    n = len(net)
    if n < 2:
        return None
    sd = net.std(ddof=1)
    return n, (net > 0).mean() * 100, net.mean(), net.mean() / (sd / np.sqrt(n)) if sd > 0 else 0.0


def main():
    rng = np.random.default_rng(17)
    rows = []
    cached = core.RES / f"ek17_{MODE}.pkl"
    if len(sys.argv) > 2 and sys.argv[2] == "cache" and cached.exists():
        return report(pd.read_pickle(cached))
    for pair in core.PAIRS:
        x = prep(pair)
        o, h, l, c = x.o.values, x.h.values, x.l.values, x.c.values
        atr = x.atr.values
        uh = x.uh.values
        srvh = x.hr.values
        per = np.where(x.utc.dt.year <= 2017, 0, np.where(x.utc.dt.year <= 2021, 1, 2))
        day = x.day.values
        for L in LS:
            rL = c / np.roll(c, L) - 1
            rL[:L] = np.nan
            z = rL / (atr / c * np.sqrt(L))
            for hh in (list(BLOCKS) if BLOCK else HOURS):
                hsel = np.isin(uh, list(BLOCKS[hh])) if BLOCK else (uh == ((hh + 12) % 24 if MODE == "plasebo_saat" else hh))
                for q in QS:
                    base = np.where(hsel & (np.abs(z) >= q) & ~np.isin(srvh, [23, 0]) & np.isfinite(atr))[0]
                    base = base[base > 20]
                    if len(base) < 50:
                        continue
                    sgn = np.sign(z[base]).astype(np.int64)
                    if "plasebo_yon" in MODE:
                        sgn = rng.choice([-1, 1], len(base)).astype(np.int64)
                    for md in ("DEVAM", "DONUS"):
                        side = sgn if md == "DEVAM" else -sgn
                        for H in HS:
                            U = atr[base] * np.sqrt(H)
                            ei, xi, ep, xp, why = core.race(o, h, l, c, base.astype(np.int64), side, TPK * U, 1.5 * U,
                                                            np.full(len(base), H, np.int64), x.cap.values.astype(np.int64))
                            m = ei >= 0
                            if m.sum() < 50:
                                continue
                            g = side[m] * (xp[m] - ep[m]) / ep[m] * 1e4
                            cs = x.cost.values[ei[m]]
                            net = g - cs
                            pr = per[ei[m]]
                            dd = day[ei[m]]
                            rec = {"pair": pair, "h": hh, "L": L, "q": q, "md": md, "H": H}
                            for pi, pn in enumerate(("K", "T", "B")):
                                s = pr == pi
                                if s.sum() < 2:
                                    rec[pn] = None
                                    continue
                                nn, ns, cc, gg = net[s], dd[s], cs[s], g[s]
                                sd_ = nn.std(ddof=1)
                                days = pd.to_datetime(ns)
                                months = max(1.0, (days.max() - days.min()).days / 30.44)
                                h2 = len(nn) // 2
                                rec[pn] = [int(len(nn)), round(float((nn > 0).mean() * 100), 1), round(float(nn.mean()), 3),
                                           round(float(nn.mean() / (sd_ / np.sqrt(len(nn)))), 2) if sd_ > 0 else 0.0,
                                           round(float((gg - 1.5 * cc).mean()), 3), round(float(len(np.unique(ns)) / months), 2),
                                           round(float(nn[:h2].mean()), 3), round(float(nn[h2:].mean()), 3)]
                            rows.append(rec)
        print(pair, len(rows), flush=True)
    pd.to_pickle(rows, core.RES / f"ek17_{MODE}.pkl")
    report(rows)


def report(rows):
    R = pd.DataFrame(rows)

    def ok1(v):
        return v is not None and v[0] >= 100 and v[1] >= 70 and v[2] > 0 and v[3] >= 3 and v[5] >= 3

    def ok_s70(v):  # P yerine t ≥ 1,3 (≈ P 0,90) hızlı süzgeç; geçenler sonra gün-kümeli bootstrap ile kesinleşir
        return v is not None and v[0] >= 60 and v[1] >= 70 and v[2] > 0 and v[3] >= 1.3 and v[4] > 0 and v[5] >= 3 and min(v[6], v[7]) >= 0

    s1 = R.loc[R.K.map(ok1).astype(bool).values]
    s2 = s1.loc[s1["T"].map(ok_s70).astype(bool).values]
    s3 = s2.loc[s2["B"].map(ok_s70).astype(bool).values]
    print(MODE, "kural", len(R), "| aşama1", len(s1), "| aşama2", len(s2), "| aşama3", len(s3))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    if len(s1):
        print(s1.head(40).to_string(index=False))
    if len(s2):
        print("AŞAMA2\n", s2.to_string(index=False))
    (core.RES / f"ek17_{MODE}_ozet.json").write_text(json.dumps({"kural": len(R), "a1": len(s1), "a2": len(s2), "a3": len(s3),
                                                                  "a2_list": s2.to_dict("records"), "a3_list": s3.to_dict("records")}, default=str, indent=1))


if __name__ == "__main__":
    main()
