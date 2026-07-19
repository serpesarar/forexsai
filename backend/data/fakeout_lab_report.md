# Fakeout Lab — %70/%70 Deney Izgarası (NDX)

| TF | TP | SL | Mod | Olay | Taban sahte% (te) | SAHTE kesinlik% | SAHTE kaps% | GERÇEK kesinlik% | GERÇEK kaps% | Geçti |
|---|---|---|---|---|---|---|---|---|---|---|
| 5m | 1.0 | 1.0 | instant | 1427 | 48.6 | None | None | None | None |  |
| 5m | 1.0 | 1.0 | delayed+1bar | 1427 | 48.6 | 70.0 | 50.7 | 83.1 | 34.6 | ✅ |
| 5m | 1.0 | 1.5 | instant | 1429 | 40.6 | None | None | None | None |  |
| 5m | 1.0 | 1.5 | delayed+1bar | 1429 | 40.6 | 81.2 | 18.6 | 76.9 | 63.6 | ✅ |
| 5m | 1.5 | 1.0 | instant | 1425 | 59.3 | 69.2 | 6.1 | None | None |  |
| 5m | 1.5 | 1.0 | delayed+1bar | 1425 | 59.3 | 68.1 | 74.1 | 78.1 | 17.1 |  |
| 5m | 0.75 | 1.0 | instant | 1427 | 43.0 | 41.4 | 6.8 | None | None |  |
| 5m | 0.75 | 1.0 | delayed+1bar | 1427 | 43.0 | 70.0 | 44.4 | 79.0 | 56.8 | ✅ |
| 15m | 1.0 | 1.0 | instant | 886 | 56.3 | None | None | None | None |  |
| 15m | 1.0 | 1.0 | delayed+1bar | 886 | 56.3 | 66.3 | 70.0 | 65.7 | 39.9 |  |
| 15m | 1.0 | 1.5 | instant | 884 | 49.2 | None | None | None | None |  |
| 15m | 1.0 | 1.5 | delayed+1bar | 884 | 49.2 | 82.8 | 24.2 | 63.2 | 47.3 |  |
| 15m | 1.5 | 1.0 | instant | 886 | 60.5 | 65.0 | 15.2 | None | None |  |
| 15m | 1.5 | 1.0 | delayed+1bar | 886 | 60.5 | 66.7 | 84.4 | 69.6 | 17.5 |  |
| 15m | 0.75 | 1.0 | instant | 886 | 46.4 | None | None | None | None |  |
| 15m | 0.75 | 1.0 | delayed+1bar | 886 | 46.4 | 69.7 | 46.4 | 69.4 | 68.4 |  |
| 30m | 1.0 | 1.0 | instant | 507 | 63.2 | None | None | None | None |  |
| 30m | 1.0 | 1.0 | delayed+1bar | 507 | 63.2 | 70.3 | 77.1 | 60.0 | 24.3 |  |
| 30m | 1.0 | 1.5 | instant | 505 | 54.9 | None | None | None | None |  |
| 30m | 1.0 | 1.5 | delayed+1bar | 505 | 54.9 | 67.4 | 60.6 | 63.8 | 40.8 |  |
| 30m | 1.5 | 1.0 | instant | 504 | 71.8 | 73.8 | 56.3 | None | None |  |
| 30m | 1.5 | 1.0 | delayed+1bar | 504 | 71.8 | 75.0 | 84.5 | 45.5 | 15.5 |  |
| 30m | 0.75 | 1.0 | instant | 509 | 57.6 | None | None | None | None |  |
| 30m | 0.75 | 1.0 | delayed+1bar | 509 | 57.6 | 68.0 | 67.4 | 62.1 | 40.3 |  |
| 1h | 1.0 | 1.0 | instant | 618 | 71.7 | 74.3 | 90.8 | None | None |  |
| 1h | 1.0 | 1.0 | delayed+1bar | 618 | 71.7 | 76.6 | 92.9 | 59.6 | 28.3 |  |
| 1h | 1.0 | 1.5 | instant | 582 | 61.6 | 63.1 | 91.3 | None | None |  |
| 1h | 1.0 | 1.5 | delayed+1bar | 582 | 61.6 | 68.9 | 87.8 | 62.0 | 45.9 |  |
| 1h | 1.5 | 1.0 | instant | 606 | 77.7 | 81.5 | 87.7 | None | None |  |
| 1h | 1.5 | 1.0 | delayed+1bar | 606 | 77.7 | 81.9 | 92.7 | None | None |  |
| 1h | 0.75 | 1.0 | instant | 622 | 62.2 | 64.9 | 94.1 | None | None |  |
| 1h | 0.75 | 1.0 | delayed+1bar | 622 | 62.2 | 67.6 | 91.9 | 70.7 | 31.4 |  |

Eşikler yalnız TRAIN'de seçildi (hedef ≥%72); tablo değerleri TEST (OOS). Purge: test, train sonundan horizon kadar boşluk sonrası başlar.