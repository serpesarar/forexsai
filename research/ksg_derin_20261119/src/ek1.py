"""ek1.py — EK-1 E116: bilanço gecesi primi KSG'ye özgü mü? python ek1.py"""
import json
import numpy as np, pandas as pd
import derin as Dn

def all_nights(name):
    b = Dn.Oy.bars30(name)
    t, o, sp = b.t.values, b.o.values, b.sp.values
    def px(u):
        i = int(np.searchsorted(t, u, side="right")) - 1
        return o[i] if i >= 0 and u - t[i] <= 2 * 3600 else np.nan
    days = pd.bdate_range("2018-06-01", Dn.E.CUT)
    days = [d for d in days if Dn.Oy.kl.is_trading_day(d.date())]
    rows = []
    for i, d in enumerate(days[:-1]):
        nd = days[i + 1]
        p15, p16, p930 = px(Dn.ts(d, 15, 0)), px(Dn.ts(d, 16, 0)), px(Dn.ts(nd, 9, 30))
        if np.isnan(p15) or np.isnan(p16) or np.isnan(p930):
            continue
        i16 = int(np.searchsorted(t, Dn.ts(d, 16, 0)))
        net = (p930 / (o[i16] + sp[i16]) - 1) * 1e4 - Dn.E.VR.FIN * (nd - d).days
        rows.append({"d": d, "net": net, "ksg": p16 < p15})
    return pd.DataFrame(rows)

def main():
    Dn.Oy.kl.ay.NYSE_HOLIDAYS = set(Dn.Oy.kl.ay.NYSE_HOLIDAYS) | Dn.Oy.holidays()
    ern = set(Dn.earnings())
    out = {}
    for f in ("MT5_NAS100", "DUKA_NDX"):
        N = all_nights(f)
        N["bil"] = N.d.isin(ern)
        cell = {f"{'KSG' if k else 'KSG_degil'}|{'bilanco' if b else 'bilancosuz'}": {"n": len(z), "ort": round(float(z.net.mean()), 1)}
                for (k, b), z in N.groupby(["ksg", "bil"])}
        fk = cell["KSG|bilanco"]["ort"] - cell["KSG|bilancosuz"]["ort"]
        fd = cell["KSG_degil|bilanco"]["ort"] - cell["KSG_degil|bilancosuz"]["ort"]
        a = N[N.ksg & N.bil]
        yil = {int(y): (len(g), round(float(g.net.mean()), 1)) for y, g in a.groupby(a.d.dt.year)}
        # fark-farkı bootstrap (gün blokları)
        rng = np.random.default_rng(41); dd = []
        for _ in range(2000):
            s = N.sample(len(N), replace=True, random_state=int(rng.integers(1e9)))
            m = s.groupby(["ksg", "bil"]).net.mean()
            dd.append((m[(True, True)] - m[(True, False)]) - (m[(False, True)] - m[(False, False)]))
        out[f] = {"hucre": cell, "ksg_icinde_fark": round(fk, 1), "karsi_kolda_fark": round(fd, 1),
                  "fark_farki": round(fk - fd, 1), "P_fark_farki_arti": round(float(np.mean(np.array(dd) > 0)), 3), "ksg_bilanco_yillar": yil}
        print(f, json.dumps(out[f], ensure_ascii=False))
    json.dump(out, open(Dn.RES / "ek1.json", "w"), indent=1, ensure_ascii=False, default=str)

if __name__ == "__main__":
    main()
