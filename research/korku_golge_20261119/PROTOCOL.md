# Korku gecesi K1 + XP — Kanal ∪ GBM vetosu İLERİ GÖLGE — ÖN KAYIT (2026-11-19, ileri sonuçlardan önce)

Kaynak: devir raporu `docs/DEVIR_RAPORU_2026-11-19.md` §6/1, backlog `bl_00fc2245ad`, defter §2.99 (XK-04).

## Neden
§2.99 EK-1'de "1 sa kanal dibi ∪ GBM" vetosu TEST'te kâr ×0,956, zarar ×0,46 verdi (160 veto). Birleşim TEST'e bakıldıktan
SONRA kuruldu, yani kanıt değil. Tek dürüst sınama: dondur, yeni işlemlere yalnız etiket yaz, ileride say.

## Dondurulan nesneler (bu commit'le sabit; sonradan değiştirilirse ileri sayım sıfırlanır)
Üretici `src/dondur.py`, çıktı `model/`:
- **GBM:** `GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)`,
  yalnız **KEŞİF (d ≤ 2021-10-31)** dört MT5 beslemesinin (NAS100, US500, US30, US2000) işlemleriyle, etiket `net < 0`.
  Girdi: `xp_kaybeden_20261119/src/analiz.py` ile aynı 117 özellik, aynı sıra; her besleme kendi KEŞİF medyanıyla doldurulur,
  kendi KEŞİF ortalama/std'siyle standartlaştırılır (DUKA_NDX kendi KEŞİF istatistiğiyle).
- **GBM eşiği:** KEŞİF içi 5 katlı zaman bloklu OOF olasılıklarının %85'liği (tek, küresel).
- **Kanal:** `T_1sa_z` = 15:00 saatlik mumu dahil son 80 saatlik 1 sa kapanışın doğrusal regresyonunda son noktanın kalıntı z'si
  (`ozellik.linreg`). Eşik: her beslemenin KEŞİF dağılımının %20'liği; z ≤ eşik → kanal vetosu.
- **Birleşik veto:** kanal vetosu VEYA GBM olasılığı ≥ GBM eşiği.
- Sürümler `model/dondurulmus.json` içine yazılır (sklearn, numpy, pandas, python), artefakt SHA-256'larıyla.

## Yeniden üretim kapısı (ileri sayımdan önce zorunlu)
Dondurulan nesneler TEST'te §2.99'un sayılarını vermeli:
- GBM tek başına, MT5 havuzu: veto 80, kâr ×1,005, zarar ×0,719 (analiz.json `model_y.gbm`).
- Kanal tek başına: piyasa başına `saglamlik.json izgara.z80_q20` TEST satırları.
- Birleşik: 160 veto, kâr ×0,956, zarar ×0,46.
- Etiketleyici (`src/etiketle.py`), özellikleri ham barlardan yeniden hesaplayıp aynı tarihlere uygulandığında araştırma tablosuyla
  aynı veto kararını vermeli (tüm TEST işlemlerinde karar uyuşması %100; olasılık farkı < 1e-9).
Biri tutmazsa ileri gölge başlamaz; fark bulunup giderilir.

## İleri dönem
- **İleri işlem:** girişi (`d`) **2026-11-06 veya sonrası** olan K1 işlemi. Gerekçe: §2.99'un kullandığı veri 2026-11-05'te bitiyor;
  bu tarihten sonraki hiçbir işlem modele, eşiğe veya birleşim seçimine girmedi. 2026-11-19 (dondurma günü) sonrası ayrıca raporlanır.
- **Besleme:** dört MT5 (birincil, havuz). Duka NDX verisi tazelenirse ek kontrol olarak yazılır, havuza girmez.
- **Etiket:** her ileri sinyale giriş anında bilinen özelliklerden `p_gbm`, `z80`, `veto_kanal`, `veto_gbm`, `veto` yazılır.
  Etiket deftere (`results/golge_defter.csv`) sinyal satırı olarak eklenir; sonuç (XP çıkışı, net bp) ayrı sütuna çıkış belli olunca
  doldurulur. Etiket bir kez yazıldıktan sonra değiştirilmez (yalnız eksik sonuç doldurulur).
- **Canlıya dokunmaz.** Veto uygulanmaz, emir yok, bot/decider kodu değişmez.

