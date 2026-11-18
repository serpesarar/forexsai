# NASDAQ yükseliş serileri ve opsiyon vadesi (OPEX) haftası (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md) (+ EK-1), kod `src/so.py`, `src/ek1.py`. ^NDX 1985 → verisi `data/` (yfinance, git dışı).

| hücre | 1985–99 (^NDX, EK-1) | 1999–2009 | 2010–17 | 2018–26 | kör SPY / DIA / IWM | hüküm |
|---|---|---|---|---|---|---|
| **6+ gün üst üste yükseliş → 5 gün AL** | **+34,6** (n 130, P 0,82) | +63,1 | +19,3 | +33,4 | +13 / −20 / −43 | **C+ (NDX'e özgü momentum; 4 dönem artı)** |
| 4+ gün → 1 / 5 gün | | −4 / +16 | +6 / +1 | −8 / −4 | eksi | X |
| OPEX haftası | | +9,7 | −13,7 | −48,9 | −16 / −17 / −18 | X |
| OPEX sonrası hafta | | −24 | +52 | +6 | | X |
| çeyrek OPEX haftası | | −85 | +23 | −39 | eksi | X |
| **çeyrek OPEX sonrası hafta** | **−24,0** (P 0,73) | −23,8 | −39,3 | −6,7 | −23 / −20 / −46 | **C+ (eksi; zayıf)** |

- **6 gün seri momentumu NASDAQ'a özgü:** dört bağımsız dönemde artı, ama öteki endekslerde yok ya da ters (IWM −43). Teknoloji
  momentumunun bir yansıması olabilir. P değerleri zayıf (0,82 / 0,96–0,98) → C+.
- Çeyrek vadesi sonrası hafta 4 dönemde ve 3 kör ETF'te eksi, ama büyüklük küçük ve istatistik zayıf → C+ (uzun açmama etiketi adayı).
