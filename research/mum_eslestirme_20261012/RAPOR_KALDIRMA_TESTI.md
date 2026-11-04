# Mum Eşleştirme — "Eşleşmeleri kaldırmadan önce / sonra" ileri sonuç testi (2026-10-12)

**Kullanıcı isteği:** En yakın eşleşmeleri kaldıran kuralları eklemeden önce test et: kaldırmadan önce ve sonra sonuç ne?
Kaç farklı zaman diliminde tespit yapılıyor ve tespitlerden sonra tahminler gerçekleşiyor mu? Varsayıma dayanarak kural ekleme.
**Betikler:** `kaldirma_testi.py` (sorgu başına sonuç), `kaldirma_ozet.py` (özet + anlamlılık + çoklu-TF uyumu).
**Ham çıktı:** `results/kaldirma/*.parquet` (git dışı), `results/kaldirma_ozet_varyant.csv`, `kaldirma_ozet_tf.csv`,
`kaldirma_hucre_testleri.csv`, `kaldirma_anlamlilik.csv`, `kaldirma_tf_uyumu.csv`.

## Sonuç (tek paragraf)

98.260 geçmiş karar anında, 4 sembol × 6 zaman diliminde (23 hücre), 3 ufukta, 4 eşleştirme yöntemiyle ve 5 kaldırma
varyantıyla ölçüldü. **Hiçbir yöntem ve hiçbir varyant yönü, hareket büyüklüğünü veya ±1 ATR hedefini basit tabanlardan iyi
tahmin etmedi.** Eşleşmelerin yön isabeti, aynı sayıda **rastgele** seçilmiş geçmiş anın isabetiyle aynı (ör. piramit
%51,7 ↔ rastgele %51,5). İkisi de "hep çoğunluk yönünü söyle" tabanının (%53,3) altında. 69 hücre × 18 yöntem-varyant
testinin **hiçbirinde** yön tabanı anlamlı geçilmedi; büyüklükte 69'da en fazla 1. Kaldırma kuralları sonucu ±0,3 puandan
fazla değiştirmiyor: kaldıracak bir bilgi yok. Komşuların çok güçlü oy verdiği anlar (%70+), birden çok zaman diliminin
aynı yönü söylediği anlar ve yalnız "yukarı" ya da yalnız "aşağı" tahminleri de tabandan farklı değil. "Kaç pips oynar"
sorusunda, o saatin tipik hareketi eşleşmelerden daha iyi tahmin ediyor.

## Yöntem

| Öğe | Tanım |
|---|---|
| Veri | NDX, DAX, XAU, OIL × 5m/15m/30m/1h (+ 1h'ten 4h/1d, broker gün sınırı NY 17:00). XAU/OIL yalnız broker satırları; DAX 1h 2020+; NDX 5m/15m Dukascopy 2025 + Pepperstone 2026 (karışık kaynak) |
| Kütüphane | Kayan 5 yıl; komşunun sonucu karar anında kapanmış olmalı (j + H ≤ t) — testin geçerliliği için tek zorunlu şart |
| Dokunulmayan dönem | Her hücrenin **son 7 ayı** (protokoldeki iç test + kalibrasyon) hiç kullanılmadı; sorguların sonucu da bu sınırdan önce bitiyor |
| Sorgu anları | 5m–1h: UTC 00/04/08/12/16/20'de kapanan barlar (TF'ler arası hizalı) · 4h: her 6. bar · 1d: her bar |
| Yöntemler | **İkiz-ATR** (son 2 mum, 0,2 ATR) · **İkiz-%** (son 2 mum, %0,02 — senin payın) · **R7** (ham 7 mum, en yakın 50) · **P33** (piramit, 33 mum, en yakın 50) |
| Kaldırma varyantları | **V0** hiçbiri · **V1** sorgunun kendi kuyruğu (mum paylaşan pencereler) · **V2** aynı olayın kopyaları (komşular arası ≥ H bar) · **V3** katı bağımsızlık (≥ kapsam + H) · **V4** uzak eşleşmeler (mesafe kabul sınırı; < 20 kalırsa tahmin yok) |
| Ufuklar | 5m {6,12,48} · 15m {4,16,32} · 30m {2,8,16} · 1h {4,8,24} · 4h {3,6,30} · 1d {1,5,20} bar |
| Tahmin | Çıplak komşu oyu (büzülme/süzgeç yok): yön = komşuların yukarı payı; büyüklük = komşuların medyan hareketi; hedef = komşuların "önce +1 ATR" payı |
| Tabanlar | Yön: kütüphanenin koşulsuz yukarı oranı → hep çoğunluk yönü (+ aynı saat). Büyüklük: aynı UTC saatinin medyan hareketi. **Plasebo:** aynı havuzdan aynı sayıda rastgele komşu (20 tekrar) |
| Anlamlılık | Hücre başına model − taban farkının gün-blok bootstrap'ı (blok ≥ ufuk), B = 1000; "iyi" P ≥ 0,975 |

