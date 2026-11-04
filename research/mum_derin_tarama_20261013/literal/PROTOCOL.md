# Literal mum eşleştirme — ön-kayıt (2026-10-13, sonuçlara bakılmadan yazıldı)

**Soru:** Kullanıcının harfiyen tanımı — son X ardışık mum (X 10–50), her mumun gövde ve iki fitili (açılışa göre %)
±%0,015 içinde — NDX geçmişinde kaç eşleşme verir; eşleşmelerden sonraki +15 dk / +1 sa / +1 gün yönü basit tabanlardan
ve rastgele komşulardan iyi tahmin ediliyor mu; ayar ailesinin herhangi bir üyesi aday ölçütlerini geçiyor mu?

**Yeni olan (PM / PM-2 / ME-00…03'e göre):** X = 10–50 birebir ve kısmi eşleşmenin İLERİ YÖN sınaması (PM yalnız
tekrar sayısı + 10 mum yön bilgisi, ME-02 en çok 2 mum İkiz veya kNN); kullanıcı payı %0,015 aynen; ufuklar saat
cinsinden 15 dk / 1 sa / 1 gün; kısmi eşleşmede son 1–3 mum zorunlu; uygunluk ve seans kısıtı aile içinde.

## Veri ve dokunulmaz dönem
- NDX (NAS100 CFD), UTC bar başlangıcı: 1m/5m `ndx_pattern_motifs/data/bars_{1m,5m}.parquet` (2025-01→), 15m aynı
  klasör (2023-10→), 1h `ndx_gate_forge/data/long_1h_utc.parquet` (2016-05→).
- **Dokunulmaz:** yüklemede `ts + TF < 2025-12-01 00:00 UTC` olmayan her bar ATILIR (assert). Hiçbir sonuç penceresi
  bu sınırı geçemez.
- Segment kırılması: ardışık barlar arası > 3 gün veya `seg` değişimi. Pencere ve sonuç segment içinde kalmalı.

## Tanımlar
- Mum özelliği (pct): `(H−O)/O, (L−O)/O, (C−O)/O` ×100. Eşleşme: üç farkın da |·| ≤ pay.
- ATR-göreli (atr): `(H−O, L−O, C−O) / A_e`, A_e = pencere SONU barının önceki 14 bar TR ortalaması (ME-01 ortak ölçek).
- Pencere hizası: sorgu mumu q−k ↔ aday mumu e−k (k = 0…X−1).
- Kurallar: **birebir** (X mumun hepsi) · **kısmi** f ∈ {%90, %80, %70} mumların en az ⌈f·X⌉'i payda VE son m ∈ {1,2,3}
  mum zorunlu (10 kural).
- Uygunluk (aç/kapa): sorgu VE aday penceresinin medyan mum aralığı ≥ 3 × pay (aynı birimde).
- Seans (aç/kapa): adayın karar saati (bar kapanışı, UTC) sorgununkinin ±1 saati içinde.
- Ufuk: karar = sorgu barının kapanışı t. Sonuç barı = kapanışı ≤ T olan son bar; 15 dk / 1 sa için kapanış tam T olmalı;
  1 gün için T = t + 24 sa (Cumartesi/Pazar'a düşerse +48/+24 sa), sonuç barının kapanışı T − 60 dk'dan geç olmalı.
  y = C(sonuç) − C(sorgu) (NDX puanı). y = 0 skor dışı.
- Nedensellik: aday e yalnız sonuç barı kapanışı ≤ t ise; kütüphane = t'den önceki 5 yıl (1m/5m/15m'de mevcut tümü).
- Bağımsız komşu: kronolojik açgözlü, [pencere başı, sonuç sonu] aralıkları çakışmaz. Tahmin BAĞIMSIZ kümeden; ham sayı
  ayrıca raporlanır.
- Çağrı: u = yukarı / (yukarı + aşağı) bağımsız komşular arasında; n_min ∈ {1, 5, 30}; u > 0,5 → yukarı, < 0,5 → aşağı;
  "güçlü oy" varyantı yalnız u ≥ 0,7 / ≤ 0,3 iken çağırır.
- Tabanlar (aynı çağrılmış sorgularda): (a) hep-çoğunluk = kütüphanenin o anki koşulsuz yukarı oranı; (b) aynı-saat =
  aynı UTC karar saatinin kütüphane yukarı oranı; (c) plasebo = aynı uygun havuzdan (aynı uygunluk/seans/pencere geçerliliği)
  aynı sayıda rastgele komşu, 20 tekrar (binom çekilişi; havuz oranı sorgu başına 1.000 rastgele havuz örneğinden).
- Sorgu ızgarası (keşif alt-örneklemi): 1m her 50 bar (2025-02-01→), 5m her 10 bar (2025-02-01→), 15m her 8 bar
  (2023-12-01→), 1h her 8 bar (2017-06-01→).
- Kapasite koruması: bir (TF, pay) hücresinde son mumu tutan aday sayısı sorgu başına ~3.000'i aşıyorsa KISMİ kurallar
  sabit bir rastgele konum alt-kümesinde (oran φ, kayıtlı) değerlendirilir; BİREBİR kural her zaman tam kütüphanede.
  Fizibilite sayımı (Faz A) inceltmesiz, sorgu başına 300 rastgele sorguda.

## Aday ölçütleri (hepsi)
1. ≥ 200 bağımsız çağrılmış sorgu olayı (sonuç pencereleri çakışmayan, kronolojik açgözlü).
2. isabet − max(hep-çoğunluk, aynı-saat) ≥ +2,0 puan.
3. isabet > plasebo isabeti.
4. Gün-blok bootstrap (15 dk/1 sa: 1 gün blok; 1 gün ufuk: 5 gün blok), B = 2.000, P(model − en iyi taban > 0) ≥ 0,975.
5. İki kronolojik yarıda da isabet − max(taban) > 0.
6. Tahmin yönünde ortalama hareket > 1,5 puan (spread).
7. Seçim düzeltmesi: tüm aile için (≥200 bağımsız olaylı tüm yapılandırmalar, tüm TF'ler) sorgu sonuçları bütün haftalarla
   kaydırılır (saat/gün korunur, dairesel), çağrılar sabit; tüm aile yeniden puanlanır, 200 tekrar. Gerçek en iyi
   "isabet − max(taban)" null maksimumunun %95'ini geçmeli; aday da öyle.
Tam aile `results/aile.csv`'ye yazılır.
