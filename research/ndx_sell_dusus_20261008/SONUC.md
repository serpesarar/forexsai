# Sonuç — NDX SELL mantığı düşüş dönemlerinde (10 yıl) (2026-10-08)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `run.py` · `results/`. Ana veri 30m 2021-06 → 2026-07 (2022 ayı piyasası,
2025 Nisan dahil); ikincil 1h 2016-05 → 2021-06 (2018 Q4, 2020 Covid). Botun panel oylarına dayalı kuralları
birebir yeniden üretilemez (E22) — bar verisinden kurulabilen MANTIKLAR, botun 80/110 geometrisiyle (fiyata oranlı),
sonraki bar açılışında giriş, aynı barda iki bariyer → SL. "DÜŞÜŞ ayı" = ay getirisi ≤ −%3 (geçmişe bakarak
etiket: senaryo analizi, kural değil). Başabaş WR %57,9.

## 30m (ANA) — DÜŞÜŞ aylarında işlem başına R
| strateji | n | WR | ort R | P(>0) | yıl yıl (düşüş ayları) |
|---|---:|---:|---:|---:|---|
| S0 her saat SELL | 1.162 | %55 | **−0,04** | %6 | 2022 −0,07, 2025 −0,13, 2026 −0,05; 2021/23/24 + |
| S1 VIXREG SELL (VIX<18,4) | 187 | %63 | **+0,09** | %93 | 2021 +0,12, 2022 +0,25, 2023 +0,05, 2024 +0,08, 2025 +0,10 · 1h: 2018 +0,20, 2019 +0,13, 2020 −0,16 |
| **S1b VIXREG BUY (VIX≥18,4)** | 975 | %52 | **−0,10** | %0 | 2021 −0,14, **2022 −0,11 (730)**, 2023 −0,66, 2024 +0,08, 2025 −0,03, 2026 −0,09 · 1h: **2018 −0,29, 2020 −0,30**, 2019 +0,26 |
| S2 momentum SELL TP×2 | 418 | %44 | +0,07 | %87 | yıllara göre karışık (2022 +0,12, 2024 −0,12, 2020 −0,09) |
| S3 kanal-üst SELL | 141 | %52 | −0,11 | %8 | — |
Ayı (tepeden ≥%15): S0 −0,10, S1b BUY −0,08 (n=1.214; 1h −0,56), S3 −0,17; VIXREG SELL neredeyse hiç
tetiklenmiyor (n=4 — ayıda VIX hep ≥18,4).

## Hüküm
1. **Düşüşte "her SELL kazanır" doğru değil:** saat başı SELL düşüş aylarında bile ≈ −0,04R. Düşüşler kısa
   sert dalgalar ve sert tepkilerle geliyor; %0,36'lık stop tepkilerde yeniyor ("korku döner", GF-12).
2. **Asıl risk VIXREG'in yön değiştirmesi:** satış dalgasında VIX 18,4'ü aşınca VIXREG BUY açar; bu BUY'lar
   80/110 brakette düşüş aylarında 9 yılın 7'sinde negatif (30m −0,10R, 1h 2018/2020 −0,29/−0,30R). VIX rejiminin
   yön öngörüsü (K1) günlük ufukta ve zaman çıkışıyla çalışıyor (CAPREV, GF-16/20); dar intraday brakette çalışmıyor
   (meta-ders 5: braket ≠ zaman).
3. **VIXREG SELL düşüşün başında iyi** (VIX henüz <18,4): düşüş aylarında 8 yılın 7'sinde +, ort +0,09R — ama
   gerçek ayıda tetiklenmiyor.
4. Momentum SELL ve kanal-üst SELL düşüşte sağlam değil.

Uyarılar: kurallar vekil (panel oyları yok); 1h'de aynı-bar belirsizliği yüksek (barların %12'si SL+TP'den geniş,
30m'de %6) → sonuçlar SL'ye doğru muhafazakâr; rejim etiketi geçmişe bakar. Defter: IO-15.

## Ek — gerçek VIXREG BUY doğrulaması (`vixreg_buy_real.py`)
- **Botun gerçek VIXREG BUY'ı yalnız 3** (07-08 ×2, 07-20): üçü de TP (+0,73R). İstatistik için yetersiz.
- **VIXREG'in oy kaynağı olan gerçek pulse1/pulse2 NDX BUY sinyalleri, VIX≥18,4 günlerinde** (06-23→25, 07-20, 07-29→31),
  broker 1m, bağımsız: n=19, 80/110 **−0,36R** (WR %37, P(>0) %5); aynı günlerde saat başı rastgele BUY −0,01R →
  yüksek VIX'te panel BUY sinyalleri rastgeleden KÖTÜ.
- Botun kapıları bunları neredeyse tamamen eliyor: trend kapısıyla 6, trend+konum kapısıyla **1** kalıyor. Botun
  gerçekte yalnız 3 VIXREG BUY açmasının sebebi bu.
- 10 yıllık vekile trend kapısı (1h EMA50 üstü) eklenince düşüş aylarında: 30m 2021-26 **−0,10 → −0,02R** (n 975 → 357,
  P(>0) %36); ama 1h 2016-21 **−0,28 → −0,25R** (2018 −0,33, 2020 −0,21). Kapı riski 2021-26'da sıfırlıyor, 2016-21'de değil.
**Güncel hüküm:** IO-15'teki risk, botun trend+konum kapıları sayesinde canlıda büyük ölçüde frenli; yine de
sert bir düşüşte (2018/2020 tipi) kapılı VIXREG BUY'lar da kaybedebilir. Acil değişiklik gerekmez; izlenir.
