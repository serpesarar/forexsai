"""IO-16 devamı: tetik sonrası en derin geri çekilme — hangi dönüş seviyesi en kârlı, ve seçim taşınıyor mu?
python3 research/tp_yakin_geri_20261009/geri_tarama.py

Her işlem için: tetik (MFE ≥ t × TP) anı, tetikten SONRA çözülmeye (TP/SL) kadar en derin geri çekilme
(TP mesafesinin kesri olarak) ve nihai sonuç. Dönüş seviyesi b için kural sonucu kapalı formda:
  derin ≤ b → b'de kapanır (b × RR), değilse taban sonucu. (Tetik barından sonraki barlar; muhtemelen kaymasız.)
Seçim dürüstlüğü: b ve t bir dönemde seçilir, diğerinde sınanır (09-02 öncesi ↔ sonrası, 1. ↔ 2. yarı).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "limit_kilit_20261007"))   # limit_kilit 'run' → load()
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402


def _mod(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


load = _mod("run", ROOT / "research" / "limit_kilit_20261007" / "run.py").load

TRIGS = (0.90, 0.92, 0.93, 0.94, 0.95)
BACKS = tuple(round(x, 2) for x in np.arange(0.0, 0.86, 0.05))


def trigger_info(c, trig: float) -> tuple[bool, float]:
    """(tetiklendi mi, tetikten sonra çözülmeye kadar en derin geri çekilme / TP)."""
    import run_mod
    fav, adv, rr = run_mod.paths(c)
    end = np.flatnonzero((adv <= -1.0) | (fav >= rr))
    k_end = end[0] if end.size else fav.size
    t = np.flatnonzero(fav[:k_end] >= trig * rr)
    if not t.size:
        return False, np.nan
    seg = adv[t[0] + 1:k_end + 1]                 # çözüm barı dahil (o barda dönüş seviyesi önce sayılır)
    return True, float(seg.min() / rr) if seg.size else 1.0


def table(items: list[dict]) -> pd.DataFrame:
    rows = []
    for x in items:
        c, r = x["c"], x["r"]
        rec = {"pid": r["pid"], "sembol": r["symbol"].split(".")[0], "side": r["side"], "half": x["half"],
               "s08": x["s08"], "base_R": x["base_R"], "rr": c.reward / c.risk, "ts": r["entry_utc"]}
        for tg in TRIGS:
            rec[f"tet_{tg}"], rec[f"derin_{tg}"] = trigger_info(c, tg)
        rows.append(rec)
    return pd.DataFrame(rows)


def rule_R(d: pd.DataFrame, tg: float, b: float) -> pd.Series:
    hit = d[f"tet_{tg}"] & (d[f"derin_{tg}"] <= b)
    return pd.Series(np.where(hit, b * d["rr"], d["base_R"]), index=d.index)


def gain(d: pd.DataFrame, tg: float, b: float) -> float:
    return float((rule_R(d, tg, b) - d["base_R"]).sum())


def best_cell(d: pd.DataFrame) -> tuple[float, float, float]:
    cells = [(gain(d, tg, b), tg, b) for tg in TRIGS for b in BACKS]
    return max(cells)


def main() -> None:
    _mod("run_mod", HERE / "run.py")
    d = table(load())
    d.to_csv(HERE / "results" / "geri_tarama.csv", index=False)
    pd.set_option("display.width", 220)

    print("== 1) 09-02 SONRASI tetiklenen (%92) işlemler — kural neden zarar etti?")
    post = d[(d.s08 == "sonra") & d["tet_0.92"]].copy()
    post["sonuç"] = np.where(post.base_R > 0, "TP", "SL")
    post["kural_%50"] = rule_R(post, 0.92, 0.5)
    print(post[["ts", "side", "sonuç", "derin_0.92", "base_R", "kural_%50"]].round(2).to_string(index=False))
    tp_pull = post[(post.base_R > 0)]["derin_0.92"]
    print(f"  TP'ye giden {len(tp_pull)} işlemin tetik sonrası en derin geri çekilmesi: medyan %{100 * tp_pull.median():.0f}, "
          f"%50 altına inen {int((tp_pull <= 0.5).sum())}")

    print("\n== 2) Tüm dönem ızgarası: toplam fark R (satır=tetik, sütun=dönüş seviyesi)")
    g = pd.DataFrame({b: [gain(d, tg, b) for tg in TRIGS] for b in BACKS}, index=TRIGS).round(1)
    print(g.to_string())

    print("\n== 3) Dürüst sınama: bir dönemde en iyi hücreyi seç → diğerinde ölç")
    for a_lab, b_lab, col in (("önce", "sonra", "s08"), ("sonra", "önce", "s08"), ("H1", "H2", "half"), ("H2", "H1", "half")):
        A, B = d[d[col] == a_lab], d[d[col] == b_lab]
        gA, tg, bk = best_cell(A)
        gB = gain(B, tg, bk)
        x = (rule_R(B, tg, bk) - B.base_R).to_numpy(float)
        lo, hi, p = boot_mean_ci(x)
        print(f"  seç {col}={a_lab:5s} → tetik %{tg * 100:.0f} dönüş %{bk * 100:.0f} (seçimde {gA:+.1f}R) | "
              f"sına {b_lab:5s}: {gB:+.1f}R, P(>0) {p:.2f}")

    print("\n== 4) NDX ve sembol bazında %92 tetik, birkaç dönüş seviyesi (toplam fark R, tüm dönem / 09-02 sonrası)")
    for b in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        parts = []
        for k, sub in d.groupby("sembol"):
            parts.append(f"{k} {gain(sub, 0.92, b):+.1f}/{gain(sub[sub.s08 == 'sonra'], 0.92, b):+.1f}")
        print(f"  dönüş %{b * 100:.0f}: " + " · ".join(parts))


if __name__ == "__main__":
    main()
