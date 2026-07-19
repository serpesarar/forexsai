# Fakeout Lab — %70/%70 Deney Izgarası (GDAXI.INDX)

| TF | TP | SL | Mod | Olay | Taban sahte% (te) | SAHTE kesinlik% | SAHTE kaps% | GERÇEK kesinlik% | GERÇEK kaps% | Geçti |
|---|---|---|---|---|---|---|---|---|---|---|
| 5m | 1.0 | 1.0 | instant | 1500 | 54.6 | 54.2 | 18.7 | 36.1 | 8.1 |  |
| 5m | 1.0 | 1.0 | delayed+1bar | 1500 | 54.6 | 74.6 | 61.1 | 88.9 | 20.2 | ✅ |
| 5m | 1.0 | 1.5 | instant | 1506 | 45.4 | 48.1 | 12.1 | 54.3 | 7.9 |  |
| 5m | 1.0 | 1.5 | delayed+1bar | 1506 | 45.4 | 73.3 | 23.6 | 72.6 | 50.1 | ✅ |
| 5m | 1.5 | 1.0 | instant | 1500 | 65.1 | 65.8 | 43.5 | None | None |  |
| 5m | 1.5 | 1.0 | delayed+1bar | 1500 | 65.1 | 69.6 | 89.6 | 71.4 | 12.6 |  |
| 5m | 0.75 | 1.0 | instant | 1502 | 49.2 | 45.1 | 11.5 | None | None |  |
| 5m | 0.75 | 1.0 | delayed+1bar | 1502 | 49.2 | 71.0 | 57.3 | 75.8 | 48.3 | ✅ |
| 15m | 1.0 | 1.0 | instant | 1240 | 59.8 | None | None | 60.2 | 24.7 |  |
| 15m | 1.0 | 1.0 | delayed+1bar | 1240 | 59.8 | 78.4 | 58.4 | 71.4 | 33.4 | ✅ |
| 15m | 1.0 | 1.5 | instant | 1230 | 48.7 | 84.6 | 7.4 | None | None |  |
| 15m | 1.0 | 1.5 | delayed+1bar | 1230 | 48.7 | 75.5 | 26.6 | 65.7 | 56.1 |  |
| 15m | 1.5 | 1.0 | instant | 1237 | 68.6 | None | None | None | None |  |
| 15m | 1.5 | 1.0 | delayed+1bar | 1237 | 68.6 | 81.2 | 65.5 | 58.1 | 20.7 |  |
| 15m | 0.75 | 1.0 | instant | 1239 | 53.4 | 66.7 | 3.4 | None | None |  |
| 15m | 0.75 | 1.0 | delayed+1bar | 1239 | 53.4 | 75.5 | 42.4 | 74.3 | 42.7 | ✅ |
| 30m | 1.0 | 1.0 | instant | 841 | 54.7 | 76.7 | 12.7 | None | None |  |
| 30m | 1.0 | 1.0 | delayed+1bar | 841 | 54.7 | 66.1 | 80.1 | 79.3 | 39.0 |  |
| 30m | 1.0 | 1.5 | instant | 838 | 46.8 | None | None | None | None |  |
| 30m | 1.0 | 1.5 | delayed+1bar | 838 | 46.8 | 85.5 | 26.4 | 80.0 | 48.9 | ✅ |
| 30m | 1.5 | 1.0 | instant | 842 | 69.9 | 82.9 | 34.7 | None | None |  |
| 30m | 1.5 | 1.0 | delayed+1bar | 842 | 69.9 | 76.3 | 87.7 | None | None |  |
| 30m | 0.75 | 1.0 | instant | 842 | 46.0 | 58.3 | 5.1 | None | None |  |
| 30m | 0.75 | 1.0 | delayed+1bar | 842 | 46.0 | 66.9 | 59.9 | 77.5 | 50.6 |  |
| 1h | 1.0 | 1.0 | instant | 935 | 57.6 | 59.6 | 17.9 | None | None |  |
| 1h | 1.0 | 1.0 | delayed+1bar | 935 | 57.6 | 67.8 | 79.4 | 79.4 | 13.0 |  |
| 1h | 1.0 | 1.5 | instant | 934 | 45.6 | 44.0 | 28.7 | 46.9 | 12.3 |  |
| 1h | 1.0 | 1.5 | delayed+1bar | 934 | 45.6 | 67.4 | 33.0 | 78.2 | 21.1 |  |
| 1h | 1.5 | 1.0 | instant | 927 | 70.7 | 61.3 | 12.0 | None | None |  |
| 1h | 1.5 | 1.0 | delayed+1bar | 927 | 70.7 | 74.6 | 89.6 | None | None |  |
| 1h | 0.75 | 1.0 | instant | 935 | 47.7 | 54.5 | 21.0 | None | None |  |
| 1h | 0.75 | 1.0 | delayed+1bar | 935 | 47.7 | 63.4 | 61.5 | 91.4 | 13.4 |  |

Eşikler yalnız TRAIN'de seçildi (hedef ≥%72); tablo değerleri TEST (OOS). Purge: test, train sonundan horizon kadar boşluk sonrası başlar.