## Geçme ölçütü (ileri, MT5 havuzu, sonuçlu işlemler)
Değerlendirme en erken **≥ 40 sonuçlu ileri işlem ve ≥ 8 vetolu işlem** olduğunda yapılır.
- **B'ye yükseltme önerisi:** altısı birden.
  1. vetolananların ortalaması ≤ +20 bp (≈ 0 ya da eksi);
  2. kalanların ortalaması > tüm ileri işlemlerin ortalaması (taban);
  3. kâr oranı (kalan toplam / taban toplam) ≥ 0,90;
  4. zarar oranı (kalanların brüt zararı / tabanın brüt zararı) ≤ 0,70;
  5. vetolanlar kalanlardan kötü, dört piyasanın en az üçünde (vetolu işlemi olan piyasalar arasında);
  6. bileşenler ayrı ayrı da raporlanır (kanal, GBM); hüküm birleşik için verilir.
- **C kalır:** vetolananlar kalanlardan kötü ama 1–4'ten biri tutmuyor.
- **X:** vetolananların ortalaması ≥ kalanların ortalaması.
- Karar kullanıcıda; B çıksa bile canlıya bağlama ayrı adım ve 2. KURAL kartı ister.

## Bilinen sınırlar
- MT5 M30 dışa aktarımı kutudan elle tazelenir (`src/tazele.py`); VIX ve QQQ yfinance'tan. Veri tazelenmezse defter ilerlemez.
- GBM 300 KEŞİF işlemiyle eğitildi; olasılık kalibre değil, yalnız sıralama için kullanılır.
- Beklenen hız: yılda ≈ 90 işlem (dört piyasa), %35'i vetolu → 40 işlem ≈ 5 ay.

## EK-1 (2026-11-19, kurulum sonrası, ileri sonuç görülmeden önce yazıldı)
- **Yeniden üretim kapısı geçti:** dondurulan nesneler TEST'te GBM 80 veto / kâr ×1,005 / zarar ×0,719, kanal 119 / ×0,992 / ×0,570,
  birleşik 160 / ×0,956 / ×0,460 (`results/yeniden_uretim.json`). KEŞİF OOF AUC 0,594, TEST AUC 0,615; GBM eşiği 0,387.
- **Etiketleyici ham barlardan:** 754/754 MT5 işleminde veto kararı birebir; işlem tablosu (`veri.build`) 764/764 aynı, Δnet 0
  (`results/dogrulama.json`). Olasılık farkı en çok 0,022 (ölçüt 1e-9 idi): tek kaynak `X_k1_genislik`. Araştırma tablosu bu sayıyı
  Duka NDX dahil *çıkışı belli işlemlerden* saymıştı; etiketleyici dört MT5 piyasasındaki *sinyallerden* sayar (ileri dönemde Duka yok,
  çıkış giriş anında bilinmez). Özelliğin GBM önemi 0,004; 39 satırda fark, hiçbir kararda fark yok. **Ölçüt bu farkla kabul edildi;**
  ileri tanım MT5 sinyal sayısıdır.
- **`veri.py` yeniden düzenlendi:** `entry_features()` ayrıldı (çıkışı belli olmayan son sinyaller için); `build()` çıktısı değişmedi.
- **Olay takvimi hatası bulundu (araştırma tablosu):** `xau_best_days_20261015/makro/out/calendar.csv` FOMC'de 2026-06-17'de, CPI'da
  2026-09-11'de, NFP'de 2026-10-02'de bitiyor; 2026-07-29, 09-16, 10-28 FOMC ve sonraki CPI/NFP günleri `olay = 0`. KEŞİF'i etkilemez;
  TEST'in son aylarında `olay` eksik. İleri takvim ayrı dosyada (`olay_takvimi.csv`, BLS ve Fed sayfalarından okundu), kapsam sonu
  2026-12-31; sonrası etiketlenmez.
- **Veri tazeleme:** MT5 M30 kutudan (Pepperstone-Demo 61628380, sunucu−UTC 7200 sn) son 650 bar, yalnız sona eklendi; VIX yfinance'tan.
  Tazelemeden sonra doğrulama yeniden koştu, sonuç aynı.
- **İleri işlemler bugün geriye dönük etiketlendi** (2026-11-06 → 11-18 sinyalleri, çıkışları belli). Bu sızıntı değil: model, eşikler
  ve özellik kodu bu commit'te donduruldu ve bu işlemlerin hiçbiri seçimde kullanılmadı. 2026-11-19 sonrası sinyaller ayrıca raporlanır.
- **Yan etki giderildi:** `vade_mantik_20261118/src/vm.py` kullanmadığı `ek3_veto`'yu içe aktarıyordu; o modül içe aktarılınca kendini
  koşup `son4_20261118/results/ek3_veto.json`'u yeniden yazıyordu (tazelenen veriyle sayıları değişti). İçe aktarma kaldırıldı, dosya
  HEAD'e geri alındı; `rapor.py test` 11/11.
