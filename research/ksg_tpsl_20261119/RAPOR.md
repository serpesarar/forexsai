# KSG — daha az zarar, daha çok kâr: gece içi TP/SL, sabah kurtarma, ekleme, kapanış emri payı — RAPOR (2026-11-19)

- Ön kayıt `PROTOCOL.md` (commit f5f2dcd3, sonuçlardan önce; EK-1 sonuçlardan sonra, hükmü değiştirmez). Kod `src/motor.py`, `src/analiz.py`,
  `src/ek1.py`; sonuçlar `results/analiz.json`, `results/ek1.json`.
- KSG jenerik (15:00 → 16:00 aşağı → 16:00 ask AL → ertesi 09:30 bid SAT). Taban: Duka NDX 1.035 gece +6,55 bp, isabet %55,5;
  MT5 NAS100 1.045 gece +7,33 bp, isabet %56,3; EET30 +7,0; NQ +9,5; U1 Duka M30 2016–17 +0,9 (n 154).
- "SL" = eksi kapanan gece, "TP" = artı kapanan gece. Hüküm beklenti + Sharpe ile, isabet betimleyici.

## Kısa cevap: isabet ↔ beklenti
| Kural (Duka NDX 2018–26) | İsabet | Gece başına net | Sharpe |
|---|---|---|---|
| **Taban (canlı KSG)** | %55,5 | +6,55 | 0,79 |
| TP 20 bp, stop yok | **%80,1** | −0,26 | −0,06 |
| TP 40 bp | %67,2 | +1,79 | 0,32 |
| TP 80 bp | %58,1 | +4,46 | 0,66 |
| TP 120 bp | %56,0 | +5,07 | 0,69 |
| TP 40 + SL 100 | %64,4 | −0,92 | −0,17 |
| TP 120 + SL 250 | %55,8 | +3,60 | 0,48 |
| **Sabah kurtarma: 09:30'da ≤ −60 bp zararda → 16:00'a tut** | %58,6 | **+8,27** | **0,88** |
| Sabah kurtarma: 09:30'da zararda olan HER gece → 16:00 (seçilmedi, betimleyici) | **%69,6** | +8,96 | 0,80 |

MT5 NAS100'de aynı tablo birebir (TP 20: %80,2 / +0,40; kurtarma −60: %59,2 / +8,94 / Sharpe 0,96).
**TP limiti isabeti yükseltir, beklentiyi öldürür:** KSG'nin kârı az sayıda büyük toparlanma gecesinden gelir (MFE ort +57 bp); her TP onları keser.
**Stop her hücrede zarar:** gece içinde dibe değen gece sabaha döner (KD-03 ile aynı yön, şimdi her mumda).
**Kaybedeni kurtarmak, kazananı kesmekten iyidir.**

## T — gece içi braket (TP 20…120 × SL yok/50…250, 30 hücre): **X**
- KEŞİF'te dondurulan en iyi iki hücre bile tabandan kötü: TP 80 yalın TEST/MT5 −2,1 bp, havuz P 0,09; TP 120 yalın −1,5 / −1,8, P 0,18.
- 30 hücrenin 30'u Duka ve MT5'te tabanın altında.

