# Art arda korku gecesi (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/ar.py`.

Fikir KC-03'ten (§2.77) geldi. Bu yüzden NDX yalnız betimleme olarak raporlandı; kör sınav US30, US2000 ve US500'de yapıldı.

## Sonuç: C+ (doz adayı, GÖLGE)
Ardışık gece = bugün K1 ∧ (dün de K1 **veya** dün 09:30 → 16:00 ≤ −%1).

| endeks | ardışık ort (n) | değil ort (n) | P | ESKİ ard./değil | YENİ ard./değil | en kötü ard. / değil |
|---|---|---|---|---|---|---|
| **US30 (kör)** | +82,5 (26) | +23,8 (136) | 0,91 | +115 / +33 | +38 / +17 | −210 / −1.024 |
| **US2000 (kör)** | +50,6 (61) | +26,3 (173) | 0,79 | +47 / +25 | +53 / +27 | −274 / −1.142 |
| **US500 (kör, 2021→)** | +51,1 (24) | +15,6 (93) | 0,87 | +60 / +6 | +49 / +17 | −202 / −611 |
| NDX Duka (betimleme) | +86,0 (59) | +45,2 (193) | 0,91 | +113 / +60 | +73 / +33 | −286 / −613 |
| NAS100 MT5 (betimleme) | +73,1 (54) | +43,6 (180) | 0,83 | +102 / +58 | +63 / +32 | −285 / −623 |

- Kör üç endeksin üçünde de ve iki dönemin hepsinde ardışık geceler daha iyi. Havuz +58,2'ye karşı +23,0 bp, **P 0,910 < 0,95** → C+.
- **Kuyruk ayrımı:** ardışık gecelerde en kötü işlem −200…−290 bp. Ardışık olmayan gecelerde −610…−1.140. Ardışık korkuda hem ortalama
  yüksek hem kuyruk ince. NDX'te işlem başına Sharpe 0,43'e karşı 0,23.
- Yorum: ilk korku günü çoğu zaman haber ya da rejim değişikliği, devamı belirsiz. İkinci gün ise satış baskısının tükenmesine yakın.
  "Korku döner" ilkesinin (§3-2) zamanlama boyutu.
- **Kullanım önerisi (karar kullanıcıda):** canlı K1 / korku gecesi kuralında ardışık gecelerde lot ×1,5–2. Önce gölge etiketiyle ileri
  izlenmeli. Ölçüt: ≥ 30 yeni ardışık gece.
