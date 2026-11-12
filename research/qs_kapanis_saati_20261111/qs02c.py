"""QS-02 Tur 2 kontrolü (sonradan, karar ölçütü değil — H2f'nin tabanı): coşku şartı mı, Pazartesi boşluğu mu?
Kontroller: K1 Pazartesi ∧ G− kısa (coşkusuz), K2 tüm Pazartesiler kısa, K3 haftalık coşku ∧ G− (her gün) kısa,
K4 haftalık coşku ∧ G− (Salı-Cuma) kısa. + broker NAS100/US500/US30/US2000 2018-26 (09:30→16:00)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from qs02b import FOREIGN, ND, END, load_yahoo_csv, clean, frame, st

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402
from qs02 import day_table  # noqa: E402


def ctrl(t: pd.DataFrame, cost: float) -> dict:
    v = t.valid & t.valid.shift(1, fill_value=False)
    mon = t.index.dayofweek == 0
    Gm = t.gap <= -0.003
    W = t.w5 >= 0.03
    s = (-(t.C / t.O - 1) * 1e4 - cost)
    return {"H2f": s[v & W & mon & Gm], "K1_pzt_G-": s[v & ~W & mon & Gm], "K2_pzt": s[v & mon],
            "K3_W_G-": s[v & W & Gm], "K4_W_G-_saCu": s[v & W & ~mon & Gm], "K5_W_pzt_G+": s[v & W & mon & (t.gap >= 0.003)]}


def broker(sym: str) -> pd.DataFrame:
    mk = Mkt(sym); t = day_table(mk)
    t = t.assign(valid=True, C1=t.C.shift(1))
    t["gap"] = t.O / t.C1 - 1; t["w5"] = t.C1 / t.C.shift(6) - 1
    # 09:30 girişi broker maliyeti (kısa)
    cost = np.array([mk.cost(int(i)) / o * 1e4 for i, o in zip(t.i570, t.O)])
    return t.iloc[10:], float(np.nanmedian(cost))


def main() -> None:
    res = {}
    for nm in FOREIGN:
        t = frame(clean(load_yahoo_csv(nm)))
        if len(t) >= 500:
            res[nm] = {k: st(v) for k, v in ctrl(t, 3.0).items()}
    for nm in ("SPY", "IWM", "QQQ"):
        x = pd.read_parquet(ND / f"{nm}.parquet"); x = x[(x.index >= "1999-03-10") & (x.index < END)].assign(valid=True)
        res[nm] = {k: st(v) for k, v in ctrl(frame(x, adj=True), 2.0).items()}
    for s in ("NAS100", "US500", "US30", "US2000"):
        t, c = broker(s)
        res["broker_" + s] = {k: st(v) for k, v in ctrl(t, c).items()} | {"maliyet_bp": round(c, 2)}
    (H / "results/qs02c.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    keys = list(next(iter(res.values())).keys())
    keys = [k for k in keys if k != "maliyet_bp"]
    print(f"{'piyasa':15s}" + "".join(f"{k:>20s}" for k in keys))
    for m, r in res.items():
        print(f"{m:15s}" + "".join(f"{(str(r[k].get('ort', 'nan')) + ' (' + str(r[k].get('n', 0)) + ')'):>20s}" for k in keys))
    fm = [m for m in FOREIGN if m in res and res[m]["H2f"].get("n", 0) >= 10]
    for k in keys:
        vals = [res[m][k]["ort"] for m in fm if res[m][k].get("n", 0) >= 10]
        print(f"havuz {k:15s} ort {np.mean(vals):6.1f}  artı {sum(v > 0 for v in vals)}/{len(vals)}")


if __name__ == "__main__":
    main()
