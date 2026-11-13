# OK-01 — Bot ↔ Decider ortak kazanç kapısı (ön kayıt, 2026-11-13)

Kullanıcı hedefi: son 3 ayın tüm işlemleri (kutudaki bot + Claude decider), ortak kazandıran noktayı
bul veya kaybettirenleri tespit edip engelle. Defter okundu (§0, §1, §2.1–2.7, §2.35, §3). İşlem-düzeyi
gösterge vetoları daha önce ileri dönemde çöktü (IO-11, IO-26, IO-12, DX-07) → **tekrarlanmıyor**.
Bu çalışmanın yeni bilgisi: iki ajanın **birbirinin kararını** kanıt olarak kullanması (defterde yok),
aile/sembol-yön tahsisinin 3 aylık güncel karnesi ve decider'ın kendi mean-rev kapısının (`gate_fired`)
açılan kararlar içinde ayırıcılığı.

Sonuçlara bakılmadan yazıldı (yalnız sayımlar ve aile toplamları görüldü — 02_summary.py çıktısı).

## Veri
- `bot_trades` → pozisyon başına (otopsi yükleyicisi), açılış 2026-06-25 → 2026-11-13. R = yön × (kapanış − giriş) / |giriş − ilk SL|.
  Bot saati broker: UTC+3 (≤ 2026-11-01), UTC+2 (sonrası) — decider icralarının günlük zamanıyla eşleştirilerek doğrulanır.
- `decider_journal` 10.315 karar; OPEN için `cf_pnl_r` (kendi geometrisi TP 1×ATR / SL 1,5×ATR, RR 0,67, başabaş %60),
  WAIT için `counterfactual.dir` yönünde aynı simülasyon.
- Bağımsızlık: decider kararları aynı sembol-yön-30 dk epizoduna indirgenir (E6); bootstrap gün blokludur.

## Hipotezler
**H1 — Decider onayı bot için kapı mı?** Her bot girişi için aynı sembolde girişten önceki 30 dk içindeki son decider kararı:
AGREE (OPEN aynı yön) · OPPOSE (OPEN ters yön) · WAIT_SAME (WAIT, cf yönü aynı) · WAIT_OPP · NONE.
Birincil: R(AGREE) − R(diğer) ve R(OPPOSE) − R(diğer).

