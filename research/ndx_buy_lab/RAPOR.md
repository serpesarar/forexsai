# NDX BUY — Neden Kazanmıyor, Nasıl Kazandırılır

**Tarih:** 2026-07-28 · **Kapsam:** NDX.INDX long tarafı
**Veri:** 11 yıl saatlik (60.052 bar), 3.4 yıl 15m (80.000 bar), 5.5 ay 1m (163.654 bar),
15.351 gerçek pulse sinyali, 341 gerçek MT5 pozisyonu
**Yöntem:** sızıntısız replay → kronolojik bölme → 7 paralel madenci → 4 bağımsız çürütücü denetçi

---

## 0. Dürüstlük sözleşmesi

| Kural | Uygulama |
|---|---|
| Açık mum yasak | Bar damgası = AÇILIŞ; karar anında ancak `damga + tf ≤ t` olan bar kapanmıştır (`merge_asof`) |
| Giriş sinyalden SONRA | Giriş = sinyalden sonraki ilk 1m barın açılışı |
| Aynı barda TP+SL → SL | Konservatif; taban dahil her varyantta aynı. **Denetimde bunun düşük RR'yi orantısız cezalandırdığı bulundu → 15m hakemiyle kalibre edildi** |
| Sürtünme | **1.3 puan** — uydurma değil, ölçülmüş: MT5 1m spread medyanı 1.3 puan; 218 gerçek SL/TP kapanışının 218'i hedef seviyeden **0.000 puan** sapmayla dolmuş |
| Makro 1 gün gecikmeli | Günün kapanışı o gün bilinemez |
| Eşik seçimi yalnız TRAIN | TRAIN → 2 gün purge → VAL → purge → TEST; TEST'e bir kez bakıldı |
| Mutlak fiyat seviyesi yasak | `close < 29.000` rejimi ezberler; yalnız ölçeksiz özellikler |
| Örtüşen etiket i.i.d. değil | Tüm GA/p değerleri **gün- veya hafta-bloklu** bootstrap; etkin gün sayısı ayrıca raporlandı |
| Sayı uydurma yok | 82 madenci kuralının TRAIN/VAL sayıları bağımsız yeniden hesaplandı → **72/72 birebir tuttu** |
| **Kendi bulgularımı çürütmeye çalıştım** | 4 bağımsız denetçi ajan; **3 ana iddiam çürütüldü, 1'i zayıfladı** — hepsi aşağıda |

---

## 1. ⚠️ ÖNCE BU: 3 SAATLİK ZAMAN DAMGASI HATASI (canlı sistemi ilgilendirir)

`candle_cache`'e yazılan barların zaman damgası **MT5 broker sunucu saati** (kış UTC+2 /
ABD-yaz UTC+3) iken **UTC olarak etiketleniyor**. `prediction_logs.created_at` ise gerçek UTC.
Yani sinyaller ile mumlar aynı saat ekseninde değil.

**Kaynak:** `yeni deneme/data_recorder.py:74` →
`datetime.fromtimestamp(epoch, tz=timezone.utc)`. MT5'in `copy_rates` `time` alanı epoch
**sunucu saatindedir** — UTC değil. (Bilinen bir MT5 tuzağı.)

**Üç bağımsız kanıt:**
1. ABD nakit açılışı (13:30 UTC) 1m barlarda **16:30 etiketinde** patlıyor.
2. Panelin kendi kaydettiği anlık fiyat (`ml_entry_price`, gerçek UTC) ile bar kapanışı
   arasındaki medyan mutlak fark: offset 0'da **71.8 puan**, offset −180 dk'da **19.9 puan**.
3. Ay bazında ölçülen offset DST ile tutarlı: 03-08 öncesi −120 dk, sonrası −180 dk,
   **2026-07-16'dan itibaren 0** (o tarihte bir düzeltme inmiş görünüyor).

