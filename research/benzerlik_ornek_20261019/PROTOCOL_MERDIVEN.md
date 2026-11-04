# Ön-kayıt — "Aylık merdiven yükseliş" benzerliği (kullanıcı tanımı) — ME-08

> 2026-10-19, sonuç hesaplanmadan yazıldı. Kullanıcı 1h NAS100 grafiklerinde 4 bölge işaretledi (Nisan–Mayıs 2026 ×2,
> Eylül 2025, Temmuz 2025 yükselişi) ve algoritmanın ölçeksiz şekil ölçüsüyle bulduğu en benzer 12 bölgenin **hepsini
> "istediğim tarzda"** onayladı (`tur1_etiketleme.png`). Kullanıcının asıl sorusu: **"yükselişin içinde miyiz, bu benzerlik
> oluşuyor mu?"** + oluştuktan / tamamlandıktan sonra 1 saat, 1 gün (+ 5 ve 20 gün) içinde ne oluyor.
> Önceki ilgili kanıt: B4 (1h EMA50 trend hizası A−), OLD-20 (momentum filtresi gerçek ama geometriye bağlı), GF-12.
> Yeni olan: kullanıcının kendi gözüyle onaylanmış, ölçeksiz + süre-esnek **aylık ölçekte şekil** (ME-02/05 en çok 50 mum).

## Veri
NDX CFD 1h (`research/ndx_gate_forge/data/long_1h_utc.parquet`, 2016-05 → 2026-07-14) + `bars_15m.parquet`'ten 1h'e
toplanmış uzatma 2026-07-15 → 2026-10-02 (hizalama daha önce %100 doğrulandı). Log kapanış.

## Benzerlik tanımı (tur 1'de kullanıcının onayladığı ölçü, değiştirilmeden)
- Şablonlar: T1 2026-04-20→05-21, T2 2026-04-14→05-13, T3 2025-09-02→09-29, T4 2025-06-30→07-30 (yalnız yükseliş;
  kullanıcı: sondaki düşüş ayrı parça).
- Pencere → 64 noktaya zaman-esnek yeniden örnekleme → z-normalize (ölçeksiz) → Öklid mesafe; D = şablonlara ve
  uzunluklara (460/510/560 bar) göre en küçük mesafe.
- Sorgu anları: her gün 20:00 UTC'de başlayan bar (günde bir).
- "Benzer" eşiği: geliştirme dönemindeki tüm gün-sonu D değerlerinin **%2'lik dilimi** (birincil), %5 (ikincil).

## (A) Oluşum sırasında — "yükselişin içinde miyiz?"
- Kısmi eşleşme: şablonların ilk f kesri (f ∈ {1/3, 1/2, 2/3}) ile son f·L barlık pencere aynı yöntemle; eşik yine o f'nin
  %2'lik dilimi.
- Ufuklar: +1 saat, +1 gün (24 bar), +5 gün (120 bar), **"kalan"** = (1−f)·510 bar (şablonun tamamlanması için kalan süre).

## (B) Tamamlandıktan sonra
- Tam pencere eşleşmesi (f = 1); ufuklar +1 saat, +1 gün, +5 gün, +20 gün (480 bar).

## Kıyaslar (aynı ufuk, aynı dönem)
1. **Koşulsuz:** tüm günler (NDX sürüklenmesi).
2. **Trend-eşli (asıl kıyas):** aynı uzunluktaki geriye dönük getirisi eşleşen günlerle aynı ondalık dilimde olan ama
   benzer OLMAYAN (D > %5 dilimi) günler — "şekil, basit 'son dönemde yükseldi' bilgisinin üstüne bir şey katıyor mu?"
- Ölçü: ortalama log getiri (bp), yukarı oranı. Bağımsızlık: ardışık eşleşme günleri olay kümesidir; olay sayısı
  (aralarında > 10 gün boşluk) ayrıca raporlanır; belirsizlik **takvim ayı blok bootstrap** (B = 10.000).
- Şablonların kendi pencereleriyle çakışan günler değerlendirmeden çıkarılır.

## Bölümler
Geliştirme 2016-06 → 2025-11-30 (sonuç ufku da bu tarihten önce biter). Doğrulama 2025-12-01 → 2026-10-02 (bir kez;
düşük güç; bu dönemde T1/T2 şablonları var → çakışan günler hariç).

## Başarı ölçütü
- Bir hücre (f × ufuk): eşleşme günleri − trend-eşli taban farkı > 0, P ≥ 0,975, iki yarıda (2016–2020 / 2021–2025-11)
  > 0, ≥ 20 bağımsız olay. Aile 16 hücre → güçlü kanıt için P ≥ 0,997 (Bonferroni).
- Ayrıca tanımlayıcı: tarihte günlerin yüzde kaçı "yükselişin içinde"; **bugün (son veri) yapı oluşuyor mu?** (D ve f).
