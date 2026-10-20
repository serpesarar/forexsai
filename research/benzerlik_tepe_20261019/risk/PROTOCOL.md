# Ön-kayıt — "Dalgalı tepe" yapısı sonrası RİSK (oynaklık + düşüş derinliği), çoklu zaman dilimi — ME-11

> 2026-10-19, sonuç hesaplanmadan yazıldı. Kullanıcı: "risk testini yap, oynaklık ve düşüş derinliği; resimler yalnız
> görsel örnekti, yapı farklı zaman dilimlerinde de aranabilir, 1 saate bağlı değil."
> Önceki: ME-09 (şablon-şekil) ve ME-10 (kural K1) yön öngörmedi. Literatür (raporu "Nasdaq dalgalı tepe yapısı testi"):
> öngörülebilen yön değil risk; kaldıraç etkisi (düşüş → oynaklık artışı), oynaklık kümelenmesi. Bu yüzden kıyas tabanı
> geriye-dönük getiriyi VE oynaklığı eşlemek zorunda (aksi hâlde bilinen etkiler yapıya yazılır).

## Zaman dilimi bağımsız tanım (mum sayısı cinsinden)
- Görsel ölçek = mum sayısı. Adım = 23 bar (1h'te ≈ 1 işlem günü). Sorgu: her 23 barda bir (düzenli ızgara, tüm TF'ler).
- **D1 — şekil dedektörü:** şablonlar NDX 1h T1 (2026-07-06→07-21, 276 bar), T2 (07-17→07-29, 207), T3 (08-13→08-20, 138)
  şekilleri (64 nokta, log kapanış, z-normalize); pencere {166, 207, 248} bar; D = en küçük mesafe; eşik = o TF/sembolün
  geliştirme dönemi sorgu D değerlerinin **%2 dilimi**. Yalnız tam eşleşme (yapı tamamlandı).
- **D2 — kural K1 (ME-10'dan aynen, gün → adım):** pencere W = 9 adım (207 bar): pos ≤ 0,222 ∧ net_s ≤ −1,524 ∧
  dist60_s ≥ −4,827 ∧ rv_ratio ≥ 0,742 ∧ swings ≥ 3 ∧ eff ≤ 0,129; σ_ref = son 252 adım getirisinin MAD-σ'sı,
  60/20 adım zirve (`kural/tepe_ozellik.py` `features`, Q = adım ızgarası).

## Veri (UTC)
- NDX: 5m, 15m (`ndx_pattern_motifs/data`), 30m (`ndx_gate_forge` long_30m + 15m'den uzatma), 1h (`merdiven_test.load`),
  4h (1h'ten, NY 17:00 sınırlı). DAX (bağımsız piyasa): 15m, 30m (`ndx_gate_forge`), 1h (`caprev_dax_recheck/data_fixed`),
  4h (1h'ten). Günlük TF kapsam dışı: 207 günlük yapı 10 yılda yeterli olay vermez (gerekçe sonuç görülmeden).

## Risk hedefleri (ufuk H ∈ {23, 69, 115} bar = 1, 3, 5 adım)
- **RV:** sonraki H barın log getirilerinin karelerinin toplamının karekökü; ölçü log(RV_ileri).
- **DD:** sonraki H barda en düşük dip / sorgu kapanışı (log), σ_H = σ_ref·√(H/23) biriminde ("kaç σ düştü"); ayrıca
  P(DD ≤ −2σ_H).

## Kıyaslar
1. **Eşli (birincil):** yapı olmayan sorgular, aynı (geriye-dönük 207 bar getirisi ondalığı × geriye-dönük 207 bar
   gerçekleşen oynaklık ondalığı) hücresinde; ondalıklar geliştirme döneminden. Fark = yapı − hücre ortalaması.
2. **HAR+kaldıraç (ikincil, yalnız RV):** geliştirme verisinde log RV_ileri ~ log RV(son 23) + log RV(son 115) +
   log RV(son 460) + getiri(son 207) + min(getiri(son 23),0) OLS; yapı sorgularının artık ortalaması.

## İstatistik
- Takvim-ayı blok bootstrap (B = 10.000), tek yönlü (risk ARTAR: RV farkı > 0, DD farkı < 0).
- Olay: aralarında > 10 adım olan yapı sorgusu kümeleri; olay sayısı, olay medyanı ve yön payı ayrıca (E6).
- Yarılar: geliştirme dönemi kronolojik ikiye.
- Bölümler: geliştirme = sonuç ufku 2025-11-30 23:00 UTC'den önce biter; doğrulama 2025-12-01 → son (bir kez); kullanıcının
  örnek dönemi 2026-07-06 → 2026-08-20 ile çakışan sorgular her yerde dışarıda.

## Başarı ölçütü
- Hücre (sembol × TF × dedektör × H × hedef): P ≥ 0,975 risk-artışı yönünde, iki yarıda aynı işaret, ≥ 20 olay, olay
  medyanı aynı işaret. NDX ailesi = 5 TF × 2 dedektör × 3 H × 2 hedef = 60 hücre → güçlü kanıt için Bonferroni
  P ≥ 0,99958. Genel karar: başarılı hücre sayısı %2,5 tesadüfü binom p < 0,01 ile aşmalı, **kötü-yön hücreleriyle simetri
  kontrolü** (E26), ve DAX'ta aynı işaret çoğunluğu.

## Uygulama ayrıntıları (sonuç görülmeden, betik yazılırken eklendi)
- DAX'ın tüm TF'leri `caprev_dax_recheck/data_fixed` (eksen-düzeltilmiş) dosyalarından, ≥ 2020-01-01 (ME-09/10 ile aynı).
  NDX 15m = `long_15m_utc` + sonrası `bars_15m`; NDX 30m = `long_30m_utc` + sonrası `bars_30m`; NDX 5m = `bars_5m`.
- "Yapı olmayan" taban kümesi: D1'de D > o TF'nin %5 dilimi (ME-08/09 geleneği), D2'de kural yanmamış sorgular.
- Eşli hücrede en az 5 taban sorgusu yoksa kaba düzeye düşülür: yalnız geriye-dönük getiri ondalığı → tüm taban ortalaması
  (ME-09 `matched_base` ile aynı).
- Değerlendirilen sorgu kümesi iki dedektörde ortak: σ_ref tanımlı (≥ 126 adım geçmiş), ≥ 460 bar geçmiş (HAR), ufuk
  sonu verinin içinde. Yarılar: o serinin geliştirme sorgularının zaman orta noktası.
- Doğrulama yalnız raporlanır (işaret + P); B sınıfı için geliştirmede geçen hücrenin doğrulamada aynı işarette olması
  ve DAX'ta aynı (dedektör, H, hedef) hücrelerinin çoğunluğunun aynı işarette olması gerekir.
- 4h serisi ~700 sorgu verir (adım 23 bar ≈ 4 gün); hacim ölçütünü büyük olasılıkla geçemez — sonuç görülmeden not edildi.
