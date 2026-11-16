"""a_retest.py — PROTOCOL §2: dondurulmuş NASDAQ kurallarının 9y 1m yeniden sınaması + önek sızıntı testi.
Çıktı: results/a_trades.parquet, results/a_retest.json, results/a_retest.md"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd

import lib
import rules

UNIT = {"C3B": "net_bp", "C3": "net_bp", "CAPREV": "R", "ORBVIX": "R", "ORBVIX_LO": "R", "CEKIC": "R", "KSG": "net_bp",
        "AYSONU_SON": "net_bp", "AYSONU_E2": "net_bp", "FOMC_GECE": "net_bp"}


def run_all(m1, D, vixp, H) -> pd.DataFrame:
    tr = []
    tr += rules.c3b(m1, D)
    tr += rules.c3b(m1, D, exit_mode="next", rule="C3")
    tr += rules.caprev(m1, D, vixp)
    tr += rules.orb(m1, D, vixp)
    tr += rules.orb(m1, D, vixp, arm="lo", rule="ORBVIX_LO")
    tr += rules.cekic(m1, H)
    tr += rules.ksg(m1, D)
    son, e2 = rules.aysonu(m1, D)
    tr += son + e2
    tr += rules.fomc_gece(m1, D)
    return lib.to_frame(tr)


def verdict(s_eski: dict, s_tum: dict) -> str:
    if s_eski.get("n", 0) == 0:
        return "ESKİ'de olay yok"
    if s_eski["mean"] <= 0:
        return "ÇÖKTÜ (ESKİ ≤ 0)"
    if s_eski["P"] >= 0.80 and s_tum["P"] >= 0.95:
        return "DAYANIYOR"
    return "ZAYIF (ESKİ > 0, P düşük)"


def prefix_test(m1, D, vixp, cut: date) -> dict:
    """Sızıntı: veriyi cut'ta kes, yeniden koş; cut − 10 gün öncesindeki işlemler birebir aynı olmalı."""
    tcut = lib.utc(cut, 0)
    n = int(np.searchsorted(m1.t, tcut))
    m1c = lib.M1(m1.t[:n], m1.o[:n], m1.h[:n], m1.l[:n], m1.c[:n], m1.spr[:n], m1.d[:n], m1.m[:n])
    Dc = D[D.d < cut].reset_index(drop=True)
    lim = pd.Timestamp(cut) - pd.Timedelta(days=10)
    out = {}
    for name, f in {"C3B": lambda a, b: rules.c3b(a, b), "CAPREV": lambda a, b: rules.caprev(a, b, vixp),
                    "ORBVIX": lambda a, b: rules.orb(a, b, vixp), "KSG": lambda a, b: rules.ksg(a, b)}.items():
        full = lib.to_frame(f(m1, D))
        part = lib.to_frame(f(m1c, Dc))
        sel = lambda x: x[pd.to_datetime(x.d) < lim][["d", "t_in", "t_out", "px_in", "px_out"]].reset_index(drop=True)
        a, b = sel(full), sel(part)
        out[name] = bool(len(a) == len(b) and np.allclose(a[["t_in", "t_out", "px_in", "px_out"]].values,
                                                          b[["t_in", "t_out", "px_in", "px_out"]].values))
    return out


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    H = rules.h1_utc(m1)
    df = run_all(m1, D, vixp, H)
    lib.RESULTS.mkdir(exist_ok=True)
    df.to_parquet(lib.RESULTS / "a_trades.parquet")
    res = {}
    for r, g in df.groupby("rule"):
        col = UNIT[r]
        st = lib.by_era_year(g, col)
        st["unit"] = col
        st["verdict"] = verdict(st["ESKI"], st["TUM"])
        res[r] = st
    res["_prefix_test"] = {"2020-06-15": prefix_test(m1, D, vixp, date(2020, 6, 15)),
                           "2023-03-01": prefix_test(m1, D, vixp, date(2023, 3, 1))}
    (lib.RESULTS / "a_retest.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    lines = ["| kural | birim | n tüm | ort tüm | P tüm | n ESKİ | ort ESKİ | P ESKİ | n YENİ | ort YENİ | P YENİ | ×1,5 tüm | en iyi 5 hariç | en kötü | MAE p5 | hüküm |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r, st in res.items():
        if r.startswith("_"):
            continue
        T, E, Y = st["TUM"], st["ESKI"], st["YENI"]
        f = lambda v, k=2: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:+.{k}f}"
        k = 3 if st["unit"] == "R" else 1
        lines.append(f"| {r} | {st['unit']} | {T['n']} | {f(T['mean'],k)} | {T['P']:.3f} | {E.get('n',0)} | {f(E.get('mean'),k)} | "
                     f"{E.get('P', float('nan')):.3f} | {Y.get('n',0)} | {f(Y.get('mean'),k)} | {Y.get('P', float('nan')):.3f} | "
                     f"{f(T['mean_s15'],k)} | {f(T['ex_top5'],k)} | {f(T['worst'],k)} | {100*T['mae_p05']:+.1f}% | {st['verdict']} |")
    lines.append("")
    lines.append("Yıl tablosu (ort; n):")
    yrs = sorted({y for r, st in res.items() if not r.startswith('_') for y in st["yil"]})
    lines.append("| kural | " + " | ".join(map(str, yrs)) + " |")
    lines.append("|---|" + "---|" * len(yrs))
    for r, st in res.items():
        if r.startswith("_"):
            continue
        k = 3 if st["unit"] == "R" else 1
        cells = [f"{st['yil'][y]['mean']:+.{k}f} ({st['yil'][y]['n']})" if y in st["yil"] else "—" for y in yrs]
        lines.append(f"| {r} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"Önek sızıntı testi: {res['_prefix_test']}")
    (lib.RESULTS / "a_retest.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
