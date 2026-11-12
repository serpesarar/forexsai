# QS-07 — Algoritma değişikliği: akışı kapı, frekans ve yerel sinyal olarak kullanmak: rapor (2026-11-12)

Ön kayıt `PROTOCOL_QS07.md` (+ EK-1 H4/H5, EK-2 H6). Kod `qs07_kapi.py` (H1), `qs07_h2h3.py`, `qs07_h4h5.py`, `qs07_h6.py`.
Sonuçlar `results/qs07*.json`. Deneme sayacı: QS-03…06 17 + QS-07 6 = 23 (E23 — aynı ABD geçmişi; bu turda kararlar bağımsız
dönem/piyasa/kural verisinde).

## Özet
| ID | Algoritma değişikliği | Sonuç | Sınıf |
|---|---|---|---|
| **H6** | **Yerel sinyal + kör piyasa: Avrupa son seansı** (endeks − Euro tahvil ay içi farkı, son gün açılış→kapanış) | kör CAC +21,6 · AEX +22,8 · IBEX +9,2 · STOXX50 +11,4 bp (4/4, havuz +16,3, P 1,00); broker GER40 +12,2 (P 0,86) — **ama 2015 sonrası zayıf** (ikinci yarılar +13/+9/+0/−4, GER40 −4,6) | **B−** (gölge, düşük öncelik) |
| H1 | Akışı strateji değil KAPI olarak canlı uzun kurallara uygula | ORB×VIX rüzgâr +17 / nötr +4 / karşı −13 bp (Sharpe 0,57 → 0,69), KSG +10 / +7 / −47; **C3b'de ters**: karşı +61 > nötr +44 (zorunlu satış C3b'nin dibini yaratıyor) | X (önemli ders) |
| H2 | İki aşama: gerçekleşen itmeyi gör, sönümüne gir | sönüm itmeyle ÖLÇEKLENMİYOR (küçük itme +26,8 > büyük +12,1; broker +30 > +6) | X |
| H3 | Çeyrek penceresi olgusu, görülmemiş 1985-2003 | yabancı 10/15, havuz +2,8, p 0,15; ^GSPC/IXIC 1985-93 eksi → 2004 sonrası çağa özgü | X |
| H4 | Frekans: haftalık dengeleme (Cuma seansı / hafta sonu gecesi) | Cuma seansı haftalık farkın YÖNÜNDE (−7 / −10 bp, broker de eksi) → dönüş yok | X (R1 için negatif kontrol) |
| H5 | Yerel sinyal: DAX − Euro tahvil (Δ_EU) | DAX R1 KEŞİF +54 / TEST +14; Δ_US ile korelasyon 0,85 / 0,68, ek bilgi yok (t −0,4 / −0,65); GER40 +0,5 | C |

## Yapısal öğrenimler (asıl kazanç)
1. **Akış kapısı kural türüne bağlı.** Gün içi/gece uzun kuralları (ORB×VIX, KSG) akışa karşı açıldığında kötüleşiyor, yönünde iyileşiyor.
   Korku dönüşü (C3b) için tersi: ay sonu zorunlu satışı C3b'nin aldığı aşırı satımı **yaratıyor** → bu kuralı akışla filtrelemek fırsatı siler.
   Meta-ders: *bir dönüş kuralını, fırsatını doğuran akışla engelleme.*
2. **Gece dönüşü akışın VARLIĞINA bağlı, büyüklüğüne değil.** Ayın ilk gecesi koşulsuz +12,3 bp (diğer geceler +3,9) ama akış yönüne göre:
   s = −1 (fonlar sattı) +25,9 · akışsız +10,7 · s = +1 (fonlar aldı) −8,6; 2014-26'da akışsız ≈ 0 (+1,1), s = −1 +24,4, s = +1 −15,1.
   Son seans hareketi = akış + haber gürültüsü; dönen yalnız akış kısmı → gerçekleşen itmeyle koşullamak gürültü ekler (H2).
   QS-06'daki "gece tersi" yorumu buna göre düzeltildi: ay dönümü gecesi tabanı var, ama 2014 sonrası etkinin tamamı akış yönünden.
3. **Dengeleme aylık takvime kilitli.** Haftalık analogda dönüş yok, trend var → R1 sıradan kısa vadeli geri dönüş değil (negatif kontrol).
4. **Yerel sinyal ABD sinyalinin kopyası** (H5): hisse–tahvil sapması küresel olarak birlikte hareket ediyor; DAX için Δ_US yeterli.
5. **Avrupa son seansı vardı, sönüyor** (H6): 2004-15 güçlü, 2015 sonrası ≈ +5 bp. ABD'de ise son dönem daha güçlü (QS-06 TEST t 4,0).

## H6 ayrıntı
Her endeks kendi takviminde D; Δ_loc = endeks ay içi − Euro AAA 10Y sentetik tahvil ay içi (D−3); s = −işaret; D açılış → kapanış, 3 bp.
CAC 169 işlem +21,6 (y1 +30,7 / y2 +12,6) · AEX 173 +22,8 (+36,4 / +9,3) · IBEX 175 +9,2 (+18,2 / +0,2) · STOXX50 158 +11,4 (+26,3 / −3,5).
Broker GER40 son seans (03:00→11:30 ET ≈ Xetra 09:00→17:30) 50 işlem +12,2 (+29,0 / −4,6). DAX'ın kendisi (görülmüş): KEŞİF +20,1, TEST +17,0.

## Öneri
- Canlı kurallara akış kapısı **bağlanmaz** (H1 X); yalnız ORB×VIX için ayrı ön-kayıtlı gölge ölçümü düşünülebilir (rüzgâr/karşı etiketi).
- GER40 son seans: gölge listesine düşük öncelikle; 2015 sonrası zayıflama nedeniyle canlı önerilmez.
- Ay sonu ailesinin çekirdeği değişmedi: ABD son seans (kart 6/6) + R1/E2 döngüsü + F1.
