# candle_cache zaman ekseni: kök neden, yapısal koruma, onarım ve dedektörün yeniden üretimi

**Tarih:** 2026-08-12
**Tetikleyici:** Kullanıcı — "bu kaymalar daha önce de oldu, sistemi detaylı incele
ve artık kayma olmayacak şekilde yapılandır."
**Betikler:** `backend/research/candle_time_audit.py` · migration
`repair_1m_shift_step1/2` · `fakeout_lab.align_1m_basis` · `fakeout_finalize.py`

---

## 1. Kök neden — iki yerde yanlış varsayım

MT5 Python API'sinin `copy_rates(...)["time"]` alanı **UTC değil, broker sunucu
saatidir** (IC Markets / Pepperstone: kış UTC+2, ABD-yaz UTC+3). Sistemde bu
gerçeği bilen tek yol `yeni deneme/data_recorder.py` idi (2026-07-28/31'de
düzeltilmiş, offset'i çalışma anında ölçüyor). İki yol ise tam tersini
varsayıyordu:

| yol | hata |
|---|---|
| `backend/routers/mt5_reconciliation.py::upload-1m-bars` | `broker_utc_offset_hours` **varsayılanı 0**; dokümantasyonda "MT5 API zaten UTC verir" yazıyordu |
| `research/mt5_pull_missing_1m.py` | `"t": int(r["time"])  # unix sec, MT5 API = UTC` |

Bu ikisi 2026-05'teki toplu 1m doldurmasında kullanıldı → **315.730 bar 3 saat
ileri damgayla** yazıldı. 5m/15m/30m/1h serileri Temmuz'daki MT5-otoriteli
onarımdan (`repair_candle_cache.py`) geçtiği için temizdi; 1m'in o partisi
onarılmadan kaldı.

## 2. Hasar haritası (`candle_time_audit.py`, gün gün, 5m referans)

| Sembol | 1m kaymış blok | kayma | 15m | 5m |
|---|---|---|---|---|
| NDX.INDX | 2026-02-11 → 05-06 (61 gün) | −180 dk | 302/302 temiz | temiz |
| GDAXI.INDX | 2026-02-11 → 04-22 (49 gün) | −180 dk | 343/343 temiz | temiz |
| XAUUSD | 2026-02-11 → 05-06 (62 gün) | −180 dk | 298/303 temiz | temiz |
| USOIL.FOREX | 2026-02-11 → 05-06 (54 gün) | −180 dk | 302/302 temiz | temiz |

Yazıcı adli incelemesi bunu doğruluyor: `fetched_at` Mayıs-2026 olan 1m satırları
tam olarak bu bar aralığını kapsıyor (NDX 83.609 · XAU 82.750 · USOIL 82.639 ·
GDAXI 66.732).

## 3. YAPISAL KORUMA — kaymanın bir daha olmaması için

**Asıl koruma yazma sınırında** (`services/candle_cache_store.persist_candles`):
bir barın damgası onun **açılış** zamanıdır, dolayısıyla geçerli hiçbir bar
"şimdi"nin ilerisinde olamaz. Kaymış bar her zaman 2-3 saat ileridedir →
**bu kapıdan geçemez.** Kaynağı ne olursa olsun (endpoint, toplu doldurma,
DataHub köprüsü) kayma sınıfının tamamı burada durur ve WARNING'le raporlanır.

Ek olarak:
- `upload-1m-bars`: yanlış dokümantasyon düzeltildi; offset verilmezse
  **payload'dan otomatik ölçülür** (en yeni bar şimdiden ileride mi) ve yanıtta
  raporlanır.
- `mt5_pull_missing_1m.py`: offset canlı tick ile ölçülüp çıkarılır
  (data_recorder yöntemi: çok sembollü medyan, 15 dk yuvarlama, bayat tick reddi).
- `candle_time_audit.py`: sembol × TF × gün kayma denetimi — düzenli koşulabilir.

## 4. Veri onarımı

1. **Yedek:** `candle_cache_shift_backup_20260812` (315.730 satır, ham hâl).
2. **İki adımlı kaydırma:** tüm partiyi tek UPDATE ile −3 saat kaydırmak
   `unique(symbol,timeframe,candle_time)` kısıtını **geçici** olarak ihlal ediyor
   (parti içi: A satırı t−3h'ye inerken orada duran B henüz kaymamış). Çözüm:
   önce 1926'ya park, sonra +100 yıl −3 saat ile geri indirme.
3. **İdempotency:** migrasyon `fetched_at`'i damgaya çeker → yanlışlıkla ikinci
   kez koşulsa bile aynı satırlar bir daha eşleşmez.

**Doğrulama:** onarım sonrası her test gününde en iyi hizalama **lag 0**;
Haziran/Temmuz günlerinde fark tam **0.00**.

### 4b. İkinci katman: fiyat tabanı farkı

Zaman düzeldikten sonra Şubat–Nisan'da 3-12 puanlık **sistematik** fark kaldı:
o dönemin 1m partisi **eski broker'dan** (USTEC / IC Markets), 5m ise güncelden
(NAS100 / Pepperstone). NDX'te bu ATR(5m)'in %10-40'ı kadar — yarış etiketi 1m,
giriş/ATR 5m ile hesaplandığı için etiketleri yanlı yapardı.
Çözüm: `fakeout_lab.align_1m_basis` — gün bazında medyan(5m−1m) kadar seviye
düzeltmesi (bar içi hareketi değiştirmez, aynı-besleme günlerinde no-op).

## 5. Dedektörün yeniden üretimi — asıl sürpriz

Onarılmış zaman ekseni + hizalanmış taban ile `fakeout_finalize.py`:

| Sembol | olay | SAHTE çağrısı | GERÇEK çağrısı | eski (bozuk etiketli) iddia | çıta |
|---|---|---|---|---|---|
| **NDX.INDX** | 1.933 | **%75,4** (kaps %48,5) | **%74,2** (kaps %55,8) | %70,0 / %83,1 | ✅ geçti |
| GDAXI.INDX | 1.559 | %69,1 (kaps %68,1) | %74,0 (kaps %45,2) | %74,6 / %88,9 | ❌ |
| XAUUSD | 1.762 | %66,3 (kaps %55,1) | %71,4 (kaps %72,9) | %71,7 / %93,1 | ❌ |
| USOIL.FOREX | 1.483 | %75,0 (kaps %46,0) | %68,4 (kaps %70,0) | %86,0 / %81,0 | ❌ |

**Doğru etiketlerle yalnız NDX %70/%70 çıtasını geçiyor.** Diğer üçünün Temmuz'daki
sayıları (DAX %89, XAU %93, USOIL %86) bozuk zaman ekseninin ürünü.

Bu, gölge karnesindeki bilmeceyi de çözüyor: canlıda dedektörün SAHTE çağrısı
%57 çıkıyordu, lab %70-93 diyordu. Artık lab da %66-75 diyor — uçurum kapandı.

**Karar:** Bozuk etiketle eğitilmiş artefaktları üretimde bırakmak yanlış olurdu;
üç sembol `force` ile **doğru etiketle** yeniden yazıldı ama dürüstçe
`verified_70_70: false` damgasıyla — tüketiciler (panel, claude_decider) bunu
zayıf kanıt olarak okumalı. Fakeout kapısı zaten GÖLGE modda
(`FAKEOUT_GATE_BLOCK=0`), yani hiçbir işlem bu modellerle bloklanmıyor.

## 6. Yan düzeltme: derin offset sayfalaması

`fakeout_miner.fetch_candles` `offset` ile sayfalıyordu; ~130k satırdan sonra
Supabase 500 veriyor ve NDX 1m çekimi ortasında düşüyordu (aynı hatayı kapı
doğrulamasında da görmüştük). **Keyset sayfalama + 3 denemeli tekrar** eklendi.

## 7. Açık kalanlar

- GDAXI/XAU/USOIL dedektörleri çıtayı geçemiyor → ya eşikler sembol bazında
  gevşetilip "zayıf kanıt" olarak kullanılacak, ya da bu semboller için dedektör
  emekliye ayrılacak. Karar veri biriktikçe verilmeli.
- Teyit ufku taraması (K=1..20) **onarım öncesi** veriyle koşmuştu; K=2-3 tavanı
  sonucu muhtemelen değişmez (yarışın ne zaman bittiği zaman eksenine değil
  fiyat hareketine bağlı) ama onarılmış veriyle tekrarlanmalı.
- Kutunun MT5'inde XAU M1 geçmişi yalnız ~7,7 gün — gölge replay'ini
  derinleştirmek için genişletilmeli.
