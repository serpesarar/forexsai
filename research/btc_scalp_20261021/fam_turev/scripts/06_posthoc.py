"""SONRADAN (post-hoc) — verdikti değiştirmez, ön-kayıtsız. Tanı sonuçlarına bakıldıktan sonra yazıldı.
(a) DV03d-S aynası: negatif funding uzlaşması sonrası BUY; (b) 5 dk ±3σ hareketlerde baz-öncülüğüne göre takip/fade;
(c) DV02-P1S-W (short-likidasyon akışını takip) ayrıntısı. → out/posthoc.csv
"""
from __future__ import annotations

import importlib.util
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0], "200"]
spec = importlib.util.spec_from_file_location("ev", HERE / "04_eval.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
C = ev.C


def run(label, t_dec, d, r, H):
    e_all = np.asarray(t_dec) + 1
    t = ev.trades(e_all, d, r, H)
    row = {"label": label, "dir": d, "r": r, "H": H}
    for nm in ("DISC", "OOS", "BLIND"):
        m = ev.seg_mask(t["e"], (nm,))
        ds = ev.describe(t, m)
        row[f"{nm}_n"] = ds["n"]
        row[f"{nm}_R"] = ds.get("meanR", np.nan)
        row[f"{nm}_bp"] = ds.get("bp", np.nan)
        row[f"{nm}_sb"] = ds.get("sb_rate", np.nan)
        if ds["n"] >= 10:
            row[f"{nm}_plc"] = ev.placebo_hour(t["e"][m], d, r, H, ds["meanR"], nrep=200)[0]
    post = ev.seg_mask(t["e"], ("OOS", "BLIND"))
    if post.sum() >= 5:
        row["POST_P_EV"] = ev.boot(t["e"][post], t["R"][post])[0]
    return row


def main():
    sig = pickle.load(open(C.CACHE / "signals.pkl", "rb"))
    get = {(s["hid"], s["par"]): s for s in sig}
    rows = []
    # (a) DV03d-S aynası
    for par in ("th0.0", "th-1.0"):
        s = get[("DV03d-S", par)]
        for r in C.RS:
            for H in (15, 60):
                rows.append(run(f"a: neg funding uzlaşması sonrası BUY {par}", s["t"], 1, r, H))
    for par in ("th1.5", "th3.0"):
        s = get[("DV03d-L", par)]
        for r in C.RS:
            for H in (15, 60):
                rows.append(run(f"a: poz funding uzlaşması sonrası SELL {par}", s["t"], -1, r, H))
    # (b) yukarı hareket takip: perp-öncülü (DV04b-U aynası) vs spot-öncülü (DV04c-U); aşağı: fade (DV04b-D) vs takip (DV04c-D)
    for par in ("b1.0", "b3.0"):
        for r in C.RS:
            for H in (15, 60):
                rows.append(run(f"b: yukarı 3σ perp-öncülü TAKİP {par}", get[("DV04b-U", par)]["t"], 1, r, H))
                rows.append(run(f"b: yukarı 3σ spot-öncülü TAKİP {par}", get[("DV04c-U", par)]["t"], 1, r, H))
    # (c) DV02-P1S-W ayrıntı
    for r in C.RS:
        for H in (15, 60):
            rows.append(run("c: 1m short-liq akışı TAKİP (BUY)", get[("DV02-P1S-W", "P1")]["t"], 1, r, H))
            rows.append(run("c: 1m short-liq akışı+OI TAKİP (BUY)", get[("DV02-P1oS-W", "P1oi")]["t"], 1, r, H))
    df = pd.DataFrame(rows)
    df.to_csv(C.OUT / "posthoc.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