**Etkisi:**
- Sinyal↔bar bağı kuran **her** analizde işlem sinyalden 3 saat ÖNCE açılıyor, özellikler
  3 saat bayat. (Bu laboratuvarın ilk sürümü dahil — düzeltilip yeniden koşuldu.)
- ⚠️ **`bot_router.py`'de kayıtlı "momentum filtresi: filtresiz TEST %51.4 → filtreli %78.6"
  doğrulaması büyük olasılıkla aynı hatanın ürünüdür.** Denetçi, kaymış eşlemeyle panelin
  snapshot'ını kullanarak **%76.9** üretti ve aynı kurgunun 240 dakikada "+191 puan ileri
  getiri öngördüğünü" gösterdi — fiziksel olarak imkânsız, klasik sızıntı imzası
  (özellikler işlemin ilk 3 saatini biliyor). **Canlı NDX BUY kapısı bu doğrulamaya
  dayanıyor; denetlenmeli.**
- Yalnız bar-bar analizleri (geometri taraması, uzun ızgara) iç tutarlı → geçerli.

Düzeltme laboratuvarda `fix_time.py` ile yapıldı ve doğrulandı (düzeltme sonrası en yüksek
1m aralık saati 14 UTC — doğru).

---

## 2. Gerçek durum — kullanıcının gözlemi doğru mu?

### Canlı MT5, 2026-06-29 → 07-28, 341 pozisyon (R cinsinden, lot bağımsız)

| Yön | Scope | n | toplam R | WR |
|---|---|---|---|---|
| BUY | MOM/SR | 15 | **−0.72R** | %46.7 |
| BUY | CHREV | 13 | **−0.92R** | %53.8 |
| BUY | VIXREG | 3 | +2.18R | %100 |
| SELL | VIXREG | **178** | +1.24R | %58.4 |
| SELL | CHREV | 9 | −2.10R | %44.4 |

