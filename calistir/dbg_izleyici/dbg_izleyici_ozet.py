"""Canlı izleyici günlük özeti. Kullanım: python dbg_izleyici_ozet.py [YYYY-MM-DD]"""
from __future__ import annotations

import collections
import json
import statistics
import sys

from dbg_izleyici import LOG_FILE, TICK_DIR


def main() -> None:
    gun = sys.argv[1] if len(sys.argv) > 1 else None
    R = [json.loads(x) for x in LOG_FILE.open(encoding="utf-8")]
    if gun:
        R = [r for r in R if r["ts_utc"].startswith(gun)]
    if not R:
        print("kayıt yok")
        return
    print("aralık:", R[0]["ts_utc"], "→", R[-1]["ts_utc"], "| kural:", {r.get("kural") for r in R if r["olay"] == "baslangic"})
    print("olaylar:", dict(collections.Counter(r["olay"] for r in R)))
    # ekleme -> TP güncelleme gecikmesi (yoklama çözünürlüğü 0,5 sn)
    giris = {r["ticket"]: r for r in R if r["olay"] == "giris"}
    lag = [r["goruldu_msc"] - g["time_msc"] for r in R if r["olay"] == "tp_degisti" and (g := giris.get(r["ticket"]))]
    if lag:
        print(f"yeni bacakta ilk TP görülme: medyan {statistics.median(lag) / 1000:.2f} sn, max {max(lag) / 1000:.1f} sn (n={len(lag)})")
    gs = [r["bar_sn"] for r in R if r["olay"] == "giris"]
    if gs:
        print(f"giriş bar içi saniye: medyan {statistics.median(gs):.2f}, >=20 sn: {sum(x >= 20 for x in gs)}/{len(gs)}")
    bars = sum(r["olay"] == "bar" for r in R)
    uy = sum(r["olay"] == "bar_uyumsuz" for r in R)
    print(f"kural kıyası (gerçek durumla): {bars} bar, {uy} uyumsuz")
    for r in R:
        if r["olay"] in ("sessizlik_basladi", "sessizlik_bitti", "reddedildi", "baglanti_yok", "baglanti_geldi", "hata"):
            print(" ", r["ts_utc"], r["olay"], {k: r[k] for k in ("sessiz_bar", "equity", "margin_level", "mesaj") if k in r})
    h = [r for r in R if r["olay"] == "hesap"]
    if h:
        print("son hesap:", {k: h[-1][k] for k in ("balance", "equity", "margin", "margin_level")})
    n = [r for r in R if r["olay"] == "nabiz"]
    if n:
        print("klon (DBG fiyatı):", {k: n[-1][k] for k in ("klon_kar", "klon_seviye")})
    print("tick dosyaları:", sorted(p.name for p in TICK_DIR.glob("*.gz"))[-5:] if TICK_DIR.exists() else [])


if __name__ == "__main__":
    main()
