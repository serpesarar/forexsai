# Paket (K1 + OPEX vetosu + XP) kaybeden/kazanan ayrımı — çok TF kanal + tam gösterge bataryası — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Son stratejide TP olan ve SL olan işlemleri kümele; SL olanların ortak özelliğini ve farkını, TP olanların ortak farkını ayrıştırana kadar
çalış. Her indikatöre, her trend kanalına, farklı zaman dilimlerindeki trend kanallarına bak; hackle."
Strateji sabit TP/SL içermez: **kazanan = net > 0**, **kaybeden = net < 0** (XP çıkışı, maliyet + finansman dahil). İkincil: net ≤ −150 bp.

## Defter kontrolü (3. KURAL)
- §2.99 XK-01…04 (K1 + XP, OPEX vetosuz): 117 özellik; tek tek tarama, kümeleme, 190 kesişim ve modellerle kaybeden ayrılmadı. GBM TEST AUC 0,615
  ve 1 sa kanal dibi → C. §3-48/50: kaybeden girişte tanınmıyor; zararı azaltan kalite filtresi.
- **Yeniden açma gerekçesi:**
  1. **Yeni popülasyon:** yalnız önerilen paket (OPEX vetolu).
  2. **Yeni özellik aileleri:** 6 zaman diliminde (30 dk, 1 sa, 2 sa, 4 sa, gün, hafta) 4 uzunlukta regresyon kanalı (z, eğim, R², genişlik),
     Donchian konumu, TF'ler arası hizalanma sayıları ve `ta` kütüphanesinin tüm göstergeleri her TF'de. XK'de yalnız 1 sa/80, 20/60 gün ve
     seans kanalı ile 30 dk/1 sa'lik dar gösterge kümesi vardı.
  3. **Yeni bağımsız veri:** 1993–2017 ETF (QQQ/SPY/DIA/IWM) günlük K1 vekili V1 (UD-01, 2018–26'da K1 ile %88 örtüşme). Günlük/haftalık
     imzalar burada (binlerce işlem) öğrenilip dondurulur, 2018–26 gerçek paket işlemlerinde **kör** sınanır.
- §1 tuzakları: E81 alt TF eşleme sızıntısı → tüm gün içi TF'ler giriş anına **çapalı** bloklarla kurulur (son blok tam olarak 16:00'da biter);
  E102/E103 örtüşme ve yıl tabanı → yıl yıl ve piyasa piyasa rapor; E147 → etiket giriş gününe göre.

