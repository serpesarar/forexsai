"""`yeni deneme/xau_shadow.py` (canlı gölge durum makinesi) ↔ mekanik R0B_G1 (mech.py + rules.py) parite sınaması.

Mekanik taraf: Duka H1 (decider_xau_tpsl_20261015/mekanik/data/duka_h1.parquet, tümü) → prep_h1 → events("R0", +1)
→ sim_cell(TP yok, SL 1,5, 20 bar, $0,12) → one_position. S2 filtreli küme: dogrulama/common.gprev_for > %1 olaylar
atılıp one_position yeniden (PROTOCOL §7). dens24 = common.brk_density.
Gölge taraf: aynı barlar canlıdaki gibi kayan 200-barlık pencereyle bar bar `xs.step`'e verilir (ilk pencere ısınma).
Karşılaştırma: olay (sinyal barı), varyant üyeliği, çıkış barı, çıkış türü, R, ATR, prevday_ret, dens24.
Çalıştır: python3 research/xau_best_days_20261015/golge_parite/parity.py [NSIM=6000]
"""
from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "research/xau_best_days_20261015/dogrulama"))
sys.path.insert(0, os.path.join(ROOT, "yeni deneme"))
import common as C  # noqa: E402  (mekanik/ ve makro/ SALT-OKUNUR import)
import xau_shadow as xs  # noqa: E402

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
WIN = xs.FETCH_H1
CODE = {"stop": "SL", "time": "TIME", "seg": "TIME"}


def mechanical(d: pd.DataFrame) -> pd.DataFrame:
    ev = C.events(d, "R0", +1)
    R, xi, code, _ = C.sim_cell(d, ev, None, 1.5, 20, +1, C.SPREAD)
    m = np.isfinite(R)
    e = ev[m].reset_index(drop=True)
    e["R"], e["xi"], e["code"] = R[m], xi[m], code[m]
    e["gprev"] = C.gprev_for(d, e.ent.to_numpy())
    e["dens24"] = C.brk_density(d)[e.sig]
    ent, x = e.ent.to_numpy(), e.xi.to_numpy()
    e["in_base"] = C.one_position(ent, x)
    s2 = e.gprev.to_numpy() > 0.01
    keep = np.zeros(len(e), bool)
    keep[~s2] = C.one_position(ent[~s2], x[~s2])
    e["in_s2"] = keep
    return e


def shadow(d: pd.DataFrame, k0: int) -> tuple[dict, dict]:
    t = (d.ts.astype("int64") // 10 ** 9).to_numpy()
    o, h, l, c = (d[k].to_numpy() for k in "ohlc")
    bars = [{"t": int(t[k]), "open": float(o[k]), "high": float(h[k]), "low": float(l[k]), "close": float(c[k])}
            for k in range(len(d))]
    st, evs, res = {"open": []}, {}, {}
    first = True
    for k in range(k0, len(bars)):
        lo = max(0, k - WIN + 1)
        view = bars[lo:k + 1]
        idx = range(len(view)) if first else [len(view) - 1]       # canlı ısınma: ilk pencerenin tamamı
        for i in idx:
            for r in xs.step(st, view, i):
                if r["kind"] == "event":
                    evs[r["sig_t"]] = r
                elif r["kind"] == "result" and r["status"] == "done":
                    res[r["sig_t"]] = r
                elif r["kind"] == "result":
                    evs.pop(r["sig_t"], None)                      # void → mekanikte olay yok
        first = False
    return evs, res


def main() -> None:
    raw = pd.read_parquet(os.path.join(C.MK, "data", "duka_h1.parquet"))
    raw["ts"] = pd.to_datetime(raw.ts, utc=True)
    d = C.prep_h1(raw[["ts", "o", "h", "l", "c", "spr"]].copy())
    n = len(d)
    k0 = n - NSIM
    ts = (d.ts.astype("int64") // 10 ** 9).to_numpy()
    me = mechanical(d)
    sevs, sres = shadow(d, k0)
    cut = k0 + WIN + 2 * xs.HOLD                                   # ısınma + iki tutma süresi sonrası karşılaştır
    for label, lo in (("son 200 bar", n - 200), (f"son {n - cut} bar", cut)):
        m = me[me.sig >= lo]
        lines = [f"== {label}: sinyal ts ≥ {d.ts.iloc[lo]:%Y-%m-%d %H:%M} =="]
        for var in ("in_base", "in_s2"):
            mset = {int(ts[s]) for s in m.sig[m[var]]}
            sset = {k for k, r in sevs.items() if r[var] and k >= ts[lo]}
            lines.append(f"  {var}: mekanik {len(mset)} olay | gölge {len(sset)} | ortak {len(mset & sset)} | "
                         f"yalnız mekanik {sorted(mset - sset)[:5]} | yalnız gölge {sorted(sset - mset)[:5]}")
        mm = m[m.in_base | m.in_s2]
        dx = dR = dA = dG = dD = pend = 0
        mxR = mxA = mxG = 0.0
        for _, r in mm.iterrows():
            k = int(ts[r.sig])
            if k not in sres:
                pend += 1
                continue
            s = sres[k]
            dx += s["exit_bar_t_research"] != int(ts[r.xi]) or CODE[s["how_research"]] != r.code
            eR, eA = abs(s["R_research"] - r.R), abs(s["atr"] - r.atr)
            mxR, mxA = max(mxR, eR), max(mxA, eA)
            dR += eR > 1e-3; dA += eA > 1e-4
            g = s["prevday_ret"]
            if not (g is None and np.isnan(r.gprev)):
                eG = abs((g if g is not None else np.nan) - r.gprev)
                mxG = max(mxG, eG if np.isfinite(eG) else 9.9); dG += not (eG <= 1e-5)
            dD += s["dens24"] != int(r.dens24)
        lines.append(f"  olay başına: n={len(mm)} çözülmüş={len(mm) - pend} bekleyen={pend} | çıkış/tür farkı {dx} | "
                     f"R farkı>1e-3 {dR} (max {mxR:.1e}) | ATR farkı {dA} (max {mxA:.1e}) | "
                     f"prevday farkı {dG} (max {mxG:.1e}) | dens24 farkı {dD}")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
