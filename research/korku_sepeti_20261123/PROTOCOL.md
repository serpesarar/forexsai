# KS — Korku sepeti risk defteri: canlı NAS100 kurallarının çakışması ve ortak lot tavanı — ÖN KAYIT (2026-11-23, sonuçlardan önce)

## Kullanıcı isteği
"Korku sepeti risk defterini başlat." Bkz. `docs/DEVIR_RAPORU_2026-11-19.md` §6 madde 1. Amaç kârı artırmak değil, en kötü günü ve maksimum düşüşü
küçültmek. Kurallar aynı korku gecelerinde birlikte alım yapıyor; ölçülecek olan bu.

## Defter kontrolü (3. KURAL)
- **MA-03 (§2.35):** eski bot ailelerinde en kötü 5 gün ≈ tüm net. Lot tavanı 5'te en kötü 5 gün −22,0 → −7,8 bin $, günlük Sharpe 0,111 → 0,154.
  Ama örneklem içi ve bağımsız dönem yok → **C**. Bu çalışma onun bugünkü canlı kitapta ve iki dönemde sınaması.
- **NX-05 (§2.57):** oynaklık-yönetimli kitap (ters oynaklık / büyütme) **X**. Bu yüzden "oynaklığa göre eşit risk payı" adayı buraya ALINMADI.
- **NX-10 (§2.57):** canlı kitap stresi (o zamanki 7 kural, KORKU yoktu): en kötü gün −1.863 $, maks. düşüş −4.455 $, açık lot en çok 4,5, tavan aşımı 0.
  KORKU (0,75) 2026-11-19'da eklendi; tavanın bugün bağlayıp bağlamadığı bilinmiyor.
- **EV-04 (§2.101):** korku bacaklarını eşit riskle eklemek Sharpe'ı artırmıyor (portföy kabulü X) → aynı bahsin birikmesi zaten görülmüş.
- **KQ-08 (§2.109 sonrası):** CAPREV'de zarar ve düşüşün %60 azalması aynı ortalama lotta yapıyla tutmadı, yalnız lot küçültmeyle oldu → **tekdüze lot
  küçültme kontrolü zorunlu** (aşağıda K).
- **KR-03/04 (§2.110):** korku koşullu ekleme (D1 zararı ≥ 50 bp → +1 birim), maks. düşüş ×1,6. Gölgede; burada yalnız betimleyici senaryo.
- **§3 ilkesi:** bu iş giriş kenarı aramıyor; aynı bahsin büyüklüğünü ayarlıyor. Kenar iddiası yok, risk ölçüsü var. Ölçüt "kâr aynı" değil, "risk başına
  kâr daha iyi" (aksi hâlde her lot küçültme geçerdi).

## Veri ve kurallar (canlı sürümler, 2026-11-23)
- **Ana besleme:** Dukascopy NDX 1m 2018-01 → 2026-11 (`research/nom_20261113/data/ndx_1m_v3_duka.parquet`, `ndx_10y_1m_20261116/src/lib.py`).
  Kural işlem listeleri hazır, kodu canlıyla birebir (önek testi 8/8):

| kural | kaynak | canlı lot (NAS100) |
|---|---|---|
| C3B | `ndx_10y_1m_20261116/results/a_trades.parquet` | 2,0; vade haftası (3. Cuma ve önceki 4 gün, giriş günü) 1,0 |
| CAPREV (NDX) | `caprev_kuyruk_20261121` olay önbelleği `yollar2.pkl` DUKA_NDX, KQ-06 hücresi `E2_U0_h0.5` | 0,4 = tetikte 0,2 (A) + D0 kapanışında 0,2 (B) |
| ORBVIX | `ndx_10y_1m_20261116/results/orb_tp3_trades.parquet` (TP 3R) | 0,75 |
| CEKIC | `a_trades.parquet` CEKIC | 0,5 |
| KSG | `a_trades.parquet` KSG + `ksg_opex_canli_20261119/results/ksg_geceler_DUKA_NDX.csv` (veto, dünkü VIX) | 0,5; dünkü VIX ≥ 25 → 1,0; vadeye 0–2 işlem günü → açılmaz |
| AYSONU_SON (iki yönlü) | `a_trades.parquet` | 1,0 |
| AYSONU_E2 | `a_trades.parquet` | 0,75 |
| KORKU (K1-T30 + OPEX + XP) | `korku_evren_20261119/results/t30_islemler_DUKA_NDX.csv` | 0,75 |

