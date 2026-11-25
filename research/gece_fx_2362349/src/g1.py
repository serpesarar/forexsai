"""Hesap 2362349 (30 FX çifti, gece scalper'ı) — eşit lot kanıtı + gerçek bid/ask'la kopya ve plasebo (GF-1).
Bar kaynakları: Duka 1m BID+ASK — EURAUD/GBPAUD/USDJPY (DH indirmesi, her dakika gerçek ask); EURUSD/GBPUSD/AUDUSD/USDCAD
(fx_yuksek; ASK yalnız Çarşamba → yıl × NY 15 dk medyan spread ile dolduruldu, E154). Giriş +1 dk açılışı (alış ask / satış bid), çıkış
sağlayıcının kapanış dakikasından sonraki açılış; plasebo aynı ISO hafta × NY 15 dk dilimi × yön rastgele dakika (×5), aynı tutuş."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
ARS = KOK.parent
sys.path.insert(0, str(ARS / "diger_hesap_20261124" / "src"))
sys.path.insert(0, str(ARS.parent / "yeni deneme"))
import broker_time as bt  # noqa: E402
import dh4_gece as G  # noqa: E402

HAM = Path.home() / "Downloads" / "2362349.positions.csv"
CIFT = ("EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "EURAUD", "GBPAUD", "USDJPY")


def islemler() -> pd.DataFrame:
    d = pd.read_csv(HAM, sep=";", dtype=str)
    d.columns = ["t_ac", "tip", "lot", "sym", "px_ac", "lot2", "t_kap", "px_kap", "kom", "swap", "kar"]
    x = d[d.tip.isin(["Buy", "Sell"])].copy()
    for c in ("lot", "px_ac", "px_kap", "kom", "swap", "kar"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x["t_ac"] = pd.to_datetime(x.t_ac, format="%Y.%m.%d %H:%M:%S")
    x["t_kap"] = pd.to_datetime(x.t_kap, format="%Y.%m.%d %H:%M:%S")
    x["sym"] = x.sym.str.rstrip("+")
    x["yon"] = np.where(x.tip == "Buy", 1, -1)
    x["net"] = x.kar + x.kom.fillna(0) + x.swap.fillna(0)
    x["bp"] = x.yon * (x.px_kap - x.px_ac) / x.px_ac * 1e4
    s = lambda c: (x[c].astype("int64") // 10**9).to_numpy()  # noqa: E731
    x["u_ac"] = s("t_ac") - np.array([bt.rule_offset_sec(int(v)) for v in s("t_ac")])
    x["u_kap"] = s("t_kap") - np.array([bt.rule_offset_sec(int(v)) for v in s("t_kap")])
    return x.sort_values("t_ac").reset_index(drop=True)


def gun_P(x, gun, n=3000):
    kod, ters = np.unique(gun, return_inverse=True)
    top, ad = np.bincount(ters, weights=x), np.bincount(ters).astype(float)
    sc = np.random.default_rng(1).integers(0, len(kod), (n, len(kod)))
    return float((top[sc].sum(1) / ad[sc].sum(1) > 0).mean())


def kopya(D: dict, u0: np.ndarray, u1: np.ndarray, y: np.ndarray, spk: float = 1.0) -> np.ndarray:
    t, o, ao = D["t"], D["o"], D["ao"]
    i = np.searchsorted(t, u0 // 60 * 60 + 60)
    j = np.maximum(np.searchsorted(t, u1 // 60 * 60 + 60), i + 1)
    ok = (j < len(t)) & (np.abs(t[np.minimum(i, len(t) - 1)] - (u0 // 60 * 60 + 60)) <= 600)
    i, j = np.minimum(i, len(t) - 1), np.minimum(j, len(t) - 1)
    sp_i, sp_j = (ao[i] - o[i]) * spk, (ao[j] - o[j]) * spk
    gir = np.where(y > 0, o[i] + sp_i, o[i])
    cik = np.where(y > 0, o[j], o[j] + sp_j)
    return np.where(ok, y * (cik - gir) / o[i] * 1e4, np.nan)


def main() -> None:
    x = islemler()
    out = {"profil": {"n": len(x), "net_usd": round(float(x.net.sum()), 1), "isabet": round(float((x.net > 0).mean()), 3)}}
    gun = x.u_ac.to_numpy() // 86400
    out["esit_lot"] = {"bp": round(float(x.bp.mean()), 3), "P": round(gun_P(x.bp.to_numpy(), gun), 4),
                       "yarilar": [round(float(x.bp[: len(x) // 2].mean()), 3), round(float(x.bp[len(x) // 2:].mean()), 3)],
                       "en_kotu5_bp": sorted(x.bp.round(1).tolist())[:5]}
    print("EŞİT LOT", out["esit_lot"], flush=True)
    rng = np.random.default_rng(20261125)
    parca = []
    for c in CIFT:
        g = x[x.sym == c]
        if len(g) < 15:
            continue
        D = G.yukle(c)
        D["ao"] = D["ao"]
        assert np.isfinite(D["ao"]).all(), "eksik ask (E154)"
        u0, u1, y = g.u_ac.to_numpy(), g.u_kap.to_numpy(), g.yon.to_numpy()
        k = kopya(D, u0, u1, y)
        k15 = kopya(D, u0, u1, y, 1.5)
        nyd = D["ny_dk"]
        anah = D["hafta"] * 1000 + nyd // 15
        sira = np.argsort(anah, kind="stable")
        sk = anah[sira]
        ii = np.minimum(np.searchsorted(D["t"], u0 // 60 * 60), len(D["t"]) - 1)
        lo, hi = np.searchsorted(sk, anah[ii], "left"), np.searchsorted(sk, anah[ii], "right")
        pl = []
        for _ in range(5):
            jj = sira[lo + (rng.random(len(g)) * np.maximum(hi - lo, 1)).astype(int)]
            tp = D["t"][jj]
            pl.append(kopya(D, tp, tp + (u1 - u0), y))
        p = np.nanmean(pl, axis=0)
        sp_gir = (D["ao"] - D["o"])[np.minimum(np.searchsorted(D["t"], u0 // 60 * 60 + 60), len(D["t"]) - 1)] / D["o"][0] * 1e4
        parca.append(pd.DataFrame({"cift": c, "u": u0, "kendi": g.bp.to_numpy(), "kopya": k, "kopya15": k15, "plasebo": p, "spread_bp": sp_gir}))
    R = pd.concat(parca).dropna(subset=["kopya"])
    gun = R.u.to_numpy() // 86400
    f = R.kopya.to_numpy() - np.nan_to_num(R.plasebo.to_numpy())
    out["kopya"] = {"n": len(R), "kendi_bp": round(float(R.kendi.mean()), 3), "kopya_bp": round(float(R.kopya.mean()), 3),
                    "kopya_P": round(gun_P(R.kopya.to_numpy(), gun), 4), "kopya_isabet": round(float((R.kopya > 0).mean()), 3),
                    "stres15_bp": round(float(R.kopya15.mean()), 3), "plasebo_bp": round(float(np.nanmean(R.plasebo)), 3),
                    "fark_bp": round(float(f.mean()), 3), "fark_P": round(gun_P(f, gun), 4), "giris_spread_bp_medyan": round(float(R.spread_bp.median()), 2),
                    "cift": R.groupby("cift").agg(n=("kopya", "size"), kendi=("kendi", "mean"), kopya=("kopya", "mean"), plasebo=("plasebo", "mean")).round(2).to_dict("index")}
    for k_, v in out["kopya"].items():
        print(k_, v, flush=True)
    (KOK / "results/g1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