**Kısmen haklısınız, ama sebep sandığınız gibi değil.** BUY'ın düzenli çalışan iki scope'u
kaybediyor; toplam BUY kârı 3 şanslı VIXREG işleminden geliyor. SELL ise 178 işlemle
**işlem başına +0.007R** üretiyor — istatistiksel olarak sıfır. SELL'in görünen üstünlüğü
**hacimden** geliyor, verimden değil. 11 yıllık ölçümde NDX short **hiçbir geometride**
+EV değil (RR 0.73'te 0/11 yıl).

---

## 3. Ne denedim, ne çıkmadı (negatif sonuçlar da sonuçtur)

7 hipotez ailesi paralel tarandı → **82 aday kural** → 5 kapılı bağımsız denetim
(üretilebilirlik / etkin gün / kör TEST / 3 yıllık holdout / gerçek sinyal):

| Aile | Aday | Kör TEST'i geçen |
|---|---|---|
| trend yapısı · geri dönüş · volatilite · seans · makro · mikroyapı · günlük rejim | **82** | **0** |

En iyi TRAIN/VAL kuralları TEST'te **tam ters** döndü:

| Kural | TRAIN lift | VAL lift | **TEST lift** | placebo p |
|---|---|---|---|---|
| `H4 yükseliş & H1 sakin` | +0.148 | +0.087 | **−0.172** | 0.999 |
| `H4 yükseliş & H1&M15 sakin` | +0.125 | +0.119 | **−0.240** | 0.999 |
| `M15 geri çekilme & H4 sağlam` | +0.213 | +0.093 | **−0.066** | 0.671 |
| `makro: faiz düştü & kredi alındı` | +0.290 | +0.274 | **−0.175** | 0.906 |

Sebep: TRAIN+VAL yükselen tape, TEST (12 Haz–25 Tem) düşen tape. Kurallar rejimi ezberledi.
Makro ailesinde ek tuzak: `n_train=1.561` görünüyor ama **etkin gün 21** — günlük özellik
tüm günü sabitliyor. Gün-bloklu bootstrap yakaladı, ham n yakalamazdı.

**Rejim kapısı da kurtarmıyor:** 124 kapı×geometri kombinasyonunun hiçbiri 11 yılın 11'inde
+EV vermiyor. Yüksek-RR long'un en kötü yılı 2022 (ayı piyasası) ve hiçbir kapı bunu
pozitife çevirmiyor.

---

## 4. Ayakta kalan bulgular (denetimden geçenler)

### 4.1 Botun geometrisi yapısal olarak kaybettiriyor

11 yıl (2016-05 → 2026-07), saatlik, **gerçekçi 1.3 puan sürtünme**, hafta-bloklu GA:

| Geometri | WR | EV/işlem | %95 GA | P(EV>0) |
|---|---|---|---|---|
| **ATR 0.727/1.0 ≈ botun 80/110'u** | %57.9 | **−0.0562R** | [−0.068, −0.044] | **%0.0** |
| ATR 1.0/1.0 | %50.8 | −0.0396R | [−0.055, −0.024] | %0 |
| ATR 1.5/1.0 | %41.3 | −0.0176R | [−0.039, +0.004] | %8.9 |
| ATR 2.0/1.0 | %34.4 | −0.0016R | [−0.028, +0.025] | %46 |
| ATR 3.0/1.0 | %24.3 | +0.0296R | [−0.006, +0.066] | %91.5 |
| ATR 4.0/1.0 | %16.4 | +0.0509R | [+0.009, +0.093] | %97.6 |

Botun geometrisi **11 yılda tek bir belirsizlik bırakmadan −EV**: GA'sı sıfırın tamamen
altında. Bu raporun en kesin sayısı.

> **Denetçi düzeltmesi (kabul edildi):** "Yüksek RR +EV'dir" ifadem **fazla iddialıydı**.
> Sürükleme çıkarılmış seride (her yılın ortalama log-getirisi sıfırlanır, bar-içi şekil korunur)
> **tüm geometriler negatif** (−0.112 … −0.144R) ve aralarındaki fark yok olur. Yani yüksek RR
> kendi başına kenar ÜRETMİYOR; NDX'in yukarı sürüklenmesine **daha az karışıyor**.
> Aynı girişlerden TP/SL koymadan 24 saat tutmak +0.216R veriyor — her geometriden iyi
> (ama sınırsız risk taşıyor, 2022'de −0.49R/işlem). Doğru ifade: **geometri kenar kaynağı
> değil, kenar KAYBI kaynağıdır; RR 0.73 bu kaybın en büyük olduğu ayardır.**

### 4.2 Momentum filtresi GERÇEK bir kenar — ama hedefi yanlış yerde

Bu, raporun en önemli olumlu bulgusu ve **sürükleme testinden geçen tek şey**.

3.4 yıl (2023-03 → 2026-07), 79.902 deneme, 1.3 puan sürtünme,
**saat-eşitlenmiş taban** (pulse seans saatlerinde yoğunlaşır; eşitlenmezse NDX'in gece
sürüklenmesi sahte asimetri üretir), hafta-bloklu GA:

| Geometri | Kapı | EV | %95 GA | P(EV>0) | **saat-eşitlenmiş lift** |
|---|---|---|---|---|---|
| Bot bugün (0.67/0.92 ATR) | yok | −0.0199 | [−0.040, +0.000] | %5 | — |
| Bot bugün | **MOM** | +0.0124 | [−0.016, +0.040] | %77 | +0.034 |
| **ATR 2.0/1.0** | yok | +0.0190 | [−0.032, +0.068] | %74 | — |
| **ATR 2.0/1.0** | **MOM** | **+0.0790** | [+0.008, +0.148] | **%96.4** | **+0.059** |
| **ATR 2.0/1.0** | **K1 & MOM** | **+0.0889** | [+0.016, +0.163] | **%97.8** | **+0.067** |
| ATR 3.0/1.0 | MOM | +0.1106 | [+0.021, +0.194] | %97.9 | +0.051 |

**Sürükleme çıkarılmış seride bile MOM'un saat-eşitlenmiş lift'i +0.054R olarak ayakta
kalıyor** (taban −0.080 iken MOM −0.024). Yani bu, beta değil; gerçek koşullu bir kenar.

**Saat düzeltilmiş gerçek pulse sinyalleriyle teyit** (5.5 ay, n küçük):
ATR 2.0/1.0'da MOM geçen NDX BUY epizodları **EV +0.344R, n=72, 42 gün,
gün-bloklu GA [+0.053, +0.626], P(EV>0)=%97.7**; MOM elenenler −0.162R.
Botun bugünkü geometrisinde aynı filtre: **+0.003R = hiçbir şey**.

**Mekanizma:** filtre "momentum devam edecek" der; bot ise devamı beklemeden
**0.67 ATR**'de kâr alır. Filtre haklı, hedef yanlış yerde.

### 4.3 K1 kapısı — mütevazı ama tutarlı

```python
K1 = not (H1_ADX > 25 and H1_eksiDI > H1_artiDI)      # güçlü H1 düşüş trendine long açma
```
11 yıl, RR 2.0: EV +0.041 → **+0.059**, kapsam %74, **10/11 yıl pozitif**, gün-bloklu
plasebo **p=0.028**. MOM ile birlikte +0.079 → +0.089. Aynanın SELL versiyonu hiçbir
fayda vermiyor → simetrik bir "trend filtresi" değil, long'a özgü.

> **Denetçi uyarısı (kabul edildi):** 27 kapılık aile içinde çoklu-test düzeltmesiyle
> tek başına anlamlılığı zayıflar. Ana kural değil, **MOM'un üstüne mütevazı ek** olarak
> raporlanmalıdır.

### 4.4 Pulse sinyalleri seçim değeri katmıyor (iki yönde de)

İlk ölçümüm "pulse SELL değer katıyor, BUY katmıyor" idi. **Denetçi bunu çürüttü ve
haklıydı:** epizodların %84'ü RTH'te üretilirken ızgara 24 saate eşit dağılıyor; NDX'in
gece yukarı sürüklenmesi tek başına ızgara SELL'i kötü, ızgara BUY'ı iyi gösteriyor.
Saat eşitlenince fark +0.062 → +0.020'ye, RTH-only kıyasta −0.008'e (BUY lehine) dönüyor;
gün×saat eşitlendiğinde pulse SELL rastgele girişten **daha kötü** (−0.079R, P(>0)=%1.4).
Sızıntısız ileri-yönlü plasebo ("sinyali gör, sonra gün içinde rastgele bir an aç")
pulse'un kendi zamanlamasını **%96** oranında yeniyor.

Saat düzeltilmiş kendi ölçümüm de aynı yere çıkıyor: bot geometrisinde
BUY seçim değeri −0.028R, SELL −0.036R. **Ne BUY ne SELL sinyali zamanlama değeri katıyor.**
Değerin geldiği yer sinyal değil, **filtre + geometri**.

---

## 5. Öneriler (UYGULANMADI — onayınızı bekliyor)

| # | Öneri | Dayanak | Beklenen etki |
|---|---|---|---|
| **Ö1** | **`data_recorder.py:74` zaman hatasını düzelt** ve geçmiş `candle_cache` satırlarını yeniden damgala (veya offset'i belgele) | §1, üç bağımsız kanıt | Tüm sinyal↔bar araştırmaları geçerli hale gelir |
| **Ö2** | **`bot_router.py` momentum filtresi OOS doğrulamasını denetle** (%51.4→%78.6) | Denetçi aynı kurguda %76.9 ve imkânsız "+191 puan öngörü" üretti | Canlı kapının kanıt temeli netleşir |
| **Ö3** | **NDX BUY hedefini ATR'ye bağla: TP = 2.0×ATR(H1), SL = 1.0×ATR(H1)** (bugün ≈ TP 240 / SL 120 puan; şu an 80/110) | §4.1 + §4.2; 3.4 yılda 4/4 yıl +EV, P(EV>0)=%96.4 | EV +0.012R → **+0.079R** |
| **Ö4** | **Momentum filtresini KORU** — çıkarma | §4.2; sürükleme testinden geçen tek kenar | Ö3 olmadan Ö4'ün değeri yok |
| **Ö5** | K1 kapısını **gölgede** ekle (bloklamadan logla) | §4.3; 10/11 yıl, ama çoklu-test uyarısı var | +0.010R ek, kanıt biriktikçe canlıya |
| **Ö6** | SELL tarafında beklentiyi düzelt: hacim artırmak kârı artırmaz | §2 + 11 yıl short taraması | Yanlış yatırımı önler |

**Not:** NDX BUY'da canlı olan `BE@30dk + TP kaldır + 0.6R iz süren` yönetimi zaten
Ö3'ün yönünde çalışıyor (hedefi kaldırıp kazananı koşturuyor) — ölçümde bu kurulum
5.5 ayda +0.064R veriyor. Ö3 bunun **yerine değil**, SL'i ATR'ye bağlayarak
**tamamlayıcısı** olarak düşünülmelidir; ikisinin birlikte etkisi ayrıca ölçülmeli.

---

## 6. Kanıtlayamadıklarım

1. **Hiçbir giriş filtresi bulunamadı.** 82 aday, kör TEST'i geçen sıfır. "Yeni filtre
   bulundu" diyemem — bulunan şey mevcut filtrenin **doğru geometriyle** çalıştığıdır.
2. **2022 kurtarılamadı.** 124 kapı×geometri denemesinin hiçbiri 11/11 yıl +EV vermedi.
   Yeni bir ayı piyasasında bu yapı kaybeder.
3. **MOM'un gerçek-sinyal teyidi küçük örneklem** (n=72, 42 gün). İşaret 3.4 yıllık
   ızgarayla uyumlu ama büyüklük (+0.34R) muhtemelen şişkin; ızgara tahmini (+0.08R)
   daha güvenilir.
4. **Kayma varsayımı sıfır.** 218/218 gerçek dolum tam seviyeden gerçekleşti ama bu bir
   DEMO hesap. Gerçek hesapta gece boşluklarında kayma olursa tüm sayılar aşağı kayar;
   denetçi 2 puan spread + 1 puan kayma senaryosunda **tüm** geometrilerin negatife
   döndüğünü gösterdi.
5. **11 yılda yalnız 2 gerçek düşüş yılı var** (2018, 2022) ve ikisinde de tüm geometriler
   negatif. "Yapısal" nitelemesi tek yönlü bir rejimden çıkarılmıştır.

---

## 7. Üretilen dosyalar

`pull_data.py` `pull_long.py` `box_export.py` (veri) · `fix_time.py` (⚠ saat düzeltmesi) ·
`engine.py` (sızıntısız çekirdek) · `build_dataset.py` `build_grid.py` `build_long_grid.py` ·
`miner.py` `features.py` (istatistik omurgası + yasak kolon listesi) · `evaluate_rules.py`
(82 kural × 5 kapı) · `geometry_sweep.py` `geometry_sweep_1h.py` · `attribution.py`
(sürükleme atfetme + al-tut kıyası) · `regime_gate_10y.py` `final_combo_10y.py`
`long_atr_gates.py` `mom_fair_test.py` `mgmt_interaction.py` `final_signal_test.py` ·
`diagnose.py` · veri: `data/`

---

## 8. UYGULANANLAR (2026-07-28, kullanıcı onayıyla)

### Ö1 — Saat hatası ✅
| Adım | Sonuç |
|---|---|
| Kök neden | `data_recorder.py:74` MT5 **sunucu** epoch'unu UTC sanıyordu. Kutuda ölçülen offset **tam +180 dk** (sunucu UTC+3) |
| Kod düzeltmesi | Offset artık çalışma anında ölçülüyor (`tick.time − gerçek UTC`, 15 dk'ya yuvarlanır) + saatte bir tazeleniyor → DST kendiliğinden çözülür |
| Veri onarımı | 4 sembol × 6 TF MT5'ten doğru UTC ile yeniden yazıldı; **121.092 hayalet satır** silindi (MT5'in otoriter serisinde bulunmayan damgalar) |
| Doğrulama | ABD nakit açılışı artık 13-14 UTC'de en yüksek 1m volatiliteyi gösteriyor: NDX **30.0** vs 16-17'de 18.5 (onarım öncesi tersiydi). 4 sembolde de aynı |
| Yan bulgu | Kirlenme `data_recorder`'dan (24 Haz) ÖNCE de vardı — Şubat'tan beri tüm aylar kaymıştı. İki yazıcı (backend köprüsü = doğru UTC, data_recorder = broker) birbirinin üzerine yazıyordu |

### Ö2 — Momentum filtresi doğrulama denetimi ✅ → **SIZINTI DOĞRULANDI**
`audit_momo_validation.py`, aynı kurguyu iki saat ekseninde koşturur:

| | filtresiz | filtre GEÇEN | filtre KALAN | Δ |
|---|---|---|---|---|
| **Kaymış eksen (orijinal kurgu)** | %68.1 | **%84.2** | %53.0 | **+31.2 puan** |
| **Saat düzeltilmiş (dürüst)** | %54.0 | **%50.8** | %56.9 | **−6.1 puan** |

**Kesin kanıt:** kaymış eksende filtre, girişten "sonraki" 180 dakikada **+148.1 puan**
hareket öngörüyor (elenenler +0.9). Fiziksel olarak imkânsız — o 180 dakika aslında
sinyalden **önceki** 3 saattir. Momentum filtresi geleceği öngörmüyor, **geçmişi ölçüyor**.
`bot_router.py`'deki kayıt düzeltildi.

⚠️ **USOIL.FOREX:SELL (%71.4→%96.6) ve GDAXI.INDX:BUY doğrulamaları aynı kurguyu
kullanıyor → aynı sızıntıya açık, henüz yeniden ölçülmedi** (backlog'a yazıldı).

**Filtre yine de korundu** — çünkü bağımsız, bu hatadan etkilenmeyen bar-bar kanıtı var
(§4.2): 3.4 yıl, saat-eşitlenmiş, sürükleme çıkarılmış → katkı +0.054R.

### Ö3 — ATR-ölçekli geometri ✅
`forexsai_demo_bot.py`: `NDX.INDX:BUY` momentum scope'u artık **TP = 2.0×ATR(H1),
SL = 1.0×ATR(H1)** (bugün ≈ TP 240 / SL 120 puan; önceki 80/110).

- **Kapsam kilidi:** yalnız `"NDX.INDX:BUY"`. CHREV (`:CHREV`) ve VIXREG (`:VIXREG`)
  scope anahtarları farklı → etkilenmez. SELL ve diğer semboller dokunulmadı.
- **Emniyet:** SL 70-200 / TP 140-400 puan kelepçesi; ATR hesaplanamazsa sessizce
  eski sabit geometriye düşer (fail-open — işlem asla bu yüzden bloklanmaz).
- Varsayılan bot kodunda (config.py gitignore'da); kutuda `ATR_GEOMETRY_ENABLED=False`
  ile kapatılabilir.
- Bot yeniden başlatması **3 açık pozisyon nedeniyle ertelendi**, borç yazıldı —
  pozisyonlar kapanınca ajan otomatik uygular.

### Kalan riskler
1. **BE@30dk + 0.6R trail** yönetimiyle etkileşim ölçülmedi; o araştırma (`trade_mgmt_ndx`)
   MT5 işlem zamanı + candle_cache kullanıyordu — ikisi de o dönemde broker saatinde
   olduğu için **kendi içinde tutarlı**, ama yeni geometriyle etkileşimi bilinmiyor.
2. Artık candle_cache UTC, MT5 işlem export'ları hâlâ broker saatinde → **ters yönde
   aynı hatayı yapma riski**. İşlem-mum eşleştiren her analiz offset çıkarmalı.
3. Yeni geometride beklenen WR ~%34 (önceki ~%58). İlk işlemlerde "kaybediyoruz"
   izlenimi normaldir — karar n≥30'da EV ile verilmeli.

---

## 9. USOIL & GDAXI doğrulamalarının yeniden ölçümü (2026-07-28)

`audit_usoil_gdaxi.py` — aynı sinyaller, aynı geometriler, İKİ saat ekseninde.

| Scope | KAYMIŞ eksen ΔWR (orijinal kurgu) | **DOĞRU eksen ΔWR** | P(Δ>0) | Sızıntı imzası (kaymış eksende "sonraki" 180 dk) |
|---|---|---|---|---|
| USOIL:SELL | +18.5 puan (P=%100) | **+4.2 puan** | %80 | geçen −0.790% / kalan −0.042% |
| USOIL:BUY | +38.4 puan (P=%100) | **+8.3 puan** | %92 | geçen +1.000% / kalan −0.088% |
| GDAXI:BUY | +39.1 puan (P=%100) | **+2.4 puan** | %58 | geçen +0.568% / kalan −0.093% |

**Üçü de aynı sızıntıyı taşıyordu.** Kaymış eksende filtre girişten "sonraki" 3 saatin
yönünü biliyor (SELL filtresi düşüşü, BUY filtreleri yükselişi); doğru eksende bu
"öngörü" sıfıra iner. `bot_router.py`'deki %96.6 / bootstrap %99.9 / placebo p=0.000
rakamlarının hepsi bu artefaktın ürünü.

### Paraya çevirisi — botun GERÇEK geometrisiyle

| Scope | RR | başabaş WR | filtresiz | EV | filtreli | EV |
|---|---|---|---|---|---|---|
| **USOIL:SELL** | 0.70 | %58.9 | %66.3 | **+0.106R** ✅ | %68.8 | **+0.148R** ✅ |
| **USOIL:BUY** | 0.70 | %58.9 | %55.1 | −0.085R ❌ | %60.7 | **+0.011R** ✅ |
| **GDAXI:BUY** | 0.56 | %64.0 | %58.9 | −0.088R ❌ | %60.2 | **−0.067R** ❌ |
| NDX:BUY (eski) | 0.73 | %57.9 | %54.0 | −0.076R ❌ | %50.8 | −0.132R ❌ |

**Sonuçlar:**
1. **USOIL:SELL gerçekten kârlı** (+0.148R) — filtre de küçük ama pozitif katkı veriyor.
   Abartılmıştı (%96.6 değil %68.8) ama iddia ÖZÜNDE doğru. Dokunma.
2. **USOIL:BUY yalnız filtreyle başabaşı geçiyor** (+0.011R) — kıl payı. Filtre şart.
3. **GDAXI:BUY filtreyle bile −EV** (−0.067R). Sebep NDX ile aynı: RR 0.56, başabaş
   %64 — piyasanın verdiği %60'ın üstünde. Canlı MT5 de bunu doğruluyor:
   GER40 BUY 15 işlem **−1.243$**. → **Askıya alınmalı veya NDX gibi ATR-ölçekli
   geometriye geçirilmeli** (henüz ölçülmedi; NDX'teki gibi 11 yıllık tarama gerekir).
