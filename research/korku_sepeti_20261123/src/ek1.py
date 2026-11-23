"""ek1.py — PROTOCOL EK-1: A0'da her kuralın lotu tek tek ×0,75 (betimleyici). → results/ek1.json"""
from __future__ import annotations

import json
from datetime import date

import kitap as K
import veri as V
from veri import lib


def main() -> None:
    m1 = lib.load_m1()
    mk = K.Marker(m1)
    days = [d for d in V._cal() if date(2018, 1, 2) <= d <= date(2026, 11, 13)]
    L, _ = V.duka_legs()
    M, _ = V.mt5_legs(L, m1)

    def book(Lx, marked):
        return K.series(mk.legs_daily(Lx, K.assign(Lx, "A0", None), marked), days)

    out = {}
    for rule in ["BAZ"] + V.ORDER:
        Ld, Mm = L.copy(), M.copy()
        if rule != "BAZ":
            Ld.loc[Ld.rule == rule, "lot0"] *= 0.75
            Mm.loc[Mm.rule == rule, "lot0"] *= 0.75
        s, sm = book(Ld, True), book(Mm, False)
        out[rule] = {"duka": K.stats(s), "yarilar": K.halves(s), "mt5": K.stats(sm)}
    (K.RES / "ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    b = out["BAZ"]
    print(f"{'kural':11} {'Δtoplam%':>9} {'ΔmaxDD%':>8} {'Δen10%':>7} {'calmar':>7} {'sharpe':>7} {'ESKI c':>7} {'YENI c':>7} {'MT5 c':>7}")
    for r, x in out.items():
        d = x["duka"]
        print(f"{r:11} {100*(d['toplam']/b['duka']['toplam']-1):9.1f} {100*(d['maks_dusus']/b['duka']['maks_dusus']-1):8.1f} "
              f"{100*(d['en_kotu_10']/b['duka']['en_kotu_10']-1):7.1f} {d['calmar']:7.2f} {d['aylik_sharpe']:7.2f} "
              f"{x['yarilar']['ESKI']['calmar']:7.2f} {x['yarilar']['YENI']['calmar']:7.2f} {x['mt5']['calmar']:7.2f}")


if __name__ == "__main__":
    main()