## Tespit sayıları — kaç zaman diliminde, kaç an

| TF | Sorgu anı (4 sembol) | İkiz-% (%0,02) tespit oranı | İkiz-ATR tespit oranı | R7 / P33 |
|---|---|---|---|---|
| 5m | 2.311 | %89 | %96 | %100 |
| 15m | 11.231 | %77 | %96 | %100 |
| 30m | 22.088 | %55 | %90 | %100 |
| 1h | 47.315 | %31 | %87 | %100 |
| 4h | 7.792 | **%0,7** | %84 | %100 |
| 1d | 7.523 | **%0** | %73 | %100 |
| **Toplam** | **98.260** (× 3 ufuk = 293.863 değerlendirme) | %38 | %87 | %100 |

Senin %0,02 payın 4h'te neredeyse hiç, 1d'de hiç eşleşme bulmuyor (fizibilite ölçümüyle tutarlı).

## Kaldırmadan önce / sonra — tüm havuz

| Yöntem | Varyant | Tespit % | Yön isabeti | Taban (hep çoğunluk) | Rastgele komşu | Büyüklük becerisi (saat tabanına göre) | Büyüklük (rastgeleye göre) | Hedef isabeti / taban |
|---|---|---|---|---|---|---|---|---|
| P33 | V0 hiçbiri | 100 | %51,69 | %53,34 | %51,49 | −%4,9 | +%3,0 | %50,7 / %50,8 |
| P33 | V1 kendi kuyruğu | 100 | %51,70 | %53,34 | %51,50 | −%4,9 | +%3,0 | %50,8 / %50,8 |
| P33 | V2 kopyalar | 100 | %51,92 | %53,37 | %51,49 | −%4,8 | +%3,2 | %50,8 / %50,8 |
| P33 | V3 katı | 100 | %51,75 | %53,36 | %51,35 | −%5,0 | +%3,1 | %50,7 / %50,7 |
| P33 | V4 uzaklar | 87 | %51,65 | %53,12 | %51,24 | −%4,4 | +%2,6 | %50,8 / %50,7 |
| R7 | V0 | 100 | %51,69 | %53,34 | %51,51 | −%5,7 | +%2,3 | %50,5 / %50,7 |
| R7 | V2 | 100 | %51,72 | %53,31 | %51,47 | −%5,6 | +%2,3 | %50,5 / %50,8 |
| R7 | V4 | 79 | %51,36 | %52,98 | %51,22 | −%4,6 | +%1,8 | %50,4 / %50,6 |
| İkiz-ATR | V0 | 87 | %51,43 | %53,07 | %51,32 | −%10,5 | +%0,7 | %50,5 / %50,6 |
| İkiz-ATR | V2 | 87 | %51,36 | %53,07 | %51,27 | −%10,5 | +%0,7 | %50,5 / %50,6 |
| İkiz-% | V0 | 38 | %50,56 | %52,55 | %50,56 | −%9,5 | +%0,5 | %50,4 / %50,6 |

Okuma:
- **Yön:** eşleşmeler rastgele komşu kadar isabetli (+0,1…+0,4 puan). Tabanın altında kalmaları, oylarının bazen az görülen
  yönü göstermesinden kaynaklanıyor; rastgele komşular da tam olarak aynı kaybı yaşıyor → şekilde yön bilgisi yok.
- **Büyüklük:** eşleşmeler rastgeleden biraz iyi (+%2–3; yani şekil oynaklık durumu hakkında *biraz* bilgi taşıyor), ama o
  saatin tipik hareketinden %4–10 kötü. Sıra korelasyonu: eşleşme 0,45–0,47 ↔ saat tabanı 0,54.
