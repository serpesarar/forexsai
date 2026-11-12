# QS-03 — Zorunlu akış ve takvim: ay sonu yeniden dengeleme, tatil öncesi, Fed net likiditesi — ön kayıt (2026-11-11)

Kullanıcı: "farklı bir şey bul, derin araştır, kapı bulana kadar dur ma". QS-01/02 fiyatın kendi mumundan türedi ve tükendi.
Bu tur **fiyat dışı bilgi sınıfları**, mekanizma ilkesi §3-21 "kim işlem yapmak zorunda?". Defter taraması: yeniden dengeleme,
tatil öncesi, net likidite **hiç sınanmadı** (FOMC öncesi GF-07/HB-03 X, ay dönümü KT-02 C, Pazartesi GF-06 bilinir, TLT
gün-düzeyi koşul GF-05'te genel tarandı ama hisse–tahvil AY İÇİ FARKI ve ay sonu penceresi değil). Sonuçlar görülmeden yazıldı.

## R1 — Ay sonu dengeleme akışı (Harvey, Mazzoleni & Melone 2023/25)
Mekanizma: sabit hisse/tahvil oranlı fonlar (emeklilik, hedef-tarih) ay sonunda oranı geri kurar; ay içinde hisse tahvilden çok
kazandıysa hisse SATAR, az kazandıysa ALIR. Akış önceden bilinir, büyüklüğü fark kadar.
- D = ayın son işlem günü (SPY takvimi). s = D−3. Ay içi fark Δ = r(hisse; önceki ay sonu kapanışı → s kapanışı) − r(tahvil; aynı).
- Hisse = SPY (temettü düzeltmeli); tahvil = TLT (düzeltmeli). 1990-2002 bağımsız dönemi: ^GSPC + sentetik 10 yıl tahvil getirisi
  r_b = y_{t−1}/252 − 7,5·Δy (^TNX/100).
- **Kural:** Δ ≥ +%2 → KISA, Δ ≤ −%2 → UZUN; tutuş s kapanışı → D kapanışı (3 işlem günü). Arada: işlem yok.
- Ölçüm araçları: QQQ (asıl), SPY, IWM, DIA (2002-08→); broker NAS100 M30 2018-26 icra (16:00 giriş/çıkış, maliyet + 3 gece swap).
- Dönemler: KEŞİF 2002-08→2013-12 · TEST 2014-01→2026-10 · BAĞIMSIZ 1990-01→2002-07 (^GSPC).
- Plasebo: aynı kural ay ortası penceresi (D−13 → D−10, Δ yine s'ye kadar) ≈ 0 beklenir.
- Ölçütler: (1) KEŞİF QQQ+SPY havuz ort > 0, P ≥ %90; (2) TEST QQQ > 0 ∧ SPY > 0, havuz P ≥ %90; (3) eğim: pencere getirisinin Δ'ya
  regresyonu KEŞİF ve TEST'te negatif; (4) BAĞIMSIZ ^GSPC ort > 0; (5) broker NAS100 net > 0.
  Sınıf: 1–5 → **B** (kart adayı) · 1, 2, 3 → **C+** · 2 ve 3 → **C** · diğer **X**.
- Betimsel: çeyrek sonu ayları ayrı; sonraki ayın ilk 2 günü (D → D+2) geri dönüş.

## R2 — Tatil öncesi gün
Mekanizma: uzun tatil öncesi açığa satıcılar pozisyon kapatır (tatil boyunca risk taşımamak için) + düşük arz.
- Tatil = hafta içi olup piyasanın (kendi takviminde) işlem görmediği gün; d = tatilden önceki son işlem günü. Takvim önceden
  yayımlanır → kullanmak sızıntı değil. Olağandışı kapanışlar (2001-09-11…14, 2012-10-29/30, 2018-12-05, 2025-01-09) hariç.
- **Kural:** UZUN d−1 kapanışı → d kapanışı. Taban: tüm günler kapanış → kapanış uzun. İkincil: d açılış → kapanış.
- Veri: ABD SPY/QQQ/DIA/IWM 1999→2026 (KEŞİF 1999-2012, TEST 2013-2026), ^GSPC 1985-1998 bağımsız erken; yabancı 12 endeks
  (`geri_cekilme_20261106/data`, kendi takvimleri, tüm dönem); broker NAS100 2018-26 icra (16:00 → 16:00, maliyet + swap).
- Ölçütler: (1) ABD KEŞİF havuz (kural − taban) > 0, P ≥ %90; (2) ABD TEST aynı; (3) yabancı piyasaların ≥ %60'ında kural − taban > 0,
  işaret p ≤ 0,10; (4) ^GSPC 1985-98 kural − taban > 0. Sınıf: 1–4 → **B** · 2 ∧ 3 → **C+** · biri → **C** · hiçbiri **X**.

## R4 — Fed net likiditesi
Mekanizma iddiası (2020 sonrası popüler): NL = WALCL − TGA − RRP büyürken risk varlıkları yükselir.
- H.4.1 Perşembe 16:30 ET yayımlanır (Çarşamba seviyesi). Sinyal: NL'nin 4 haftalık % değişimi > 0. Tutuş: Cuma açılışı →
  sonraki Cuma açılışı, QQQ (düzeltmeli). Kural UZUN-ya-da-NAKİT; kıyas her zaman uzun.
- Dönemler: KEŞİF 2003-01→2014-12 · TEST 2015-01→2026-10 (anlatı 2020 sonrası kuruldu → TEST'in 2020 öncesi kısmı ayrıca).
- Ölçüt: fark = ort(NL↑ haftaları) − ort(NL↓ haftaları) KEŞİF ve TEST'te > 0, ikisinde de P ≥ %90 ve TEST 2015-19 alt kümesinde > 0.
  Geçerse → **C+** (haftalık, n büyük ama otokorelasyonlu); değilse **X**.

## Ortak
Bootstrap: ay-blok (R1, R4: hafta), 5.000. Maliyet ETF 2 bp gidiş-dönüş. Deneme sayacı: 3 hipotez (R1, R2, R4) + betimseller.
Sızıntı: R1 Δ yalnız s kapanışına kadar; R2 takvim; R4 giriş yayından sonraki ilk açılış.
