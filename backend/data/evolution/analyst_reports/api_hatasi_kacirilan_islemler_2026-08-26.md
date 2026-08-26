# API Hatası Yüzünden Kaçırılan İşlemler — Geriye Dönük Hesap

**Tarih:** 2026-08-26 · **Kapsam:** decider_journal tamamı (4.313 karar, Haziran–Ağustos)

## Soru

API/kota hatası yüzünden düşen decider kararları yüzünden kaç işlem kaçtı, ne kaybettirdi?

## 1. Hata hacmi ve zaman çizelgesi

855 karar hata ile düştü (journal'ın %19,8'i).

| ay | toplam karar | hata | hata oranı | 429 kota |
|---|---|---|---|---|
| 2026-06 | 210 | 6 | %3 | 0 |
| 2026-07 | 2.852 | 317 | %11 | 2 |
| 2026-08 | 1.251 | 532 | **%43** | **257** |

Hata türü: `diğer exit` 498 (%58) · `429 kota` 259 (%30) · `timeout` 95 (%11) · `parse fail` 3.

Sembol: XAUUSD 288 · NDX 247 · GDAXI 220 · USOIL 100.

**Ağustos'ta patlama var** — kota tükenmesi 21–25 Ağustos'ta yoğunlaştı (bkz. CLAUDE.md
maliyet denetimi: her çağrıda CLAUDE.md prompt'a yükleniyordu, çağrı başına ~$0,27 israf).

## 2. KRİTİK ÇERÇEVE: decider emir GÖNDERMİYOR

`run_decider.execute()` hâlâ **stub** — "shadow doğrulanmadan canlı emir gönderilmez".
Yani düşen kararların çoğu **doğrudan para kaybı değil**. Gerçek para kanalı tek:
botun `TQ_DECIDER_APPROVAL` köprüsü — çukur pencerelerde botun oyu yetmezse, decider'ın
taze (≤45 dk) aynı-yön OPEN kararı "çok emin" onayı sayılır ve **fail-closed**'dur.

## 3. Gölge taraf — kaçırılan gölge işlemler

Hücre-eşleştirmeli tahmin (sembol × kapı_ateşledi × rev_chan bandı; hatasız satırlardaki
gerçek LLM açma oranı ve gerçek sonuçları kullanılarak), 4.000 turlu bootstrap:

| ölçüt | değer |
|---|---|
| beklenen kaçırılan işlem | ~367 |
| net sonuç (medyan) | **+1,7R** |
| %95 aralık | [−28,6R, +32,3R] |
| P(kârlı olurdu) | %54 |

**Sıfırdan ayırt edilemez.** Sebebi, decider'ın kendi kenarının zaten başabaş olması:
LLM'in gerçekten açtığı 1.129 işlem toplam −3,9R (ort −0,003R).

> Yan bulgu — LLM'in seçiciliği gerçek değer taşıyor: reddettiği kurulumların
> karşı-olgusu **−184,8R** (n=1.817, ort −0,102R), açtıkları ise başabaş.
> Yani "beklemek" doğru karardı; hata yüzünden beklenenler de büyük ihtimalle
> zaten beklenecekti.

## 4. Gerçek para tarafı — bot engellemeleri

Bot logunda (`demo_bot.log`) "decider onayı yok → açılmadı" satırları: 2.008 ham satır →
**53 ayrı epizot** (aynı sembol/yön/aile 30 dk birleştirme; bot aynı kurulumu ~70 sn'de
bir yeniden logluyor, ham sayım 38× yanıltıyor).

Bu 53 epizodun sebep atfı (karar anından 45 dk geriye, aynı sembol):

| sebep | epizot |
|---|---|
| decider o sembolü hiç değerlendirmedi ("ilginç" değildi) | 34 |
| decider meşru WAIT dedi (hata değil) | 11 |
| **sadece hata vardı → API hatasına atfedilebilir** | **6** |
| decider uygun OPEN vermiş (bot başka sebeple açmadı) | 1 |

### Atfedilebilen 6 engellemenin karşı-olgusu

| tarih | sembol | yön | çukur | sonuç |
|---|---|---|---|---|
| 08-07 14:28 | GDAXI | BUY | Cuma | LOSS −1,00R |
| 08-17 16:12 | NDX | SELL | 16 UTC | WIN +0,67R |
| 08-21 00:01 | XAUUSD | BUY | Cuma | LOSS −1,00R |
| 08-21 07:37 | XAUUSD | BUY | Cuma | WIN +0,67R |
| 08-21 15:56 | XAUUSD | BUY | Cuma | WIN +0,67R |
| 08-21 17:59 | GDAXI | BUY | Cuma | WIN +0,67R |
| | | | **net** | **+0,68R** |

Ağustos bot işlemlerinde 1R ≈ $184 (ort. kaybeden işlem büyüklüğü) →
**≈ +$125 kaçırılmış kâr.** n=6, istatistiksel olarak gürültü.

## 5. Sonuç

**Para kaybı ihmal edilebilir.** Gölge tarafta ~367 işlem sıfır beklentiyle kaçtı;
gerçek para tarafında yalnız 6 işlem engellendi, toplam etki ≈ +$125.

**Asıl zarar VERİ kaybı:** 855 karar gözlemi hiç üretilmedi. Decider'ın kendi
değerlendirmesi (WR/EV, drift nöbetçisi, kalibrasyon) bu örneklem üzerinden
yürüdüğü için istatistiksel güç kaybedildi — Ağustos'ta kararların %43'ü eksik.

**Aksiyon:** maliyet kökü zaten kapatıldı (sandbox cwd, çağrı başına $0,274 → $0,068;
kutuda $0,0196). Kalan eksik: 429 oranı panelde **görünmüyor** — decider saatlerce
karar üretmeden "çalışıyor" görünebiliyor. Backlog: `bl_f692130dcd` (high).
