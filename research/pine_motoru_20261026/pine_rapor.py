"""Pine Motoru kapsama + hüküm tabloları → SONUCLAR.md (anlatı RAPOR.md'de elle)."""
from __future__ import annotations

import gzip
import json
import pickle
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, binomtest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gosterge_cakisma_20261025"))
import config as GC  # noqa: E402

SYMS = ("NDX", "DAX", "XAU", "USOIL")


def coverage() -> tuple[dict, pd.DataFrame]:
    rows = []
    for p in sorted((HERE / "data/runs/recent").glob("part_*.pkl.gz")):
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                st = {s: v["status"] for s, v in r["per_sym"].items()}
                nstate = {s: len(v["states"]) for s, v in r["per_sym"].items()}
                errs = [v.get("error") or "" for v in r["per_sym"].values() if v["status"] != "ok"]
                flags = set(f for v in r["per_sym"].values() for f in (v.get("flags") or []))
                rows.append(dict(sid=r["sid"], name=r["name"], boosts=r.get("boosts") or 0, version=r.get("version"),
                                 ok_any=any(v == "ok" and nstate.get(s, 0) > 0 for s, v in st.items()),
                                 status_ndx=st.get("NDX"), err=errs[0][:60] if errs else "",
                                 lookahead="lookahead_on" in flags, states_ndx=nstate.get("NDX", 0)))
    df = pd.DataFrame(rows)
    if df.empty:
        return {}, df
    cls = df.status_ndx.value_counts().to_dict()
    err_cls = Counter(re.sub(r"[\d'\"(),]+", "", e).split(":")[0][:45] for e in df.err if e)
    q = pd.qcut(df.boosts.rank(method="first"), 4, labels=["en az popüler %25", "2. çeyrek", "3. çeyrek", "en popüler %25"])
    by_pop = df.groupby(q, observed=True).ok_any.mean().round(3).to_dict()
    cov = dict(scripts=len(df), uygulanan=int(df.ok_any.sum()), oran=round(df.ok_any.mean(), 4),
               boost_agirlikli_oran=round((df.boosts * df.ok_any).sum() / max(df.boosts.sum(), 1), 4),
               ndx_durum=cls, hata_siniflari=dict(err_cls.most_common(15)), populerlige_gore=by_pop,
               lookahead_on=int(df.lookahead.sum()))
    return cov, df


def verdict() -> dict:
    out = {}
    for s in SYMS:
        p = HERE / "results" / s / "cells.csv"
        if not p.exists():
            continue
        c = pd.read_csv(p)
        meta = json.load(open(HERE / "results" / s / "meta.json"))
        n_sel = len(c)
        meas = [x for x in meta["nulls"] if x["thr95"] == x["thr95"]]
        over = sum(1 for h in sorted(set(c.h)) if c[(c.h == h)].kesif_secimden_sag.any())
        vp, vw, tp, tw = int(c.val_ok.sum()), int(c.val_wrong.sum()), int(c.test_ok.sum()), int(c.test_wrong.sum())
        out[s] = dict(durum_sayisi=meta["n_states"], script_durumlu=meta["n_scripts_with_states"], secilen=n_sel,
                      kanitli=int(c.kanitli.sum()), bos_beklenti=round(n_sel * 0.0025, 2),
                      bos_q99=int(binom.ppf(0.99, n_sel, 0.0025)) if n_sel else 0,
                      kanitli_p=round(float(binom.sf(int(c.kanitli.sum()) - 1, n_sel, 0.0025)), 3) if n_sel else None,
                      dogr=f"{vp}/{vw}", kasa=f"{tp}/{tw}",
                      kasa_simetri_p=round(binomtest(tp, tp + tw).pvalue, 4) if tp + tw else None,
                      kesif_esik_ustu_ufuk=over, olculebilir_ufuk=len(meas),
                      esikler=[round(x["thr95"], 2) for x in meta["nulls"]],
                      kanitli_lookahead=int(c[c.kanitli].lookahead_on.sum()) if "lookahead_on" in c else 0)
    return out


