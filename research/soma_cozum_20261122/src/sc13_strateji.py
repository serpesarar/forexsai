"""SC-13 — çözülen Soma tarzından türeyen strateji ailesi (PROTOCOL SC-13). 4 giriş × 4 çıkış, GELISTIRME keşif → DOGRULAMA tek atış.

Kullanım: .venv/bin/python -I src/sc13_strateji.py [GELISTIRME|DOGRULAMA <hucre>|HESAP]
Çıktı: results/sc13_<donem>.json (+ deneme defteri).
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
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
R = KOK / "results"
KANAL_ATR = 0.25
GOVDE_MIN = 0.5
N_TABAN = 5
CIKIS = {"X1": dict(T=240), "X2": dict(T=480), "X3": dict(T=480, sl=1.0), "X4": dict(T=1200, sl=1.5, iz_akt=1.0, iz=1.0)}
ARALIK = {"GELISTIRME": ("2018-01-01", "2022-01-01"), "DOGRULAMA": ("2022-01-01", "2024-11-01"),
          "HESAP": ("2024-11-01", "2026-11-14")}


# ───────────────────────── girişler ─────────────────────────
def model_ates(M: F.Motor, a: str, b: str) -> pd.DataFrame:
    X = pd.read_parquet(R / "sc08_matris_son.parquet")
    oz = SM.ozellik_listesi(X)
    tr = X[(X["bolum"] == "KESIF") & X["hesap"].isin(["2268766", "karsi"])]
    model = HistGradientBoostingClassifier(max_depth=4, max_iter=300, learning_rate=0.05, class_weight="balanced",
                                           l2_regularization=1.0, random_state=0).fit(tr[oz].to_numpy(np.float32),
                                                                                       (tr["hesap"] == "2268766").to_numpy())
    G0 = pd.read_parquet(R / "sc08_skor_son.parquet").assign(t=lambda d: d["t"] + 60)
    kesim = X.loc[(X.hesap == "2268766") & (X.bolum == "ILERI"), "t_giris"].min()
    esik = float(np.quantile(G0.loc[G0.t < kesim, "skor"], 0.998))
    G = C10.skorla(M, model, oz, a, b)
    K.SOGUMA = 0
    A = K.ateslemeler(G.assign(ok=G.skor >= esik))
    return pd.DataFrame({"k": A["j"].to_numpy(), "y": A["y"].to_numpy().astype(np.int32)})  # j = karar dakikası barı (Motor içi)


def soma_tetik(M: F.Motor, a: str, b: str) -> pd.DataFrame:
    bar = M.bar
    c = bar.c
    e1440 = pd.Series(c).ewm(span=1440, adjust=False).mean().to_numpy()
    e240 = pd.Series(c).ewm(span=240, adjust=False).mean().to_numpy()
    y = np.where(c > e1440, 1, -1)
    trend = np.sign(c - e240) == y
    D1, H4 = M.tf["D1"], M.tf["H4"]
    ayni = np.r_[False, D1.kova_1m[1:] == D1.kova_1m[:-1]]
    onc_h, onc_l = np.r_[np.nan, D1.kumh[:-1]], np.r_[np.nan, D1.kuml[:-1]]
    yeni_uc = ayni & np.where(y > 0, bar.h > onc_h, bar.l < onc_l)
    bc = np.clip(np.searchsorted(H4.kova, H4.kova_1m) - 1, 0, len(H4.C) - 1)
    hh, ll, atr4 = H4.g["hh20"][bc], H4.g["ll20"][bc], H4.g["atr"][bc]
    kanal = np.where(y > 0, c >= hh - KANAL_ATR * atr4, c <= ll + KANAL_ATR * atr4)
    rng = np.maximum(bar.h - bar.l, 1e-12)
    govde = (c - bar.o) * y / rng >= GOVDE_MIN
    ok = trend & yeni_uc & kanal & govde & np.isfinite(atr4)
    ok &= (bar.t >= D.ts(a)) & (bar.t < D.ts(b))
    k = np.flatnonzero(ok)
    gun = D1.kova_1m[k]
    df = pd.DataFrame({"k": k, "y": y[k].astype(np.int32), "gun": gun})
    df = df.drop_duplicates(["gun", "y"], keep="first")              # sunucu günü × yön başına ilk olay
    return df[["k", "y"]].reset_index(drop=True)


def girisler(M: F.Motor, a: str, b: str) -> dict[str, pd.DataFrame]:
    e1 = model_ates(M, a, b)
    e3 = soma_tetik(M, a, b)
    return {"E1": e1, "E2": e1[e1["y"] > 0].reset_index(drop=True), "E3": e3, "E4": e3[e3["y"] > 0].reset_index(drop=True)}


# ───────────────────────── çıkış + simülasyon ─────────────────────────
def atr_h1(M: F.Motor, k: np.ndarray) -> np.ndarray:
    H1 = M.tf["H1"]
    bc = np.clip(np.searchsorted(H1.kova, H1.kova_1m[k]) - 1, 0, len(H1.C) - 1)
    return H1.g["atr"][bc]


def sim(M: F.Motor, k: np.ndarray, y: np.ndarray, cikis: dict, sk: float = 1.0) -> pd.DataFrame:
    bar = M.bar
    i0 = k + 1
    a = atr_h1(M, k)
    m = (i0 < len(bar) - 2) & np.isfinite(a) & (a > 0)
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:] = i0[m], y[m]
    e.t_cik[:] = bar.t[i0[m]] + cikis["T"] * 60
    if "sl" in cikis:
        e.sl_d[:] = cikis["sl"] * a[m]
    if "iz" in cikis:
        e.iz_akt[:], e.iz_d[:] = cikis["iz_akt"] * a[m], cikis["iz"] * a[m]
    return S.simule(bar, e, sk=sk)


def taban(M: F.Motor, k: np.ndarray, y_aile: str, a: str, b: str, rng) -> list[tuple[np.ndarray, np.ndarray]]:
    bar = M.bar
    saat = (bar.t // 3600) % 24
    ok = (bar.t >= D.ts(a)) & (bar.t < D.ts(b)) & np.isfinite(atr_h1(M, np.arange(len(bar))))
    havuz = {h: np.flatnonzero(ok & (saat == h)) for h in range(24)}
    e1440 = pd.Series(bar.c).ewm(span=1440, adjust=False).mean().to_numpy()
    out = []
    for _ in range(N_TABAN):
        kk = np.array([rng.choice(havuz[h]) for h in saat[k]], dtype=np.int64)
        yy = np.ones(len(kk), np.int32) if y_aile == "alis" else np.where(bar.c[kk] > e1440[kk], 1, -1).astype(np.int32)
        out.append((kk, yy))
    return out


def hucre(M: F.Motor, G: pd.DataFrame, ad_e: str, ad_x: str, tb: list, a: str, b: str) -> dict:
    k, y = G["k"].to_numpy(), G["y"].to_numpy()
    cx = CIKIS[ad_x]
    r = sim(M, k, y, cx)
    rs = sim(M, k, y, cx, sk=1.5)
    t = np.mean([sim(M, kk, yy, cx)["bp"].to_numpy() for kk, yy in tb], axis=0)
    o = D.ozet(r)
    yil = o.get("yillik", {})
    return {**o, "taban": round(float(t.mean()), 3), "fark": round(float(r["bp"].mean() - t.mean()), 3),
            "fark_P": round(D.fark_P(r["bp"].to_numpy(), t, r["t0"].to_numpy() // 86400), 4),
            "stres": round(float(rs["bp"].mean()), 3), "tek_poz": round(float(D.tek_pozisyon(r)["bp"].mean()), 3),
            "yil_arti": int(sum(v > 0 for v in yil.values())), "yil_n": len(yil),
            "gunluk": round(len(r) / max((D.ts(b) - D.ts(a)) / 86400 * 5 / 7, 1), 2)}


def gel_gecer(h: dict) -> bool:
    return (h["ort_bp"] > 0 and h["fark"] > 0 and h["fark_P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0 and h["stres"] > 0
            and h["yil_arti"] >= 3)


def dog_gecer(h: dict) -> bool:
    return (h["ort_bp"] > 0 and h["fark"] > 0 and h["fark_P"] >= 0.95 and h["yari1"] > 0 and h["yari2"] > 0 and h["stres"] > 0
            and h["tek_poz"] > 0)


def kos(donem: str, sadece: str | None = None) -> dict:
    a, b = ARALIK[donem]
    M = F.yukle("2017-01-01")
    Gs = girisler(M, a, b)
    rng = np.random.default_rng(D.TOHUM)
    sonuc: dict = {"bar_surumu": V.bar_surumu(), "n_giris": {k: len(v) for k, v in Gs.items()}}
    for ad_e, G in Gs.items():
        tb = taban(M, G["k"].to_numpy(), "alis" if ad_e in ("E2", "E4") else "iki", a, b, rng)
        for ad_x in CIKIS:
            ad = f"{ad_e}{ad_x}"
            if sadece and ad != sadece:
                continue
            h = hucre(M, G, ad_e, ad_x, tb, a, b)
            sonuc[ad] = h
            D.kaydet("SC-13", donem, {"hucre": ad}, h)
            print(ad, {kk: h.get(kk) for kk in ("n", "ort_bp", "taban", "fark", "fark_P", "yari1", "yari2", "stres", "tek_poz",
                                                 "yillik", "gunluk")}, flush=True)
    return sonuc


def main() -> None:
    donem = sys.argv[1] if len(sys.argv) > 1 else "GELISTIRME"
    sadece = sys.argv[2] if len(sys.argv) > 2 else None
    if donem == "DOGRULAMA" and not sadece:
        raise SystemExit("DOGRULAMA tek atış: hücre adı gerekir (PROTOCOL SC-13)")
    s = kos(donem, sadece)
    if donem == "GELISTIRME":
        gecen = [k for k, v in s.items() if isinstance(v, dict) and "fark" in v and gel_gecer(v)]
        s["gecen"] = gecen
        s["dogrulamaya"] = max(gecen, key=lambda k: s[k]["fark"]) if gecen else None
        print("GEÇEN:", gecen, "→ DOGRULAMA:", s["dogrulamaya"])
    if donem == "DOGRULAMA":
        s["hukum"] = "B" if dog_gecer(s[sadece]) else "X"
        print("HÜKÜM:", s["hukum"])
    (R / f"sc13_{donem}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
