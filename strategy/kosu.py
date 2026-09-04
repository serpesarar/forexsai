#!/usr/bin/env python3
"""Tüm stratejileri bir sembolde koştur.

    python3 strategy/kosu.py --sembol NAS100 \
        --barlar nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv \
        --islemler nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv

XAUUSD / USOIL / DAX için: aynı komut, sembol + iki CSV yolu değişir.
(Barları kutudan çekmek için backend/research/box_export_trades_30d.py ve
 1m dökümü scriptleri kullanılır — bkz. README §Yeni sembol nasıl eklenir.)
"""
from __future__ import annotations
import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import veri as V, olcum  # noqa: E402

STRATEJILER = ["s01_atr_sikisma", "s02_cuma_blogu", "s03_tp_buyutme",
               "s04_kar_takipli_stop", "s05_htf_seviye", "s06_konum_kapisi",
               "s07_teyit_bekleme", "s08_geri_cekilme_limit"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sembol", required=True)
    ap.add_argument("--barlar", required=True)
    ap.add_argument("--islemler", required=True)
    ap.add_argument("--sadece", nargs="*", help="yalnız bu stratejiler")
    ap.add_argument("--tam-izgara", action="store_true", help="tüm hücreleri tara")
    a = ap.parse_args()

    v = V.yukle(a.sembol, a.barlar, a.islemler)
    print(f"SEMBOL {a.sembol} · {len(v.islemler)} işlem · {len(v.barlar)} bar")
    if not v.islemler:
        sys.exit("işlem yok — sembol adı veya CSV yolu yanlış olabilir")

    # ── KAPI 0: zaman ekseni hizalaması (atlanmaz) ────────────────────────
    h = V.hizalama_kontrol(v)
    print(f"HİZALAMA: en iyi lag={h['en_iyi_lag']:+d} dk, uyum %{h['uyum']:.1f}")
    if not h["temiz"]:
        print("  ⛔ VERİ KAYIK — analiz DURDURULDU. Önce zaman eksenini düzelt.")
        print(f"     lag taraması: {h['oranlar']}")
        sys.exit(2)
    print(f"BAZ: {v.baz_usd():+.0f} USD\n")

    secili = a.sadece or STRATEJILER
    for ad in secili:
        m = importlib.import_module(ad)
        izgara = m.IZGARA if a.tam_izgara else m.IZGARA[:1]
        print("=" * 78)
        print(f"{ad} — {m.ACIKLAMA}")
        print(f"  NDX verdikti: {m.VERDIKT_NDX}")
        print("=" * 78)
        en = None
        for p in izgara:
            try:
                d = m.calistir(v, **p)
            except Exception as exc:
                print(f"  {p} → HATA: {exc}")
                continue
            o = olcum.ozet(v.islemler, d)
            etk = o["usd"] - v.baz_usd()
            print(f"  {str(p):<46} USD={o['usd']:+9.0f} ({etk:+8.0f})  "
                  f"WR=%{o['wr']:.1f}  ortR={o['ortR']:+.3f}")
            if en is None or o["usd"] > en[0]:
                en = (o["usd"], p, d)
        if en and a.tam_izgara:
            print(f"\n  EN İYİ: {en[1]}")
            print(olcum.kart(v.islemler, en[2],
                             dis_orneklem="YAPILMADI — yeni haftada tekrar koş"))
        print()


if __name__ == "__main__":
    main()
