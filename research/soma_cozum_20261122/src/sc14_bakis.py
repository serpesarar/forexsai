"""SC-14 — farklı bakış açıları (PROTOCOL SC-14): A stop×süre platosu, B yapısal stop, C rejim, D başarısızlığı tersine çevir,
E piramit, F piyasadan öğrenilmiş seçim. Keşif GELISTIRME; `DOGRULAMA <hucre>` / `KASA <hucre>` tek atış.
Çıktı: results/sc14_<donem>.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SC08_AN", "son")
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_model as SM  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc10_klon_kar as C10  # noqa: E402
import sc13_strateji as S13  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

R = S13.R
ARALIK = {**S13.ARALIK, "KASA": ("2010-03-01", "2018-01-01")}
N_TABAN = 5
A_K = (0.5, 0.75, 1.0, 1.5, 2.0)
A_T = (240, 480, 960)
B_M = (0.0, 0.25, 0.5)
REF = "A_k1.0_T480"   # = E2X3


# ───────────────────────── ortak ─────────────────────────
def model_ve_esik() -> tuple:
    X = pd.read_parquet(R / "sc08_matris_son.parquet")
    oz = SM.ozellik_listesi(X)
    tr = X[(X["bolum"] == "KESIF") & X["hesap"].isin(["2268766", "karsi"])]
    model = HistGradientBoostingClassifier(max_depth=4, max_iter=300, learning_rate=0.05, class_weight="balanced",
                                           l2_regularization=1.0, random_state=0).fit(tr[oz].to_numpy(np.float32),
                                                                                       (tr["hesap"] == "2268766").to_numpy())
    G0 = pd.read_parquet(R / "sc08_skor_son.parquet").assign(t=lambda d: d["t"] + 60)
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    q = {qq: float(np.quantile(G0.loc[G0.t < kesim, "skor"], qq)) for qq in (0.99, 0.998)}
    return model, oz, q


def skorlar(M: F.Motor, donem: str, model, oz) -> pd.DataFrame:
    yol = R / f"sc14_skor_{donem}.parquet"
    if yol.exists():
        return pd.read_parquet(yol)
    a, b = ARALIK[donem]
    G = C10.skorla(M, model, oz, a, b)
    G.to_parquet(yol)
    return G


def alis_ates(G: pd.DataFrame, esik: float) -> np.ndarray:
    K.SOGUMA = 0
    A = K.ateslemeler(G.assign(ok=G["skor"] >= esik))
    return A.loc[A["y"] > 0, "j"].to_numpy()


def sim_d(M: F.Motor, i0: np.ndarray, y: np.ndarray, sl: np.ndarray, T: int, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    m = (i0 < len(bar) - 2) & np.isfinite(sl) & (sl > 0)
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:], e.sl_d[:] = i0[m], y[m], sl[m]
    e.t_cik[:] = bar.t[i0[m]] + T * 60
    r = S.simule(bar, e, sk=sk)
    r["src"] = np.flatnonzero(m)
    return r


def sharpe_tum(r: pd.DataFrame, a: str, b: str) -> float:
    g = r.groupby(r["t0"] // 86400)["bp"].sum()
    gunler = pd.bdate_range(a, b, inclusive="left").view("int64") // 10 ** 9 // 86400
    x = g.reindex(gunler, fill_value=0.0).to_numpy()
    return round(float(x.mean() / x.std() * np.sqrt(252)), 3) if x.std() > 0 else 0.0


def rastgele(M: F.Motor, k: np.ndarray, a: str, b: str, rng, uygun: np.ndarray | None = None) -> list[np.ndarray]:
    bar = M.bar
    saat = (bar.t // 3600) % 24
    ok = (bar.t >= D.ts(a)) & (bar.t < D.ts(b)) & np.isfinite(S13.atr_h1(M, np.arange(len(bar))))
    if uygun is not None:
        ok &= uygun
    havuz = {h: np.flatnonzero(ok & (saat == h)) for h in range(24)}
    return [np.array([rng.choice(havuz[h]) for h in saat[k]], dtype=np.int64) for _ in range(N_TABAN)]


def degerle(r: pd.DataFrame, rs: pd.DataFrame, tb: np.ndarray, a: str, b: str) -> dict:
    o = D.ozet(r)
    yil = o.get("yillik", {})
    n = min(len(r), len(tb))
    return {**{k: o.get(k) for k in ("n", "ort_bp", "isabet", "toplam_bp", "yari1", "yari2", "yillik", "maks_dusus_bp")},
            "taban": round(float(np.mean(tb)), 3), "fark": round(float(r["bp"].mean() - np.mean(tb)), 3),
            "fark_P": round(D.fark_P(r["bp"].to_numpy()[:n], tb[:n], r["t0"].to_numpy()[:n] // 86400), 4),
            "stres": round(float(rs["bp"].mean()), 3), "tek_poz": round(float(D.tek_pozisyon(r)["bp"].mean()), 3),
            "yil_arti": int(sum(v > 0 for v in yil.values())), "sharpe": sharpe_tum(r, a, b)}


def gecit(h: dict, ref_sharpe: float | None) -> bool:
    return bool(h["n"] and h["ort_bp"] > 0 and h["fark"] > 0 and h["fark_P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0
                and h["stres"] > 0 and h["yil_arti"] >= 3 and (ref_sharpe is None or h["sharpe"] > ref_sharpe))


# ───────────────────────── açılar ─────────────────────────
def hucre_sabit(M, k, kt, kk_list, a, b, sl_kat: float, T: int) -> dict:
    sl = sl_kat * S13.atr_h1(M, k)
    r, rs = sim_d(M, k + 1, np.ones(len(k), np.int32), sl, T), sim_d(M, k + 1, np.ones(len(k), np.int32), sl, T, 1.5)
    tb = np.mean([sim_d(M, kk + 1, np.ones(len(kk), np.int32), sl_kat * S13.atr_h1(M, kk), T)["bp"].to_numpy()
                  for kk in kk_list], axis=0)
    return degerle(r, rs, tb, a, b)


def yapisal_sl(M: F.Motor, k: np.ndarray, m: float) -> np.ndarray:
    H4 = M.tf["H4"]
    bc = np.clip(np.searchsorted(H4.kova, H4.kova_1m[k]) - 1, 0, len(H4.C) - 1)
    a = S13.atr_h1(M, k)
    giris = M.bar.o[np.minimum(k + 1, len(M.bar) - 1)] + M.bar.s[np.minimum(k + 1, len(M.bar) - 1)]
    d = giris - (H4.g["hh20"][bc] - m * a)
    return np.clip(d, 0.25 * a, 3.0 * a)


def rejim(M: F.Motor, k: np.ndarray, ad: str) -> np.ndarray:
    D1 = M.tf["D1"]
    bc = np.clip(np.searchsorted(D1.kova, D1.kova_1m[k]) - 1, 0, len(D1.C) - 1)
    C = D1.C
    if ad == "R1":
        return C[bc] > D1.g["ema200"][bc]
    if ad == "R2":
        z = D1.g["atr"] / C
        med = pd.Series(z).rolling(250, min_periods=120).median().to_numpy()
        return z[bc] > med[bc]
    tepe = pd.Series(D1.H).rolling(252, min_periods=120).max().to_numpy()
    return C[bc] >= 0.97 * tepe[bc]


def piramit(M: F.Motor, k: np.ndarray, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    a = S13.atr_h1(M, k)
    r1 = sim_d(M, k + 1, np.ones(len(k), np.int32), a, 480, sk)
    i2, src2 = [], []
    for row in r1.itertuples():
        s = row.src
        hedef = row.giris + a[s]
        j_bit = row.j
        seg = bar.h[row.i0:j_bit]
        hit = np.flatnonzero(seg >= hedef)
        if len(hit) and row.i0 + hit[0] + 1 < j_bit:
            i2.append(row.i0 + hit[0] + 1)
            src2.append(s)
    i2, src2 = np.array(i2, dtype=np.int64), np.array(src2, dtype=np.int64)
    r2 = pd.DataFrame(columns=["src", "bp"])
    if len(i2):
        bar_t = bar.t
        m = S.Emir.yeni(len(i2))
        m.i0[:], m.yon[:], m.sl_d[:] = i2, 1, a[src2]
        m.t_cik[:] = bar_t[k[src2] + 1] + 480 * 60
        r2 = S.simule(bar, m, sk=sk)
        r2["src"] = src2
    ek = r2.groupby("src")["bp"].sum() if len(r2) else pd.Series(dtype=float)
    r1 = r1.copy()
    r1["bp_tek"] = r1["bp"]
    r1["bp"] = r1["bp"] + r1["src"].map(ek).fillna(0.0).to_numpy()
    r1["birim"] = 1 + r1["src"].isin(ek.index).astype(int)
    return r1


def tersine(M: F.Motor, k: np.ndarray, sk: float = 1.0) -> tuple[pd.DataFrame, np.ndarray]:
    a = S13.atr_h1(M, k)
    r = sim_d(M, k + 1, np.ones(len(k), np.int32), a, 480)
    m = (r["neden"] == "STOP").to_numpy() & ((r["t1"] - r["t0"]).to_numpy() <= 3600)
    jj = r["j"].to_numpy()[m] + 1
    kk = r["j"].to_numpy()[m]
    out = sim_d(M, jj, -np.ones(len(jj), np.int32), S13.atr_h1(M, kk), 240, sk)
    return out, kk


def ogrenilmis(M: F.Motor, G: pd.DataFrame, q: dict, a: str, b: str) -> np.ndarray:
    """Katman-dışı seçilen ALIŞ ateşlemelerinin k'ları (2018–19 ↔ 2020–21)."""
    k = alis_ates(G, q[0.99])
    t = M.bar.t[k]
    X = M.ozellik(k, M.bar.c[k], np.ones(len(k)), t + 60)
    oz = [c for c in X.columns if c[:3] in ("M1_", "M5_", "M15", "M30", "H1_", "H4_", "D1_", "SV_", "HC_") or c in ("Z_saat", "Z_gun")]
    hedef = np.full(len(k), np.nan)
    r = sim_d(M, k + 1, np.ones(len(k), np.int32), S13.atr_h1(M, k), 480)
    hedef[r["src"].to_numpy()] = (r["bp"].to_numpy() > 0)
    yil = pd.to_datetime(t, unit="s").year
    kat = np.where(yil <= 2019, 0, 1)
    secim = np.zeros(len(k), bool)
    for f in (0, 1):
        tr, te = (kat != f) & np.isfinite(hedef), kat == f
        mdl = HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.05, l2_regularization=1.0,
                                             random_state=0).fit(X.loc[tr, oz].to_numpy(np.float32), hedef[tr].astype(int))
        s_tr = mdl.predict_proba(X.loc[tr, oz].to_numpy(np.float32))[:, 1]
        esik = np.quantile(s_tr, 2 / 3)
        secim[te] = mdl.predict_proba(X.loc[te, oz].to_numpy(np.float32))[:, 1] >= esik
    return k[secim]


