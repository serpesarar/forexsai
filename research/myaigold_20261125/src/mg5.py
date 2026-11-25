"""MG-5 — G0 (MG-4 adayı) üstüne farklı açılardan geliştirme (PROTOCOL MG-5).
Kullanım: python src/mg5.py KESIF | TASIMA | TEST ad1,ad2,..."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anatomi as A  # noqa: E402
import mg4 as M  # noqa: E402
import veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
R = KOK / "results"
ARS = KOK.parent
G0 = {"saatler": M.YOGUN_SAAT, "rejim": "yok", "atr_rel": None, "geri": None, "tp": 59.2, "sl": 94.7, "L": 38.2, "ks": 37.9}


# ───────────── veri ─────────────
def b_yukle(ens: str) -> pd.DataFrame:
    if ens == "XAU":
        return V.xau_1m()
    if ens == "NDX":
        d = pd.read_parquet(ARS / "nom_20261113/data/ndx_1m_v3_duka.parquet", columns=["t", "open", "high", "low", "close", "spr"])
        d["sp"] = d.spr
    else:
        d = pd.read_parquet(ARS / "fibo_altin_bolge_20261116/cache/DAX_1m_raw.parquet").rename(
            columns={"o": "open", "h": "high", "l": "low", "c": "close"})
        sp = (d.ask_open - d.open).where(lambda s: s > 0)
        d["sp"] = sp.fillna(sp.median())
    d = d[["t", "open", "high", "low", "close", "sp"]].dropna().sort_values("t").drop_duplicates("t").reset_index(drop=True)
    return d


def hazirla(ens: str = "XAU") -> dict:
    B = b_yukle(ens)
    H = A.h1(B)
    gun = H.kova // 24
    Dg = H.groupby(gun).c.last()
    ema = Dg.ewm(span=50, adjust=False).mean()
    rej = np.sign(Dg - ema).shift(1)
    H["d1_rejim"] = gun.map(rej).to_numpy()
    H["atr_rel"] = H.atr / H.atr.rolling(480, min_periods=200).median().shift(1)
    saat = H.kova.to_numpy()[300:] + 1
    F = A.karar_ozellik(H, saat)
    F["u"] = saat * 3600
    F["yil"] = pd.to_datetime(F.u, unit="s").dt.year
    F = F[F.gecerli & (F.gun < 5)].reset_index(drop=True)
    t = B.t.to_numpy()
    F["ii"] = np.searchsorted(t, F.u.to_numpy())
    F = F[F.ii < len(t) - 2].reset_index(drop=True)
    return {"ens": ens, "B": B, "F": F, "t": t, "o": B.open.to_numpy(), "h": B.high.to_numpy(), "l": B.low.to_numpy(),
            "sp": B.sp.to_numpy(), "kom": 0.08 if ens == "XAU" else 0.0}


# ───────────── sinyal / geometri ─────────────
def sinyal(F: pd.DataFrame, c: dict) -> tuple[np.ndarray, np.ndarray]:
    d12 = np.sign(F.r12_atr.to_numpy())

    def kosul(d):
        uz = d * F.fiyat_ema50_atr.to_numpy()
        kz = np.where(d > 0, F.konum24, 1 - F.konum24)
        ok = (d * F.r12_atr.to_numpy() >= 1.0) & (np.abs(F.r4_atr.to_numpy()) <= 0.5) & (uz >= 1.0) & (kz >= 0.55) & (kz <= 0.95)
        if c["saatler"] is not None:
            ok &= np.isin(F.saat_utc.to_numpy(), c["saatler"])
        if c["atr_rel"] is not None:
            ok &= (F.atr_rel.to_numpy() >= c["atr_rel"][0]) & (F.atr_rel.to_numpy() <= c["atr_rel"][1])
        if c["geri"] is not None:
            g = d * F.r4_atr.to_numpy()
            ok &= (g >= c["geri"][0]) & (g <= c["geri"][1])
        return ok
    al = kosul(np.ones(len(F))) & (d12 > 0)
    rj = F.d1_rejim.to_numpy()
    if c["rejim"] in ("b1", "b2"):
        al &= rj > 0
    sat = (kosul(-np.ones(len(F))) & (d12 < 0) & (rj < 0)) if c["rejim"] == "b2" else np.zeros(len(F), bool)
    return al | sat, np.where(sat, -1, 1)


def kos(D: dict, idx: np.ndarray, yy: np.ndarray, c: dict, spk: float = 1.0, tek: bool = True, kom: float | None = None) -> pd.DataFrame:
    F = D["F"]
    if c.get("atr_geom"):
        atr = F.atr.to_numpy()[idx]
        g = c["atr_geom"]
        tp, sl, L, ks = g["tp"] * atr, g["sl"] * atr, g["L"] * atr, g["ks"] * atr
    else:
        px = D["o"][F.ii.to_numpy()[idx]]
        tp, sl, L, ks = (px * c[k] / 1e4 for k in ("tp", "sl", "L", "ks"))
    Rr, t0 = M._sim(D["t"], D["o"], D["h"], D["l"], D["sp"], F.ii.to_numpy()[idx].astype(np.int64), yy.astype(np.int64), tp, sl, L, ks,
                    M.T_DK, spk, D["kom"] if kom is None else kom, tek)
    m = t0 > 0
    assert np.isfinite(Rr[m]).all(), "NaN (E154)"
    return pd.DataFrame({"t0": t0[m], "R": Rr[m], "y": yy[m], "yil": F.yil.to_numpy()[idx][m], "saat": F.saat_utc.to_numpy()[idx][m]})


def olc(D: dict, c: dict, a: str, b: str, ek: bool = False) -> dict:
    """mg4.olc ile aynı metrikler (plasebo: aynı yıl × UTC saati × yön)."""
    M.kos, eski = (lambda D_, idx, yy, c_, spk=1.0, tek=True, kom=0.08: kos(D_, idx, yy, c_, spk, tek, None if kom == 0.08 else kom)), M.kos
    M.sinyal, eski_s = sinyal, M.sinyal
    try:
        return M.olc(D, c, a, b, ek)
    finally:
        M.kos, M.sinyal = eski, eski_s


def iyi(h: dict, t: dict) -> bool:
    if not M.gecer(h):
        return False
    return h["aylik_R"] > t["aylik_R"] or (h["sharpe"] > t["sharpe"] and h["aylik_R"] >= 0.9 * t["aylik_R"])


# ───────────── hücreler ─────────────
def saat_secimi(D: dict) -> list[int]:
    c = {**G0, "saatler": None}
    ok, d = sinyal(D["F"], c)
    F = D["F"]
    don = ((F.u >= pd.Timestamp("2018-01-01", tz="UTC").timestamp()) & (F.u < pd.Timestamp("2022-01-01", tz="UTC").timestamp())).to_numpy()
    idx = np.flatnonzero(ok & don)
    r = kos(D, idx, d[idx], c, tek=False)
    s = r.groupby("saat").R.mean()
    return sorted(int(h) for h, v in s.items() if v > 0)


def hucreler(D: dict) -> list[dict]:
    A1 = saat_secimi(D)
    H = [{"ad": "G0", **G0},
         {"ad": "A1_kesif_artı_saatler", **G0, "saatler": A1},
         {"ad": "A2_tum_saatler", **G0, "saatler": None},
         {"ad": "B1_d1_rejim", **G0, "rejim": "b1"},
         {"ad": "B2_rejim_ayna_sat", **G0, "rejim": "b2"},
         {"ad": "C1_oynaklik_0.8_1.5", **G0, "atr_rel": (0.8, 1.5)},
         {"ad": "C2_geri_cekilme", **G0, "geri": (-0.5, 0.0)},
         {"ad": "C3_ileri_kayma", **G0, "geri": (0.0, 0.5)},
         {"ad": "D1_tp80", **G0, "tp": 80.0},
         {"ad": "D2_tp120", **G0, "tp": 120.0},
         {"ad": "D3_kilit50_40", **G0, "L": 50.0, "ks": 40.0},
         {"ad": "D4_sl70", **G0, "sl": 70.0}]
    return H


def kesif() -> None:
    D = hazirla("XAU")
    a, b = M.DONEM["KESIF"]
    out = {}
    hs = hucreler(D)
    for c in hs:
        h = olc(D, c, a, b)
        out[c["ad"]] = {"tanim": c, **h}
        print(c["ad"], {k: h.get(k) for k in M.KOL}, flush=True)
    t = out["G0"]
    gec = [k for k, v in out.items() if k != "G0" and iyi(v, t)]
    gec.sort(key=lambda k: -out[k]["aylik_R"])
    out["_gecen"] = gec
    if gec:
        bir = {**G0}
        for k in gec:
            for kk, vv in out[k]["tanim"].items():
                if kk != "ad" and vv != G0.get(kk):
                    bir[kk] = vv
        bir["ad"] = "BIRLESIK"
        h = olc(D, bir, a, b)
        out["BIRLESIK"] = {"tanim": bir, **h, "iyi": iyi(h, t)}
        print("BIRLESIK", {k: h.get(k) for k in M.KOL}, flush=True)
    print("GEÇEN", gec, flush=True)
    (R / "mg5_kesif.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    pd.DataFrame([{"ad": k, **{x: v.get(x) for x in M.KOL}} for k, v in out.items() if not k.startswith("_")]).to_csv(R / "mg5_kesif.csv", index=False)


def tasima() -> None:
    DX = hazirla("XAU")
    F = DX["F"]
    k = (F.u < pd.Timestamp("2022-01-01", tz="UTC").timestamp()) & (F.u >= pd.Timestamp("2018-01-01", tz="UTC").timestamp())
    atr_bp = float(np.median(F.atr[k] / F.c[k] * 1e4))
    geom = {x: G0[x] / atr_bp for x in ("tp", "sl", "L", "ks")}
    out = {"xau_atr_bp_medyan": round(atr_bp, 2), "atr_geom": {k_: round(v, 3) for k_, v in geom.items()}}
    print("ATR geometrisi", out["atr_geom"], flush=True)
    for ens in ("NDX", "DAX"):
        D = hazirla(ens)
        for saat_ad, saatler in (("G0_saatleri", G0["saatler"]), ("tum_saatler", None)):
            c = {**G0, "saatler": saatler, "atr_geom": geom}
            res = {d: olc(D, c, *M.DONEM[d]) for d in ("KESIF", "TEST", "KOR")}
            out[f"{ens}_{saat_ad}"] = res
            print(ens, saat_ad, {d: {k_: res[d].get(k_) for k_ in ("n", "ayda", "ort_R", "P_EV", "fark_R", "fark_P", "yillik_R")} for d in res},
                  flush=True)
    (R / "mg5_tasima.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def test(adlar: list[str]) -> None:
    D = hazirla("XAU")
    j = json.loads((R / "mg5_kesif.json").read_text())
    t0 = olc(D, G0, *M.DONEM["TEST"], ek=True)
    out = {"G0_TEST": t0}
    for ad in adlar:
        c = j[ad]["tanim"]
        for k in ("saatler", "atr_rel", "geri"):
            c[k] = None if c.get(k) is None else c[k]
        h = olc(D, c, *M.DONEM["TEST"], ek=True)
        h["kontrol"] = {"P_EV_0.99": h["P_EV"] >= 0.99, "plasebo_0.99": h["fark_R"] > 0 and h["fark_P"] >= 0.99,
                        "yarilar_stres_en_iyi10": h["yari1"] > 0 and h["yari2"] > 0 and h["stres_R"] > 0 and h["en_iyi10_haric"] > 0,
                        "2022_25": all(h["yillik_R"].get(y, -1) > 0 for y in (2022, 2023, 2024, 2025)), "n150": h["n"] >= 150,
                        "icra": h["iyimser_R"] - h["ort_R"] <= h["ort_R"] / 2,
                        "G0dan_iyi": h["aylik_R"] > t0["aylik_R"] and h["sharpe"] >= 0.9 * t0["sharpe"]}
        h["hukum"] = "B" if all(h["kontrol"].values()) else "X"
        h["kor"] = olc(D, c, *M.DONEM["KOR"])
        out[ad] = h
        print(ad, h["hukum"], h["kontrol"], {k: h.get(k) for k in M.KOL + ("yillik_R",)}, "| KÖR", {k: h["kor"].get(k) for k in ("n", "ort_R")},
              flush=True)
    print("G0 TEST", {k: t0.get(k) for k in ("n", "ayda", "ort_R", "aylik_R", "sharpe")})
    (R / "mg5_test.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"KESIF": kesif, "TASIMA": tasima}.get(sys.argv[1], lambda: test(sys.argv[2].split(",")))()
