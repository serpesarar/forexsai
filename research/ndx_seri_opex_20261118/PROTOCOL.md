# Ön kayıt — NASDAQ yükseliş serileri ve opsiyon vadesi (OPEX) haftası (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
- **Yükseliş serisi:** düşüş serileri (K6) korku ailesinde zayıf çıktı; yükseliş serileri hiç sınanmadı. İki yön önceden tanımlı: momentum
  (devam) / aşırı alım (dönüş).
- **OPEX:** NASDAQ'ta yalnız mevcut kurallara koşul olarak sınandı (TS-01: C3b vade haftası doz). Tek başına haftalık sürüklenme
  sınanmadı. Literatür (Stivers–Sun): vade haftası artı, sonraki hafta eksi. DAX'ta (DP-02) vade haftası eksi çıktı.

## Veri
QQQ günlük 1999-03 → 2026-11 (ana), SPY/DIA/IWM kör. Maliyet 2 bp + finansman (uzun). Dönemler: KEŞİF 1999–2009, TEST 2010–2017,
YENİ 2018–2026.

## Hücreler (8)
- **S1/S2:** art arda N yükseliş kapanışı (N ≥ 4 / N ≥ 6; serinin N'inci günü, sonra her ek gün de sayılır) → kapanışta AL, 1 gün ve
  5 gün tut (4 hücre). Taban: tüm günler, aynı ufuk.
- **O1:** OPEX haftası (3. Cuma'yı içeren hafta): önceki haftanın son kapanışı → OPEX haftasının son kapanışı.
- **O2:** OPEX sonrası hafta: OPEX haftası son kapanışı → sonraki haftanın son kapanışı.
- **O3/O4:** O1/O2'nin çeyrek vadeli (Mar/Haz/Eyl/Ara) hâli. Taban: öteki haftalar.

## Ölçüt
Fark (tetik − taban) üç dönemde aynı işaret ∧ tüm dönem P ≥ 1 − 0,05/8 = 0,994 ∧ kör 3 ETF'in ≥ 2'sinde aynı işaret → B
(devam ya da dönüş yönünde). P hariç → C+. Değilse X. Haftalık hücrelerde hafta-bootstrap, günlükte blok bootstrap (blok = ufuk).

## EK-1 — NASDAQ'ın kendi bağımsız eski dönemi: ^NDX 1985-10 → 1999-02 (ilk koşu görüldükten sonra; yalnız iki aday, tanımlar aynen)
Kullanıcı yalnız NASDAQ istiyor; kör ETF sınavı genellik sınar, NDX geçerliliğini değil. ^NDX günlük (yfinance, temettüsüz endeks),
QQQ öncesi dönem, bu sorular için hiç bakılmadı. Maliyet aynı (2 bp + finansman).
- **S N6 h5** (6+ gün üst üste yükseliş → 5 gün): 1985–1999'da fark > 0 ∧ P ≥ 0,95 → "NDX'e özgü B" (4 bağımsız dönemde artı).
  Fark > 0 ama P altı → C+. Fark ≤ 0 → X kesinleşir.
- **O4** (çeyrek OPEX sonrası hafta): 1985–1999'da fark < 0 ∧ P(fark < 0) ≥ 0,95 → B (eksi; uzun pozisyon vetosu / SAT); fark < 0 ama P
  altı → C+ kalır; fark ≥ 0 → X.