# ───────────────────────── koşucu ─────────────────────────
def kesif() -> dict:
    a, b = ARALIK["GELISTIRME"]
    M = F.yukle("2017-01-01")
    model, oz, q = model_ve_esik()
    G = skorlar(M, "GELISTIRME", model, oz)
    k = alis_ates(G, q[0.998])
    rng = np.random.default_rng(D.TOHUM)
    kt = rastgele(M, k, a, b, rng)
    sonuc: dict = {"n_E2": len(k)}

    def kaydet(ad, h):
        sonuc[ad] = h
        D.kaydet("SC-14", "GELISTIRME", {"hucre": ad}, h)
        print(ad, {x: h.get(x) for x in ("n", "ort_bp", "taban", "fark", "fark_P", "yari1", "yari2", "stres", "yil_arti", "sharpe",
                                         "maks_dusus_bp")}, flush=True)

    for kk_ in A_K:
        for T in A_T:
            kaydet(f"A_k{kk_}_T{T}", hucre_sabit(M, k, None, kt, a, b, kk_, T))
    ref_sh = sonuc[REF]["sharpe"]
    for m in B_M:
        sl = yapisal_sl(M, k, m)
        r, rs = sim_d(M, k + 1, np.ones(len(k), np.int32), sl, 480), sim_d(M, k + 1, np.ones(len(k), np.int32), sl, 480, 1.5)
        tb = np.mean([sim_d(M, kk + 1, np.ones(len(kk), np.int32), yapisal_sl(M, kk, m), 480)["bp"].to_numpy() for kk in kt], axis=0)
        kaydet(f"B_m{m}", degerle(r, rs, tb, a, b))
    for ad in ("R1", "R2", "R3"):
        f = rejim(M, k, ad)
        kr = k[f]
        uygun = rejim(M, np.arange(len(M.bar)), ad)
        ktr = rastgele(M, kr, a, b, rng, uygun)
        kaydet(f"C_{ad}", hucre_sabit(M, kr, None, ktr, a, b, 1.0, 480))
    r, kk_stop = tersine(M, k)
    rs, _ = tersine(M, k, 1.5)
    ks = rastgele(M, kk_stop, a, b, rng)
    tb = np.mean([sim_d(M, x + 1, -np.ones(len(x), np.int32), S13.atr_h1(M, x), 240)["bp"].to_numpy() for x in ks], axis=0)
    kaydet("D_ters", degerle(r, rs, tb, a, b))
    rp, rps = piramit(M, k), piramit(M, k, 1.5)
    tb = np.mean([piramit(M, x)["bp"].to_numpy() for x in kt], axis=0)
    h = degerle(rp, rps, tb, a, b)
    h["birim_basi_bp"] = round(float(rp["bp"].sum() / rp["birim"].sum()), 3)
    h["ek_birim_payi"] = round(float((rp["birim"] == 2).mean()), 3)
    kaydet("E_piramit", h)
    kf = ogrenilmis(M, G, q, a, b)
    kft = rastgele(M, kf, a, b, rng)
    kaydet("F_ogrenilmis", hucre_sabit(M, kf, None, kft, a, b, 1.0, 480))
    # A plato seçimi
    for ad in [x for x in sonuc if x.startswith("A_")]:
        i, j = A_K.index(float(ad.split("_k")[1].split("_")[0])), A_T.index(int(ad.split("_T")[1]))
        kom = [sonuc[f"A_k{A_K[ii]}_T{A_T[jj]}"]["fark"] for ii, jj in ((i, j), (i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
               if 0 <= ii < len(A_K) and 0 <= jj < len(A_T)]
        sonuc[ad]["plato_fark"] = round(float(np.mean(kom)), 3)
    gecen = {x: v for x, v in sonuc.items() if isinstance(v, dict) and "fark" in v and x != REF and gecit(v, ref_sh)}
    a_gecen = [x for x in gecen if x.startswith("A_")]
    if a_gecen:
        en_a = max(a_gecen, key=lambda x: sonuc[x]["plato_fark"])
        gecen = {x: v for x, v in gecen.items() if not x.startswith("A_") or x == en_a}
    sonuc["ref_sharpe"] = ref_sh
    sonuc["gecen"] = list(gecen)
    sonuc["aday"] = max(gecen, key=lambda x: gecen[x]["sharpe"]) if gecen else None
    print("REF E2X3 sharpe", ref_sh, "| GEÇEN:", list(gecen), "→ ADAY:", sonuc["aday"])
    return sonuc


def main() -> None:
    donem = sys.argv[1] if len(sys.argv) > 1 else "GELISTIRME"
    if donem != "GELISTIRME":
        raise SystemExit("DOGRULAMA/KASA tek atışı aday belli olunca ayrı fonksiyonla yazılır (PROTOCOL SC-14)")
    s = kesif()
    (R / "sc14_GELISTIRME.json").write_text(json.dumps(s, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
