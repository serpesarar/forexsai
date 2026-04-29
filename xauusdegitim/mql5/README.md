# MT5 Export — Talimatlar

## Adımlar (Windows)

1. **MetaEditor'ü aç** (MT5 içinden F4 ya da Tools menüsü).
2. **File → Open** → `ExportHistoryToCSV.mq5` seç.
3. **F7** ile derle (alt panelde "0 errors" görmeli).
4. MT5 ana ekranına dön → herhangi bir grafik aç (sembol önemsiz).
5. **Navigator → Scripts → ExportHistoryToCSV** → çift tıkla.
6. Dialog'da inputlar:
   - `YearsBack` = **5** (3 yıl da olur, çoğu broker'ın geçmişi sınırlı)
   - `XAUUSD_Symbol` = brokerinde nasıl listeleniyorsa (genelde `XAUUSD`)
   - `DXY_Symbol`, `US10Y_Symbol`, `VIX_Symbol` = brokerin yoksa boş bırak ya da varsayılan
7. OK → script çalışır, Experts panelinde log akar (~30sn–2dk).
8. **File → Open Data Folder** → `MQL5/Files/xauusd_export/` klasörü.
9. O klasörü zip'le → Mac'e kopyala → şuraya çıkart:

```
panel/xauusdegitim/data/raw/
```

## Beklenen Dosyalar

```
XAUUSD_M5.csv
XAUUSD_M15.csv
XAUUSD_M30.csv
XAUUSD_H1.csv
XAUUSD_H4.csv
XAUUSD_D1.csv
USDX_H1.csv     (varsa)
USDX_D1.csv
US10YT_H1.csv   (varsa)
US10YT_D1.csv
VIX_H1.csv      (varsa)
VIX_D1.csv
```

## Sembol Adları Bulamıyorsa

MT5'te **View → Symbols (Ctrl+U)** → sol panelde "Show symbol" → DXY/VIX'i ara. Tam adı kopyalayıp script input'una yapıştır. Yoksa atla — XAUUSD tek başına da yeter.

## Format

CSV başlık: `timestamp,open,high,low,close,tick_volume,real_volume,spread`
Timestamp UTC ISO8601 (broker'ın server time'ı GMT'ye çevrilmiş gibi raporlanır — broker GMT+2/+3 ise `MqlDateTime` server time döner; ML pipeline'ı ben Python'da broker offset'i hesaba katacağım. CSV'leri yolladığında bana **broker'ının GMT offset'ini de söyle** — örn "GMT+3").