**H2 — Bot onayı decider için kapı mı?** Her decider OPEN epizodu için: BOT_SAME (karar anında bot aynı sembol-yönde açık pozisyonda
veya önceki 60 dk'da aynı yönde açtı) · BOT_OPP · BOT_NONE. Birincil: cf_pnl_r(BOT_SAME) − cf_pnl_r(BOT_NONE), BOT_OPP − BOT_NONE.

**H3 — Kaybettireni engelle (tahsis).** Her ajan × aile × sembol × yön (n ≥ 30, 2026-08-13 → 11-13): iki kronolojik yarıda da ort R < 0
ve gün-blok bootstrap P(ort<0) ≥ %90 → ENGEL adayı; 06-25 → 08-12 ön döneminde de < 0 ise sınıf B, yoksa C.
Decider için birincil ölçü journal OPEN epizodları (icra edilenler bunun alt kümesi), ikincil gerçek icra.

**H4 — Decider'ın kendi kapısı (`gate_fired`) açılan kararlar içinde ayırıyor mu?** Sembol-yön başına OPEN epizodlarında
gate_fired=True vs False.

## Geçme ölçütü (hepsi)
1. Etiketli grup n ≥ 30 bağımsız karar (H2/H4 epizod; H1 pozisyon).
2. Fark iki kronolojik yarıda da aynı işaretli.
3. Gün-blok bootstrap (2.000) P(fark doğru işaretli) ≥ %95.
4. Plasebo: etiket aynı gün içinde rastgele kaydırılmış (zaman ±2–6 s döngüsel) 500 tekrarda gerçek fark ≥ %95 yüzdelik (H1/H2).
5. Portföy etkisi: kapı uygulanmış toplam R ve $ (bot için gerçek lot), boşalan zaman dahil değil (E19 uyarısı rapora yazılır).
Geçen → GÖLGE + ileri kart (yeni kapı canlıya 2. KURAL olmadan girmez). Kısmen geçen → C. Diğerleri X.

## Çoklu sınama
H1 2 karşılaştırma × H2 2 × H3 ~12 grup × H4 ~6 grup. Kazananın seçim yükü raporda belirtilir; H3/H4'te aynı aramanın
dairesel-kaydırma boş dağılımı ile "en iyi" sonucun yüzdeliği verilir.

## EK-1 (H1–H4 sonuçlarından SONRA, H5 sonuçlarından ÖNCE yazıldı)
H1/H2 geçmedi; H3'te üç decider grubu ENGEL ölçütünü geçti; H4 sınanamadı (açılan kararların %95+'i zaten gate_fired).
**H5 — Decider çıkış politikası.** journal `exit_grades` (ATR biriminde, brüt) her OPEN epizodu için ~7–12 çıkış politikasını
hesaplıyor. Maliyet = `spread_atr` (her işlem bir kez). Sembol-yön başına her politika vs taban `fixed_1.0/1.5`
(decider'ın canlı geometrisi). Geçme: (i) 08-13→11-13 iki yarıda da politika − taban > 0, (ii) gün-blok P ≥ %95,
(iii) 06-25→08-12 ön döneminde de > 0, (iv) R yerine ATR/işlem net beklenti > 0 (yalnız tabandan iyi olmak yetmez).
Seçim yükü: tüm (grup × politika) hücreleri raporlanır; kaç hücrenin geçtiği, aynı ölçütleri tarihleri gün içinde
karıştırılmış (yarı/ön dönem etiketi rastgele gün ataması) 200 plaseboda kaç hücrenin geçtiği ile kıyaslanır.

## EK-2 (H5 sonucu 0/25 görüldükten SONRA, H6 sonuçlarından ÖNCE)
**H6 — Mekanik mean-rev tetiği seans/saat bağımlı mı?** Popülasyon: journal'daki TÜM kararlar (OPEN + WAIT) içinden
`gate_fired=True` olanlar (LLM takdirinden bağımsız mekanik tetik), cf yönünde decider geometrisi, net R (`cf_pnl_r_net`),
sembol-yön-30 dk epizod. Kova: UTC saati 4'lü dilim (00-04, 04-08, 08-12, 12-16, 16-20, 20-24) × sembol-yön.
Geçme: n ≥ 40, üç dilimin (06-25→08-12 / 08-13→09-30 / 10-01→11-13) ÜÇÜNDE de net R > 0, gün-blok P(>0) ≥ %95.
Seçim yükü: hücre sayısı raporlanır; aynı ölçüt saat etiketi gün içinde rastgele karıştırılmış 200 plaseboda.

## EK-3 (H6 sonucu görüldükten SONRA, H7'den ÖNCE)
H6: mekanik tetik 6/6 sembol-yönde net eksi; saat hücresi 1/28 (plasebo ort 0,45) → X.
**H7 — LLM seçimi mekanik tetiğe değer katıyor mu? (doğal deney)** gate_fired epizodlarını üçe ayır: OPEN (LLM açtı),
LLM_WAIT (gerçek LLM bekle kararı), SAHTE_WAIT (CLI hatası/timeout/spawn — piyasadan bağımsız, LLM görüşü yok = kontrol).
Kural kapısı WAIT'leri (seans/skor/KANIT KURALI) ayrı tutulur. Karışıklık (E29) için kıyas **aynı ISO haftası** içinde yapılır:
hafta başına ort(OPEN) − ort(kontrol), haftalar n'e göre ağırlıklı; hafta-blok bootstrap. Geçme: sembol-yön başına
OPEN − SAHTE_WAIT > 0 ve OPEN − LLM_WAIT > 0, iki kronolojik yarıda aynı işaret, P ≥ %95, ≥ 30 OPEN epizodu.

## EK-4 (H7 X görüldükten SONRA, ters çevirme sonucundan ÖNCE)
**H8 — Mekanik tetiğin tersi (momentum aynası).** Aynı epizodlar; ters işlem = karşı yön, TP = orijinal SL mesafesi (1,5 ATR),
SL = orijinal TP mesafesi (1 ATR). Ters ATR sonucu = −1,5·cf_pnl_r − spread_atr (spread bir kez daha ödenir); R birimi 1 ATR.
Geçme: sembol-yön başına üç çağda da > 0, gün-blok P ≥ %95, n ≥ 100. QS-13/OLD-18 uyarısı: ters çevirme çoğunlukla bedava değil.

## EK-5 (H8 görüldükten SONRA)
H8: NDX BUY tetiğinin tersi üç çağda + ama P 0,917 (<0,95), seçilmiş (6 gruptan), ve OLD-15/E16 (mom_cont sızıntısız −0,08R) ile aynı aile → X.
**H9 — Kendi karnesi anahtarı (bot aileleri).** Her bot aile-sembol-yön dizisinde (06-29→11-13), işlem t'nin R'si ile aynı dizinin önceki
k ∈ {3,5,10} işleminin ort R'si; havuzlanmış Spearman ve "önceki k ort > 0 ise işlem al" kuralının toplam R'si vs hepsini al.
Geçme: üç k'nın üçünde de kural > hepsi, ilk ve ikinci yarıda da, havuzlanmış Spearman > 0 (P ≥ %95, aile-içi karıştırma plasebosu 1.000).

## EK-6 (H9 sonucu görüldükten SONRA — ters yönde anlamlı; bu ek post-hoc bulguyu DOĞRULAMAK için)
H9: "iyi seriden sonra al" kuralı her k'da kaybettirdi; Spearman −0,09/−0,09/−0,14, aile-içi karıştırma plasebosunun %0–1,1 yüzdeliği
(yani anlamlı NEGATİF seri bağımlılık). Bu post-hoc bir yöndür; kabul için:
**H10 — "Kendi karnesi geri dönüşü" (aile performansı ortalamaya döner).** Kural: aynı aile-sembol-yönde, girişten ÖNCE KAPANMIŞ son k
işlemin ort R'si ≤ 0 ise işlemi al, > 0 ise atla. k ∈ {1,3,5,10}.
Sınama sırası (sonuçlar görülmeden donduruldu):
1. Bot (nedensel yeniden hesap): her k'da atlananların ort R'si < alınanlarınkinden; iki kronolojik yarıda aynı işaret; aile-içi
   karıştırma plasebosu (1.000) gerçek farkın ≥ %95 yüzdeliğinde; en az 4 aileden 3'ünde aynı işaret.
2. **Bağımsız popülasyon — decider journal OPEN epizodları** (sonuç zamanı = entry_bar_time + bars_to_outcome×5 dk; bilinmiyorsa
   karar + 120 dk), sembol-yön dizileri, net R. Aynı ölçütler. Ayrıca decider gate_fired mekanik dizisi (OPEN + WAIT).
3. **Bağımsız popülasyon 2 — panel `prediction_logs`** (completed/stopped, atr_ladder_v1 epoch, model-sembol-yön dizileri, sonuç
   zamanı = updated_at/resolved_at) — veri erişimi varsa.
Geçme: 1 ve 2'de ölçütler; 3 destek. Mekanizma sorusu (fiyat geri dönüşü mü, bracket nedeni mi) ayrıca raporlanır.
Uyarı E102/E85: kural lot artırmaz, yalnız giriş süzer; martingal değildir.

## EK-7 (decider sonucu görüldükten SONRA, panel sonucundan ÖNCE)
Decider (H10-2): mekanik dizi farkları +0,01…+0,05 (plasebo %41–89), OPEN karışık → **bağımsız popülasyon 2'de tekrarlanmadı.**
Yapısal fark: decider/panel kararları dakikalarca çakışan yoğun diziler; bot aileleri tek-pozisyonlu seyrek diziler.
Panel sınaması iki biçimde, ikisi de raporlanır: (a) ham dizi, (b) **tek-pozisyon inceltmesi** (anahtar başına önceki sinyal
kapanmadan yenisi alınmaz — botun yapısı). Aynı (b) inceltmesi decider'a da uygulanır. Ölçütler EK-6 ile aynı.
Panel R = `signal_metrics.signal_outcome` (kanonik), sonuç zamanı `closed_at`/`exit_time`, dönem 2026-07-28 → (atr_ladder_v1 dönemi),
anahtar = model × sembol × yön.

## EK-8 (bot ayrıntısı + decider tek-poz X görüldükten SONRA; vekil sonucu görülmeden)
Bot ayrıntısı: plato k=1…12 hepsi + (k≥2: +0,07…+0,25R); k=5 gün-blok P 0,93; etki VIXREG SELL ve MOMSR'de; DAYCOMBO'da ters;
$ olarak kural −10,6k$ (büyük lotlu REENTRY/DAYCOMBO kazananlarını atlıyor). Decider tek-poz: X.
**H11 — Bağımsız 10 yıllık vekil sınama (NDX, bot yapısı birebir: tek pozisyon, 80/110 oranlı braket, sonraki bar açılışı + yarım spread).**
`ndx_sell_dusus_20261008/run.py` stratejileri (S0 taban SELL, S1 VIXREG SELL, S1b VIXREG BUY, S2 momentum SELL, S3 kanal-üst SELL)
+ ayna S2b momentum BUY (kapanış > EMA50, EMA20 > EMA50, 2 bar getirisi > 0) ve S0b taban BUY. Veri: 30m 2021-06→2026-07 (ANA),
1h 2016-05→2021-06 (ikincil, bağımsız dönem). Kural H10 (nedensel, son k kapanmış işlem ort ≤ 0 → al), k ∈ {3,5,10}.
Geçme: ANA'da havuzlanmış fark > 0 (gün-blok P ≥ %95) ve stratejilerin çoğunda + ; ikincil dönemde aynı işaret. Plasebo: işlem R'lerinin
strateji içinde karıştırılması (500). S1 (VIXREG vekili) ayrıca raporlanır.

## EK-9 (sonuç kaydı)
H11 vekil (10 yıl NDX, 7 strateji × 2 dönem): VIXREG vekilinde Δ ≈ 0/ters, taban BUY'da anlamlı ters; yalnız S3 kanal-üst SELL ANA'da +0,10
(pl %93–98) ama 1h'de tutarsız → X. Panel tek-poz (7.073 sinyal, 53 anahtar): TERS yönde (k=3 Δ −0,095R, plasebo %0) → H10 X.
Uygulanan: decider canlı izin listesinden XAUUSD:BUY çıkarıldı (H3, B).

## EK-10 (OK-01 kapanışından SONRA, kullanıcı "bulana kadar dur(ma)" dedi; bu sonuçlar görülmeden yazıldı)
**H12 — Farklı emtialarla birlikte: çapraz varlık hizası / gecikme yakalama.** Broker 1m (`indicator_snapshots`, gerçek UTC).
Her işlem/sinyal (sembol S, yön d, giriş t) için 30 dk pencerede yön-işaretli getiriler (ATR değil, %):
own = d·r_S(t−30m,t), peer = d·r_P(t−30m,t). Eş: NDX↔DAX, USOIL→NDX (risk eşi), XAU→NDX.
- **F1 eş hizası:** peer > 0 (eş de işlem yönünde gidiyor).
- **F2 gecikme yakalama (BİRİNCİL):** peer − own > 0 (eş, işlem yönünde S'den daha çok gitmiş → S yetişir).
- **F3 risk-off karşıtlığı (yalnız endeks işlemleri):** d·(−r_XAU) > 0.
Popülasyonlar: (A) bot pozisyonları 06-29→11-12 (NDX/DAX/USOIL), (B) panel tek-pozisyon dizisi (≈7.000), (C) decider mekanik tetik epizodları (≈2.000).
Geçme (F2 için): üç popülasyonda da ort R(F2) − ort R(¬F2) > 0; B'de iki yarı aynı işaret ve gün-blok P ≥ %95; B'de sembol bazında
çoğunluk aynı işaret. 15/60 dk pencereler ve F1/F3 duyarlılık/ikincil olarak raporlanır, seçim için kullanılmaz.

## EK-11 (H12 sonuç kaydı)
F2 (birincil): bot Δ +0,010 (P 0,58), panel Δ −0,274 (P 0,000, TERS), decider Δ −0,013 → X. Panel'deki büyük etkiler (F1 +0,11, F2 −0,27)
kendi 30 dk getirisinin beşliklerinde monoton (−0,27 → +0,34R); bot ve decider'da düz. Teşhis: panel `ml_entry_price` kayıt anındaki
fiyattan medyan 25–45 dk (p75 40–95 dk) eski → kayıttan önceki hareket sonucu mekanik belirler (E124). H10'un panel sonucu da bu yüzden
kanıt sayılmaz (bot H10 hükmü decider + 10 yıllık vekille X olarak kalır).
