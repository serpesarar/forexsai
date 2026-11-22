"""EK-9: EURDKK ERM-II taahhüt bandında büyük sapma → merkeze dönüş. ECB günlük fiks 1999→ (PROTOCOL.md EK-9)."""
import itertools
import numpy as np, pandas as pd
import core

E = pd.read_csv(core.HERE / "data/ecb/eurofxref-hist.csv", na_values="N/A").set_index("Date").sort_index()
E.index = pd.to_datetime(E.index)
CENTER = 7.46038
COST = 1.5 * 5.8 + 7.0 / (100_000 * 1.16) * 1e4
SWAP = {1: -0.13, -1: -0.30}


def sim(px: pd.Series, center, z, slx):
    p = px.dropna()
    cen = pd.Series(center, index=p.index) if np.isscalar(center) else center.reindex(p.index)
    s = ((p / cen - 1) * 1e4).values
    v, d = p.values, p.index
    rows, i = [], 0
    while i < len(v) - 1:
        if np.isnan(s[i]) or abs(s[i]) < z:
            i += 1; continue
        side = -int(np.sign(s[i])); e = v[i + 1]; ce = cen.values[i + 1]
        sl_dev = abs(s[i]) + slx
        j = i + 1; why = 0
        while j < len(v) and j - i <= 250:
            dev = (v[j] / ce - 1) * 1e4
            if side * -dev <= -sl_dev + 0 and abs(dev) >= sl_dev and np.sign(dev) == -side: why = -1; break
            if abs(dev) <= 5: why = 1; break
            j += 1
        j = min(j, len(v) - 1)
        gross = side * (v[j] / e - 1) * 1e4
        nights = (d[j] - d[i + 1]).days
        rows.append({"time": d[i], "side": side, "dev": s[i], "why": why, "gun": nights, "gross": gross,
                     "swap": SWAP[side] * nights, "cost": COST})
        i = j + 1
    t = pd.DataFrame(rows)
    if len(t):
        t["net"] = t.gross + t.swap - t.cost
    return t


def report(name, px, center):
    out = []
    for z, slx in itertools.product([15, 25], [20, 40]):
        t = sim(px, center, z, slx)
        if len(t) == 0:
            out.append({"kur": name, "z": z, "sl+": slx, "n": 0}); continue
        mid = t.time.min() + (t.time.max() - t.time.min()) / 2
        for per, g in (("yari1", t[t.time < mid]), ("yari2", t[t.time >= mid])):
            ep = int((g.time.diff().dt.days.fillna(99) > 28).sum())
            out.append({"kur": name, "z": z, "sl+": slx, "yari": per, "ilk": str(g.time.min())[:10] if len(g) else "", "n": len(g), "epizod": ep,
                        "wr": round((g.net > 0).mean() * 100, 1) if len(g) else None, "tp%": round((g.why == 1).mean() * 100, 1) if len(g) else None,
                        "ort": round(g.net.mean(), 2) if len(g) else None, "en_kotu": round(g.net.min(), 1) if len(g) else None,
                        "gun_med": g.gun.median() if len(g) else None})
    return out


rows = report("EURDKK", E.DKK, CENTER)
for cur in ("SEK", "NOK"):
    px = E[cur]
    rows += report("EUR" + cur + "(hayalet)", px, px.expanding(250).median().shift(1))
pd.set_option("display.width", 250)
R = pd.DataFrame(rows); R.to_csv(core.RES / "dkk.csv", index=False)
print(R.to_string(index=False))
print("bugün EURDKK sapma bp", round((E.DKK.dropna().iloc[-1] / CENTER - 1) * 1e4, 1), E.DKK.dropna().index[-1].date())
