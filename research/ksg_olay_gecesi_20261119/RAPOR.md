# KSG × olay öncesi gece — bileşik sınama — RAPOR (2026-11-19)

- Ön kayıt `PROTOCOL.md` (commit 2e1c3bcf, sonuçlardan önce). Kod `src/olay.py`, sonuç `results/olay.json`.
- O = ertesi gün FOMC ∨ ertesi sabah CPI/NFP ∨ bugün kapanış sonrası 12 dev şirketten bilanço. Pozisyon 16:00 AL → ertesi 09:30 SAT, maliyetli.
- Jenerik KSG canlı kodla örtüşmesi: 1.041 / 1.046 gece (1.040 ortak).

## H1 — KSG gecesinde olay öncesi (doz/etiket)
| Veri | KSG ∧ O | KSG ∧ ¬O | Δ_KSG (P) | KSG-değil'de Δ | Fark-farkı (P) |
|---|---|---|---|---|---|
| S MT5 NAS100 2018–26 (görülmüş) | +22,4 (n 242) | +2,8 | +19,6 (0,998) | +4,1 | +15,4 (0,945) |
| — KEŞİF / TEST | +23,0 / +22,0 | +3,2 / +2,5 | +19,8 / +19,5 | | +24,6 (0,93) / +9,4 (0,79) |
| S Duka NDX | +21,7 | +1,4 | +20,3 (0,997) | +4,3 | +16,0 (0,936) |
| Kör US500 / US30 / US2000 | +8,7 / +6,5 / +14,9 | | +7,4 / +7,8 / +8,9 | +7,4 / +5,1 / +4,5 | 0,0 / +2,7 / +4,4 (≤ 0,70) |
| **U1 Duka M30 2016-04 → 2017-09 (dokunulmamış)** | **+1,9 (n 36)** | +0,6 | **+1,3 (0,58)** | +3,4 | **−2,1 (0,42)** |
| U1 EET30 2016-11 → 2017-10 | +11,4 (n 10) | −3,0 | +14,4 (0,98) | +5,8 | +8,6 (0,75) |
| Havuz S MT5 + U1 Duka | | | +17,2 | | +13,0 (0,93) |

- Hafta günü eşli taban (E114): KSG ∧ O +22,4 vs eşli +2,7 → fark +19,7 (gün etkisi değil).
- Doz ×1,5 (canlı VIX ≥ 25 dozu üstüne) Sharpe: MT5 KEŞİF 1,085 → 1,114, TEST 0,739 → 0,834, U1 Duka 0,255 → 0,287.
- Bileşenler (KSG gecesi, S MT5): FOMC +37,4 (n 35), CPI +34,8 (n 49), bilanço +24,7 (n 154), **NFP −1,8 (n 46)**. NFP öncesi gece katkısızdır.
- **Ön kayıt ölçütü harfiyen: B** (U1'in iki beslemesinde Δ > 0, havuz fark-farkı P 0,93, doz üç sette Sharpe artırıyor).
- **Ama:** havuz ölçütünü hipotezi doğuran görülmüş veri taşıdı. Tek dokunulmamış büyük beslemede (Duka 2016–17) etki +1,3 bp'ye iniyor, P 0,58,
  fark-farkı eksi. EET30 artı ama n 10. Kör endekslerde fark-farkı ≈ 0. **Pratik hüküm C+:** KSG'ye özgü olay primi yalnız NDX 2018–26'da açık,
  bağımsız dönemde teyit edilemedi. Doz canlıya önerilmez; lotu değiştirmeyen gölge etiketi (O bayrağı) ile ileri ölçüm önerilir.
  Yöntem hatası defterde E149.

## H2 — KSG'siz, tüm gecelerde olay öncesi uzun (ayrı kural adayı)
| Veri | ort(O) | ort(¬O) | Δ_TUM (P) | yeni kısım (NFP ∨ bilanço, FOMC/CPI hariç) | yarılar |
|---|---|---|---|---|---|
| U2 QQQ 2008–18 (günlük vekil) | +4,4 | −2,0 | +6,3 (0,975) | +4,6 | +5,0 / +7,4 |
| U2 SPY / DIA / IWM | +1,1 / +0,4 / +2,2 | | +4,3 / +3,3 / +4,8 (0,82–0,89) | +2,6 / +2,1 / +3,5 | hepsi artı |
| U2 havuz | | | +4,7 (**P 0,903 < 0,95**) | +3,2 (P 0,75) | +5,8 / +3,5 |
| U3 bilanço gecesi 2002–07 | QQQ −6,8, SPY −3,3, DIA −3,0, IWM −4,5 | | **dördü de eksi** (−0,7…−7,5) | | |
| S MT5 NAS100 (görülmüş) | +10,0 | −2,0 | +12,0 (0,995) | +7,7 | |
| U1 Duka 2016–17 | +1,7 | −0,7 | +2,4 (0,66) | +0,2 | |

- U2 bileşenleri: FOMC +13…+19 bp (bilinen FG-01 primi), CPI −3,7…−0,1, NFP +2…+5, bilanço −0,8…+4,9.
- **Hüküm X:** koşulsuz bileşik, FOMC primini sulandırıyor. Bilanço gecesi 2002–07'de dört ETF'de eksi, CPI 2008–18'de sıfır.
  Olay öncesi gece primi = FOMC (zaten FG-01 kartı, SHADOW önerisi).

## Sonuç
- Yeni ayrı kural yok (H2 X). KSG ∧ olay öncesi gece NDX'te güçlü (+22 vs +3 bp, iki dönem, iki besleme) ama bağımsız dönemde zayıf → **C+ gölge etiketi**.
- NFP öncesi gece bileşiğe dahil edilmemeliydi (KSG'de −1,8, tüm gecelerde −4,8). Bunu şimdi çıkarmak sonuca bakarak seçim olur. Yalnız gözlem olarak kaydedildi.
- Önerilen ileri gölge: `ksg_live` girişinde lotu değiştirmeyen `olay_oncesi` bayrağı (FOMC/CPI/bilanço ayrı alt etiket), n ≥ 40'ta KSG ∧ O vs KSG ∧ ¬O.
