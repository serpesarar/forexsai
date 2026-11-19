# KSG derin araştırma — gece yolu gruplaması, bilanço gecesi, koşullu çıkış — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Daha detaylı araştır, daha detaylı gruplandır, daha çok özelliğine bak — bu stratejiyle ilgili." KA-01 (§2.102): giriş anı fiyat/gösterge
özelliklerinden kaybeden ayrılmıyor (TEST AUC 0,49–0,52). §3-51: aynı veriden yeni gösterge aynı bilgiyi yeniden paketler → **yeni bilgi** gerekir.

## Defter kontrolü
Sınanmış: koşulsuz çıkış zamanı 09:30/09:32/09:45 (NK-07), erken/geç giriş + limit (KT-01 B), FOMC öncesi gece B / CPI C (TS-01 E),
C3b çakışması (KT-01 H3 A), koşulsuz 7 mega-cap bilanço gecesi C (HB-03 S13b), fitil B (FK), VIX ≥ 25 doz (canlı), OPEX B (GX-05/06), Cuma X.
**Sınanmamış (bu çalışma):** gece yolunun dilimlere ayrılması, KSG × bilanço gecesi etkileşimi, giriş sonrası yola koşullu çıkış.

## Veri
Canlı kodla KSG geceleri (ksg_opex_canli_20261119/oynat.py): MT5 NAS100 + Duka NDX; kör MT5 US500 (2018-06+)/US30/US2000.
KEŞİF ≤ 2021-10-31, TEST sonrası. Fiyatlar M30 bar açılışları (ET): 16:00 giriş (ask), 18:00, 20:00, 00:00, 03:00, 06:00, 08:30, 09:30 çıkış.

## A — Gece yolu gruplaması (betimleyici)
- Dilimler: AH 16:00→18:00, ASYA 18:00→03:00, AVRUPA 03:00→08:30, VERİ 08:30→09:30. Her gecenin net'i = dilimlerin toplamı − maliyet.
- Kazanan/kaybeden ortalama dilim katkısı; zararın hangi dilimde doğduğu (kaybeden gecelerde en eksi dilim payı).
- Kaybeden tipleri: dilim vektörüyle KMeans (k siluetle 2–5), tip başına sayı, ortalama, giriş anında tanınma (KA-01 özellikleriyle L1, TEST AUC).
- Ayrıntılı grup tablosu (betimleyici, iki dönem): VIX üçte birlikleri, son saat derinliği üçte birlikleri, haftanın günü, vadeye gün,
  FOMC/CPI/NFP ertesi sabah, C3b gecesi, KORKU-T30 gecesi, bilanço gecesi.

## B — Bilanço gecesi × KSG (yeni hipotez)
- Bilanço: AAPL, MSFT, NVDA, AMZN, GOOGL, META, AVGO, TSLA, NFLX, AMD, ORCL, COST; kapanış sonrası (≥ 15:00 ET) açıklama günü (yfinance).
- Hipotez (yön önceden yok, iki taraflı): KSG ∧ bilanço gecesi vs KSG ∧ bilançosuz. Ölçüt: fark iki dönemde aynı işaret, iki beslemede
  aynı işaret, |fark| P ≥ 0,95; kör üç endeksin ≥ 2'sinde aynı işaret → B (veto ya da doz adayı). Aksi C/X.

## C — Giriş sonrası koşullu çıkış (yeni bilgi: gece yolu)
- Kural: kontrol saati t ∈ {20:00, 00:00, 03:00, 06:00} ET'de açık kâr/zarar ≤ −k bp (k ∈ {50, 100, 150}) → t'de çık (bid); değilse 09:30.
  Ayna: ≥ +k → t'de çık (kâr al). 24 hücre.
- Seçim yalnız NAS100 KEŞİF (gece başına net ortalaması, tabana göre); en iyi 2 hücre dondurulur.
- Geçme: dondurulan hücre TEST NAS100 ve Duka'da tabandan yüksek, gün bloklu bootstrap P ≥ 0,95 (Bonferroni 2 hücre → 0,975),
  kör üç endeksin ≥ 2'sinde tabandan yüksek, kitap Sharpe iki beslemede artar → B. Aksi X.
- Not: KG/XG'de (§2.97) korku gecesinde erken kesme zararı artırdı; KSG'de ayrıca sınanıyor.

## EK-1 (A/B/C sonuçlarından SONRA; hüküm değişmez, E116 zorunlu kontrolü)
B'nin bilanço gecesi etkisi KSG'ye özgü mü, koşulsuz bilanço gecesi primi mi (HB-03 S13b C)? Ölçülür: tüm işlem günleri 16:00 → ertesi
09:30 (aynı maliyet), {KSG, KSG değil} × {bilanço, bilançosuz} dört hücre, NAS100 + Duka; ve KSG ∧ bilanço yıl yıl. KSG ∧ bilanço farkı
karşı koldaki (KSG değil) bilanço farkından anlamlı büyük değilse etki "bilanço gecesi primi"dir, KSG kapısı değil.

## EK-2 (betimleyici, EK-1'den sonra): bilanço gecesinde KSG lotu ×2 kitap etkisi (canlı VIX ≥ 25 dozu ve OPEX vetosuyla birlikte), NAS100 + Duka,
KEŞİF / TEST ayrı. Canlıya bağlama kararı buradan VERİLMEZ; doz önerisi ileri gölge etiketi + kullanıcı kararı ister.
