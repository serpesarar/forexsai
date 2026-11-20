"""analiz.py — PROTOCOL.md: S/H/T seçim (Duka KEŞİF, 2 hücre) + geçme; E ailesi; SL/TP betimleme. python cr_analiz.py"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import cr_motor as M

KES = pd.Timestamp(M.KESIF_SON)
NB = 3000
RNG = np.random.default_rng(71)
FEEDS = ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000", "DUKA_DAX", "MT5_GER40", "EET30", "NQ",
         "MT5_LONG1H", "U_NDX_GUNLUK", "U_NDX_GUNLUK_2016"]
BLIND = ["MT5_US500", "MT5_US30", "MT5_US2000"]
FEATS = ["vix", "vix_chg", "r1", "r5", "dvol", "depth", "from_close", "from_hi20", "last_hour"]
BINS = ["pre_open", "opex02", "wd"]


def load() -> dict[str, pd.DataFrame]:
    K = {}
    for f in FEEDS:
        x = pd.read_parquet(M.HERE / f"cache/{f}.parquet")
        x["opex02"] = x.opex.isin([0, 1, 2])
        x["blk"] = x.d.dt.to_period("M").astype(str)
        K[f] = x.sort_values("d").reset_index(drop=True)
    return K


def boot_pos(v: np.ndarray, blk: np.ndarray) -> float:
    ub = np.unique(blk)
    idx = {u: np.flatnonzero(blk == u) for u in ub}
    return round(float(np.mean([v[np.concatenate([idx[u] for u in RNG.choice(ub, len(ub))])].mean() > 0 for _ in range(NB)])), 4)


def sharpe(d: pd.Series, pnl: pd.Series) -> float:
    days = pd.bdate_range(d.min(), d.max())
    s = pnl.groupby(d.values).sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan


def stats(K: pd.DataFrame, cell: str) -> dict:
    v = K[cell]
    return {"n": len(K), "ort": round(float(v.mean()), 2), "fark": round(float((v - K.base).mean()), 2),
            "isabet": round(float((v > 0).mean()), 3), "isabet_taban": round(float((K.base > 0).mean()), 3),
            "sharpe": sharpe(K.d, v), "sharpe_taban": sharpe(K.d, K.base),
            "en_iyi5_haric_fark": round(float(np.sort((v - K.base).values)[:-5].mean()), 2) if len(K) > 5 else None}


def select(D: pd.DataFrame, cells: list[str]) -> list[str]:
    k = D[D.d <= KES]
    return sorted(cells, key=lambda c: (k[c] - k.base).mean(), reverse=True)[:2]


def judge(K: dict, cell: str) -> dict:
    D = K["DUKA_NDX"]
    test = D[D.d > KES]
    res = {f: stats(x, cell) for f, x in K.items()} | {"DUKA_TEST": stats(test, cell), "DUKA_KESIF": stats(D[D.d <= KES], cell)}
    parts = [test, K["DUKA_DAX"], K["U_NDX_GUNLUK"]]
    diff = np.concatenate([(x[cell] - x.base).values for x in parts])
    blk = np.concatenate([(x.feed.iloc[0] + "|" + x.blk).values for x in parts])
    P = boot_pos(diff, blk)
    ok = {"test": res["DUKA_TEST"]["fark"] > 0, "mt5": res["MT5_NAS100"]["fark"] > 0, "havuz_P": P >= 0.975,
          "kor_2_3": sum(res[f]["fark"] > 0 for f in BLIND) >= 2,
          "bagimsiz": res["U_NDX_GUNLUK"]["fark"] > 0 and res["DUKA_DAX"]["fark"] > 0,
          "sharpe": all(res[f]["sharpe"] > res[f]["sharpe_taban"] for f in ("DUKA_NDX", "MT5_NAS100"))}
    h = "B" if all(ok.values()) else ("X" if not (ok["test"] and ok["mt5"]) else "C")
    return {"hucre": cell, "olcum": res, "havuz_P": P, "olcut": ok, "hukum": h}


# ───────── E ─────────
def filt_mask(x: pd.DataFrame, rule: dict) -> pd.Series:
    f = rule["f"]
    if f in BINS:
        return x[f] != rule["drop"]
    lo, hi = rule["cut"]
    v = x[f]
    keep = ~((v >= lo) & (v <= hi))
    return keep | v.isna()


def e_family(K: dict) -> dict:
    D = K["DUKA_NDX"]
    k = D[D.d <= KES]
    cands = []
    for f in FEATS:
        z = k.dropna(subset=[f])
        if len(z) < 15:
            continue
        q = z[f].quantile([1 / 3, 2 / 3]).values
        for lab, cut in (("alt", (-np.inf, q[0])), ("orta", (q[0], q[1])), ("ust", (q[1], np.inf))):
            r = {"f": f, "tertil": lab, "cut": [float(cut[0]), float(cut[1])]}
            m = filt_mask(k, r)
            cands.append(r | {"kesif_fark": float(k[m].base.mean() - k.base.mean()), "kept": int(m.sum())})
    for f in BINS:
        for val in sorted(k[f].dropna().unique()):
            r = {"f": f, "drop": val.item() if hasattr(val, "item") else val}
            m = filt_mask(k, r)
            if m.sum() < len(k) * 0.5:
                continue
            cands.append(r | {"kesif_fark": float(k[m].base.mean() - k.base.mean()), "kept": int(m.sum())})
    best = max(cands, key=lambda r: r["kesif_fark"])
    out = {"secilen": best, "aday_sayisi": len(cands), "olcum": {}}
    sets = {"DUKA_TEST": D[D.d > KES], "MT5_NAS100_TEST": K["MT5_NAS100"][K["MT5_NAS100"].d > KES],
            "DUKA_DAX": K["DUKA_DAX"], "U_NDX_GUNLUK": K["U_NDX_GUNLUK"]}
    diffs, blks = [], []
    for nm, x in sets.items():
        if x[best["f"]].isna().all():
            out["olcum"][nm] = "özellik yok"
            continue
        m = filt_mask(x, best)
        fark = float(x[m].base.mean() - x.base.mean())
        out["olcum"][nm] = {"n": len(x), "kalan": int(m.sum()), "fark": round(fark, 2), "atilan_ort": round(float(x[~m].base.mean()), 1)
                            if (~m).any() else None}
        if nm != "MT5_NAS100_TEST":
            diffs.append((x.base - x.base.mean())[m].values)        # ort(kalan) − ort(tümü) = bunların ortalaması
            blks.append((nm + "|" + x.blk)[m].values)
    P = boot_pos(np.concatenate(diffs), np.concatenate(blks))
    ok = [isinstance(v, dict) and v["fark"] > 0 for v in out["olcum"].values() if v != "özellik yok"]
    out["havuz_P"] = P
    out["hukum"] = "B" if all(ok) and P >= 0.975 else ("X" if not (isinstance(out["olcum"]["DUKA_TEST"], dict) and out["olcum"]["DUKA_TEST"]["fark"] > 0) else "C")
    return out


def describe_sl_tp(K: dict) -> dict:
    """SL ↔ TP özellik farkı (betimleyici) + stoplanan işlemin sonrası."""
    out = {}
    for f in ("DUKA_NDX", "DUKA_DAX", "U_NDX_GUNLUK", "U_NDX_GUNLUK_2016"):
        x = K[f]
        g = {c: x[x.cls == c] for c in ("SL", "TP", "ZK")}
        row = {"sinif": {c: [len(v), round(float(v.base.mean()), 1)] for c, v in g.items()}}
        feats = {}
        for ft in FEATS + ["pre_open", "opex02"]:
            a, b = g["SL"][ft].dropna().astype(float), g["TP"][ft].dropna().astype(float)
            if len(a) < 5 or len(b) < 5:
                continue
            obs = a.mean() - b.mean()
            pool = np.concatenate([a, b])
            perm = []
            for _ in range(2000):
                p = RNG.permutation(pool)
                perm.append(p[:len(a)].mean() - p[len(a):].mean())
            feats[ft] = {"SL": round(float(a.mean()), 4), "TP": round(float(b.mean()), 4),
                         "p": round(float(np.mean(np.abs(perm) >= abs(obs))), 3)}
        row["ozellik"] = feats
        sl = g["SL"]
        row["stop_sonrasi"] = {"n": len(sl), "stop_bp": round(float(sl.base.mean()), 1),
                               "stopsuz_D0c": round(float(sl.d0c_bp_nostop.mean()), 1),
                               "stopsuz_D1c": round(float(sl.d1c_bp_nostop.mean()), 1),
                               "D0c_stoptan_iyi_pay": round(float((sl.d0c_bp_nostop > sl.base).mean()), 3),
                               "D0c_arti_pay": round(float((sl.d0c_bp_nostop > 0).mean()), 3)}
        out[f] = row
    return out


def main() -> None:
    K = load()
    res = {"taban": {f: stats(K[f], "base") | {"SL_pay": round(float((K[f].cls == "SL").mean()), 3),
                                                "R": round(float(K[f].R.mean()), 3)} for f in FEEDS}}
    for f in FEEDS:
        print(f, res["taban"][f]["n"], res["taban"][f]["ort"], "SL", res["taban"][f]["SL_pay"], "Sh", res["taban"][f]["sharpe_taban"], flush=True)
    allc = M.S_CELLS + M.H_CELLS + M.T_CELLS
    res["tablo"] = {f: {c: stats(K[f], c) for c in allc} for f in ("DUKA_NDX", "MT5_NAS100", "DUKA_DAX", "U_NDX_GUNLUK", "U_NDX_GUNLUK_2016")}
    for fam, cells in (("S", M.S_CELLS), ("H", M.H_CELLS), ("T", M.T_CELLS)):
        res[fam] = [judge(K, c) for c in select(K["DUKA_NDX"], cells)]
        for j in res[fam]:
            o = j["olcum"]
            print(fam, j["hucre"], j["hukum"], {k: v for k, v in j["olcut"].items()}, "P", j["havuz_P"],
                  "| KES", o["DUKA_KESIF"]["fark"], "TEST", o["DUKA_TEST"]["fark"], "MT5", o["MT5_NAS100"]["fark"],
                  "DAX", o["DUKA_DAX"]["fark"], "U", o["U_NDX_GUNLUK"]["fark"], flush=True)
    res["E"] = e_family(K)
    print("E", json.dumps(res["E"], ensure_ascii=False, default=str))
    res["SL_TP"] = describe_sl_tp(K)
    print("SLTP", json.dumps(res["SL_TP"], ensure_ascii=False, default=str)[:3000])
    (M.HERE / "results/analiz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
