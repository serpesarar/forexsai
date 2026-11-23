"""SC-03 — itki devamı IT(a), zaman çıkışı, rastgele trend tabanına karşı (PROTOCOL.md SC-03).

Çıktı: results/sc03_sonuc.json, results/sc03_tablo.md; defter satırları.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc_degerlendir as D  # noqa: E402
import sc_ozellik as F  # noqa: E402
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
A_IZGARA = [4.0, 6.0, 8.0]
T_IZGARA = [60, 240, 480]
BIRINCIL = (6.0, 240)
TABAN_TEKRAR = 5


def zaman_sim(bar: V.Bar, k: np.ndarray, y: np.ndarray, T: int, sk: float = 1.0) -> pd.DataFrame:
    i0 = k + 1
    m = i0 < len(bar) - 2
    e = S.Emir.yeni(int(m.sum()))
    e.i0[:], e.yon[:] = i0[m], y[m]
    e.t_cik[:] = bar.t[i0[m]] + T * 60
    return S.simule(bar, e, sk=sk)


def taban_k(bar: V.Bar, oz: F.Ozellik, k: np.ndarray, maske: np.ndarray, rng) -> tuple[np.ndarray, np.ndarray]:
    """Kural sinyallerinin UTC saat dağılımıyla aynı dönemden rastgele dakikalar; yön EMA1440."""
    saat = (bar.t // 3600) % 24
    havuz = {h: np.flatnonzero(maske & (saat == h) & np.isfinite(oz.atr_oran)) for h in range(24)}
    secim = np.array([rng.choice(havuz[h]) for h in saat[k]], dtype=np.int64)
    return secim, np.where(bar.c[secim] > oz.ema1440[secim], 1, -1).astype(np.int32)


def yakalama(bar: V.Bar, k: np.ndarray, y: np.ndarray, hesap: str) -> dict:
    p = V.islemler(hesap, sessiz=True)
    ilk = p[p["bar_var"]].groupby("sinyal").first()
    ts, ys = ilk["t_giris"].to_numpy(), ilk["yon"].to_numpy()
    tk = bar.t[k]
    yak = [bool(np.any((np.abs(tk - t) <= 1800) & (y == yy))) for t, yy in zip(ts, ys)]
    a, b = ts.min(), ts.max()
    mk = (tk >= a) & (tk <= b)
    kes = [bool(np.any((np.abs(ts - t) <= 1800) & (ys == yy))) for t, yy in zip(tk[mk], y[mk])]
    return {"saglayici_yakalanan": round(float(np.mean(yak)), 3), "kural_saglayiciyla_ortak": round(float(np.mean(kes)), 3),
            "kural_n_saglayici_doneminde": int(mk.sum())}


def main() -> None:
    rng = np.random.default_rng(D.TOHUM)
    bar = V.barlar()
    oz = F.hesapla(bar)
    sonuc, md = {"bar_surumu": V.bar_surumu()}, ["# SC-03 itki devamı (bp, sinyal başına; spread + komisyon dahil)\n"]
    for a in A_IZGARA:
        k_tum, y_tum = F.itki_sinyal(bar, oz, a)
        for donem in ("HESAP", "GELISTIRME"):
            m = D.donem_maske(bar.t[k_tum], donem)
            k, y = k_tum[m], y_tum[m]
            dm = D.donem_maske(bar.t, donem)
            tabanlar = [taban_k(bar, oz, k, dm, rng) for _ in range(TABAN_TEKRAR)]
            for T in T_IZGARA:
                r = zaman_sim(bar, k, y, T)
                rs = zaman_sim(bar, k, y, T, sk=1.5)
                tb = [zaman_sim(bar, kk, yy, T) for kk, yy in tabanlar]
                tb_ort = np.mean([t["bp"].to_numpy() for t in tb], axis=0)
                oz_ = D.ozet(r)
                gun = r["t0"].to_numpy() // 86400
                kayit = {"a": a, "T": T, "donem": donem, **oz_, "stres_ort": round(float(rs["bp"].mean()), 3),
                         "taban_ort": round(float(tb_ort.mean()), 3),
                         "fark": round(float(r["bp"].mean() - tb_ort.mean()), 3),
                         "fark_P": round(D.fark_P(r["bp"].to_numpy(), tb_ort, gun), 4),
                         "tek_poz_ort": round(float(D.tek_pozisyon(r)["bp"].mean()), 3)}
                if donem == "HESAP" and T == T_IZGARA[0]:
                    kayit["yakalama_soma"] = yakalama(bar, k, y, "2268766")
                sonuc[f"a{a:g}_T{T}_{donem}"] = kayit
                D.kaydet("SC-03", donem, {"a": a, "T": T}, kayit)
                isaret = " **(birincil)**" if (a, T) == BIRINCIL else ""
                md.append(f"| {donem} | a {a:g} | T {T} | n {oz_['n']} | ort {oz_['ort_bp']} | taban {kayit['taban_ort']} | "
                          f"fark {kayit['fark']} (P {kayit['fark_P']}) | yarılar {oz_['yari1']}/{oz_['yari2']} | "
                          f"stres {kayit['stres_ort']} | tek poz {kayit['tek_poz_ort']} | yıllık {oz_['yillik']}{isaret} |")
    b = sonuc[f"a{BIRINCIL[0]:g}_T{BIRINCIL[1]}_GELISTIRME"]
    gec = b["ort_bp"] > 0 and b["fark"] > 0 and b["fark_P"] >= 0.95 and b["yari1"] > 0 and b["yari2"] > 0
    sonuc["hukum"] = "B" if gec else "X"
    md.append(f"\n**Hüküm (birincil a 6 / T 240, GELISTIRME): {sonuc['hukum']}**")
    for kk, v in sonuc.items():
        if isinstance(v, dict) and "yakalama_soma" in v:
            md.append(f"\nSoma yakalama a={v['a']:g}: {v['yakalama_soma']}")
    (KOK / "results" / "sc03_sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    (KOK / "results" / "sc03_tablo.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
