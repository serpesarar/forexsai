"""SC-20 — NASDAQ E2X3 dallanması (PROTOCOL SC-20). Ana gövde: Soma klon modeli AL, SL 1×ATR_H1, 480 dk.

Kullanım:
  python src/sc20_ndx_dal.py KESIF                 → results/sc20_kesif.csv + .json (≈110 hücre, aday seçimi)
  python src/sc20_ndx_dal.py DOGRULAMA a,b,c       → results/sc20_dogrulama.json (aday başına tek atış)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_model as SM  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc10_klon_kar as C10  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc14_bakis as B  # noqa: E402
import sc19_canli_kart as K19  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

R = S13.R
DONEM = {"KESIF": ("2018-01-15", "2022-11-14"), "DOGRULAMA": ("2022-11-14", "2026-11-14")}
TUM = ("2018-01-15", "2026-11-14")
SKOR = R / "sc20_ndx_skor.parquet"
MACRO = V.ROOT / "research" / "nom_20261113" / "data" / "macro" / "macro_daily.parquet"
VIX_ESIK = 18.4
N_TABAN = 5
TABAN = dict(yon=1, q=0.998, sl=1.0, T=480)


# ───────────────────────── veri ─────────────────────────
def hazirla() -> dict:
    bar, vol, _ = K19.ndx_bar()
    M = F.Motor(bar, vol)
    model, oz, _ = B.model_ve_esik()
    if SKOR.exists():
        G = pd.read_parquet(SKOR)
    else:
        G = C10.skorla(M, model, oz, *TUM)
        G.to_parquet(SKOR)
    X = pd.read_parquet(R / "sc08_matris_son.parquet")
    G0 = pd.read_parquet(R / "sc08_skor_son.parquet").assign(t=lambda d: d["t"] + 60)
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    esik = {q: float(np.quantile(G0.loc[G0.t < kesim, "skor"], q)) for q in (0.99, 0.995, 0.997, 0.998, 0.999)}
    return {"M": M, "G": G, "esik": esik, "e4": S13.soma_tetik(M, *TUM)}


def ates(G: pd.DataFrame, esik: float, yon: int) -> pd.DataFrame:
    K.SOGUMA = 0
    A = K.ateslemeler(G.assign(ok=G["skor"] >= esik))
    A = A[A["y"] == yon]
    return A[["j", "t", "skor"]].reset_index(drop=True)


def ozellik_ek(M: F.Motor, A: pd.DataFrame) -> pd.DataFrame:
    """Süzgeç alanları (hepsi karar anında bilinir)."""
    k = A["j"].to_numpy()
    t = M.bar.t[k] + 60
    ny = pd.to_datetime(t, unit="s", utc=True).tz_convert("America/New_York")
    mac = pd.read_parquet(MACRO)[["date", "VIX_close", "VIX3M_close"]].dropna(subset=["VIX_close"])
    mac["date"] = pd.to_datetime(mac["date"]).dt.normalize()
    gun = pd.to_datetime(ny.date)
    idx = np.searchsorted(mac["date"].to_numpy(), gun.to_numpy(), side="left") - 1      # önceki NY günü kapanışı
    ok = idx >= 0
    vix = np.where(ok, mac["VIX_close"].to_numpy()[np.clip(idx, 0, None)], np.nan)
    v3 = np.where(ok, mac["VIX3M_close"].to_numpy()[np.clip(idx, 0, None)], np.nan)
    dk = ny.hour * 60 + ny.minute
    H4, D1 = M.tf["H4"], M.tf["D1"]
    b4 = np.clip(np.searchsorted(H4.kova, H4.kova_1m[k]) - 1, 0, len(H4.C) - 1)
    b1 = np.clip(np.searchsorted(D1.kova, D1.kova_1m[k]) - 1, 0, len(D1.C) - 1)
    onceki = np.r_[np.inf, np.diff(t)]
    return A.assign(vix=vix, vix_oran=vix / v3, ny_dk=dk.to_numpy(), gun=ny.weekday.to_numpy(),
                    h4_trend=H4.C[b4] > H4.g["ema50"][b4], d1_trend=D1.C[b1] > D1.g["ema200"][b1], ara_s=onceki)


SEANS = {"asya": lambda d: (d >= 18 * 60) | (d < 2 * 60), "avrupa": lambda d: (d >= 120) & (d < 570),
         "abd": lambda d: (d >= 570) & (d < 960), "aksam": lambda d: (d >= 960) & (d < 1080)}


def suzgec(A: pd.DataFrame, ad: str | None, esik: float) -> np.ndarray:
    if ad is None:
        return np.ones(len(A), bool)
    f = {
        "vix_yuksek": A.vix >= VIX_ESIK, "vix_dusuk": A.vix < VIX_ESIK,
        "egri_ters": A.vix_oran >= 1, "egri_normal": A.vix_oran < 1,
        "nakit": (A.ny_dk >= 570) & (A.ny_dk < 960), "nakit_disi": ~((A.ny_dk >= 570) & (A.ny_dk < 960)),
        "h4_ust": A.h4_trend, "h4_alt": ~A.h4_trend, "d1_ust": A.d1_trend, "d1_alt": ~A.d1_trend,
        "skor_ust": A.skor >= np.median(A.skor), "skor_alt": A.skor < np.median(A.skor),
        "ara_kisa": A.ara_s < 86400, "ara_uzun": A.ara_s >= 86400,
    }
    for s, fn in SEANS.items():
        f[f"seans_{s}"] = fn(A.ny_dk)
    for g in range(5):
        f[f"gun_{g}"] = A.gun == g
    return np.asarray(f[ad], bool)


# ───────────────────────── simülasyon ─────────────────────────
def sim(M: F.Motor, k: np.ndarray, c: dict, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    i0 = k + 1
    a = S13.atr_h1(M, k)
    m = (i0 < len(bar) - 2) & np.isfinite(a) & (a > 0)
    sl = c["sl"] * a[m]
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:], e.sl_d[:] = i0[m], c["yon"], sl
    e.t_cik[:] = bar.t[i0[m]] + c["T"] * 60
    if c.get("tp"):
        e.tp_d[:] = c["tp"] * sl
    if c.get("iz"):
        e.iz_akt[:], e.iz_d[:] = c["iz"][0] * sl, c["iz"][1] * sl
    if c.get("be"):
        e.be_akt[:], e.be_off[:] = c["be"] * sl, 0.0
    r = S.simule(bar, e, sk=sk, komisyon_usd=0.0)
    r["R"] = r["bp"] / (sl / bar.o[i0[m]] * 1e4)
    r["puan"] = r["bp"] * bar.o[i0[m]] / 1e4
    r["k"] = k[m]
    return r


def piramit(r: pd.DataFrame) -> pd.DataFrame:
    """Tek pozisyon + açıkken gelen İLK ek ateşleme (+1 birim, kendi çıkışıyla)."""
    d = r.sort_values("t0").reset_index(drop=True)
    tut, son, ek = [], -1, False
    for i, (a, b) in enumerate(zip(d.t0.to_numpy(), d.t1.to_numpy())):
        if a >= son:
            tut.append(i)
            son, ek = b, False
        elif not ek:
            tut.append(i)
            ek = True
    return d.iloc[tut]


def olc(M: F.Motor, r: pd.DataFrame, rs: pd.DataFrame, tbl: list[np.ndarray], a: str, b: str, mod: str = "tek") -> dict:
    if len(r) < 2:
        return {"n": len(r)}
    x, gun = r["bp"].to_numpy(), r["t0"].to_numpy() // 86400
    n_tb = min([len(r)] + [len(z) for z in tbl])
    tb = np.mean([z[:n_tb] for z in tbl], axis=0)
    tek = piramit(r) if mod == "piramit" else (r if mod == "eszamanli" else D.tek_pozisyon(r))
    yil = (D.ts(b) - D.ts(a)) / 86400 / 365.25
    gunluk = tek.groupby(tek["t0"] // 86400)["puan"].sum()
    bd = pd.bdate_range(pd.to_datetime(D.ts(a), unit="s"), pd.to_datetime(D.ts(b), unit="s"))
    g = gunluk.reindex(bd.asi8 // 10**9 // 86400, fill_value=0.0)
    egri = np.cumsum(tek.sort_values("t0")["puan"].to_numpy())
    kaz, kay = x[x > 0], x[x <= 0]
    yari = len(x) // 2
    yr = pd.to_datetime(r["t0"], unit="s").dt.year
    return {"n": len(x), "ort_bp": round(float(x.mean()), 3), "ort_R": round(float(r["R"].mean()), 4),
            "isabet": round(float((x > 0).mean()), 3),
            "basabas_isabet": round(float(-kay.mean() / (kaz.mean() - kay.mean())), 3) if len(kaz) and len(kay) else None,
            "P_EV": round(D.gun_blok_P(x, gun), 4), "taban_bp": round(float(tb.mean()), 3),
            "fark": round(float(x[:n_tb].mean() - tb.mean()), 3), "fark_P": round(D.fark_P(x[:n_tb], tb, gun[:n_tb]), 4),
            "yari1": round(float(x[:yari].mean()), 3), "yari2": round(float(x[yari:].mean()), 3),
            "stres": round(float(rs["bp"].mean()), 3), "tek_n": len(tek), "tek_R": round(float(tek["R"].mean()), 4),
            "tek_isabet": round(float((tek["bp"] > 0).mean()), 3),
            "puan_yil": round(float(tek["puan"].sum() / yil), 1), "sharpe": round(float(g.mean() / g.std() * np.sqrt(252)), 3),
            "maks_dusus_puan": round(float((np.maximum.accumulate(egri) - egri).max()), 1),
            "yillik_R": {int(y): round(float(v), 3) for y, v in r.groupby(yr)["R"].mean().items()}}


# ───────────────────────── hücreler ─────────────────────────
def hucreler() -> list[dict]:
    H = []
    for sl in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0):
        for T in (120, 240, 480, 960, 1440, 2880):
            H.append({"ad": f"F1_sl{sl}_T{T}", **TABAN, "sl": sl, "T": T})
    for tp in (1, 1.5, 2, 3, 5):
        H.append({"ad": f"F2_tp{tp}", **TABAN, "tp": tp})
    for akt in (0.5, 1, 2):
        for dd in (0.5, 1):
            H.append({"ad": f"F2_iz{akt}_{dd}", **TABAN, "iz": (akt, dd)})
    H.append({"ad": "F2_be1", **TABAN, "be": 1.0})
    for q in (0.99, 0.995, 0.997, 0.999):
        H.append({"ad": f"F3_q{q}", **TABAN, "q": q})
    for f in ("vix_yuksek", "vix_dusuk", "egri_ters", "egri_normal", "nakit", "nakit_disi", "h4_ust", "h4_alt", "d1_ust", "d1_alt",
              "skor_ust", "skor_alt", "ara_kisa", "ara_uzun", *[f"seans_{s}" for s in SEANS], *[f"gun_{g}" for g in range(5)]):
        H.append({"ad": f"F4_{f}", **TABAN, "filtre": f})
    H.append({"ad": "F5_satis", **TABAN, "yon": -1})
    H.append({"ad": "F6_eszamanli", **TABAN, "mod": "eszamanli"})
    H.append({"ad": "F6_piramit", **TABAN, "mod": "piramit"})
    H.append({"ad": "F7_e4_ayni_gun", **TABAN, "filtre": "e4"})
    return [{"ad": "TABAN", **TABAN}] + H + ek1()


def ek1() -> list[dict]:
    H = []
    for be in (0.5, 0.75, 1.0, 1.5):
        for T in (480, 960):
            for mod in ("tek", "piramit"):
                H.append({"ad": f"EK1_be{be}_T{T}_{mod}", **TABAN, "T": T, "be": be, "mod": mod})
    return H


def kos_hucre(ctx: dict, c: dict, a: str, b: str) -> dict:
    M, G = ctx["M"], ctx["G"]
    A = ates(G, ctx["esik"][c["q"]], c["yon"])
    A = A[(M.bar.t[A.j.to_numpy()] >= D.ts(a)) & (M.bar.t[A.j.to_numpy()] < D.ts(b))].reset_index(drop=True)
    A = ozellik_ek(M, A)
    if c.get("filtre") == "e4":
        e4 = ctx["e4"]
        e4 = e4[e4.y > 0]
        gun_e4 = pd.Series(M.tf["D1"].kova_1m[e4.k.to_numpy()], index=e4.k.to_numpy())
        ilk = gun_e4.groupby(gun_e4.values).apply(lambda s: s.index.min())
        gk = M.tf["D1"].kova_1m[A.j.to_numpy()]
        m = np.array([g in ilk.index and ilk[g] <= j for g, j in zip(gk, A.j.to_numpy())])
    else:
        m = suzgec(A, c.get("filtre"), ctx["esik"][c["q"]])
    k = A.j.to_numpy()[m]
    r, rs = sim(ctx["M"], k, c), sim(ctx["M"], k, c, 1.5)
    rng = np.random.default_rng(D.TOHUM)
    kt = B.rastgele(M, k, a, b, rng) if len(k) else []
    tbl = [sim(M, z, c)["bp"].to_numpy() for z in kt]
    return olc(M, r, rs, tbl, a, b, c.get("mod", "tek"))


def gecer_kesif(h: dict, t: dict) -> bool:
    if h.get("n", 0) < 150:
        return False
    temel = h["fark"] > 0 and h["fark_P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0 and h["stres"] > 0 and h["tek_R"] > 0
    s_up, p_up = h["sharpe"] > t["sharpe"], h["puan_yil"] > t["puan_yil"]
    diger = (h["puan_yil"] >= 0.9 * t["puan_yil"]) if s_up else (h["sharpe"] >= 0.9 * t["sharpe"])
    return temel and (s_up or p_up) and diger


def kesif(ek: bool = False) -> None:
    ctx = hazirla()
    a, b = DONEM["KESIF"]
    out = {"esik": ctx["esik"]}
    liste = ([{"ad": "TABAN", **TABAN, "be": 1.0}] + ek1()) if ek else hucreler()
    for c in liste:
        h = kos_hucre(ctx, c, a, b)
        out[c["ad"]] = {"tanim": {k: v for k, v in c.items() if k != "ad"}, **h}
        D.kaydet("SC-20", "KESIF", {"hucre": c["ad"]}, {k: v for k, v in h.items() if k != "yillik_R"})
        print(c["ad"], {x: h.get(x) for x in ("n", "ort_R", "isabet", "fark", "fark_P", "tek_n", "puan_yil", "sharpe", "maks_dusus_puan")},
              flush=True)
    t = out["TABAN"]
    gec = [k for k, v in out.items() if k not in ("esik", "TABAN") and isinstance(v, dict) and gecer_kesif(v, t)]
    if ek:
        gec = [k for k in gec if out[k]["sharpe"] >= 0.9 * t["sharpe"]]
        gec.sort(key=lambda k: -out[k]["puan_yil"])
        out["gecen"], out["aday"] = gec, gec[:2]
    else:
        gec.sort(key=lambda k: -out[k]["sharpe"])
        out["gecen"], out["aday"] = gec, gec[:3]
    print("GEÇEN", gec, "→ ADAY", out["aday"])
    son = "_ek1" if ek else ""
    (R / f"sc20_kesif{son}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    pd.DataFrame([{"ad": k, **{x: v.get(x) for x in ("n", "ort_bp", "ort_R", "isabet", "basabas_isabet", "fark", "fark_P", "stres",
                                                     "tek_n", "tek_R", "tek_isabet", "puan_yil", "sharpe", "maks_dusus_puan")}}
                  for k, v in out.items() if isinstance(v, dict) and "tanim" in v]).to_csv(R / f"sc20_kesif{son}.csv", index=False)


def dogrulama(adlar: list[str], taban: str = "TABAN") -> None:
    ctx = hazirla()
    a, b = DONEM["DOGRULAMA"]
    tanim = {c["ad"]: c for c in hucreler()}
    out = {"kiyas": taban}
    t = kos_hucre(ctx, tanim[taban], a, b)
    out["TABAN"] = t
    for ad in adlar:
        c = tanim[ad]
        h = kos_hucre(ctx, c, a, b)
        yr = h.get("yillik_R", {})
        s_up, p_up = h["sharpe"] > t["sharpe"], h["puan_yil"] > t["puan_yil"]
        diger = (h["puan_yil"] >= 0.9 * t["puan_yil"]) if s_up else (h["sharpe"] >= 0.9 * t["sharpe"])
        kart = (h["n"] >= 150 and h["ort_R"] > 0 and h["P_EV"] >= 0.90 and h["yari1"] >= 0 and h["yari2"] >= 0 and h["stres"] > 0
                and h["tek_R"] > 0)
        yil_ok = all(yr.get(y, -1) > 0 for y in (2023, 2024, 2025, 2026))
        h["hukum"] = "B" if (kart and yil_ok and h["fark_P"] >= 0.95 and (s_up or p_up) and diger) else "X"
        h["kontrol"] = {"kart_5olcut": kart, "son4_yil": yil_ok, "fark_P": h["fark_P"] >= 0.95, "tabandan_iyi": (s_up or p_up) and diger}
        out[ad] = h
        D.kaydet("SC-20", "DOGRULAMA", {"hucre": ad}, {k: v for k, v in h.items() if k not in ("yillik_R", "kontrol")})
        print(ad, h["hukum"], h["kontrol"], {x: h.get(x) for x in ("n", "ort_R", "isabet", "puan_yil", "sharpe", "yillik_R")}, flush=True)
    print("TABAN", {x: t.get(x) for x in ("n", "ort_R", "isabet", "puan_yil", "sharpe", "yillik_R")})
    (R / f"sc20_dogrulama{'_ek1' if taban != 'TABAN' else ''}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    if sys.argv[1] == "KESIF":
        kesif(ek=len(sys.argv) > 2 and sys.argv[2] == "EK1")
    else:
        dogrulama(sys.argv[2].split(","), sys.argv[3] if len(sys.argv) > 3 else "TABAN")
