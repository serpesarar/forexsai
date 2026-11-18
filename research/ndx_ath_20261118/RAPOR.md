# NASDAQ tüm zamanların zirvesi (ATH) dinamiği (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/ath.py` (`gunluk`, `gunici`).

## Sonuç: ATH bilgi taşımıyor; yalnız "art arda ATH" küçük bir dönüş izi (C+)
**Günlük (QQQ 1999–2026; kör SPY/DIA/IWM):**
- A1 (ara sonrası ilk ATH) ve A2 (≥ %10 düşüş sonrası toparlanma ATH'si) X: işaret dönemler arasında dönüyor.
  A2'de 2018–26 fark −137 (20 gün), 1999–2009'da +397.
- **A3 art arda ATH (bugün ve dün ATH) → ertesi gün:** fark KEŞİF −33 / TEST −5 / YENİ −12 bp; SPY −2,5, DIA −2,4, IWM −10,5 → üç dönem ve
  üç kör ETF'te eksi, P 0,94 (dönüş yönünde) → **C+** (küçük; zirve serisinde yeni uzun açmama etiketi).

**Gün içi ATH kırılımı (NDX Duka 2018–26; MT5, NQ):** önceki tüm zamanların en yükseği 10:00–15:00'te ilk aşıldığında AL ya da SAT,
aynı gün / ertesi gün çıkış: 4 hücrenin hepsi ≈ 0 (AL ertesi 16:00 +9,0 vs yakınlık tabanı +3,1, P 0,75; NQ +0,4) → **X**.
Zirve kırılımında beklenen arz/talep asimetrisi fiyata yansımış.
