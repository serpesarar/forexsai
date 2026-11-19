"""esik.py — Eksen B: NDX gün içi K1 eşik gevşetme (−%0,4, −%0,3) ve K1 ∪ K3; OPEX vetolu, XP çıkışlı; yalnız marjinal işlemler.
python esik.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
sys.path.insert(0, str(ROOT / "research/xp_kaybeden_20261119/src"))
import ozellik as O  # noqa: E402

_s = importlib.util.spec_from_file_location("xp_veri", ROOT / "research/xp_gelistir_20261119/src/veri.py")
VR = importlib.util.module_from_spec(_s)
_s.loader.exec_module(VR)
CUT = pd.Timestamp("2026-11-05")
MT5 = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000"]
RNG = np.random.default_rng(29)
CELLS = {"K1": lambda f: (f.twap_uz <= -50) & (f.son_saat < 0),
         "T40": lambda f: (f.twap_uz <= -40) & (f.son_saat < 0),
         "T30": lambda f: (f.twap_uz <= -30) & (f.son_saat < 0),
         "K1uK3": lambda f: ((f.twap_uz <= -50) & (f.son_saat < 0)) | (f.son_saat <= -30)}


def feeds() -> dict:
    out = {"DUKA_NDX": (VR.G.ndx_bars(), 60)}
    for s in ("NAS100", "US500", "US30", "US2000"):
        b = O.load_market(s)
        out[f"MT5_{s}"] = (b, 1800)
    return out


def build_cell(b, step, name, fn) -> pd.DataFrame:
    orig = VR.entry_features

    def patched(bb, ss, ev=None):
        dp, f, _ = orig(bb, ss, ev)
        return dp, f, fn(f).fillna(False)
    VR.entry_features = patched
    try:
        t = VR.build(b, step, name)
    finally:
        VR.entry_features = orig
    t = t[(t.d <= CUT) & ~t.opex_k.isin([0, 1, 2])]
    return t[["besleme", "d", "net", "donem"]]


def boot(v, days, n=2000) -> float:
    ud = np.unique(days)
    pos = {u: np.flatnonzero(days == u) for u in ud}
    return float(np.mean([np.concatenate([v[pos[u]] for u in RNG.choice(ud, len(ud))]).mean() > 0 for _ in range(n)]))


def sharpe(t: pd.DataFrame) -> float:
    days = pd.bdate_range("2018-05-01", CUT)
    s = t.groupby("d").net.sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 2)


def main() -> None:
    F = feeds()
    T = {c: pd.concat([build_cell(b, st, nm, fn) for nm, (b, st) in F.items()], ignore_index=True) for c, fn in CELLS.items()}
    base = T["K1"]
    key = set(zip(base.besleme, base.d))
    res = {"K1_paket": {nm: {"n": int((base.besleme == nm).sum()), "ort": round(float(base[base.besleme == nm].net.mean()), 1),
                             "sharpe": sharpe(base[base.besleme == nm])} for nm in F}}
    for c in ("T40", "T30", "K1uK3"):
        t = T[c]
        m = t[[(b, d) not in key for b, d in zip(t.besleme, t.d)]]
        rec = {}
        for era in ("KESIF", "TEST"):
            mm = m[(m.donem == era) & m.besleme.isin(MT5)]
            rec[era] = {"n": len(mm), "yilda": round(len(mm) / max(1, mm.d.dt.year.nunique()), 1), "ort": round(float(mm.net.mean()), 1) if len(mm) else None,
                        "isabet_%": round(float((mm.net > 0).mean() * 100), 1) if len(mm) else None,
                        "en_kotu": round(float(mm.net.min()), 1) if len(mm) else None,
                        "P": round(boot(mm.net.values, mm.d.values), 3) if len(mm) > 5 else None,
                        "piyasa": {nm: round(float(mm[mm.besleme == nm].net.mean()), 1) for nm in MT5 if (mm.besleme == nm).any()}}
        d = m[(m.besleme == "DUKA_NDX") & (m.donem == "TEST")]
        rec["DUKA_TEST"] = {"n": len(d), "ort": round(float(d.net.mean()), 1) if len(d) else None}
        rec["sharpe"] = {nm: {"K1": res["K1_paket"][nm]["sharpe"], c: sharpe(t[t.besleme == nm])} for nm in F}
        rec["toplam_islem_yilda_NAS100"] = {"K1": round(len(base[base.besleme == "MT5_NAS100"]) / 8.5, 1), c: round(len(t[t.besleme == "MT5_NAS100"]) / 8.5, 1)}
        kk, te = rec["KESIF"], rec["TEST"]
        ok_piy = sum(1 for v in te["piyasa"].values() if v > 0)
        sh_ok = sum(1 for nm in F if rec["sharpe"][nm][c] >= rec["sharpe"][nm]["K1"])
        rec["hukum"] = ("B" if (kk["ort"] or 0) > 0 and (te["ort"] or 0) > 0 and ok_piy >= 3 and (rec["DUKA_TEST"]["ort"] or 0) > 0
                        and (te["P"] or 0) >= 0.983 and sh_ok >= 3 else ("C" if (te["ort"] or 0) > 0 and (kk["ort"] or 0) > 0 else "X"))
        rec["sharpe_tutan_besleme"] = f"{sh_ok}/5"
        res[c] = rec
        print(c, "marjinal KEŞİF", kk["n"], kk["ort"], "| TEST", te["n"], te["yilda"], "/yıl ort", te["ort"], "isabet", te["isabet_%"], "en kötü", te["en_kotu"],
              "P", te["P"], te["piyasa"], "| Duka TEST", rec["DUKA_TEST"], "| Sharpe tutan", rec["sharpe_tutan_besleme"], rec["sharpe"], "→", rec["hukum"], flush=True)
    (RES / "esik.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
