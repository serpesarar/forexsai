# ME-08 — Kullanıcı tanımlı "aylık merdiven yükseliş" benzerliği — sonuç (2026-10-19)

Ön-kayıt: `PROTOCOL_MERDIVEN.md`. Betik: `merdiven_test.py` (bir kez). Tanılama (sonradan): olay bazında liste (bu dosyada).
Benzerlik ölçüsü: kullanıcının 4 bölgesinden (T1–T4) ölçeksiz + süre-esnek şekil (64 nokta, z-normalize); kullanıcı tur 1'deki
en benzer 12 bölgenin **hepsini onayladı** (`tur1_etiketleme.png`) → ölçü kullanıcının gözünü yakalıyor.

## Tespit ("yükselişin içinde miyiz?")
- Sıkı eşik (%2): 2016–2025'te günlerin %2'si; yükselişin 1/3'ünde 26, yarısında 19, 2/3'ünde 17, tamamında 14 bağımsız olay
  (yılda ~2). Dedektör çalışıyor (tanımlayıcı).
- **Bugün (2026-10-01 kapanışı 30.527):** yapı oluşmuyor — benzerlik yüzdeliği %27–71 (eşik %2/%5); son 60 günde benzer gün yok.

## Tahmin (geliştirme 2016-06 → 2025-11; kıyas = aynı geriye-dönük getirili ama benzer olmayan günler)
| Aşama | +1 saat | +1 gün | +5 gün | kalan / +20 gün |
|---|---|---|---|---|
| 1/3 tamam (26 olay) | +2,3 bp (P 0,80) | +3,1 (0,58) | +46 (0,90) | +61 (0,84) |
| 1/2 tamam (19) | +1,4 (0,71) | −3,1 (0,37) | −35 (0,17) | −111 (0,04) |
| 2/3 tamam (17) | 0,0 (0,50) | −7,3 (0,35) | −90 (0,004) | −128 (0,000) |
| tamamlandı (14) | −5,6 (0,013) | −19 (0,03) | −75 (0,035) | +33 (0,61) |
P = P(fark > 0), takvim-ayı blok bootstrap. Ön-kayıtlı yön (fark > 0) hiçbir hücrede geçmedi.

**Negatif görünen hücreler sağlam değil (sonradan tanılama):** olay bazında 2/3 aşamasında 17 olayın 9'u negatif, medyan −%0,04,
en kötü olay hariç ortalama +%0,19; tamamlanmışta 14'ün 7'si negatif, medyan +%0,16. Gün-bazı anlamlılık iki çöküşten
(2018-01 −%8, 2020-08/09 −%6…−9) ve bunların çakışan günlerinden geliyor (E6). Doğrulama döneminde benzer gün yok (şablon
çakışması hariç tutulunca) → sınanamadı.

## Okuma
- Kullanıcının benzerlik tanımı **ölçülebilir ve tespit edilebilir**; ama tespit sonrası yön/büyüklük tabandan ayrışmıyor
  (olay bazında yazı-tura). Kayda değer tek tanımlayıcı gözlem: merdivenlerin küçük bir kısmı sert düşüşle bitiyor
  (2018-01, 2020-09, kullanıcının kendi Temmuz 2025 örneği) — kuyruk riski, öngörülebilir değil.
- 15 dakikalık ufuk bu ölçekte test edilmedi (15m veri yalnız 3 yıl).
