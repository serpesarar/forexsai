"""fam_stres — seçim (yalnız KEŞİF), kart (OOS∪KÖR), Holm, max-z, asimetri, N2 stres-SELL yasağı.

Önce run_stres.py koşmalı (results/trades_placebo.pkl). Çıktı: results/analysis.json + ekrana özet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_stres as rs  # noqa: E402  (hücre tanımları + veri)
from engine import OUT, block_boot, single_pos, stats  # noqa: E402

PK = pd.read_pickle(OUT / "trades_placebo.pkl")
TR, PL = PK["trades"], PK["placebo"]
CELLS = pd.read_csv(OUT / "cells.csv")
CONF = ("OOS", "KOR")
GROUPS = ("G1", "G2", "G3", "G4")
MIN_DISC = 20


def card(df: pd.DataFrame, plc: np.ndarray | None) -> dict:
    st = stats(df)
    if st["n"] == 0:
        return {"stats": st}
    sp = single_pos(df)
    m, m_st, m_opt = df.R.mean(), df.R_st.mean(), df.R_opt.mean()
    chk = {
        "1_hacim": bool(st["n"] >= 150),
        "2_beklenti": bool(m > 0 and st["P_EV"] >= 0.90),
        "3_yarilar": bool(st["yari1"] is not None and st["yari1"] >= 0 and st["yari2"] >= 0),
        "4_spread_x1.5": bool(m_st > 0),
        "5_icra": bool(abs(m_opt - m) <= 0.5 * abs(m)),
        "6_tek_poz": bool(sp.R.mean() > 0),
    }
    verdict = "RED" if not chk["1_hacim"] else ("LIVE" if all(chk.values()) else "SHADOW")
    day_sum = sp.groupby("day").R.sum().sort_values(ascending=False)
    yrs = df.groupby("year").R.sum()
    out = {"stats": st, "ortR_spread_x1.5": round(float(m_st), 4), "ortR_iyimser": round(float(m_opt), 4),
           "ortR_sabit15usd": round(float(df.R_fix.mean()), 4), "tek_poz_n": int(len(sp)),
           "tek_poz_ortR": round(float(sp.R.mean()), 4),
           "tek_poz_en_iyi5_gun_haric_toplamR": round(float(sp.R.sum() - day_sum.head(5).sum()), 2),
           "tek_poz_toplamR": round(float(sp.R.sum()), 2),
           "yillar": {int(k): round(float(v), 2) for k, v in yrs.items()},
           "kart": chk, "kart_gecen": int(sum(chk.values())), "kart_verdikt": verdict}
    if plc is not None and np.isfinite(plc).any():
        out["plasebo_ort"] = round(float(np.nanmean(plc)), 4)
        out["plasebo_yuzdelik"] = round(float(np.mean(plc < m)), 3)
    return out


def holm(p: dict) -> dict:
    items = sorted(p.items(), key=lambda kv: kv[1])
    m, adj, run = len(items), {}, 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        adj[k] = round(run, 4)
    return adj


def maxz(names: list[str]) -> dict:
    zs, nulls = [], []
    for nm in names:
        kd = TR[nm][TR[nm].seg == "KESIF"]
        pk = PL[nm]["KESIF"]
        mu, sd = np.nanmean(pk), np.nanstd(pk)
        zs.append((kd.R.mean() - mu) / sd)
        nulls.append((pk - mu) / sd)
    nulls = np.nanmax(np.vstack(nulls), axis=0)
    zmax = float(np.nanmax(zs))
    return {"z_max": round(zmax, 3), "hucre": names[int(np.nanargmax(zs))],
            "p_sel": round(float(np.mean(nulls >= zmax)), 3)}


def main() -> None:
    res: dict = {"secim": {}, "kart_onay": {}, "kart_tum": {}, "maxz": {}}
    sel = {}
    for g in GROUPS:
        c = CELLS[(CELLS.group == g) & (CELLS.KESIF_n >= MIN_DISC)]
        best = c.sort_values("KESIF_ortR", ascending=False).iloc[0]
        sel[g] = best.cell
        res["secim"][g] = {"hucre": best.cell, "KESIF_ortR": best.KESIF_ortR, "KESIF_n": int(best.KESIF_n),
                           "aday_sayisi": int(len(c)), "KESIF_pozitif": bool(best.KESIF_ortR > 0)}
        res["maxz"][g] = maxz(list(c.cell))
    sel["G5"] = sel["G4"].replace("G4", "G5")
    pvals = {}
    for g, nm in sel.items():
        df = TR[nm]
        cf = df[df.seg.isin(CONF)]
        res["kart_onay"][g] = {"hucre": nm, **card(cf, PL[nm]["ONAY"]),
                               "OOS": stats(df[df.seg == "OOS"]), "KOR": stats(df[df.seg == "KOR"])}
        res["kart_tum"][g] = {"hucre": nm, **card(df, None)}
        if g in GROUPS:
            pvals[g] = res["kart_onay"][g]["stats"]["p_tek"]
    res["holm_onay_4"] = holm(pvals)
    prim = CELLS[CELLS.group.isin(GROUPS)]
    res["holm_tum_birincil_38"] = {k: v for k, v in holm(dict(zip(prim.cell, prim.ONAY_P_EV.rsub(1.0)))).items()
                                   if v < 0.5}
    # asimetri G4 − G5 (OOS∪KÖR), her hücre çifti
    asym = {}
    for nm in [c for c in TR if c.startswith("G4_")]:
        a = TR[nm][TR[nm].seg.isin(CONF)]
        b = TR[nm.replace("G4", "G5")][TR[nm.replace("G4", "G5")].seg.isin(CONF)]
        ba = block_boot(a.R.to_numpy(), a.day.to_numpy(), seed=1)
        bb = block_boot(b.R.to_numpy(), b.day.to_numpy(), seed=2)
        ka = TR[nm][TR[nm].seg == "KESIF"]
        kb = TR[nm.replace("G4", "G5")][TR[nm.replace("G4", "G5")].seg == "KESIF"]
        asym[nm[3:]] = {"onay_fark": round(float(a.R.mean() - b.R.mean()), 4),
                        "P_fark_poz": round(float(np.mean(ba - bb > 0)), 3),
                        "kesif_fark": round(float(ka.R.mean() - kb.R.mean()), 4)}
    res["asimetri_G4_eksi_G5"] = asym
    # Pzt–Per alt kümesi (bilgi) seçilen CAPREV hücreleri
    res["pzt_per"] = {}
    for g in ("G1", "G2"):
        df = TR[sel[g]]
        wd = pd.to_datetime(df.t_in * 60, unit="s").dt.weekday
        cf = df[df.seg.isin(CONF) & (wd <= 3)]
        res["pzt_per"][g] = stats(cf)
    # post-hoc bilgi: ön-kayıtta seçilmeyen ama üç segmentte de pozitif hücreler
    seg_pos = CELLS[(CELLS.KESIF_ortR > 0) & (CELLS.OOS_ortR > 0) & (CELLS.KOR_ortR > 0)]
    res["posthoc_uc_segment_pozitif"] = {}
    for nm in seg_pos.cell:
        df = TR[nm]
        res["posthoc_uc_segment_pozitif"][nm] = {
            "tum": card(df, None), "onay": card(df[df.seg.isin(CONF)], PL.get(nm, {}).get("ONAY"))}
    res["N2"] = n2()
    (OUT / "analysis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:20000])


def n2() -> dict:
    """Taban SELL üreteci: her saat başı SELL, stop 1×ATR14(1h), 4 s çıkış; hücre = stres(k=1)∧son 1h kapanış<pdl."""
    t = rs.H1E.astype(np.int64)
    close = rs.H1C
    g = rs.geom(t, "H", 4, "atr", 1.0, -1)
    df = rs.m1.simulate(**g, mode="base").set_index("k")
    day = t // 1440
    st = rs.day_flags(1.0, "")
    stv = st.reindex(day).fillna(False).to_numpy()
    pdl = rs.D.pdl.reindex(day).to_numpy()
    cell = stv & (close < pdl)
    df["cell"] = cell[df.index.to_numpy()]
    df["seg"] = rs.seg_of(df.t_in.to_numpy())
    df["year"] = pd.to_datetime(df.t_in * 60, unit="s").dt.year
    df["hour"] = (t[df.index.to_numpy()] % 1440) // 60
    out = {}
    for lab, segs in (("KESIF", ("KESIF",)), ("ONAY", CONF), ("TUM", ("KESIF", "OOS", "KOR"))):
        x = df[df.seg.isin(segs)]
        base = x[~x.cell].groupby(["year", "hour"]).R.mean()
        c = x[x.cell].copy()
        c["base"] = base.reindex(pd.MultiIndex.from_arrays([c.year, c.hour])).to_numpy()
        c = c.dropna(subset=["base"]).sort_values("t_in")
        c["diff"] = c.R - c.base
        bs = block_boot(c["diff"].to_numpy(), c.day.to_numpy())
        h = len(c) // 2
        out[lab] = {"n_hucre": int(len(c)), "gun": int(c.day.nunique()), "hucre_ortR": round(float(c.R.mean()), 4),
                    "disari_ortR": round(float(x[~x.cell].R.mean()), 4),
                    "eslenik_fark": round(float(c["diff"].mean()), 4),
                    "fark_ci95": [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
                    "P_fark_neg": round(float(np.mean(bs < 0)), 3),
                    "yari1_fark": round(float(c["diff"].iloc[:h].mean()), 4),
                    "yari2_fark": round(float(c["diff"].iloc[h:].mean()), 4)}
    return out


if __name__ == "__main__":
    main()
