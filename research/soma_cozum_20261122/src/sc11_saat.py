"""SC-11 Aşama 0 — sağlayıcı saatinin Dukascopy tik saatine saniye düzeyinde hizası (PROTOCOL SC-11).

Ay başına L ∈ [−120, +120] sn: hata = giriş fiyatı − Duka (alışta ask, satışta bid)(t + L); skor = hatanın medyan mutlak sapması (taban serbest).
Seçilen L'nin skoru L ± 60 sn skorlarının küçüğünden ≥ %20 düşük değilse o ay saniye hizası TANIMSIZ.
Çıktı: results/sc11_saat.json  {hesap: {ay: {L, mad, mad_60, keskin, n, tanimli}}}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc_degerlendir as D  # noqa: E402
import sc_tick as TK  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
LAG = np.arange(-120, 121)
KESKIN_MIN = 0.20


def hatalar(hesap: str) -> tuple[pd.DataFrame, np.ndarray]:
    p = V.islemler(hesap, sessiz=True)
    a, b = D.DONEM["HESAP"]
    p = p[p["bar_var"] & (p["t_giris"] >= D.ts(a)) & (p["t_giris"] < D.ts(b))].reset_index(drop=True)
    E = np.full((len(p), len(LAG)), np.nan)
    for i, (t, px, y) in enumerate(zip(p["t_giris"].to_numpy("int64"), p["open_price"].to_numpy(float), p["yon"].to_numpy(int))):
        h0, h1 = (t - 121) // 3600 * 3600, (t + 122) // 3600 * 3600
        if not all(TK.yol(h).exists() for h in range(h0, h1 + 1, 3600)):
            continue
        tt, bid, ask, _ = TK.aralik(t - 300, t + 122)
        if len(tt) < 5:
            continue
        j = np.searchsorted(tt, (t + LAG + 1) * 1000) - 1
        ok = j >= 0
        fiyat = np.where(y > 0, ask, bid)[np.maximum(j, 0)]
        E[i] = np.where(ok, px - fiyat, np.nan)
    return p, E


def _mad(e: np.ndarray) -> np.ndarray:
    med = np.nanmedian(e, axis=0)
    return np.nanmedian(np.abs(e - med), axis=0)


def hizala(hesap: str) -> dict:
    p, E = hatalar(hesap)
    ay = pd.to_datetime(p["t_giris"], unit="s").dt.strftime("%Y-%m").to_numpy()
    var = np.isfinite(E).all(axis=1)
    sonuc: dict[str, dict] = {}
    for m in sorted(set(ay)):
        sec = var & (ay == m)
        if sec.sum() < 10:
            sonuc[m] = {"n": int(sec.sum()), "tanimli": False}
            continue
        mad = _mad(E[sec])
        i = int(np.argmin(mad))
        L = int(LAG[i])
        yan = [mad[k] for k in (i - 60, i + 60) if 0 <= k < len(LAG)]
        mad60 = float(min(yan)) if yan else float("nan")
        keskin = 1 - mad[i] / mad60 if mad60 > 0 else 0.0
        sonuc[m] = {"L": L, "mad": round(float(mad[i]), 4), "mad_60": round(mad60, 4), "keskin": round(float(keskin), 3),
                    "mad_L0": round(float(mad[LAG == 0][0]), 4), "n": int(sec.sum()), "tanimli": bool(keskin >= KESKIN_MIN)}
    mad = _mad(E[var])
    sonuc["TUM"] = {"L": int(LAG[np.argmin(mad)]), "mad": round(float(mad.min()), 4), "n": int(var.sum())}
    return sonuc


def L_ay(sonuc: dict, t: np.ndarray) -> np.ndarray:
    """Her zaman için o ayın L'si (tanımsız ayda tüm dönem L'si)."""
    ay = pd.to_datetime(t, unit="s").strftime("%Y-%m")
    return np.array([sonuc.get(m, {}).get("L", sonuc["TUM"]["L"]) if sonuc.get(m, {}).get("tanimli") else sonuc["TUM"]["L"]
                     for m in ay], dtype="int64")


def main() -> None:
    R = {h: hizala(h) for h in ("2268766", "2347514")}
    (KOK / "results" / "sc11_saat.json").write_text(json.dumps(R, indent=1))
    for h, r in R.items():
        print(h, "TÜM", r["TUM"])
        print(pd.DataFrame({m: v for m, v in r.items() if m != "TUM"}).T.to_string())


if __name__ == "__main__":
    main()
