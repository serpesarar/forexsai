# 🧭 ARAÇ REHBERİ — hangi bat ne işe yarar, ne zaman çalıştırılır? (2026-07-10)

> Unutunca buraya bak. İki tür araç var:
> **🟢 SÜREKLİ** = pencere açık kalır, sistemi ÇALIŞTIRIR. **🔵 RAPOR** = çift tıkla → okur → kapanır;
> hiçbir şey değiştirmez (istisnalar not edildi). Rapor araçlarını açık tutmaya GEREK YOK.

## 🟢 SÜREKLİ AÇIK (sistemin kendisi — 5 süreç)
| Bat | Ne yapar | Terminal |
|---|---|---|
| **1_veri_kaydedici** | MT5 → Supabase OHLC + 29 gösterge kaydı (analiz hammaddesi) | IC Markets |
| **2_oto_trade_bot** | Kural-bazlı GERÇEK işlem botu (momentum/SR + CHREV + VIXREG scope'ları) | IC Markets |
| **3_claude_decider** | Opus karar katmanı (shadow) — journal'ı DOLDURAN süreç; rapor araçlarının tüm verisi buradan | Pepperstone |
| **4_vix_kaydedici** | Pepperstone canlı VIX → Supabase (bulut sistem + VIXREG scope beslenir) | Pepperstone |
| **16_tick_kaydedici** | bid/ask tick arşivi → yerel disk (spread/mikro-yapı; scalp motoru için) | IC Markets |

## 🔵 RAPOR ARAÇLARI (haftada 1-2 kez, çift tıkla-oku-kapat)
| Bat | SORUSU (ne işe yarar) | Ne zaman | Verdict |
|---|---|---|---|
| **5_decider_ozet** | "Decider şu ana kadar kaç açtı, WR/EV ne, **gerçekleşen + VAZGEÇİLEN R** ne?" | Merak ettiğinde (30 sn) | Tut — en hızlı nabız |
| **6_decider_ogrenme** | ÖĞRENME MOTORU: journal'ı damıtır, aday dersleri taze veriyle YENİDEN test eder (≥2 ardışık geçen → ✅ ders; geçmeyen SİLİNİR), ders-etki ölçer | **Haftada 1** (tek yazan rapor: LESSONS günceller) | KRİTİK — öğrenme bununla döner |
| **7_kacirilan_analiz** | "AÇMADIKLARIM kazanır mıydı?" — fazla-korumacı filtre tespiti + gevşetme adayı | Haftada 1 | Tut (360-kaçırma bunu doğruladı) |
| **8_opus_vs_gate** | "LLM gate'ten iyi mi?" — beyin değer katıyor mu, yoksa mekanik kapı yeter mi | 2 haftada 1 | Tut — varlık sorusu |
| **9_cikis_optimizasyon** | **TP/SL YAPILANDIRMA**: her işlemi 6 çıkışla (sabit 1.0/1.5/2.0×ATR, trailing, breakeven→tp2, time-stop) yeniden oynatır → sembol başına EN KÂRLI çıkışı söyler | Haftada 1 | ÖNEMLİ — son bulgu: XAU'da time_2h +0.85 vs sabit +0.34 |
| **10_kalibrasyon** | "Kanıt tabloları doğru mu söylüyor?" — söz verilen WR vs gerçekleşen (şişik hücre tespiti) | Haftada 1 (11'den ÖNCE) | Tut — 11'in tetikleyicisi |
| **11_evidence_tazele** | Kanıt base-rate'lerini canlı sonuçlarla Bayesyen günceller. Varsayılan DRY-RUN; `--apply` yazma yapar (yedekli) | Kalibrasyon "şişik" deyince | Tut — dikkatli kullan |
| **12_model_kiyas** | ESKİ canlı-gölge dönemi Opus-vs-Fable kıyası | — | **Emekli** (canlı gölge kapalı; yerine 14) |
| **13_sl_otopsi** | **ORTAK PAYDA TESPİTİ**: kaybı kazançtan AYIRAN koşullar (hacim/VIX/kanal/S-R yakınlığı, FDR-korumalı) + SL/TP YOL analizi (anlık-kayıp vs dönüş-kaybı, SL-avı, "TP birazcık uzaktı") | Haftada 1 | KRİTİK — "yanlışların ortak kümesi" aracın tam bu |
| **14_fable_toplu_analiz** | Fable + Opus'a biriken kararları TEK toplu çağrıyla sorar (sızıntısız A/B) + kümülatif skorbord. Journal'a işaret YAZAR | Günde/2 günde 1 (~$2) | Tut — model kıyasının yeni yolu |
| **15_gosterge_tarama** | 29 göstergedeki OLAYLARI (MACD/RSI/BB/SAR kesişim-eşik) tarar, scalp ayırt gücünü placebo+OOS ile ölçer | Araştırma modunda, ayda 1-2 | Tut — yeni edge keşif aracı |

## ❓ "Çalıştırmama gerek var mı?" — NET CEVAP
- **Her gün açık olması gerekenler:** yalnız 🟢 (1,2,3,4,16). Bunlar kapalıysa sistem veri/işlem üretmiyor demektir.
- **Rapor araçları kendiliğinden çalışmaz ve çalışmazlarsa sistem BOZULMAZ** — ama öğrenme durur:
  6 (ders damıtma) + 10→11 (kanıt tazeleme) çalıştırılmazsa decider ESKİ base-rate'lerle karar verir
  (bu hafta yaşandı: %80+ iddialı hücreler gerçekte %60 veriyordu).
- **Önerilen ritim:** Günlük: 14. Haftalık paket (15 dk): 5 → 13 → 9 → 7 → 10 → (gerekirse 11 --apply) → 6.
- Sıralama önemli: 10 (teşhis) → 11 (tedavi) → 6 (dersleri güncelle).

## 🔒 Güvenlik notları
- Yalnız 3 araç DOSYA YAZAR: **6** (LESSONS), **11 --apply** (evidence_tables, yedekli), **14 --write** (journal'a işaret). Gerisi salt-okuma.
- 2026-07-10'dan itibaren TÜM rapor araçları **donuk-kopya karantinalı** okur (hafta sonu frozen-feed
  kayıtları otomatik dışlanır) ve decider **DataContract** ile bozuk barları reddeder.
