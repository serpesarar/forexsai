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
    ilk_tp: dict[int, dict] = {}
    for r in R:                       # yalnız bacağın İLK TP değişikliği: sonrakiler başka eklemelerin sonucu
        if r["olay"] == "tp_degisti" and r["ticket"] in giris:
            ilk_tp.setdefault(r["ticket"], r)
    lag = [r["goruldu_msc"] - giris[t]["time_msc"] for t, r in ilk_tp.items()]
    if lag:
        print(f"yeni bacakta İLK TP değişikliği: medyan {statistics.median(lag) / 1000:.2f} sn, max {max(lag) / 1000:.1f} sn (n={len(lag)})")
    gs = [r["bar_sn"] for r in R if r["olay"] == "giris"]
    if gs:
        print(f"giriş bar içi saniye: medyan {statistics.median(gs):.2f}, >=20 sn: {sum(x >= 20 for x in gs)}/{len(gs)}")
    # Sürüm 1'in bar alanları hatalı (dbg_izleyici.IZLEYICI_SURUM); kıyas yalnız sürüm 2'den itibaren
    bas = next((i for i, r in enumerate(R) if r["olay"] == "baslangic" and r.get("izleyici_surum", 1) >= 2), None)
    V2 = R[bas:] if bas is not None else []
    bars = sum(r["olay"] == "bar" for r in V2)
    uy = [r for r in V2 if r["olay"] == "bar_uyumsuz"]
    print(f"kural kıyası (gerçek durumla, sürüm 2): {bars} bar, {len(uy)} uyumsuz")
    tf = [r["tp_vwap_farki"] for r in R if r["olay"] == "tp_degisti" and "tp_vwap_farki" in r]
    if tf:
        print(f"TP − ortalama: medyan {statistics.median(tf):.2f} $ (n={len(tf)})")
    lf = [r for r in R if r["olay"] == "giris" and "lot_formul" in r and abs(r["lot"] - r["lot_formul"]) > 1e-9]
    print(f"lot formülüne uymayan giriş: {len(lf)}")
    for r in R:
        if r["olay"] in ("sessizlik_basladi", "sessizlik_bitti", "reddedildi", "baglanti_yok", "baglanti_geldi", "hata",
                        "yeni_magic", "bakiye_islem", "bekleyen_emir"):
            print(" ", r["ts_utc"], r["olay"], {k: r[k] for k in ("sessiz_bar", "equity", "margin_level", "mesaj", "magic", "tutar", "adet") if k in r})
    h = [r for r in R if r["olay"] == "hesap"]
    if h:
        print("son hesap:", {k: h[-1][k] for k in ("balance", "equity", "margin", "margin_level")})
    n = [r for r in R if r["olay"] == "nabiz"]
    if n:
        print("klon (DBG fiyatı):", {k: n[-1][k] for k in ("klon_kar", "klon_seviye")})
    print("tick dosyaları:", sorted(p.name for p in TICK_DIR.glob("*.gz"))[-5:] if TICK_DIR.exists() else [])


if __name__ == "__main__":
    main()
