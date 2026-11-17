"""Adım 6 — DOSYA_HUKUMLERI.md: diskteki her NASDAQ mum dosyasının hükmü (s01 + s05 sonuçlarından)."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main() -> None:
    e = json.loads((BASE / "results/s05_ek_kaynak.json").read_text())
    L = ["# Dosya hükümleri — diskteki tüm NASDAQ mum dosyaları", "",
         "Üretici: `src/s06_dosya_hukumleri.py` (`s01_envanter`, `s05_ek_kaynak` sonuçlarından). Her dosya ya bir beslemenin "
         "**ana kaynağı**, ya o beslemenin **doğrulanmış kopyası**, ya da **türetilemez / reddedildi**.", "",
         "## Ana kaynaklar", "", "| Dosya | Besleme | Kullanım |", "|---|---|---|",
         "| research/nom_20261113/data/ndx_1m_v3_duka.parquet + aynı klasörün `duka_m1/*.bi5` ham günleri (v3 sonrası 2026-11-13, 11-15; ndx_1m_v1 ile birebir) | DUKA | 1m → 2/3/90/210 |",
         "| research/c1_turev_20261105/data/mt5/NAS100_{M1,M5,M15,M30,H1}.csv.gz | MT5 NAS100 (sunucu saati) | M1 → 2/3; M1/M5/M15/M30 → 90/210; H1 doğrulama |",
         "| research/yon_lab_20261114/data/mt5/NAS100_{M1,M5}.csv.gz | MT5 NAS100 | birleşim (ortak barlar %100) |",
         "| nasdaq_tam_veri_2026-08-29/1m_veri, `nasdaq_tam_veri_2026-08-29 2/1m_veri`, islem_paketi_2026-08-27/NASDAQ/1m_veri | MT5 NAS100 (UTC) | birleşim (ortak barlar %100; '…2' birebir kopya) |",
         "| out/kutu_taze/NAS100_{M1,M5,M15,M30,H1}.csv.gz — 2026-11-17 kutudan (`calistir/arac_nas100_mum_export.py`, Pepperstone-Demo) | MT5 NAS100 | birleşim (eski dosyalarla ortak barlar %100) |",
         "| 1MDATA/mt5_ustec_1m_bars.json, RECOVER/mt5_ustec_1m_bars.json | MT5 USTEC — önceki broker (sunucu saati) | 1m → 2/3/90/210 (iki dosya ortak 77.932 barda %100) |", "",
         "## Dukascopy kopyaları (ana dosya + ham bi5 kuyruğuyla kıyas)", "",
         "| Dosya | ortak bar | birebir | ana dosyada olmayan işlem günü |", "|---|---|---|---|"]
    for k, v in e["duka_ailesi"].items():
        if "ortak" in v:
            yr = ", ".join(f"{y}: %{p}" for y, p in v["yila_gore_birebir_%"].items() if p < 100)
            L.append(f"| {k} | {v['ortak']:,} | %{v['birebir_%']}{' (' + yr + ')' if yr else ''} | "
                     f"{v['ana_dosyada_olmayan_gun']} ({v['o_gunlerde_bar']} bar{'; ' + ', '.join(v['ornek_gunler']) if v['ornek_gunler'] else ''}) |")
        else:
            L.append(f"| {k} | {v['n']:,} | satır satır aynı: {v['ana_dosyayla_satir_satir_ayni']} | — |")
    L += ["", "HistData ve onu içeren v3'ün 2018'i farklı besleme (%4 uyum; FAZ_0 E137) → katılmadı. Ham bi5'te ana dosyada olmayan "
          "eski günler (2018 Pazar akşamları, tatiller) temizlikten sonra boş: yalnız düz sıfır-hacim dolgu barı.", "",
          "## MT5 kökenli kopyalar — gün gün MT5'in yerli barıyla birebir sınama", "",
          "Kabul = o işlem gününün TÜM yerli barları kopyadan kurulan karşılığıyla birebir; tek bar farkı günü reddeder. "
          "Kabul edilen 1 dk günleri 2/3 dk'ya katıldı (terminalde olmayan barlar `kaynak_tf=M1_kopya`).", "",
          "| Dosya | TF | damga | aralık (UTC) | referans | sınanan gün | NAS100 kabul | red | red günlerden USTEC'le birebir |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in e["mt5_ailesi"].items():
        L.append(f"| {k} | {v['tf_dk']}m | {v['damga']} | {v['bas'][:10]} → {v['bit'][:10]} | {v.get('ref', '')} | "
                 f"{v.get('sinanan_gun', '—')} | {v.get('kabul_gun', '—')} | {v.get('red_gun', '—')} | {v.get('red_gunlerden_USTEC_birebir', '—')} |")
    x = e.get("mt5_m1_eklenen")
    if x:
        L += ["", f"Birleşime giren kabul günleri: {x['gun']} gün, {x['bar']:,} bar ({x['ilk']} → {x['son']}); terminalle çakışan her bar "
              "birebir (s03 birleşimi dayatır)."]
    L += ["", "Red nedenleri: (1) **USTEC beslemesinin kopyası** — 2026-05-06 öncesi candle_cache ve ondan türeyenler, "
          "`sr_rejection_research`, `bot_live_audit` (bazıları `time_utc` etiketli ama sunucu saatinde); NAS100 ile hiçbir kaydırmada "
          "eşleşmez, seviye farkı 10–35 puan. USTEC ana kaynağı (json) 2026-06-12'de bittiği için sonraki USTEC günleri tek kopyada kalır ve "
          "doğrulanamadığından katılmadı (aşağıdaki sayı). (2) Kaymış dönem: candle_cache 2026-02 → 03-08 +60 dk (E4), 07-08/09 ~12 dk. "
          "(3) Yarım gün / eksik dakika kopyaları — tek bar farkı günü reddeder; bu günlerin hepsi terminal M1'inde zaten var. Panel "
          "`candle_history` npz'lerinin 15m/30m'si NAS100 yerli barlarının kopyası (yeni gün eklemiyor), 5m'nin 2025'i karışık besleme.", ""]
    late = {k: v.get("red_gun_USTEC_bitisinden_sonra", 0) for k, v in e["mt5_ailesi"].items()}
    L += ["USTEC json bitişinden (06-12) sonra NAS100 ile tutmayan gün: " +
          ", ".join(f"`{k.split('/')[-1]}` {n}" for k, n in late.items() if n) + " — bunlar USTEC'in tek kopyası ya da eksik "
          "dakikalı NAS100 kopyası; ikisi de bağımsız referansla sınanamadığı için katılmadı.",
          "", "## Türetilemez / mum değil", "", "| Dosya | Neden |", "|---|---|"]
    for k, v in e["turetilemez"].items():
        L.append(f"| {k} | {v} — 2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil |")
    (BASE / "DOSYA_HUKUMLERI.md").write_text("\n".join(L) + "\n")
    print(len(L), "satır")


if __name__ == "__main__":
    main()
