# KSG × olay öncesi gece — bileşik sınama — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği ve köken
"Olay gecesi sına". KD-01 (§2.103) grup tablosunda KSG'nin kaybeden oranı en düşük geceleri planlı olay öncesi gecelerdi
(FOMC öncesi %20/%25, ertesi sabah CPI/NFP %31/%33, bilanço gecesi %38/%31). **Bu bileşik o tabloya bakılarak kuruldu** →
2018–26 verisi (S) yalnız betimleyicidir; hüküm **dokunulmamış** verilerden (U1, U2, U3) çıkar.

## Defter kontrolü
FOMC öncesi gece (TS-01 E / FG-01) **B, koşulsuz** (KSG'den bağımsız; KSG varken +36,9, yokken +19,4). CPI öncesi KSG C (2008–18'de 0).
Koşulsuz bilanço gecesi C (HB-03 S13b, 2026 eksi). KSG ∧ bilanço B ama KSG'ye özgü kısım C+ (KD-02, E116 P 0,86).
Meta-ders §3-32: "takvim kuralı değil geceyi seçer" → E116 karşı kolu zorunlu. NFP öncesi gece ayrı sınanmadı.

## Tanımlar (takvim bilgisi; olay tarihi önceden bilinir, sızıntı yok)
- d = sinyal günü (işlem günü), nd = sonraki işlem günü. Pozisyon: d 16:00 AL (ask) → nd 09:30 SAT, maliyet = spread + gece finansmanı.
- FOMC_ONCE: nd planlı FOMC karar günü. VERI_ONCE: nd'de 08:30 CPI ya da NFP. BILANCO: d'de 12 dev şirketten ≥ 1'i kapanış sonrası açıklama
  (AAPL MSFT NVDA AMZN GOOGL META AVGO TSLA NFLX AMD ORCL COST; `ksg_derin_20261119/data/earnings.json`).
- **O = FOMC_ONCE ∨ VERI_ONCE ∨ BILANCO.** Takvim: `xau_best_days_20261015/makro/out/calendar.csv` (2008+).
- KSG = canlı kod (15:00 → 16:00 M30 açılışı aşağı). Tatil/erken kapanış günleri atlanır.

## Hipotezler
- **H1 (KSG doz/etiket):** Δ_KSG = ort(KSG ∧ O) − ort(KSG ∧ ¬O) > 0; E116: Δ_KSG − Δ_KSG-değil (fark-farkı) > 0.
- **H2 (bağımsız kural adayı, tüm geceler):** Δ_TUM = ort(O) − ort(¬O) > 0 ve ort(O) net > 0.

## Veri rolleri
- **S** (görülmüş, betimleyici): MT5 NAS100, Duka NDX 2018-05 → 2026-11-05; kör MT5 US500 (2018-06+), US30, US2000.
- **U1** (dokunulmamış gün içi): Duka M30 dışa aktarım 2016-04 → 2017-12; EET30 (başka MT broker) 2016-11 → 2017-12 (aynı dönemin ikinci beslemesi).
  Spread 1,5 puan + gece finansmanı (FK-03 ile aynı).
- **U2** (bağımsız zaman, günlük vekil kapanış → ertesi açılış, yalnız H2): QQQ, SPY, DIA, IWM 2008-01 → 2018-05-24; maliyet 2 bp + 1,8 bp/gece.
  FOMC ve CPI bileşenleri bu dönemde daha önce bakıldı (FG-01, TS-01) → ayrıca **yeni kısım** raporlanır: (NFP ∨ BILANCO) ∧ ¬FOMC_ONCE ∧ ¬CPI.
- **U3** (bağımsız zaman, yalnız BILANCO bileşeni): aynı dört ETF 2002-04 → 2007-12 (makro takvim yok).

## Geçme ölçütleri (sabit)
- **H1 → B (gölge etiketi + doz adayı):** U1 Duka Δ_KSG > 0 **ve** EET30 Δ_KSG > 0; havuz (S MT5 + U1 Duka) fark-farkı > 0, ay bloklu bootstrap
  P ≥ 0,90; KSG ∧ O lotu ×1,5 kitap Sharpe'ı MT5 KEŞİF (≤ 2021-10-31), MT5 TEST ve U1 Duka'da artırır.
  **C+:** Δ_KSG her yerde > 0 ama fark-farkı P < 0,90 ya da doz Sharpe'ı her yerde artmıyor. **X:** U1'de Δ_KSG ≤ 0.
- **H2 → B (ayrı 2. KURAL kartı adayı, ayrı adım):** U2 bileşik Δ_TUM > 0 dört ETF'nin ≥ 3'ünde, ETF havuzu ay bloklu P ≥ 0,95, U2'nin iki yarısı
  (2008-01 → 2013-02, 2013-03 → 2018-05) > 0; yeni kısım Δ > 0 ≥ 3/4 ETF'de; U1 Duka ort(O) net > 0; S MT5 ort(O) net > 0, Δ_TUM > 0, kör ≥ 2/3 Δ > 0.
  **C:** U2 bileşik geçer ama yeni kısım ya da U1 düşer. **X:** U2 bileşik geçmez.
- U3 betimleyici (hükmü değiştirmez); yan kontrol: hafta günü eşli taban (E114) S MT5'te.
- Canlıya bağlama bu çalışmadan VERİLMEZ.
