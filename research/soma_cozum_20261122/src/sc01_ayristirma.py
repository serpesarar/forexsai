"""SC-01 — Soma (ve tekrar olarak CWDT) altın P&L ayrıştırma merdiveni (PROTOCOL.md SC-01).

Çıktı: results/sc01_sonuc.json, results/sc01_tablo.md, defter satırları.
Kullanım: .venv/bin/python -I research/soma_cozum_20261122/src/sc01_ayristirma.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc_degerlendir as D  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
N_PLASEBO = 200
MAKS_BOSLUK = 600
KAYMALAR_DK = [-60, -15, -5, 5, 15, 60, 240, 1440, 10080]
L5_KAT = 20


def ema(c: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(c).ewm(span=n, adjust=False).mean().to_numpy()


class Hazir:
    def __init__(self):
        self.bar = V.barlar()
        self.ema240 = ema(self.bar.c, 240)
        self.ema1440 = ema(self.bar.c, 1440)

    def trend(self, i0: np.ndarray, ema_: np.ndarray) -> np.ndarray:
        k = np.maximum(i0 - 1, 0)  # dolum anında kapanmış son bar
        return np.where(self.bar.c[k] > ema_[k], 1, -1).astype(np.int32)


def bacak_sim(H: Hazir, t_hedef: np.ndarray, sure: np.ndarray, yon: np.ndarray, lot: np.ndarray, sinyal: np.ndarray,
              sk: float = 1.0) -> pd.DataFrame:
    """t_hedef: dolum için en erken zaman (sn). Dolum = t_hedef'ten sonra/eşit ilk bar; tutuş sure sn (zaman çıkışı)."""
    bar = H.bar
    i0 = np.minimum(bar.idx(t_hedef), len(bar) - 1)
    gecerli = (bar.t[i0] - t_hedef >= 0) & (bar.t[i0] - t_hedef <= MAKS_BOSLUK) & (i0 < len(bar) - 2)
    e = S.Emir.yeni(int(gecerli.sum()))
    e.i0[:] = i0[gecerli]
    e.yon[:] = yon[gecerli]
    e.t_cik[:] = bar.t[e.i0] + sure[gecerli]
    e.etiket = {"sinyal": sinyal[gecerli], "lot": lot[gecerli]}
    return S.simule(bar, e, sk=sk)


def sinyal_bp(r: pd.DataFrame) -> pd.Series:
    return r.groupby("sinyal").apply(lambda q: np.average(q["bp"], weights=q["lot"]), include_groups=False)


