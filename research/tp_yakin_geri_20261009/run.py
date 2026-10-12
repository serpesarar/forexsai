"""TP'ye çok yaklaşıp geri dönen işlemler — "%92'ye geldi, %50'ye döndü → koru/kapat" (2026-10-09).

Ön-kayıt (sonuçtan önce): ANA = tetik %92 (MFE ≥ 0,92 × TP mesafesi), geri dönüş %50, eylem:
  V2 "kapat"  — fiyat tetikten SONRA %50'ye dönünce işlem %50 seviyesinden kapanır
               (kullanıcının "TP'yi %30'a çek" tarifinin MT5'teki fiili sonucu: TP fiyatın arkasında kalır).
  V1 "kilit"  — %50'ye dönünce SL = +%30 (TP aynı). Matematiksel olarak "tetikte SL=%30" ile özdeş.
Izgara: tetik {0,85, 0,90, 0,92, 0,93, 0,95} × geri dönüş {0,40, 0,50, 0,60}. Eylem tetik barından SONRAKİ bardan
geçerli; aynı barda eylem seviyesi ve TP → eylem (muhafazakâr); seviye dolumu kaymasız (iyimser — not edilir).
Taban: aynı girişin yönetimsiz (1,1) yeniden oynatması. Veri: tüm bot kararları (MANUEL hariç), broker 1m.
python3 research/tp_yakin_geri_20261009/run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "limit_kilit_20261007"))

from run import S08_CUTOFF, load  # noqa: E402  (limit_kilit_20261007 yükleyicisi: karar başına ilk bacak + taban R)
from scripts.islem_otopsi import settings as S  # noqa: E402
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402

TRIGS = (0.85, 0.90, 0.92, 0.93, 0.95)
BACKS = (0.40, 0.50, 0.60)
LOCK = 0.30
MAIN = (0.92, 0.50)


def paths(c) -> tuple[np.ndarray, np.ndarray, float]:
    a, s = c.sb.a, c.s
    j1 = min(c.i_in0 + S.REPLAY_MAX_HOLD_MIN, a["close"].size)
    hi, lo = a["high"][c.i_in0:j1], a["low"][c.i_in0:j1]
    adj = 0.0 if s > 0 else c.spread
    fav = s * ((hi if s > 0 else lo) + adj - c.entry) / c.risk
    adv = s * ((lo if s > 0 else hi) + adj - c.entry) / c.risk
    return fav, adv, c.reward / c.risk


def rule(fav: np.ndarray, adv: np.ndarray, rr: float, trig: float, back: float, mode: str) -> float:
    """R (orijinal risk birimi). mode: 'kapat' (geri dönüş seviyesinde çık) | 'kilit' (SL=+LOCK·TP)."""
    end = np.flatnonzero((adv <= -1.0) | (fav >= rr))
    k_end = end[0] if end.size else None
    t = np.flatnonzero(fav >= trig * rr)
    k_t = t[0] if t.size else None
    if k_t is None or (k_end is not None and k_end <= k_t):
        if k_end is None:
            return np.nan
        return -1.0 if adv[k_end] <= -1.0 else rr
    level = (back if mode == "kapat" else LOCK) * rr
    after = np.flatnonzero((adv[k_t + 1:] <= level) | (fav[k_t + 1:] >= rr))
    if not after.size:
        return np.nan
    k = k_t + 1 + after[0]
    return level if adv[k] <= level else rr


def build(items: list[dict]) -> pd.DataFrame:
    rows = []
    for x in items:
        c, r = x["c"], x["r"]
        fav, adv, rr = paths(c)
        rec = {"pid": r["pid"], "sembol": r["symbol"].split(".")[0], "side": r["side"], "family": r["family"],
               "half": x["half"], "s08": x["s08"], "base_R": x["base_R"], "rr": rr,
               "mfe_frac_once": _mfe_before_end(fav, adv, rr)}
        for tg in TRIGS:
            for bk in BACKS:
                rec[f"kapat_{tg}_{bk}"] = rule(fav, adv, rr, tg, bk, "kapat")
            rec[f"kilit_{tg}"] = rule(fav, adv, rr, tg, 0.5, "kilit")
        rows.append(rec)
    return pd.DataFrame(rows)


def _mfe_before_end(fav: np.ndarray, adv: np.ndarray, rr: float) -> float:
    end = np.flatnonzero((adv <= -1.0) | (fav >= rr))
    k = end[0] if end.size else fav.size
    return float(fav[:k].max() / rr) if k > 0 else 0.0


def effect(d: pd.DataFrame, col: str) -> dict:
    x = (d[col] - d["base_R"]).dropna()
    lo, hi, p = boot_mean_ci(x.to_numpy(float))
    m = d.dropna(subset=[col])
    saved = int(((m.base_R < 0) & (m[col] > m.base_R)).sum())
    killed = int(((m.base_R > 0) & (m[col] < m.base_R)).sum())
    return {"n": len(x), "fark_R": round(float(x.sum()), 2), "ort_fark": round(float(x.mean()), 4),
            "%95": f"{lo:+.3f}…{hi:+.3f}", "P(>0)": round(p, 2), "kurtarılan_SL": saved, "kesilen_TP": killed}


def main() -> None:
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    d = build(load())
    d.to_csv(out / "kurallar.csv", index=False)
    pd.set_option("display.width", 220)
    print("karar:", len(d), "| TP'ye ulaşmadan ≥%92 MFE görüp sonra SL olan:",
          int(((d.mfe_frac_once >= 0.92) & (d.base_R < 0)).sum()),
          "| aynı eşikte sonra TP olan (tetiklenip TP'ye giden):", int(((d.mfe_frac_once >= 0.92) & (d.base_R > 0)).sum()))
    main_k, main_l = f"kapat_{MAIN[0]}_{MAIN[1]}", f"kilit_{MAIN[0]}"
    for title, col in (("ANA V2: %92 → %50'ye dönünce KAPAT", main_k), ("V1: %92 → SL +%30 (kilit)", main_l)):
        print(f"\n=== {title}")
        rows = [{"kapsam": "TÜMÜ", **effect(d, col)}]
        for k, g in d.groupby("sembol"):
            rows.append({"kapsam": k, **effect(g, col)})
        for k, g in d[d.sembol == "NDX"].groupby("side"):
            rows.append({"kapsam": k, **effect(g, col)})
        for k, g in d.groupby("half"):
            rows.append({"kapsam": f"yarı {k}", **effect(g, col)})
        for k, g in d.groupby("s08"):
            rows.append({"kapsam": f"09-02 {k}", **effect(g, col)})
        print(pd.DataFrame(rows).to_string(index=False))
    print("\n=== Izgara (TÜMÜ ve NDX): toplam fark R")
    grid = []
    for tg in TRIGS:
        for bk in BACKS:
            col = f"kapat_{tg}_{bk}"
            grid.append({"eylem": "kapat", "tetik": tg, "dönüş": bk, "TÜMÜ": effect(d, col)["fark_R"],
                         "NDX": effect(d[d.sembol == "NDX"], col)["fark_R"],
                         "H1": effect(d[d.half == "H1"], col)["fark_R"], "H2": effect(d[d.half == "H2"], col)["fark_R"]})
        col = f"kilit_{tg}"
        grid.append({"eylem": "kilit%30", "tetik": tg, "dönüş": "—", "TÜMÜ": effect(d, col)["fark_R"],
                     "NDX": effect(d[d.sembol == "NDX"], col)["fark_R"],
                     "H1": effect(d[d.half == "H1"], col)["fark_R"], "H2": effect(d[d.half == "H2"], col)["fark_R"]})
    print(pd.DataFrame(grid).to_string(index=False))


if __name__ == "__main__":
    main()
