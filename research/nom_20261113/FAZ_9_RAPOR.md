# FAZ 9 — Sürekli öğrenme: yeniden eğitim, sürümleme, drift (NOM, 2026-11-13)

## 1. Periyodik yeniden eğitim pipeline'ı — `src/faz9_retrain.py`
`run`: (1) Dukascopy'den eksik günleri indir (best effort) → `faz0_build` → `faz12_build` (aynı özellik/etiket kodu);
(2) değerlendirme penceresi **W = [şampiyonun eğitim sonu + 1 gün ambargo, veri sonu]** — şampiyon (ACTIVE) da
meydan okuyan (W başına kadar veriyle, aynı sabit yapılandırma) da W'yi **görmemiştir**; (3) her hedefte saat-iklimine
göre Brier becerisi; (4) **terfi kuralı (hepsi):** W'de ≥ 300 satır, meydan okuyan hedeflerin ≥ %60'ında daha iyi,
ortalama fark ≥ 0, hiçbir hedefte fark < −0,01. Geçerse tüm veriyle yeniden eğitim (`faz5_econ.py bundle`) +
`model_store.promote`; geçmezse şampiyon kalır. Karar `results/faz9_retrain_<tarih>.json`.
Önerilen sıklık: ayda bir (Faz 4: beceri veri büyüdükçe artıyor). Eşikler/“kanıtlı” bayrakları yeniden eğitimde
**değişmez** — yön önerisi için yeni kanıt ancak yeni bir ön kayıtlı Faz 5 ile verilebilir.

**Mekanizma sınaması (`dryrun`, terfi uygulanmadı):** şampiyon ≤ 2026-08-01, meydan okuyan ≤ 2026-09-15,
W = 2026-09-16 → 11-03, 1 s hedefleri (W'de 3.040 satır/hedef): meydan okuyan 10 hedefin **7'sinde** daha iyi,
ortalama fark **+0,0005**, en kötü −0,0039 → kural "TERFİ" derdi. Kazanç küçük: aylık yenilemenin değeri düşük ama
pozitif; asıl değer rejim kaymasında kalibrasyonun tazelenmesi (Faz 5: final dönem eğimi 0,54–0,68).

## 2. Sürümleme ve geri alma — `backend/services/nom/model_store.py`
`backend/models/nom/<sürüm>/` (40 LightGBM + 40 isotonic JSON + meta.json: özellik listesi, hedef istatistikleri,
WF bantları, kanıt bayrakları, PSI referansları), `ACTIVE` (etkin sürüm), `HISTORY.jsonl` (her terfi: zaman, eski,
yeni, gerekçe). `promote(sürüm, gerekçe)`, `rollback()` (son terfiden önceki sürüme), `delete_version` (etkin sürüm
silinemez). Test: `test_promote_rollback`. Motor her istekte `ACTIVE`'i okur → terfi/geri alma yeniden başlatma
gerektirmez.
Geçmiş: `nom_v1_20261113` (ilk paket) → `nom_v1b_20261113` (takvim düzeltmesi: BLS 2026 CPI/NFP eklendi, takvim
kapsamı dışı olay özelliği NaN yerine "≥3 gün" tavanı — canlıda eğitimde görülmemiş NaN oluşuyordu). v1 hatalı takvim
taşıdığı için silindi (geri alma hedefi olmamalı).

## 3. Drift izleme — `backend/services/nom/drift.py`, `GET /api/probability/nasdaq/drift`
- **Özellik kayması**, son 14 gün (15 dk ızgara), üç sınıf: takvim-belirli özellikler ölçülmez; **yavaş** (günlük/H4/makro,
  ayrık kalıcı durumlar) → eğitim [q01, q99] desteği dışı oranı (≥ %50 KAYMA); **hızlı** (gün-içi) → PSI (≥ 0,25 KAYMA).
  İlk sürümde yavaş özelliklere de PSI uygulanmıştı ve 14 günlük pencerede anlamsız değerler (8,3) verdi → düzeltildi.
- **Kalibrasyon bozulması**: `calibration.side_report` — son 14 günün Brier becerisi önceki dönemden ≥ 0,03 düşük veya
  ≥ 2 kova WF bandı dışında.
- `alarm` = önemli özelliklerde (meta.top_features) KAYMA veya kalibrasyon uyarısı → yeniden eğitim (Faz 9 §1) veya geri
  alma değerlendirmesi.
- **Bugünkü durum (2026-11-13):** alarm **AÇIK** — önemli özelliklerden H1 ATR rejimi kaymış (PSI 1,97); ayrıca D1 ATR
  oranının %50'si eğitim desteği dışında, yuvarlak seviye uzaklıkları ve seans aralığı/ADR kaymış. Hepsi aynı olgu:
  NDX şu an eğitim yılının üst ucunda bir oynaklık rejiminde (H1 ATR ~145 p, VIX 18,7). Final dönemdeki kalibrasyon
  eğimi düşüşüyle tutarlı. Öneri: canlı kalibrasyon (gölge) birikene kadar olasılıkları bant genişliğiyle okumak.
  Rapor: `results/faz9_drift_20261113.json`.

## 4. Açık kalanlar
- 2018-01 → 2021-10 ve 2026-01-01 → 02-07 Dukascopy indirmesi sunucu engeliyle tamamlanamadı; `faz9_retrain.run`
  her koşuda eksikleri yeniden dener (2020 çöküşü rejimi eklenirse model v2).
- Yön-koşullu tek model (Faz 4: Brier %0,7 daha iyi) v2 adayı — terfi kuralıyla sınanmalı.
- Gölge modunun kalıcı açılması (`NOM_SHADOW_ENABLED=1`) kullanıcı kararı.
