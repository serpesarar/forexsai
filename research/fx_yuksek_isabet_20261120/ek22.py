"""EK-22 (2): HK3 tetiği → vekil enstrümanda işlem (PROTOCOL.md EK-22)."""
import json
import numpy as np, pandas as pd
import core

PROX = {"USDCNH": 1, "USDSGD": 1, "USDX": 1, "HK50": -1, "CHINAH": -1, "CN50": -1, "FXI.US": -1, "EWH.US": -1}
META = json.loads((core.RES / "kutu_cek_vekil.json").read_text())
META.update(json.loads((core.RES / "kutu_cek.json").read_text()))


def d1(s):
    x = pd.read_csv(core.FX / f"{s}_D1.csv.gz"); x["d"] = pd.to_datetime(x.t, unit="s").dt.normalize()
    x = x[x.d.dt.weekday < 5].reset_index(drop=True)
    m = (META.get(s) or {}).get("meta", {})
    pt = float(m.get("point", core.point(s)))
    sp = (x.sp.astype(float) * pt / x.o * 1e4).where(x.sp > 0)
    x["cost"] = 1.5 * sp.fillna(sp.median()) + (core.comm_bp(s) if s[:3] in core.BASE_USD and len(s) == 6 else 0.0)
    sw = {1: m.get("swap_long", 0.0), -1: m.get("swap_short", 0.0)}
    x["sw_l"] = float(sw[1] or 0) * pt / x.c * 1e4
    x["sw_s"] = float(sw[-1] or 0) * pt / x.c * 1e4
    return x


def main():
    h = pd.read_csv(core.FX / "USDHKD_H1.csv.gz"); h["d"] = pd.to_datetime(h.t, unit="s").dt.normalize()
    trig = sorted(h[h.c <= 7.7520].d.unique())
    hit = h.groupby("d").h.max() >= 7.7540
    hd = pd.Series(hit.values, index=hit.index)
    out = {}
    rng = np.random.default_rng(22)
    for s, side in PROX.items():
        x = d1(s); pos = pd.Series(np.arange(len(x)), index=x.d.values)
        for ex in ("TP", 5, 20):
            rows, busy = [], -1
            for d in trig:
                j = pos.index.searchsorted(d, side="right")
                if j >= len(x) - 1 or j <= busy or pd.Timestamp(d) < x.d.iloc[0]:
                    continue
                if ex == "TP":
                    fut = hd[(hd.index > d)]
                    tpd = fut[fut].index[:1]
                    k = pos.index.searchsorted(tpd[0], side="right") - 1 if len(tpd) else j + 60
                    k = min(max(k, j), j + 60, len(x) - 1)
                else:
                    k = min(j + ex - 1, len(x) - 1)
                g = side * (x.c.iloc[k] / x.o.iloc[j] - 1) * 1e4
                nights = k - j + 1
                g += nights * (x.sw_l.iloc[j] if side > 0 else x.sw_s.iloc[j])
                rows.append({"d": x.d.iloc[j], "net": g - x.cost.iloc[j], "gun": k - j + 1})
                busy = k
            R = pd.DataFrame(rows)
            if len(R) == 0:
                continue
            ep = int((R.d.diff().dt.days.fillna(99) > 7).sum())
            # rastgele gün kontrolü: aynı sayıda giriş, aynı tutuş uzunlukları
            base = []
            for _ in range(200):
                js = rng.integers(0, len(x) - 61, len(R))
                v = [side * (x.c.iloc[min(j_ + L - 1, len(x) - 1)] / x.o.iloc[j_] - 1) * 1e4 - x.cost.iloc[j_] for j_, L in zip(js, R.gun)]
                base.append(np.mean(v))
            out[f"{s}|{ex}"] = {"n": len(R), "epizod": ep, "wr": round(float((R.net > 0).mean() * 100), 1), "ort": round(float(R.net.mean()), 1),
                                "en_kotu": round(float(R.net.min()), 1), "medyan_gun": float(R.gun.median()),
                                "rastgele_p95": round(float(np.quantile(base, 0.95)), 1), "ilk": str(R.d.min().date())}
            print(s, ex, out[f"{s}|{ex}"], flush=True)
    (core.RES / "ek22.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
