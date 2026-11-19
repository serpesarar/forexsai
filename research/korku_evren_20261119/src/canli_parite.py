"""canli_parite.py — yeni deneme/korku_live.py saf fonksiyonları MT5 NAS100 M30 geçmişinde koşulur, araştırma işlemleriyle
(results/t30_islemler_MT5_NAS100.csv, kart_t30.py) giriş günü ve çıkış günü birebir kıyaslanır. Tarih öncesi NYSE tatilleri araştırma
takviminden (G.nyse_ok) eklenir (canlı modül 2025-2028 listesini taşır). python canli_parite.py"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import pandas as pd

import esik as E

sys.path.insert(0, str(E.ROOT / "yeni deneme"))
import korku_live as kl  # noqa: E402


def main() -> None:
    b, _ = E.feeds()["MT5_NAS100"]
    b = b[b.t < E.VR.ts(E.CUT + timedelta(days=1), 0, 0)]
    bars = [{"t": int(t), "open": float(o), "close": float(c)} for t, o, c in zip(b.t, b.o, b.c)]
    d0, d1 = date(2018, 5, 1), E.CUT.date()
    hol = {d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)}
    hol = {d for d in hol if d.weekday() < 5 and not E.VR.G.nyse_ok(d)}
    kl.ay.NYSE_HOLIDAYS = set(kl.ay.NYSE_HOLIDAYS) | hol
    tab = kl.day_table(bars)
    live = []
    for d in sorted(tab):
        if kl.find_signal(tab, d) and not kl.opex_veto(d):
            ex = kl.xp_exit(tab, d, d1 + timedelta(days=10), 16 * 60)
            live.append({"d": pd.Timestamp(d), "cikis_canli": pd.Timestamp(ex[1]) if ex else pd.NaT})
    L = pd.DataFrame(live)
    R = pd.read_csv(E.RES / "t30_islemler_MT5_NAS100.csv", parse_dates=["d", "cikis"])[["d", "cikis", "net"]]
    j = R.merge(L, on="d", how="outer", indicator=True)
    both = j[j._merge == "both"]
    print("araştırma", len(R), "canlı", len(L), "ortak", len(both), "yalnız araştırma", int((j._merge == "left_only").sum()),
          "yalnız canlı", int((j._merge == "right_only").sum()))
    print("çıkış günü aynı:", int((both.cikis == both.cikis_canli).sum()), "/", len(both))
    print(j[j._merge != "both"][["d", "net", "_merge"]].to_string())
    print(both[both.cikis != both.cikis_canli][["d", "cikis", "cikis_canli", "net"]].head(10).to_string())


if __name__ == "__main__":
    main()
