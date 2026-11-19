# Vade mantığının genişletilmesi — MX-01…04 (2026-11-18)

Ön kayıt `PROTOCOL.md` + EK-1/EK-2. Kod `src/vm.py`, `ek1_tom.py`, `ek2_sonra.py`; çıktılar `results/`. Kartlar
`go_live_cards/ndx_opex_korku_vetosu.json` (kapsam k0–2'ye genişledi), `go_live_cards/ndx_vade_sonrasi_korku_dozu.json` (yeni).

## Korku alımının vade döngüsü profili (9 set: C3b QQQ/^NDX 1985–99, K1 QQQ/SPY, gün içi K1 5 besleme; z havuz)
| Bölge | Sonraki vadeye kalan k / son vadeden geçen a | Havuz | Setler | Hüküm |
|---|---|---|---|---|
| Vade Cuma'sı | k = 0 | −0,23z, P(eksi) 0,9996 | 8/8 eksi | veto kapsamına eklendi |
| Vade öncesi Çar/Per | k = 1–2 | −0,31z, P 1,00 | 9/9 eksi (^NDX 1985–99 −240 bp) | **veto B (SV-01)** |
| **Vade sonrası 3.–7. gün** | a = 3–7 | **+0,105z, P(artı) 0,9986** | 8/9 artı (US500 −1); K1 QQQ +25, SPY +12, ^NDX 1985–99 C3b +23, gün içi +19…+59 | **doz B−** (ikinci yarı +0,02z) |
| Vade sonrası Pzt/Salı | a = 1–2 | +0,05z, P 0,87 | karışık | X |
| Döngü ortası | a 8–17, k 3–12 | ≈ 0 | — | etkisiz |

## Diğer sınamalar
- **Çeyreklik vade** veto gücü aylıkla aynı (−0,29z / −0,29z); **vadeli kontrat devir haftası** etkisiz (+0,03z) → X.
- **Ay dönümü** (TOM) korku alımında tersine zayıf (−0,065z, P 0,94; gün içi beslemelerde −25…−66 bp) — C (ayrı izlenmeli; canlı ay başı
  uzun ile çakışma). Vade sonrası kovası ay dönümünden bağımsız (TOM dışı +0,075z P 0,978).
- **Doğal deney (MX-03):** kendi vade takvimi olan Nikkei (2. Cuma), KOSPI (2. Perşembe), Hang Seng (sondan 2. iş günü), ASX
  (3. Perşembe), Nifty (son Perşembe), TAIEX (3. Çarşamba): yerel vade öncesi korku alımı kötüleşmiyor (havuz +0,065z), ABD penceresi de
  etkisiz; 3. Cuma'lı Avrupa endeksleri karışık → **mekanizma "her vade" değil, ABD opsiyon vadesine özgü.** Sınır: bu piyasalarda korku
  dönüşünün kendisi zayıf (GN-06), yani bastırılacak bir kenar da az.

## Kitap etkisi (veto + doz)
| Set | Taban toplam / Sharpe | Veto | Veto + doz |
|---|---|---|---|
| K1 QQQ 1999–2026 | 31.259 bp / 0,95 | 35.979 / 1,04 | 42.534 / 1,06 |
| C3b QQQ | 21.319 / 0,77 | 22.004 / 0,84 | 25.162 / 0,82 |
| K1 gün içi Duka NDX 2018–26 | 13.797 / 1,04 | 14.495 / 0,98 | 16.743 / 1,01 |
| K1 gün içi MT5 US2000 | 7.641 / 0,79 | 8.042 / 0,87 | 10.339 / 0,93 |
Veto işlem başı ortalamayı %20–30 artırıyor; kısa (9 yıl) gün içi NDX'te yıllık Sharpe hafif düşüyor (yıl sayısı az, E110).
