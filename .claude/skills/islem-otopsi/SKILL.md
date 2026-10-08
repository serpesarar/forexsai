---
name: islem-otopsi
description: Bot işlemlerinin derin otopsisi — her SL NEDEN oldu, her TP NASIL oldu; hacim (SL olurken hacim düşüyor mu), kırılma/diverjans, erken uyarı, rastgele-giriş plasebosu ve SL/TP geometri karşı-olgusuyla her şeyi birbirine kıyaslayıp anlam + önlem sentezi yazar. "işlemleri analiz et", "neden SL oldu", "SL/TP otopsisi", "bot işlemleri", "trader bot analizi", "/islem-otopsi NDX 7" gibi isteklerde kullan. Rutin UI/sinyal işi için değil.
---

# İşlem Otopsisi (`/islem-otopsi`)

Kullanıcı argümanları: `$ARGUMENTS` (boş olabilir; doğal dil de olabilir: "nasdaq son 7 gün vixreg").

Motor salt-okumadır: Supabase `bot_trades` (gerçek MT5 kapanışları) + `bot_entry_fingerprints` +
`indicator_snapshots` (broker 1m, tick hacmi) okur; `output/islem_otopsi/` altına yazar. **Emir açmaz,
kapı/bayrak/config değiştirmez, süreç yeniden başlatmaz.** Bu skill'in işi ölçmek ve anlamlandırmaktır;
canlıya dokunan her öneri GÖLGE → canlıya alma kartı (CLAUDE.md 2. KURAL) yolundan geçer.

## 1. Argümanları komuta çevir