def main():
    cov, df = coverage()
    ver = verdict()
    rep_p = HERE / "results/tekrar_pine.csv"
    rep = pd.read_csv(rep_p) if rep_p.exists() else pd.DataFrame()
    json.dump(dict(kapsama=cov, hukum=ver), open(HERE / "results/hukum_pine.json", "w"), indent=1, ensure_ascii=False,
              default=str)
    L = ["# Pine Motoru — sonuç tabloları (otomatik)", "", "## Kapsama", ""]
    if cov:
        L += [f"- Çalıştırılan script: **{cov['scripts']}** (kütüphaneler hariç)",
              f"- En az bir sembolde çalışıp ≥1 tepki üreten (uygulanan): **{cov['uygulanan']}** (%{cov['oran'] * 100:.1f}; "
              f"boost ağırlıklı %{cov['boost_agirlikli_oran'] * 100:.1f})",
              f"- NDX durum dağılımı: {cov['ndx_durum']}", f"- Popülerliğe göre uygulanma oranı: {cov['populerlige_gore']}",
              f"- `lookahead_on` bayraklı script: {cov['lookahead_on']}", "", "En sık uygulanamama nedenleri:", ""]
        L += [f"- {k}: {v}" for k, v in cov["hata_siniflari"].items()]
    L += ["", "## Hüküm (sembol başına, 1h son 12.000 bar, 6 ufuk)", "",
          "| Sembol | Tepki durumu | Seçilen | Kanıtlı | Boş beklenti (q99) | p | Doğr. geçen/ters | Kasa geçen/ters | Keşifte eşik üstü ufuk |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s, v in ver.items():
        L.append(f"| {s} | {v['durum_sayisi']:,} | {v['secilen']} | **{v['kanitli']}** | {v['bos_beklenti']} ({v['bos_q99']}) | "
                 f"{v['kanitli_p']} | {v['dogr']} | {v['kasa']} | {v['kesif_esik_ustu_ufuk']}/{v['olculebilir_ufuk']} |")
    if len(rep):
        L += ["", "## Tekrarlanma (doğrulamayı geçen adaylar; boş beklenti her yön için %5)", "",
              "| Pencere | Ölçüm | Aynı yön anlamlı | Ters yön anlamlı |", "|---|---:|---:|---:|"]
        lab = {"past": "geçmiş 12.000 bar (aynı sembol, 1h)", "old": "son pencereden önceki tüm tarih (aynı sembol, 1h)",
               "recent": "diğer semboller (aynı dönem, 1h)"}
        for win in ["past", "old", "recent"] + [w for w in sorted(set(rep.window)) if w.startswith("tf_")]:
            o = rep[(rep.window == win) & rep.n_ok]
            if len(o):
                L.append(f"| {lab.get(win, win.replace('tf_', '') + ' (aynı sembol, son 12.000 bar)')} | {len(o)} | "
                         f"{int((o.z >= GC.Z_PASS).sum())} (%{(o.z >= GC.Z_PASS).mean() * 100:.1f}) | "
                         f"{int((o.z <= -GC.Z_PASS).sum())} (%{(o.z <= -GC.Z_PASS).mean() * 100:.1f}) |")
    kan = []
    for s in SYMS:
        p = HERE / "results" / s / "cells.csv"
        if p.exists():
            c = pd.read_csv(p)
            kan.append(c[c.kanitli])
    kan = pd.concat(kan) if kan else pd.DataFrame()
    L += ["", f"## Kanıtlı adaylar ({len(kan)})", ""]
    if len(kan):
        L += ["| Sembol | h | Script | Tepki | Eş | Yön | Keşif z | Doğr. z | Kasa z | Kasa isabet/taban | Past z |",
              "|---|---:|---|---|---|---|---:|---:|---:|---|---:|"]
        for _, r in kan.iterrows():
            pz = ""
            if len(rep):
                m = rep[(rep.window == "past") & (rep.sid == r.sid) & (rep.state == r.state) & (rep.h == r.h)]
                pz = f"{m.z.iloc[0]:.2f}" if len(m) else "—"
            L.append(f"| {r.sym} | {r.h} | {str(r.script)[:40]} | `{r.state}` | `{r.partner if isinstance(r.partner, str) else ''}` | "
                     f"{r.dir} | {r.KESIF_z:.2f} | {r.DOGRULAMA_z:.2f} | {r.KASA_z:.2f} | {r.KASA_hit:.3f}/{r.KASA_base:.3f} | {pz} |")
    (HERE / "SONUCLAR.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("SONUCLAR.md yazıldı")


if __name__ == "__main__":
    main()
