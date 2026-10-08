# Sonuç — sembol başına TP/SL optimizasyonu (2026-10-08)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `run.py` · `results/grid.csv`, `results/ozet.csv`.
551 bağımsız bot kararı; eğitim = son 45 gün (112), test = öncesi (439). 56 SL×TP çarpanı, her işlem kendi
girişiyle yönetimsiz yeniden oynatıldı; (1,1) gerçek TP/SL'yi %98,5 tutuyor.

## 1. Ön-kayıtlı yöntem: son 1,5 ayın en iyisini seç → önceki işlemlerde sına (aynı lot, toplam R)

| kapsam | son 1,5 ayın en iyisi | son 1,5 ay | önceki dönemde | mevcut ayar önceki dönemde | test sırası | sıralama korelasyonu |
|---|---|---:|---:|---:|---:|---:|
| NDX BUY (20/56) | SL×1,25 TP×3 | +16,2 | **−10,9** | +5,1 | **56/56** | −0,10 |
| NDX SELL (32/202) | SL×2 TP×0,5 | +9,9 | **−10,3** | −1,6 | 49/56 | **−0,58** |
| USOIL BUY (23/77) | SL×0,5 TP×1,5 | +8,0 | **−11,1** | −5,8 | 33/56 | +0,55 |
| NDX (52/258) | SL×1 TP×1,25 | +15,5 | +2,4 | +3,5 | 29/56 | −0,19 |
| USOIL (23/122) | SL×0,5 TP×1,5 | +8,0 | −18,1 | −16,7 | 28/56 | +0,59 |

DAX, XAU: eğitim ya da testte <20 karar (XAU'nun bot işlemleri yalnız decider'ın 10-05 sonrası).
**Hiçbir sembolde geçmedi** — son 1,5 ayın kazananı önceki dönemde mevcut ayardan kötü (NDX BUY'da en kötüsü).

## 2. Keşif: iki dönemde de iyi olan hücre (artık temiz test yok — yalnız aday üretir)

| aday | aynı lot R/işlem | **aynı risk R/işlem** | eşli fark P(>0) | son 1,5 ay | hüküm |
|---|---:|---:|---:|---:|---|
| NDX BUY SL×2 TP×1,5 | +0,17 → +0,31 | **+0,167 → +0,155** | %88 | −0,06 | kazanç riski 2× almaktan; geometri değil |
| NDX BUY SL×2,5 TP×2,5 | +0,17 → +0,33 | +0,167 → +0,133 | %78 | −0,08 | aynı |
| DAX BUY SL×2 TP×2 | +0,08 → +0,19 | +0,075 → +0,097 | %67 | −0,04 (n=11) | gürültü |
| USOIL BUY SL×1,25 TP×0,75 | −0,01 → +0,06 | −0,006 → +0,045 | %83 | −0,09 | son dönemde kötü |
| **NDX SELL SL×1 TP×2** | +0,008 → +0,057 | +0,008 → +0,057 | %82 | +0,03 | tek risk-eşit iyileşme; WR %57→%42; zayıf (C) |

## Hüküm
TP/SL'yi yakın geçmişe göre ayarlamak geçmişe uyum (aşırı uyum): sıralama dönemden döneme korunmuyor.
"Daha çok kazandıran" geniş SL'ler aynı lotta riski 2–2,5 katına çıkardığı için kazandırıyor; risk eşitlenince
fark yok — bu lot büyütmekle eşdeğer (lot zaten 30). Tek zayıf aday NDX SELL TP×2 (80→160 puan, SL 110):
risk aynı, +0,05R/işlem, P=%82, 234 karar — gölge adayı. Not: canlı NDX BUY'da BE30+koştur (M3) var; bu
tablo yönetimsiz. Defter: IO-13.