| Kullanıcı der ki | Bayrak |
|---|---|
| NDX / nasdaq / NAS100 · DAX / GER40 · USOIL / petrol / WTI · XAU / altın (virgülle birden fazla) | `--symbol NDX` (yoksa `all`) |
| "son 7 gün", "bu hafta" (=7), "bugün" (=1) | `--days 7` (varsayılan 14 = odak penceresi) |
| VIXREG, MOMSR (momentum/SR), CHREV, DAYCOMBO, REENTRY, DECIDER, USOIL_BRK | `--family VIXREG` |
| "şu tarihten beri" / ileri doğrulama | `--since 2026-10-07T00:00:00+00:00` |
| "daha uzun geçmişle kıyasla" | `--base-days 180` (varsayılan 120 = kıyas tabanı) |
| "tüm kartlar", "grafik çok" | `--max-cards 200 --trade-charts 20` |
| belirli işlem(ler) — "dünkü iki SL", ticket/pozisyon no | `--pid 397377651,397915523` (önce `bot_trades`'ten pozisyon no'yu bul: `raw->>'position_id'`) → `otopsi_<pid>.md` |
| "en baştan beri" | `--base-days 400` (bot_trades 2026-06-29'da başlıyor) |

Odak penceresi = kartlar ve "son dönem"; taban = istatistik. Taban içinde odaktan önceki kısım **keşif**,
odak **sınama** dönemidir (aday önlemler keşifte seçilir, odakta sınanır).

## 2. Çalıştır

Depo kökünden (≈10–30 sn; ilk koşu mum önbelleğini doldurur):

```bash
python3 -m scripts.islem_otopsi --symbol <SEMBOL|all> --days <N> [--family <AİLE>]
```

Son satır `RAPOR: <klasör>/rapor.md` verir. Çıkış kodları: `0` tamam · `2` **saat ekseni MISALIGNED** →
DUR, analizi okuma, kullanıcıya kayma dağılımını ve olası nedeni (DST/broker saati değişimi, veri
boşluğu) bildir · `3` filtreye uyan işlem yok (sembol/aile/gün aralığını genişletmeyi öner).

## 3. Okuma sırası (önce güven, sonra anlam)

1. `ozet.json` → `clock.status`, `replay.durum`/`uyum` (≥%85 değilse §11 geometri ve plasebo sayıları
   güvenilmez — söyle), `summaries`, `placebo`, `sl_causes`, `tag_frequency`.
2. `rapor.md` §0 (güvenilirlik kapısı) → §1 özet → §2b plasebo → §3 SL → §4 TP → §5 hacim → §6 kırılma →
   §7 erken uyarı → §8 tüm özellikler → §10 adaylar → §11 geometri → §12 kartlar.
3. Odak penceresindeki en pahalı 2–4 SL'nin grafiğini **Read ile aç** (`grafikler/islem_<pid>.png`) ve
   kartıyla birlikte yorumla.
4. Öneri yazmadan ÖNCE `docs/KAPI_KAYIT_DEFTERI.md` §1 (tuzaklar), §2 (denenmiş her şey), §3 (meta-dersler)
   oku — CLAUDE.md 3. KURAL. `registry` sütunu ilgili defter kimliğini zaten gösterir.

## 4. Derin düşünme protokolü — bu soruları SIRAYLA cevapla

**A. Açıklanacak bir şey var mı?** WR'ı başabaş WR ile, ort R'yi %95 aralığı ve P(EV>0) ile oku (çıplak WR
yasak). Sonra §2b: *gerçek giriş − aynı geometride rastgele giriş* eşli farkı. Fark ≈0 ise ilk cümlen şu
olmalı: "botun giriş ANI rastgeleden ayırt edilemiyor; SL'lerin çoğu braketin (SL/TP mesafesinin) doğal
sonucu." O zaman SL'lere tek tek "neden" aramak ikincil önemdedir — kenar giriş zamanlamasında değil.

**B. Hangi SL mekanizması BOTA ÖZGÜ?** §3 mekanizma paylarını §2b'deki rastgele girişin paylarıyla kıyasla
(yön doğru / yön yanlış / hiç çalışmadı / neredeyse TP). Yalnız rastgeleden belirgin fazla olan pay botun
kendi hatasıdır; eşit olanlar mekaniktir. Sembol-yön satırlarında da aynısını yap (ör. bir taraf rastgeleden
kötüyse orası asıl sorun).

**C. Hikâye mi, istatistik mi?** Ana neden kodları kurala dayalı hükümdür. Her bayrak için §3 "bayrak
sıklığı" tablosuna bak: `SL oranı (varken)` tabandan ≥8pp yüksek değilse ve n≥15 değilse o bayrak SL'yi
AÇIKLAMAZ (TP'lerde de aynı sıklıktadır). Kartlardaki "Bayrakların geçmiş ağırlığı" satırı bunu işlem
başına söyler — "etkisiz" yazan bayrağı neden diye sunma.

**D. Hacim sorusu (kullanıcının özel sorusu) — açıkça evet/hayır/kanıt yok de.** §5 tablosu: giriş öncesi,
ilk 15 dk, işlem boyu, son üçte bir/ilk üçte bir (sönme), çıkıştan önceki 10 dk, çıkış barı, çıkışa götüren
bacak / ilk bacak, en iyi noktadaki hacim. Medyanları, AUC'yi ve q'yu sayıyla ver; `hacim_cikis.png`
grafiğini yorumla. Hatırlat: MT5 *tick* hacmi (fiyat güncelleme sayısı) — borsa hacmi değil; mevsimsel
düzeltilmiş (×1 = o saatte normal). "Hacim düşerken SL oluyor" iddiası ancak SL medyanı TP'den belirgin
düşük + q<0,10 + dönem tutarlı ise kurulabilir.

**E. Kırılma / uyumsuzluk.** §6: karar-anı olayları (RSI diverjansı aleyhte/lehte, hacim diverjansı, SL yapı
içinde, 1h trend, VIX rejimi) için SL oranı var/yok farkı. Yol olayları (yapı kırılımı, ters hacim şoku, 5m
dönüş) için TP'lerin de ne kadarında görüldüğünü mutlaka söyle — "yapı kırıldı → SL oldu" ancak TP'lerde
nadirse bir uyarı işaretidir. Kırılma ile SL arasındaki tipik süreyi kartlardan özetle.

**F. Ne zaman belli oluyor?** §7 ayrışma dakikası + `ayrisma.png`. Erken çıkış satırlarında net R negatifse
"erken kapatmak kurtardığından fazla kazanan öldürüyor" de. Defter **M9** (BE/kilit/zikzak, 487 işlem,
ELENDİ) ve **M7** (zaman stopu, X) — bunları yeniden öneri olarak SUNMA; en fazla "izleme göstergesi".

**G. Geometri.** §11: tüm SL/TP çarpanlarında `ort_r_ayni_risk` ≈0 ise "stopu genişletmek/daraltmak
kurtarmıyor" de (defter OLD-20: sorun geometri ama basit ölçekleme değil). Yön doğru SL'lerin
"yaşatacak stop" medyanını (§3) bu tabloyla birlikte oku: geniş stop yön yanlış olanlarda kaybı büyütür.

**H. Nerede yoğunlaşıyor?** §2 kırılımları + §3 hüküm×strateji tablosu: zarar hangi aile/sembol-yön/seansta?
Bir grup kapalı/yasaklı bir kapıya (defter B1, B17 vb.) denk geliyorsa işlem TARİHLERİNİ kapının devreye
giriş tarihiyle kıyasla — eski dönemi bugünün sorunu diye sunma.

**I. Aday önlemler.** §10 yalnız karar-anı özellikleri: keşifte seçildi → odakta sınandı. Bir aday ancak
odakta da `kurtarilan_r > rastgele_beklenen_r` ve pozitifse "gölgeye alınabilir" olur. Defterde aynı/yakın
fikir varsa sonucunu söyle ve tekrar önerme (3. KURAL §0.1).

**İ. Geçmiş benzerleri.** Her kartta "en benzer 10 geçmiş işlemin x'i SL (taban %y)" satırı var; `--pid`
dosyasında komşu listesi ve özellik bazında "SL'lere mi TP'lere mi benziyor" tablosu. Komşular yalnız o
işlemden ÖNCE kapanmış aynı sembol-yön işlemleridir. Değerleri tüm geçmişin 0–10. yüzdeliğinde kalan
işlem "bot bu koşulu hiç görmemiş" demektir — söyle. k=10 → ipucu, kanıt değil.

**J. İşlem işlem.** Odak penceresindeki her SL için 1–2 cümle: ana neden + bu nedenin istatistiksel
ağırlığı (C) + çıkış sonrası hüküm. Benzer olanları grupla. TP'ler için temiz/acı çektiren/şanslı ayrımı.

## 5. Kullanıcıya çıktı (Türkçe, düz anlatım)

1. **Kısa hüküm** (3–5 madde; en önemli bulgu ilk): giriş zamanlaması rastgeleden iyi mi, zarar nerede
   yoğun, hacim sorusunun cevabı, en güçlü ve tutarlı karar-anı işareti.
2. **SL'ler neden oldu** — mekanizmalar sayı + $ + R ile, "bota özgü / mekanik" ayrımıyla.
3. **TP'ler nasıl oldu** — temiz/acı çektiren/şanslı payları; TP sonrası devam (hedef erken mi).
4. **Hacim** — açık cevap + sayılar.
5. **Kırılmalar ve uyumsuzluklar** — hangisi gerçekten uyarı işareti, hangisi TP'lerde de var.
6. **Önlemler — üç kademe:** (a) *kanıtlı ve uygulanabilir* (genelde YOK — öyleyse açıkça söyle);
   (b) *gölgeye alınabilecek aday* (kural, keşif/odak sayıları, ileri doğrulama komutu
   `--since <bugün>`); (c) *denenmiş ve elenmiş — yapma* (defter kimliğiyle).
7. **Odak penceresi işlem tablosu** (pid, sembol-yön, aile, sonuç, R, $, ana neden).
8. Rapor yolu: `output/islem_otopsi/<klasör>/rapor.md` (markdown linki).

Aynı sentezi `<klasör>/SENTEZ.md` olarak da yaz. Her sayıyı rapordan al — tahmin etme, yuvarlarken
yönünü bozma; n ve güven aralığını ver; "kanıtlandı" deme (en fazla "bu veride tutarlı").

## 6. Kayıt (CLAUDE.md 1. ve 3. KURAL)

- Yeni bir aday önlem veya test edilmemiş fikir çıktıysa backlog'a ekle:
  ```bash
  python3 backend/scripts/evolution_session_log.py "islem_otopsi: <kısa bulgu>" --backlog "<başlık>|<keşif/odak sayıları + ileri doğrulama komutu>|experiment|medium"
  ```
- Bir kapı/filtre fikri sınandıysa (aday ELENDİ dahil) `docs/KAPI_KAYIT_DEFTERI.md` §2.7'ye satır ekle.
- Kod değiştirmediysen commit/push gerekmez.

## 7. Tuzaklar (bu projede yaşandı)

- `bot_trades` zamanları broker saatinde (UTC+3; Kasım'da +2). Motor işlem başına fiyat eşleştirmesiyle
  ölçer; `clock.offsets` beklenmedik bir değer gösterirse (ör. 0 ve −3 karışık) kullanıcıya söyle.
- `sl0/tp0` = pozisyonu açan emrin ilk planı. BE/iz ile taşınan stoplar `BE`/`IZ_SL`/`KISMI_SL` sınıfıdır,
  tam SL değildir.
- Lot zamanla değişti (5 → 30): dönemler arası $ kıyası yanıltır; **R** esas birimdir.
- Kaynak tablo donmuşsa (ajan düşmüş) son işlemler eksik görünür: `islemler.csv` en yeni `exit_utc` çok
  eskiyse `python3 scripts/remote.py health` ile ajan kalp atışına bak ve söyle.
- Tek işlemde nedensellik kanıtlanamaz; kart bir hükümdür, toplu tablo kanıttır.
- Daha ince veri (gerçek spread, MT5 M1, bot logu) gerekiyorsa `python3 scripts/remote.py sh ...` ile
  kutudan salt-okuma çek (bkz. `research/bot_loss_veto_20261002/pull.py` kalıbı) — emir/süreç komutu YOK.