- **Hedef (±1 ATR önce hangisi):** isabet %50,4–50,8, taban %50,6–50,8 → bilgi yok.
- **Kaldırma kuralları:** V1 hiçbir şeyi değiştirmiyor; V2 en fazla +0,2 puan (gürültü içinde); V3 uzun TF'lerde zararlı
  (1d P33: Brier −%2,1 → −%8,9 — ortalama komşu 45'ten 18'e düşüyor; kapasite sınırı); V4 tahmin kapsamını %51–87'ye
  düşürüyor, isabeti artırmıyor.

## Anlamlılık — 69 hücre (sembol × TF × ufuk) her yöntem/varyant için

| Ölçüt | Tabandan anlamlı İYİ hücre (18 yöntem-varyantın her birinde) | Anlamlı KÖTÜ hücre |
|---|---|---|
| Yön | **0** (hepsinde) | 15–33 |
| Büyüklük (saat tabanına göre) | 0–1 | 50–67 |
| Hedef (±1 ATR) | 0–5 (beklenen tesadüf ~1,7) | 0–8 |

Yönde en iyi hücreler (OIL 5m/30m, +3,4…+4,0 puan) P = 0,85–0,97 ile eşiği geçmiyor, 600–5.400 sorguluk küçük hücreler;
1.242 test arasında bu büyüklük tesadüf düzeyinde.

## Akla gelen üç ek soru

**1. Komşular güçlü oy verince (≥ %70 aynı yön) isabet artıyor mu?** Hayır. P33 V2: %57,1 ama aynı anlarda taban %56,4;
R7: %57,2 ↔ %56,9; İkiz-ATR: %51,0 ↔ %54,1. Güçlü oylar zaten tabanın yüksek olduğu dönemlere denk geliyor.

**2. Yalnız "yukarı" ya da yalnız "aşağı" tahminleri?** "Yukarı" dediğinde gerçekleşme %54,0, o anlardaki yukarı taban
oranı %53,7; "aşağı" dediğinde %47,3, taban %47,7. Koşullu bilgi yok.

**3. Birden çok zaman dilimi aynı yönü söyleyince (5m/15m/30m/1h, 4 saatlik ufuk)?** Tutarlı bir artış yok. NDX dört TF
aynı yön: R7 %59,3 ↔ taban %59,3; P33 %51,3 ↔ %52,4. DAX üç TF aynı yön: %54,4 ↔ %54,5. XAU İkiz-ATR: %62,6 ↔ %61,8.
OIL P33: %44,9 ↔ %51,0. Farklar hem yönde hem işarette dağınık, örneklem 50–1.000.

**Sembol bazında:** dört sembolde de yön tabanın altında ve rastgele komşu düzeyinde (NDX %53,6 ↔ rastgele %53,2 ↔ taban %55,2;
DAX %51,9 ↔ %51,4 ↔ %53,7; XAU %51,4 ↔ %50,9 ↔ %53,0; OIL %50,8 ↔ %50,5 ↔ %51,7).

## Sınırlar

- Keşif testi; geliştirme döneminde yapıldı. Son 7 ay temiz duruyor ama bu dönem artık "ilk kez bakılacak" olarak saklanmalı.
- Komşu sayısı 50 sabit; büzülme yok. Ham oyun gürültüsü Brier'de ~−%2 taban kaybı yaratır; bu yüzden ana kıyas
  rastgele-komşu plasebosu (aynı gürültü).
- Faz 0 veri temizliği henüz yok (NDX 5m/15m karışık kaynak; segment dışı ufak boşluklar). Sonuçların sıfıra bu kadar yakın
  ve 4 sembolde aynı olması, temizliğin tabloyu değiştirmesini olası kılmıyor.
- Bağlam (VIX rejimi, stres, seans süzgeci) bilerek eklenmedi — istek "varsayıma göre kural ekleme" idi. Bağlamın kendisi
  ayrı bir hipotezdir; şekil eşleştirmesinin katkısı ancak "yalnız bağlam" tabanına karşı ölçülebilir.

## Önceki kanıtla tutarlılık

PM (NAS100 atlası: tekrar sonrası yön taban ±2 puan), OLD-13 (analog-kNN yön yok), IO-18 (benzer işlemler sonucu
tekrarlamıyor, AUC 0,46–0,50), MK-01..05 (mum formasyonları elendi) ile aynı sonuç; bu kez 4 sembol × 6 TF × 4 yöntemde.
