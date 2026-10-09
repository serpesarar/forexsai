# Canlıya alma adayları — ön kayıt (2026-10-09, sonuçlara bakılmadan yazıldı)

Kapı defteri §0'a göre. Ölçütler CLAUDE.md 2. Kural ile aynı (6 ölçüt). Çıplak WR değil, R.

## A. Sınananlar (bu oturumda zaten koşuldu, sonuçlar RAPOR.md'de)
- **VIXREG canlı işlem kartı** (`live_card.py VIXREG`): bot_trades, karar bazında. Diğer canlı aileler aynı kartla (taban).
- **Sahte kırılım dedektörü gölge kartı** (`fakeout_shadow_card.py`): shadow_pattern_trades source=fakeout.

## B. DAYCOMBO — seçimde görülmemiş veride bar yeniden kurulumu (`daycombo_oos.py`)
Kural (bot `forexsai_demo_bot.check_daycombo`, aynen):
1. Karar anı = 5m bar kapanışı T, 14:00 ≤ T ≤ 19:30 UTC; Cuma hariç (bot B2 NDX Cuma yasağı).
2. Son kapalı 5m bar yeşil ve gövde/aralık > 0,5.
3. Gece pozitif: günün 00:00 UTC ilk 5m açılışı < başlangıcı ≤ 13:20 olan son 5m barın kapanışı.
4. Son kapalı 15m bar (bitişi ≤ T): kapanış > EMA20 ve EMA20 > 3 bar önceki EMA20.
5. Açık DAYCOMBO pozisyonu yoksa: giriş = T'den sonraki ilk 1m açılışı + 1,5 puan spread (BUY ask).
   TP = giriş + 80, SL = giriş − 110 (puan); 1m high/low ile; aynı barda ikisi → SL. 3 gün içinde
   çözülmezse son kapanıştan kapat. Veri boşluğunu aşan pozisyon atılır.
Dönemler: **OOS-A** 2025-01-02→2025-12-30 (Dukascopy, kural seçiminde HİÇ kullanılmadı),
**IS** 2026-02-10→2026-07-28 (seçim verisi, yalnız referans), **OOS-B** 2026-07-29→2026-10-02.
Kart **OOS-A ∪ OOS-B** üzerinde. Sadakat kontrolü: OOS-B yeniden kurulumunun canlı 31 DAYCOMBO işlemiyle
gün/saat eşleşmesi ve ortR'si raporlanır. Duyarlılık (karar değiştirmez): Cuma dahil; spread ×1,5.
Geçme: kart 6/6 ve OOS-A ile OOS-B'nin ikisi de ortR > 0.

## C. CAPREV portföyü NDX + DAX (`caprev_pooled.py`)
Kural `round4.events(stress, hi)` ve `cross_market.events` aynen (GF-16/18), 1h, çıkış o piyasanın seans
kapanışı (R_d0), stop 1×günlük vol, giriş sonraki bar açılışı + spread. Kart birleşik işlem listesinde;
1. ölçüt işlem sayısıyla, ayrıca **bağımsız gün** sayısı raporlanır (aynı gün NDX+DAX birlikte → 1 gün).
Gün-bloklu bootstrap (aynı gün iki işlem tek blok). Geçme: 6/6 ve bağımsız gün ≥ 100.
