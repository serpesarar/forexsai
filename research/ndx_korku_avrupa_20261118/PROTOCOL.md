# Ön kayıt — NDX korku gecesi → Avrupa endeksleri ertesi gün (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
GN-06: Avrupa'nın kendi kapanış korkusu dönmüyor. CC-02: DAX korkusu NDX'e artımsal bilgi taşımıyor. Ters yön sınanmadı: ABD korku
gecesinde NDX'in ertesi gün toparlanması Avrupa'ya yayılıyor mu? Avrupa endeksi, NDX'in 16:00 kapanış anında (Berlin ~22:00) hâlâ
işlem görüyor.

## Kural
NDX Duka K1(d) (§2.71) → NDX 16:00 NY anındaki (UTC hizalı) ilk Avrupa barında AL (ask) → Avrupa'nın sonraki işlem günü yerel nakit
kapanışında çık (DAX/STOXX 17:30 Berlin, CAC 17:30 Paris, UK100 16:30 Londra). Dukascopy 1m, sabit spread (2025 ASK medyanı).
Finansman `lib.FIN_BP_PER_DAY`. Taban: K1 olmayan NDX günleri, aynı giriş/çıkış.

## Ölçüt (seçimsiz, 4 endeks)
Endeks "geçti": ESKİ ve YENİ'de ort > 0 ∧ > taban. Havuz P (tarih kümeli) ≥ 0,95 ∧ ≥ 3/4 endeks → B; ≥ 2/4 → C; değilse X.

## EK-1 (ilk koşu sonrası, kapsama hatası düzeltmesi)
İlk koşuda CAC ve Stoxx'ta yalnız 44 / 22 eşleşme vardı (DAX 233). Sebep: Dukascopy CAC/Stoxx verisi 21:59 Berlin'de bitiyor. NY 16:00 =
22:00 Berlin olduğu için yalnız yaz saati uyumsuz haftalar eşleşti; örneklem seçilmiş, ilk koşunun hükmü geçersiz. Düzeltme, kural
dört endekse simetrik:
- (a) Giriş = NY 16:00'da ya da sonrasındaki ilk bar (≤ 18 saat). CAC/Stoxx için bu ertesi sabah açılışıdır.
- (b) Bilgi: dört endeks de ertesi gün yerel nakit açılışında (DAX/STOXX/CAC 09:00, UK100 08:00) alınıp aynı gün kapanışta satılır.
Hüküm (a) ile, aynı ölçütle verilir.
