# Ön-kayıt — 2026-10-19 NDX ardışık SL zinciri (2026-10-20)

Kullanıcı: dün NASDAQ'ta hızlı hızlı ardışık SL'ler oldu. (1) Hangi kurallar bunları neden açtı?
(2) Ne olsaydı SL'den kurtulunurdu? (3) Yeni eklenen kurallar mı açtı?

## Olgu (bot logu `results/log_1019.txt`, bot_trades, islem_otopsi `output/islem_otopsi/2026-10-20_1409_ndx/`)
Zincirin tamamı NDX BUY, 30 lot, sabit 80/110 geometri; iki aile DAYCOMBO (magic +4) ve REENTRY (magic +6).
Kurallar sonuçlara bakmadan sabitlendi (aşağıdaki K1–K6). Defter: B14 (SQZ, GÖLGE B), M2 (REENTRY, C),
CK-03 (DAYCOMBO OOS −0,03R, X), M9 (BE/kilit elendi — önerilmeyecek), SCOPE_LOSS_COOLDOWN (bağlanmadı, "nötr").

## Karşı-olgu kuralları (DECIDER ayrı süreç ve 0,1 lot → hem engelleyen hem engellenen dışında)
- K1 günlük zarar freni TÜM magic'leri sayarsa: UTC günü içinde realize NDX net ≤ −3.000 $ olunca o günün kalan girişleri yok.
- K2 üst üste binme yok: aynı yönde açık bot NDX pozisyonu varken yeni giriş yok.
- K3 SL soğuması: aynı yönde SL'den sonraki 60 dk içinde giriş yok.
- K4 DAYCOMBO günde en fazla 1.
- K5 SQZ ≥ 1,00 (ATR14/ATR100, 1m, kapanmış barlar) — DAYCOMBO+REENTRY; referans: tüm bot aileleri.
- K6 REENTRY yalnız TP sonrası (SL sonrası yeniden giriş yok).
Bir ebeveyn engellenirse onun doğurduğu REENTRY de yok sayılır (zincir).

## Ölçüm
Dönemler: geçmiş 2026-06-30 → 10-18 (kural seçimine katılmadı) ve 10-19 ayrı. Birim R (lot 1→30 değişti; $ ikincil).
Her kural: engellenen n, engellenenlerin ΣR ve $, kalan ort R; plasebo = aynı sayıda rastgele uygun işlemi engellemek
(2.000 kez) → gerçek kurtarılan R'nin yüzdeliği.
**Geçme (gölgeye aday):** geçmişte kurtarılan R > 0 VE plasebo yüzdeliği ≥ %90 VE iki kronolojik yarıda da ≥ 0.
Geçmeyen kural "dünü kurtarırdı ama genelde kurtarmıyor" diye raporlanır. Bot koduna dokunulmaz;
düzeltme önerisi (ör. fren hatası) kullanıcı onayıyla.