- **Korku ailesi** (önceden tanımlı): C3B, KSG, KORKU, CAPREV, ORBVIX ("korkudan / düşüşten sonra endeks AL"). Diğerleri: CEKIC, AYSONU_SON, AYSONU_E2.
- **İkinci besleme (kontrol):** MT5 NAS100. KORKU (`t30_islemler_MT5_NAS100.csv`), KSG (`ksg_geceler_MT5_NAS100.csv`) ve CAPREV (`yollar2.pkl` MT5_NAS100)
  MT5'ten alınır. Diğer beş kural Duka'dan kalır (MT5'te 1m/5m geometrisi yok). Yani bu kitap **yarı bağımsızdır**; korku ailesinin üç kuralı bağımsız.
- **$ birimi:** 1 lot = 1 $/puan. İşlem $ = lot × giriş fiyatı × net_bp / 1e4 (net_bp maliyet ve finansman dahil, kaynaktaki tanım).
- **Günlük işaretleme (ana ölçü):** açık pozisyon her NY takvim gününün son 1m kapanışıyla işaretlenir; çıkış günü kalan = toplam − önceki işaretler.
  Böylece işlem toplamı kaynağıyla birebir kalır. MT5 kitabı ve "gerçekleşen" ölçü: işlem $ tamamı çıkış gününe yazılır (iki besleme aynı tanımla kıyaslanır).
- **Zaman:** C3B 15:30 ET; KSG ve KORKU 16:00 ET; CAPREV A tetik dakikası (Duka `a_trades` CAPREV `t_in`, aynı gün yoksa D0 15:00), B D0 16:00;
  çıkış adımı s'nin 16:00 ET'si; diğerleri kaynaktaki `t_in`/`t_out`. Aynı dakikadaki girişlerin sırası katalog sırası:
  C3B, CAPREV, ORBVIX, CEKIC, KSG, AYSONU_SON, AYSONU_E2, KORKU.
- **Dönemler:** ESKİ 2018-01 → 2021-10-31, YENİ 2021-11 → 2026-11 (`lib.ESKI_END`).

## Adaylar (sırası ve parametreleri sabit; toplam 5 aday + 1 kontrol)
Hepsinde sembol tavanı 4,5 brüt açık lot (iki yön toplamı) korunur. Tavan aşılırsa bugünkü kural: işlem **atlanır**.
- **A0 bugünkü:** yalnız 4,5 sembol tavanı, ilk gelen alır.
- **A1-T (T = 2,5 / 3,0 / 3,5):** korku ailesinin açık lot toplamı ≤ T. Yeni korku işlemi tavanı aşarsa **kalan kapasite kadar** açılır
  (0,01'e aşağı yuvarlı; < 0,10 ise atlanır).
- **A2 çakışma yarım lotu:** korku ailesinde açık pozisyon varken açılan her yeni korku işlemi canlı lotunun yarısıyla açılır.
- **A3 = A1-3,0 ∧ A2.**
- **K kontrol (aday değil):** A0'ın tüm lotları tekdüze f ile çarpılır; f, A0'ın maks. düşüşü adayınkine eşit olacak biçimde seçilir. Bir aday ancak
  K'yı yenerse anlamlıdır. Ölçüt 2'deki Calmar şartı bunu doğrudan sınar: K'nın Calmar'ı A0'ınkine eşittir.

## Ölçüler
Toplam $, aylık Sharpe (2018-01 → 2026-11 her ay, boş ay = 0), maks. düşüş (gün sonu özkaynak), en kötü gün, **en kötü 10 günün toplamı**,
Calmar = toplam / |maks. düşüş|, günlük %1 CVaR, yıl yıl toplam. Aday − A0 Sharpe farkı için aylık eşli bootstrap P (4.000).

## Betimleyici bölüm (hüküm yok)
1. Her gün sonunda açık korku kuralı sayısı → dağılım, gün başı $ ortalaması, toplam zararın hangi çakışma düzeyinden geldiği.
2. En kötü 10 gün ve maks. düşüş penceresinin (tepe → dip) kural bazında bileşimi.
3. A0'da tavan yüzünden atlanan işlemler: sayı, kural, $ sonucu.
4. Kurallar arası günlük $ korelasyonu (açık gün içinde).
5. **KR-03 senaryosu:** A0 + KORKU D1 16:00 zararı ≥ 50 bp → +0,75 lot D1 16:00 → KORKU çıkışı (tavan dahil). Etkisi raporlanır, aday değildir.

## Geçme ölçütü (Duka işaretli kitap ana; A0'a göre)
1. **Kuyruk:** maks. düşüş ≤ A0'ın %70'i **ve** en kötü 10 gün toplamı ≤ A0'ın %70'i (mutlak değerce).
2. **Risk başına kâr:** Calmar ≥ 1,10 × A0 **ve** aylık Sharpe ≥ A0.
3. **Dayanıklılık:** ölçüt 2'nin iki koşulu (çarpan 1,00) ESKİ ve YENİ yarılarda ayrı ayrı ve MT5 gerçekleşen kitapta da sağlanır.
- **B:** 1 + 2 + 3. **C:** 1 + 2 ama 3 eksik, ya da 2 + 3 ama 1 eksik. **X:** diğerleri.
- Birden çok aday B ise hepsi raporlanır; öneri en az kural değiştiren (A1 → A2 → A3 sırası), eşitlikte daha yüksek Duka Calmar.
- B çıkarsa 2. KURAL kartı ayrı adımda yazılır; canlı lot değişikliği kullanıcı kararıdır (bu görevde canlıya dokunulmaz).

## Sızıntı ve tuzaklar
- Tavan kararları yalnız o ana kadar açık olan pozisyonlarla verilir (olay sırası taraması). Lotlar kaynak işlem sonucundan bağımsızdır.
- Kaynak listeleri önceki oturumlarda canlı kodla eşlenmiş; burada yeniden üretim kontrolü: kural başı n ve ortalama bp kaynak raporlarıyla aynı olmalı
  (C3B 132 / +68,1; ORB TP3 741; KSG 1.078; KORKU T30 Duka 324 / +74,3; CAPREV E2_U0_h0.5 DUKA_NDX KQ-06 raporundaki değer).
- Aday sayısı küçük tutuldu (5). Sonuç görüldükten sonra yeni eşik eklenirse EK-n olarak işaretlenir, hüküm değiştirmez.

## EK-1 (2026-11-23, ana sonuçlardan SONRA — betimleyici, hüküm değiştirmez)
Ana koşuda en kötü 10 günün zararının %57'si C3B'den, kârın %36'sı C3B'den geldi (sonradan görüldü). Bunun bir portföy ağırlığı sorusu olup olmadığını
görmek için: A0'da **her kuralın lotu tek tek ×0,75** (diğerleri sabit, 4,5 tavanı aynı). Duka işaretli, iki yarı ve MT5 gerçekleşen kitapta toplam,
maks. düşüş, en kötü 10 gün, Calmar ve aylık Sharpe raporlanır. Sekiz hücrenin hepsi yazılır, seçim yapılmaz. Lot önerisi buradan çıkmaz; ancak ileri bir ön
kayıtlı sınamanın gerekçesi olabilir.