def hesap_merdiveni(H: Hazir, hesap: str, rng) -> tuple[dict, pd.DataFrame]:
    p = V.islemler(hesap)
    a, b = D.DONEM["HESAP"]
    p = p[p["bar_var"] & (p["t_giris"] >= D.ts(a)) & (p["t_cikis"] < D.ts(b))].reset_index(drop=True)
    t0 = p["t_giris"].to_numpy() // 60 * 60 + 60           # sonraki dakika
    t1 = p["t_cikis"].to_numpy() // 60 * 60 + 60
    yon, lot, sid = p["yon"].to_numpy().astype(np.int32), p["volume"].to_numpy(), p["sinyal"].to_numpy()
    sure = np.maximum(t1 - t0, 60)

    tablo = pd.DataFrame(index=np.unique(sid))
    tablo["t"] = p.groupby("sinyal")["t_giris"].min()
    tablo["L0_kendi"] = p.groupby("sinyal").apply(lambda q: np.average(q["bp_kendi"], weights=q["volume"]),
                                                  include_groups=False)
    r1 = bacak_sim(H, t0, sure, yon, lot, sid)
    tablo["L1_kopya"] = sinyal_bp(r1)
    tablo["L1_stres"] = sinyal_bp(bacak_sim(H, t0, sure, yon, lot, sid, sk=1.5))
    # çıkış plasebosu: tutuşlar karıştırılır
    top = pd.Series(0.0, index=tablo.index)
    adet = pd.Series(0.0, index=tablo.index)
    for _ in range(N_PLASEBO):
        s = sinyal_bp(bacak_sim(H, t0, rng.permutation(sure), yon, lot, sid))
        top = top.add(s, fill_value=0)
        adet = adet.add(s * 0 + 1, fill_value=0)
    tablo["L2_cikis_plasebo"] = top / adet
    for dk in KAYMALAR_DK:
        tablo[f"L3_{dk:+d}dk"] = sinyal_bp(bacak_sim(H, t0 + dk * 60, sure, yon, lot, sid))
    i0 = np.minimum(H.bar.idx(t0), len(H.bar) - 1)
    for ad, y in (("L4_hep_al", np.ones_like(yon)), ("L4_ema240", H.trend(i0, H.ema240)),
                  ("L4_ema1440", H.trend(i0, H.ema1440))):
        tablo[ad] = sinyal_bp(bacak_sim(H, t0, sure, y, lot, sid))
    top[:] = 0
    adet[:] = 0
    for _ in range(N_PLASEBO // 4):
        s = sinyal_bp(bacak_sim(H, t0, sure, rng.choice([-1, 1], len(yon)).astype(np.int32), lot, sid))
        top = top.add(s, fill_value=0)
        adet = adet.add(s * 0 + 1, fill_value=0)
    tablo["L4_rastgele_yon"] = top / adet
    # yön uyumu (betimleyici)
    uyum = {"ema240": float((H.trend(i0, H.ema240) == yon).mean()), "ema1440": float((H.trend(i0, H.ema1440) == yon).mean())}
    return {"hesap": hesap, "n_bacak": len(p), "n_sinyal": int(tablo["L1_kopya"].notna().sum()),
            "saat": p.attrs.get("saat_modeli"), "yon_uyum": uyum,
            "sadakat_kor_L0_L1": round(float(tablo[["L0_kendi", "L1_kopya"]].corr().iat[0, 1]), 3),
            "_yapi": (t0 - p.groupby("sinyal")["t_giris"].transform("min").to_numpy() // 60 * 60 - 60, sure, lot, sid)}, tablo


def L5(H: Hazir, yapi: tuple, donem: str, n_sinyal: int, rng) -> pd.Series:
    """Becerisiz trend izleyici: rastgele dakika + EMA1440 yönü + sağlayıcının sinyal yapısı (bacak gecikmeleri, tutuşlar, lotlar)."""
    gecikme, sure, lot, sid = yapi
    sinyaller = np.unique(sid)
    a, b = D.DONEM[donem]
    aday = np.flatnonzero((H.bar.t >= D.ts(a)) & (H.bar.t < D.ts(b)))
    aday = aday[aday > 1440]
    secim = rng.choice(sinyaller, n_sinyal * L5_KAT)
    baslangic = H.bar.t[rng.choice(aday, len(secim))]
    th, su, lo, yo, si = [], [], [], [], []
    for k, (s, t) in enumerate(zip(secim, baslangic)):
        m = sid == s
        th.append(t + gecikme[m])
        su.append(sure[m])
        lo.append(lot[m])
        si.append(np.full(m.sum(), k))
    th, su, lo, si = map(np.concatenate, (th, su, lo, si))
    i_ilk = np.minimum(H.bar.idx(baslangic), len(H.bar) - 1)
    yon_s = H.trend(i_ilk, H.ema1440)
    yo = yon_s[si]
    r = bacak_sim(H, th, su, yo, lo, si)
    s = sinyal_bp(r)
    s.index = baslangic[s.index.to_numpy()]
    return s


def fark_tablosu(tablo: pd.DataFrame) -> list[dict]:
    gun = (tablo["t"].to_numpy() // 86400)
    satir = []
    for k in tablo.columns.drop("t"):
        x = tablo[k].to_numpy()
        m = np.isfinite(x)
        satir.append({"kol": k, "n": int(m.sum()), "ort_bp": round(float(np.nanmean(x)), 2),
                      "medyan": round(float(np.nanmedian(x)), 2), "P_ort>0": round(D.gun_blok_P(x[m], gun[m]), 3),
                      "L1_fark": round(float(np.nanmean(tablo["L1_kopya"].to_numpy() - x)), 2),
                      "P_L1>kol": round(D.fark_P(tablo["L1_kopya"].to_numpy(), x, gun), 3) if k != "L1_kopya" else None})
    return satir


def main() -> None:
    rng = np.random.default_rng(D.TOHUM)
    H = Hazir()
    cikti = {"bar_surumu": V.bar_surumu()}
    md = ["# SC-01 sonuç tablosu (HESAP dönemi, sinyal birimi, bp)\n"]
    for hesap in ("2268766", "2347514"):
        bilgi, tablo = hesap_merdiveni(H, hesap, rng)
        yapi = bilgi.pop("_yapi")
        satir = fark_tablosu(tablo)
        l5 = {}
        for donem in ("HESAP", "GELISTIRME"):
            s = L5(H, yapi, donem, bilgi["n_sinyal"], rng)
            l5[donem] = D.ozet(pd.DataFrame({"bp": s.to_numpy(), "t0": s.index.to_numpy()}))
            D.kaydet("SC-01", donem, {"hesap": hesap, "kol": "L5"}, l5[donem])
        bilgi["L5"] = l5
        bilgi["merdiven"] = satir
        bilgi["L1_ozet"] = D.ozet(pd.DataFrame({"bp": tablo["L1_kopya"], "t0": tablo["t"]}))
        D.kaydet("SC-01", "HESAP", {"hesap": hesap, "kol": "merdiven"}, {"merdiven": satir})
        cikti[hesap] = bilgi
        tablo.to_parquet(KOK / "results" / f"sc01_sinyal_{hesap}.parquet")
        md.append(f"\n## {V.HESAPLAR[hesap][1]} ({hesap}) — {bilgi['n_sinyal']} sinyal, sadakat kor(L0,L1) {bilgi['sadakat_kor_L0_L1']}, "
                  f"yön uyumu EMA240 %{bilgi['yon_uyum']['ema240'] * 100:.0f} / EMA1440 %{bilgi['yon_uyum']['ema1440'] * 100:.0f}\n")
        md.append("| kol | n | ort bp | medyan | P(ort>0) | L1 − kol | P(L1 > kol) |\n|---|---|---|---|---|---|---|")
        for s_ in satir:
            md.append(f"| {s_['kol']} | {s_['n']} | {s_['ort_bp']} | {s_['medyan']} | {s_['P_ort>0']} | {s_['L1_fark']} | {s_['P_L1>kol']} |")
        for donem, oz in l5.items():
            md.append(f"\nL5 becerisiz trend izleyici {donem}: n {oz['n']}, ort {oz['ort_bp']} bp, P {oz['P']}, yıllık {oz['yillik']}")
    (KOK / "results" / "sc01_sonuc.json").write_text(json.dumps(cikti, indent=1, ensure_ascii=False, default=str))
    (KOK / "results" / "sc01_tablo.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
