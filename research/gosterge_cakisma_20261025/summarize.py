"""Sonuç özeti + tekrarlanma (PROTOCOL §7.8–§7.9).

1) TF × ufuk tablosu: seçilen, DOĞRULAMA/KASA geçen, ters yönde anlamlı, boş beklenti.
2) Tekrarlanma: DOĞRULAMA'yı geçen her kombinasyon, aynı tanımla tüm (sembol, TF, h) hücrelerinde yeniden ölçülür
   (seçilmediği hücrelerde bu bir ön-kayıtlı sınamadır; aynı sembolün aynı takvim dönemi bağımsız DEĞİLDİR).
Kullanım: python summarize.py
"""
from __future__ import annotations

import json
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import binom, binomtest

import config as C
import data
import engine as E
import indicators

P_PASS = 0.05


def load_all() -> tuple[pd.DataFrame, pd.DataFrame, list]:
    cells, models, metas = [], [], []
    for sym in C.SOURCES:
        for tf in C.SOURCES[sym]:
            p = C.RES / sym / tf
            if not (p / "cells.csv").exists():
                continue
            c = pd.read_csv(p / "cells.csv")
            c["sym"], c["tf"] = sym, tf
            cells.append(c)
            if (p / "model.csv").exists():
                m = pd.read_csv(p / "model.csv")
                m["sym"], m["tf"] = sym, tf
                models.append(m)
            metas.append(json.load(open(p / "meta.json")))
    return (pd.concat(cells, ignore_index=True) if cells else pd.DataFrame(),
            pd.concat(models, ignore_index=True) if models else pd.DataFrame(), metas)


def _wrong_flags(cells: pd.DataFrame) -> pd.DataFrame:
    """Ters-yön bayrakları ön kayıttaki asgari n (n_min/4) ile yeniden hesaplanır (EK-4)."""
    nmin = cells.tf.map(C.N_MIN) / 4
    cells = cells.copy()
    cells["val_wrong"] = (cells.DOGRULAMA_z <= -C.Z_PASS) & (cells.DOGRULAMA_n >= nmin)
    cells["test_wrong"] = (cells.KASA_z <= -C.Z_PASS) & (cells.KASA_n >= nmin)
    return cells


def cell_table(cells: pd.DataFrame, metas: list) -> pd.DataFrame:
    cells = _wrong_flags(cells)
    thr = {(m["sym"], m["tf"], n["h"]): (n["thr95"], n["pool_over_thr"]) for m in metas for n in m["nulls"]}
    g = cells.groupby(["sym", "tf", "h"]).agg(secilen=("combo", "size"), kesif_sag=("kesif_secimden_sag", "sum"),
                                               dogr=("val_ok", "sum"), kasa=("test_ok", "sum"), kanitli=("kanitli", "sum"),
                                               dogr_ters=("val_wrong", "sum"), kasa_ters=("test_wrong", "sum")).reset_index()
    g["esik"] = [round(thr.get((s, t, h), (np.nan, 0))[0], 2) for s, t, h in zip(g.sym, g.tf, g.h)]
    g["havuz_esik_ustu"] = [thr.get((s, t, h), (0, 0))[1] for s, t, h in zip(g.sym, g.tf, g.h)]
    return g


def verdict(g: pd.DataFrame) -> dict:
    n_sel = int(g.secilen.sum())
    exp = n_sel * P_PASS * P_PASS
    q99 = int(binom.ppf(0.99, n_sel, P_PASS * P_PASS)) if n_sel else 0
    pv, pw = int(g.dogr.sum()), int(g.dogr_ters.sum())
    tv, tw = int(g.kasa.sum()), int(g.kasa_ters.sum())
    return dict(secilen=n_sel, kanitli=int(g.kanitli.sum()), bos_beklenti=round(exp, 2), bos_q99=q99,
                dogr_gecen=pv, dogr_ters=pw, dogr_simetri_p=round(binomtest(pv, pv + pw).pvalue, 4) if pv + pw else None,
                dogr_bos_beklenti=round(n_sel * P_PASS, 1),
                kasa_gecen=tv, kasa_ters=tw, kasa_simetri_p=round(binomtest(tv, tv + tw).pvalue, 4) if tv + tw else None,
                kesif_secimden_sag=int(g.kesif_sag.sum()))


# ── tekrarlanma ──────────────────────────────────────────────────────────────
TOKEN = re.compile(r"^(T|S|R):(.+)$")


def _parse(combo: str):
    parts = [TOKEN.match(p.strip()).groups() for p in combo.split(" & ")]
    return parts


def _col(names_idx, kind, name, ns):
    j = names_idx.get(name)
    if j is None:
        return None
    return 1 + j if kind == "S" else 1 + ns + j


def replicate(cands: pd.DataFrame) -> pd.DataFrame:
    """Her aday kombinasyonu her (sembol, TF, h) hücresinde, üç bölmede yeniden ölç."""
    rows = []
    for sym in C.SOURCES:
        for tf in C.SOURCES[sym]:
            if not (C.RES / sym / tf / "meta.json").exists():
                continue
            d = data.load(sym, tf)
            names, Sm, T, Rm, ind = E.matrices(indicators.compute(d, tf))
            X = E.x_matrix(Sm, Rm)
            idx = {k: i for i, k in enumerate(names)}
            ns = len(names)
            for h in C.HORIZONS:
                L = E.labels(d, data.bucket(d, tf), h, C.SPREAD[sym])
                W = E.weights(L)
                Th = E.thin(T, h)
                for _, c in cands.iterrows():
                    parts = _parse(c["combo"])
                    ti = idx.get(parts[0][1])
                    cols = [_col(idx, k, n, ns) for k, n in parts[1:]]
                    if ti is None or any(x is None for x in cols):
                        continue
                    m = Th[:, ti].copy()
                    for x in cols:
                        m &= X[:, x]
                    ev = np.flatnonzero(m)
                    vec = W[ev].sum(axis=0)
                    dsign = 1.0 if c["dir"] == "BUY" else -1.0
                    r = dict(src_sym=c["sym"], src_tf=c["tf"], src_h=c["h"], combo=c["combo"], dir=c["dir"],
                             sym=sym, tf=tf, h=h, same_cell=(sym, tf, h) == (c["sym"], c["tf"], c["h"]))
                    for s, sn in enumerate(("KESIF", "DOGRULAMA", "KASA")):
                        out = E.directional(E.split_stats(vec, s), np.array(dsign), L["cost"][s])
                        r[f"{sn}_n"], r[f"{sn}_z"] = float(out["n"]), float(out["z"])
                        r[f"{sn}_lift"] = float(out["lift"])
                    rows.append(r)
            print(f"  tekrar: {sym} {tf} bitti", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    cells, models, metas = load_all()
    if cells.empty:
        print("sonuç yok")
        return
    g = cell_table(cells, metas)
    g.to_csv(C.RES / "hucre_tablosu.csv", index=False)
    v_all = {sym: verdict(g[g.sym == sym]) for sym in g.sym.unique()}
    v_all["TUMU"] = verdict(g)
    json.dump(v_all, open(C.RES / "hukum.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(v_all, indent=1, ensure_ascii=False))
    cands = cells[cells.val_ok].drop_duplicates(["sym", "tf", "h", "combo"])
    if len(cands) and "--skip-rep" not in sys.argv:
        rep = replicate(cands)
        rep.to_csv(C.RES / "tekrarlanma.csv.gz", index=False)
    if not models.empty:
        models.to_csv(C.RES / "model_tablosu.csv", index=False)


if __name__ == "__main__":
    main()
