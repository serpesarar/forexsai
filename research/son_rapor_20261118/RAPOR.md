# Kapı karnesi — onaylanabilir kapıların uçtan uca yeniden sınaması (2026-11-18)

Kod `src/rapor.py` (`python rapor.py test` 11/11 birim testi; `python rapor.py kos`), çıktı `results/son_rapor.json`, `results/kos_log.txt`.
Sayfa: `kapi_karnesi.html` (Artifact). Veri Dukascopy NDX 1m + MT5 NAS100 M30, 2018-04 → 2026-11.

Önerilen paket (K1 + OPEX vetosu + XP çıkışı): yılda 23–24 işlem, isabet %80–83, ort +96…+103 bp, en kötü −783…−786, en kötü %10 ort
−285…−298, maks düşüş −801…−814 bp, 9/9 yıl artı. Onay: OPEX korku vetosu, XP çıkışı, ertesi seans, art arda korku dozu, KSG OPEX vetosu,
C3b + OPEX vetosu. Zayıf (bu dönemde NDX'te): olay günü vetosu (vetolananlar +16…+20), vade sonrası 3–7. gün dozu (dozlu ≈ ortalama).
Hata yakalandı: veriden üretilen takvimde gelecek vade günleri yoktu → takvim NYSE iş günleriyle ileri uzatıldı (canlı kullanımda şart).
