# Korku gecesi ayı çağlarında da çalışır mıydı? Günlük vekil ile 1993–2017 (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md) (+ EK-1), kod `src/ka.py` (`ana`, `ek1`). Günlük ETF (QQQ/SPY/DIA/IWM), 2 bp + finansman.

## Vekil doğrulaması
V1 = kapanış ≤ gün orta noktası × 0,995 ∧ kırmızı gün, d kapanışında AL → d+1 kapanışı.
2018–26 QQQ: +34,7 vs −2,5 bp (fark +37,3, n 342). NDX K1 gecelerinin %88'i V1. → vekil geçerli.

## Sonuç 1: korku gecesi 33 yılda, ayı çağları dahil sağlam
| fark (bp), V1 − taban | 93–98 | 99–02 dot-com | 03–07 | 08–09 kriz | 10–17 | 18–26 |
|---|---|---|---|---|---|---|
| QQQ | — | **+48,0** | +17,0 | **+62,5** | +13,5 | +37,3 |
| SPY | +7,3 | +11,4 | +19,8 | +27,2 | +15,4 | +23,8 |
| DIA | −5,2 (n 36) | +16,6 | +17,4 | +39,5 | +25,1 | +19,7 |
| IWM | — | +12,7 | +5,7 | +72,9 | +23,4 | +27,9 |

- 24 hücrenin 23'ü artı. Ayı çağlarında ortalamanın kendisi de artı (QQQ 99–02 +23,5, 08–09 +44,2 bp).
- Ama birikimli düşüş büyük: QQQ 99–02 −3.459 bp, SPY 08–09 −3.010. Lot küçük ve kuyruk riski kabul edilerek açılmalı.
- W2 haftalık korkunun (YK-03) tersine, günlük kapanış korkusu çağdan bağımsız. **K1 ailesinin kanıtı güçlendi.**

## Sonuç 2 (EK-1): iki C+ aday bağımsız dönemde B'ye yükseldi
| | QQQ | SPY | DIA | IWM |
|---|---|---|---|---|
| **GN-05 art arda** ort / değil (1993–2017) | **+52,7 / +10,0** (252 / 643) | +22,4 / +6,9 | +25,1 / +13,0 | +24,4 / +14,6 |
| **ZA-04** olay günü V1 fark / habersiz fark (2008–17) | **−41,3 / +36,2** | −48,9 / +26,3 | −32,4 / +35,1 | −24,8 / +44,7 |

- **Art arda korku gecesi** dört ETF'te de güçlü → GN-05 **B** (doz adayı: lot ×1,5).
- **Makro olay günü korku gecesi** 2008–17'de dört ETF'te de eksi → ZA-04 **B** (veto: olay gününde korku gecesi açma ya da lot ½).
  NDX 2018–26'da olay günü hâlâ +31 (küçük artı); Dow/Russell eksi. Muhafazakâr uygulama lot ½.
- Not: kanıt günlük vekille. Canlı kurala bağlanmadan önce kart eki ve gölge etiketi gerekir (karar kullanıcıda).