## Veri ve kümeler
- **Paket işlemleri:** `xp_gelistir_20261119/results/islemler.parquet` (K1 + XP), OPEX vetosu (vadeye 0–2 işlem günü kala açılmaz),
  **d ≤ 2026-11-05** (ileri gölge dönemi 2026-11-06'dan başlar; dokunulmaz). MT5 NAS100/US500/US30/US2000 (M30, tik hacmi) + Duka NDX.
  - KEŞİF ≤ 2021-10-31: MT5 havuzu 264 işlem / 60 kaybeden; TEST: 374 / 85; Duka 85/13 ve 121/23.
- **ÇAĞ (ETF vekili):** V1(d) = kapanış ≤ (yüksek + düşük)/2 × 0,995 ∧ kırmızı gün; OPEX vetosu aynı; XP: sonraki ilk yükselen kapanışta,
  en geç 5. gün; net = getiri − 2 bp − finansman. 1993–2017 (QQQ 1999+, DIA 1998+, IWM 2000+). Gün içi veri yok → yalnız gün/hafta TF.
- Barlar: tüm özellikler giriş anından (16:00 NY) önce kapanmış verilerle. Gün içi TF'ler: son N×m adet 30 dk mum geriye doğru m'li bloklara
  (m = 1, 2, 4, 8). Gün: 09:30–16:00 nakit seansı mumu (ETF ile aynı tanım). Hafta: son günlük mumların geriye doğru 5'li blokları.
  Her TF'de pencere 400 blok (durumlu göstergeler için aynı ısınma); yetersiz geçmiş → eksik değer.

## Özellikler (her TF için)
- **Kanal:** L ∈ {20, 50, 100, 200} doğrusal regresyon: son noktanın z'si, eğim (bp/blok), R², kalıntı σ / fiyat (bp); Donchian(50/100) konumu.
- **`ta` bataryası:** 86 sütun; fiyat düzeyi verenler (BB/KC/DC bantları, SMA/EMA, Ichimoku, PSAR, KAMA, VWAP) kapanıştan bp uzaklığa,
  fiyat birimli olanlar (ATR, MACD, AO, DPO) bp'ye çevrilir; birikimli/ölçeğe bağlı olanlar atılır (ADI, OBV, VPT, NVI, CR, FI, EM).
- **Hizalanma:** eğimi (L50) eksi olan TF sayısı, z(L50) < −1 olan TF sayısı, RSI14 < 30 olan TF sayısı (gün içi 4 + gün + hafta).
- Tur 1'de (ÇAĞ → kör) yalnız **fiyat** tabanlı gösterge (hacim ETF'de gerçek, CFD'de tik → aktarılamaz).

## Turlar (sıra ve ölçütler sabit)
- **Tur 1 — Gün/hafta imzası, ÇAĞ'da öğren → 2018–26 kör:** ÇAĞ'da piyasa içi AUC + 1.000 permütasyonla aile hatası eşiği; L1 lojistik
  ve GBM (derinlik 2, 200 ağaç) ÇAĞ'da eğitilir, eşik ÇAĞ içi zaman bloklu OOF %85'lik. Donmuş model + eşik 2018–26 paket işlemlerine
  (MT5 dört piyasa + Duka; KEŞİF ve TEST ikisi de kör) uygulanır.
- **Tur 2 — Gün içi çok TF (30 dk–4 sa) + gün/hafta, MT5 KEŞİF → TEST:** aynı tarama + L1 lojistik, GBM, LightGBM (güçlü düzenlileştirme);
  eğitim MT5 KEŞİF, sınama MT5 TEST + Duka TEST.
- **Tur 3 — Birleşik:** Tur 1 + Tur 2 + XK'nin 117 özelliği; yalnız KEŞİF eğitimi; TEST.
- **Kümeleme (her turda):** KEŞİF kaybedenleri PCA-10 + KMeans k = 2…6 (siluet); kaybeden yoğun küme TEST'te de yoğun mu.
- **Kazananların ortak farkı:** aynı AUC tablolarının ters yönü (kazananı işaret eden özellikler) ayrıca listelenir.

## Geçme ölçütleri (kör küme: Tur 1'de MT5 + Duka 2018–26, Tur 2/3'te TEST)
- **Ayrışma (kullanıcının hedefi):** kör AUC ≥ 0,62 MT5 havuzunda **ve** 4 piyasanın ≥ 3'ünde > 0,55 **ve** Duka ≥ 0,60.
- **Veto B:** en riskli %15 vetolanınca vetolananların ortalaması < 0 ve blok-bootstrap P ≥ 0,90; kâr ≥ ×0,95; zarar ≤ ×0,80;
  yön ≥ 3/4 piyasa + Duka.
- **C:** vetolananlar kalanlardan ≥ 30 bp kötü ve ≥ 3/4 piyasa. **X:** hiçbiri.
- B çıkarsa canlıya değil, ileri gölge etiketine aday (2. KURAL ayrı).
- Toplam özellik, hücre ve model sayısı raporlanır. Her yeni tur önce EK olarak buraya yazılır, sonra koşulur; sonradan bakılan hüküm değiştirmez.

## EK-1 (Tur 1–3 sonuçlarından SONRA, Tur 4 koşulmadan önce yazıldı)
Tur 1–3 hükmü yukarıdaki ölçütlerle değişmez (Tur 1 X; Tur 2 LightGBM C; Tur 3 GBM C, TEST AUC 0,615 / Duka 0,599 — ayrışma çıtası
kıl payı kaçtı). Gözlem: L1 lojistik C = 0,02'de tüm katsayıları sıfırladı (model yok); GBM/LightGBM KEŞİF içi OOF AUC < 0,5 (çağlar arası
işaret dönüyor). Küçük bir küme (panik günleri) iki dönemde de büyük kazanan — betimleyici.
**Tur 4 (ön kayıt):**
1. **Eğitim kümesi büyütülür:** KEŞİF'teki TÜM K1 + XP işlemleri (OPEX vetolular dahil) ve Duka KEŞİF eğitime girer; sınama yine yalnız
   paket TEST (MT5 + Duka). Gerekçe: kaybeden mekanizması OPEX'e bağlı değil; 60 kaybedenle güç yok.
2. **Sürekli hedef:** net bp (KEŞİF %2,5/%97,5 yüzdeliklerinde kırpılmış) GBM ve LightGBM regresyonu; en düşük tahmin %15'i (KEŞİF OOF %15'lik
   eşiği) vetolanır. Sınıflandırıcılar da aynı büyük kümeyle yeniden.
3. **L1 lojistik:** C ∈ {0,005, 0,01, 0,02, 0,05, 0,1, 0,3, 1} KEŞİF içi zaman bloklu OOF AUC ile seçilir.
4. **Yeni aileler:**
   - **Yol şekli:** giriş gününün 13 yarım saatlik getirisi (09:30–16:00) + önceki seansın 13'ü, günlük ATR'ye bölünmüş (26 boyut);
     kNN puanı = en yakın 25 KEŞİF işleminin ortalama neti (KEŞİF içinde aynı tarih hariç).
   - **Çapraz varlık (MT5 M30, 16:00'a kadar):** GER40, XAUUSD, SpotCrude için gün (16:00→16:00), seans (09:30→16:00) ve son saat getirisi.
5. Ölçütler aynı (ayrışma + veto B/C/X). Model sayısı: 2 sınıflandırıcı + 2 regresör + L1 = 5 (her biri tüm özellik kümesiyle).
Tur 4 de geçmezse hüküm verilir; yeni bir tur ancak yeni bilgi kaynağıyla (ör. opsiyon/emir akışı, ES gece verisi) açılır.
