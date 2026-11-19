# Kapı karnesi — onaylanabilir kapıların uçtan uca yeniden sınaması (2026-11-18)

Kod `src/rapor.py` (`python rapor.py test` 11/11 birim testi; `python rapor.py kos`), çıktı `results/son_rapor.json`, `results/kos_log.txt`.
Sayfa: `kapi_karnesi.html` (Artifact). Veri Dukascopy NDX 1m + MT5 NAS100 M30, 2018-04 → 2026-11.

Önerilen paket (K1 + OPEX vetosu + XP çıkışı): yılda 23–24 işlem, isabet %80–83, ort +96…+103 bp, en kötü −783…−786, en kötü %10 ort
−285…−298, maks düşüş −801…−814 bp, 9/9 yıl artı. Onay: OPEX korku vetosu, XP çıkışı, ertesi seans, art arda korku dozu, KSG OPEX vetosu,
C3b + OPEX vetosu. Zayıf (bu dönemde NDX'te): olay günü vetosu (vetolananlar +16…+20), vade sonrası 3–7. gün dozu (dozlu ≈ ortalama).
Hata yakalandı: veriden üretilen takvimde gelecek vade günleri yoktu → takvim NYSE iş günleriyle ileri uzatıldı (canlı kullanımda şart).

## Genişletilmiş koşu (`src/genis.py`): kör US500/US30/US2000, canlı KSG kitabı, C3b 1985–2026
OPEX korku vetosu kör 3/3 (vetolanan −21 / −22 / −9 bp), C3b QQQ −11,6 (P 0,999), ^NDX 1985–99 −176 (P 0,999). KSG vetosu kör 3/3
(−11 / −6 / −11), canlı kitap −4,7 (P 0,97). **Olay günü vetosu kör 3/3 güçlü (−13 / −39 / −55, P 0,97–0,998) — NASDAQ'ta zayıf.**
Art arda doz kör 3/3. Ertesi seans 3/3 artı. **XP çıkışı US2000'de maksDD −1.304 → −2.483 (riskli).** Vade sonrası dozu karışık
(US500 ✗, US30/US2000 ✓, C3b QQQ hafif ✓, ^NDX 1985–99 ✗).