## R — sabah kurtarma (09:30'da açık net ≤ −k → H'ye tut; 24 hücre): **C** (E116 güçlü)
| Besleme | R(−60, 16:00) farkı | Sharpe taban → R |
|---|---|---|
| Duka KEŞİF / TEST | +2,06 / +1,45 | 0,86 → 1,02 / 0,74 → 0,77 |
| MT5 NAS100 | +1,62 | 0,89 → 0,96 |
| Kör US500 / US30 / US2000 | +3,06 / +2,43 / +2,62 | hepsi ↑ |
| EET30 / NQ | +1,42 / +4,39 | 0,83 → 0,89 / 1,23 → 1,71 |
| **U1 Duka M30 2016–17** | **−1,54** (n 154) | 0,26 → −0,15 |
- Havuz P 0,887 < 0,975, U1 eksi → ön kayıt hükmü **C**. İkinci hücre R(−30, 10:30) TEST +0,05, P 0,76 → C.
- **EK-1 karşı kol (E116):** 09:30'da ≤ −60 bp zararla açılan gecede 09:30 → 16:00:
  KSG gecesi Duka +10,3 (medyan +15,2, n 172), MT5 +9,8 (+20,5), EET30 +9,3, NQ +38,7, kör +24 / +22 / +16;
  **KSG-olmayan aynı gecelerde −6,8 / −11,9 / −15,1 / −21,6, kör −6 / −14 / +1.** Etki KSG'ye özgü (genel boşluk-dönüşü değil), medyanlar artı.
  Ama en iyi 5 hariç ≈ −3…+9 → kuyruğa dayalı; en kötü tutuş −508 bp (gün içi risk eklenir).
- Pratik: **C, gölge etiketi önerisi** (canlı KSG çıkışında "kurtarma olsaydı" 16:00 fiyatını kaydet; n ≥ 40 tutulan gecede ort > 0 ise karar).

## A — gece düşüşünde ikinci birim (t × −k, 15 hücre): **C**, 18:00 hali **E97 artefaktı**
- Dondurulan A(18:00, −40): eklenen birim Duka +88 bp (n 41), MT5 +71, EET30 +54, NQ +97, kör +41 / +9 / +111; Sharpe Duka 0,79 → 1,00,
  MT5 0,89 → 1,03; havuz P 0,998. U1 Duka M30 dışa aktarımında 17:00–01:00 ET mumları yok → 0 ekleme, sınanamadı → ön kayıt hükmü **C**.
  A(20:00, −40) TEST'te Sharpe düşer → X.
- **EK-1 icra:** 18:00 = vadeli/CFD yeniden açılışı; Duka spread medyanı 0,87 → 1,99 (E97). Gecikmeli giriş:
  Duka 18:00 +88 → 18:05 +62 → 18:15 +63 → 18:30 +51 (medyan 54 → 24 → 29 → 17); NQ +97 → +53 → +39 → +37 (en iyi 5 hariç 18:05+ **eksi**);
  MT5 18:30 +49, EET30 18:30 +19 (en iyi 5 hariç −3,7). Karşı kol (KSG-olmayan aynı düşüş) her yerde ≈ 0 / eksi → KSG'ye özgü.
- Yılda ≈ 5 olay, 2020 tek başına 10/41 (+216 bp). Bilanço gecesi örtüşmesi 19/41; bilançosuz kısım da artı.
- Pratik: icra edilebilir hali (18:30) kuyruğa dayalı, yılda ~5 olay → **C**, canlı yok. Not: eklenen birim zarardaki geceye risk ikiler.

## M — 15→16 düşüşünün son 10 dk payı (kapanış emri satışı): **X**
- m ≥ 0,5 vs < 0,5: Duka KEŞİF +13,8 vs +2,9 (fark +10,9) → **TEST +4,5 vs +7,3 (−2,8)**; NQ +9,3 vs +9,6 (−0,3); havuz P 0,58.
  İşaret döndü → X. Tertillerde düzen yok.

## Sonuç
- **KSG'ye TP/SL koymak X:** isabeti %56'dan %80'e çıkarmak mümkün, ama beklenti sıfıra iner. Stop her eşikte zarar.
- Tek tutarlı iyileştirme yönü **zararlı sabahı kapatmamak**: KSG'nin "korkuyu satın al" mantığı 09:30'dan sonra da sürüyor, KSG-olmayan
  gecelerde tersi. Bağımsız eski dönemde (2016–17) tutmadı ve kuyruğa dayalı → C, gölge etiketi.
- Kaybeden gece giriş anında tanınmıyor (KA-01), gece içinde kesilemiyor (KD-03, T). Kalan yol çıkış tarafında: kurtarma (R) gölgesi.
