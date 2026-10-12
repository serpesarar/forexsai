# Ön-kayıt — "sürekli SL olan ortak işlem tipleri" (2026-10-09)

Kullanıcı: kazananları değil, tekrar tekrar SL olan işlem TİPLERİNİ bul; her sembol ayrı, en derin NASDAQ.
Defter: IO-11 (4.104 veto, havuzda genelleşmedi), IO-04 (sezgisel bayraklar etkisiz), IO-05 (RSI_DIV_KARSI aday),
IO-12 (decider eşik kuralları plaseboyla aynı), IO-17 (karar anında ayrım yok).
Yeni olan: sembol-yön başına arama, giriş anında 56 gösterge + panel + VIX, "benzer geçmiş işlemler SL olduysa bu da olur mu"
doğrudan testi, SL kümelemesi ve NASDAQ'ta BOTUN ÇALIŞMADIĞI bağımsız dönemde (2025-01 → 2026-06) doğrulama.

## Veri
Bot kararları (`bot_trades`, karar başına ilk bacak, TP/tam SL), giriş anında yalnız KAPANMIŞ barlar (E1/E16).
NASDAQ doğrulama: `research/ndx_gate_forge/data/bars_1m_all.parquet` (Dukascopy 2025 + cache 2026, tek UTC ekseni,
E4 onarımlı), ts < 2026-06-15; bot benzeri sentetik giriş: hafta içi 06–20 UTC saat başı, iki yön, botun NDX medyan
risk/fiyat (%0,373) ve RR (0,73), giriş bar açılışı + spread, aynı barda iki bariyer → SL.

## Özellikler (giriş anı)
islem_otopsi `pre_*` + `geo_*` + zaman (≈45) · genis.py göstergeleri 1m/5m/15m/1h (56) · bot için ayrıca: aile, panel
modelleri (son 30 dk), önceki gün VIX, önceki işlem bağlamı. Sayısal özellikler keşif kümesinin tertillerine bölünür.

## Yöntemler (sembol başına ve sembol-yön başına)
A. Alt-grup madenciliği: tek koşul ve iki koşul VE (tertil kutuları + kategoriler), destek ≥12 karar. Sıralama: SL oranı
   farkı (taban üstü). Keşif ilk %60 → sınama son %40 ve tersi; plasebo = keşifte sonuçlar karıştırılarak 50 tekrar,
   en iyi 10 alt-grubun sınama SL farkı ortalaması gerçek vs plasebo.
B. Benzerlik tekrarı: her işlem için, çıkışı bu işlemin girişinden ÖNCE olan aynı sembol-yön işlemlerinden k=10 en benzeri
   (standart özellik uzayı); skor = benzerlerin SL oranı. AUC(skor → SL) + 200 etiket-karıştırma plasebosu. k=5/20 ve
   özellik seti (bar / gösterge / hepsi) duyarlılık.
C. SL kümeleme: keşifte SL işlemlerinde k-ortalamalar (k=4); tüm sınama işlemleri en yakın merkeze atanır → küme başına
   SL oranı vs taban. Küme merkezleri sade dille betimlenir.
D. NASDAQ bağımsız doğrulama: bot NDX kararlarında (yön başına) tek/çift koşul, destek ≥15, iki kronolojik yarıda da tabanın
   üstünde SL → SL farkına göre en iyi 10 (yalnız sentetikte hesaplanabilen bar/gösterge/zaman özellikleri). Aynı koşullar
   2025-01 → 2026-06 sentetik girişlerde (aynı yön): SL oranı farkı ve ort R farkı, gün-blok bootstrap. Plasebo: destek
   şartını sağlayan 200 rastgele çift-koşul aynı biçimde.
Geçme (D): 10 koşulun en az yarısında bağımsız dönemde SL farkı > 0 ve %95 aralığı sıfırın üstünde, VE gerçek koşulların
ortalama farkı plasebo dağılımının %90'ını aşar. Geçen koşul yalnız GÖLGE aday (2. KURAL).
