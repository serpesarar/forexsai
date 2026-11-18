# Ön kayıt — NASDAQ tüm zamanların zirvesi (ATH) dinamiği (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "korku gecesini bırak, farklı şeyler, yalnız NASDAQ".

## Gerekçe
Defter: ATH yalnız altında (MK-11) ve sistemde "ATH bölgesinde SELL blok" kuralı olarak geçiyor; NDX'te hiç sınanmadı. Mekanizma:
ATH üstünde zararda bekleyen satıcı (arz duvarı) yok; açık pozisyon stopları ve trend takipçileri kırılımda alıcı → devam beklenir.
Ters hipotez de önceden tanımlı: ATH'de kâr realizasyonu → dönüş. Coşku sınamaları (CC-01, YK-01) "coşku dönmez" dedi; ATH coşkudan
farklı bir yapısal seviyedir.

## Bölüm A — Günlük (QQQ 1999-03 → 2026-11; kör SPY 1993 →, DIA, IWM)
- ATH_d: kapanış ≥ o güne kadarki en yüksek kapanış.
- **A1 yeni ATH (ara sonrası):** bugün ATH ∧ son 20 işlem günü ATH yok → kapanışta AL; çıkış 1 / 5 / 20 gün sonra kapanış.
- **A2 toparlanma ATH'si:** bugün ATH ∧ son 250 günde zirveden en az %10 düşüş yaşanmış → 20 / 60 gün.
- **A3 ATH serisi:** bugün ATH ∧ dün de ATH → 1 / 5 gün.
- Maliyet 2 bp + finansman (taban da öder). Taban: tüm günler, aynı ufuk. Örtüşmeli ufuklarda gün-blok bootstrap (blok = ufuk).
- Dönemler: KEŞİF 1999–2009, TEST 2010–2017, YENİ 2018–2026.

## Bölüm B — Gün içi ATH kırılımı (NDX Duka 1m 2018 →; MT5 NAS100 M30, NQ 5m bağımsız)
- Önceki tüm barların en yüksek değeri (ATH seviyesi, 1m high) 10:00–15:00 arasında ilk kez aşıldığında, sonraki 1m açılışında AL (ask);
  çıkış aynı gün 16:00 veya ertesi 16:00. Günde bir.
- Taban: aynı gün türünde değil, **aynı saatte rastgele giriş** (ATH'ye ≤ %1 yakın günlerde; yakınlık etkisini ayırmak için) ve tüm günler.
- Ayna: ATH'nin ilk aşıldığı anda SAT (kâr realizasyonu hipotezi).
- Seçim yok (2 çıkış × 2 yön = 4 hücre); dönemler ESKİ 2018-04 → 2021-10 / YENİ 2021-11 →.

## Ölçütler
- Bölüm A hücresi: üç dönemde de fark (tetik − taban) aynı işaret ∧ tüm dönem P ≥ 1 − 0,05/7 = 0,993 ∧ SPY/DIA/IWM ≥ 2'sinde aynı işaret → B.
  Üç dönem + kör ama P altı → C+. Değilse X.
- Bölüm B hücresi: iki dönemde ort > yakınlık tabanı ∧ > 0; MT5 ve NQ'da aynı; P ≥ 0,9875 → B; P altı → C+; değilse X.
