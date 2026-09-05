# Sahte çoğaltma: gölge karnesini bozan hata + GDAXI kararının geri alınması

**Tarih:** 2026-09-05 · **Sınıf:** KRİTİK (ölçüm bütünlüğü + canlı kural geri alma)

## 1. Kullanıcının sorusu doğruydu: "USOIL %99, kaçak mı var?"

Kaçak yok — ama daha sinsi bir şey var: **sahte çoğaltma (pseudo-replication)**.

Bot 60-75 saniyede bir tarıyor ve **aynı koşul sürdükçe aynı gölge kararını
tekrar tekrar kaydediyordu.** Ardışık kayıtlar arası medyan süre 75-78 sn:

| kural | ham kayıt | bağımsız epizod | şişme |
|---|---:|---:|---:|
| pos_tight XAUUSD BUY | 617 | 36 | **17,1×** |
| pos_tight USOIL BUY | 276 | 26 | **10,6×** |
| pos_tight GDAXI BUY | 113 | 14 | **8,1×** |
| pos_tight NDX SELL | 62 | 18 | 3,4× |

Aynı epizoddaki 50 kayıt aynı fiyat hareketiyle çözülür → hepsi birlikte WIN ya
da hepsi LOSS olur. Böylece n sahte büyür ve **p değerleri felaket derecede
yanlış çıkar.**

## 2. ⛔ 2026-09-02'deki canlı kararım HATALIYDI — geri alındı

O gün GDAXI için `POS_TIGHT_BLOCK=True` açtım, gerekçe: *"22W/55L, n=77,
z=−6,47, p≈1e-10"*. Epizod bazında gerçek tablo:

| kural | sembol/yön | epizod | W | L | WR | başabaş | fark | p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| pos_tight | **GDAXI BUY** | 14 | **2** | **6** | %25,0 | %64,0 | −39,0 | **0,022** |
| pos_tight | USOIL BUY | 26 | 11 | 1 | %91,7 | %58,9 | +32,8 | 0,021 |
| pos_tight | NDX SELL | 18 | 8 | 6 | %57,1 | %57,9 | −0,8 | 0,955 |
| pos_tight | XAUUSD BUY | 36 | 17 | 19 | %47,2 | %42,9 | +4,4 | 0,597 |
| squeeze | NDX SELL | 5 | 2 | 0 | %100 | %57,9 | — | 0,228 |

**GDAXI'nin yönü hâlâ doğru** (bloklananlar başabaşın altında) ama kanıt
**n=8 çözülmüş epizod** ve 6 karşılaştırmada Bonferroni eşiği p<0,0083 →
0,022 **geçmiyor**. Karar geri alındı: `POS_TIGHT_BLOCK=False`,
`POS_TIGHT_SYMBOLS=()`. Ölçüm sürüyor.

Ayrıca **USOIL %99 çözüldü**: gerçek değer %91,7 (11W/1L, 12 çözülmüş epizod).
Hâlâ "bloklama" diyor ama abartılı değil — ve zaten bloklamıyorduk.

NDX SELL de artık "kanıt yok" (p=0,955); önceki %62 okuması da şişikmiş.

## 3. Kalıcı düzeltme — iki katmanlı

**(a) Kayıt tarafı** — `shadow_log.record_shadow()` artık epizod bastırıyor:
aynı `(scope, kural)` için **30 dk sessizlik olmadan ikinci kayıt yazılmaz**
(`EPIZOD_SESSIZLIK=1800`). Yani ham veri bundan sonra zaten temiz gelecek.

**(b) Analiz tarafı** — `backend/research/golge_karne.py` eklendi: kayıtları
zaman boşluğuna göre epizoda böler, her epizodun İLK anını gerçek TP/SL
geometrisiyle çözer, sembolün kendi başabaş oranıyla karşılaştırır ve
**Bonferroni eşiğini ekrana basar.** Eski (şişik) kayıtlarda da doğru çalışır.

Bu iki katman birbirini yedekliyor: kayıt bastırması ileriye dönük, epizod
bölme geriye dönük ve unutulamaz.

## 4. Meta engine arka plana bağlandı

Kullanıcının "ana panelde neden bu kadar az sonuç var" sorusunun cevabı:
meta (Core ensemble) `background_scheduler`'da **hiç yoktu** — yalnız biri
`/neural/{sembol}` sayfasını açtığında hesaplanıp loglanıyordu.

| model | tetikleyici | 21 günde kayıt |
|---|---|---:|
| pulse1/2/3, ml, smc, emel | arka plan, 3-15 dk | 500-540 |
| meta (Core) | **sayfa ziyareti** | 6-29 |

`log_meta_signals_if_needed()` eklendi (5 dk'da bir değerlendirme; yazma
`meta_signal_logger`'ın kendi 20 dk aralığıyla sınırlı, DB şişmez).
Artık ölçüm görünürlükten bağımsız ve örneklem yansız.

## 5. Ders
**Bir kapı her tarama turunda ateşliyorsa, kayıt sayısı olay sayısı DEĞİLDİR.**
İstatistik hep bağımsız olay üzerinden yapılmalı. Bu hata p değerini 4 kat
büyüklük mertebesi yanlış gösterdi (1e-10 → 0,022) ve canlı bir kuralı
haksız yere açtırdı.
