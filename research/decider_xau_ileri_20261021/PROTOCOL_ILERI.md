# Ön-kayıt — Decider XAUUSD: DX-02 kurallarının İLERİ sınaması + SL otopsisinden yeni adaylar (2026-10-21)

Kullanıcı: decider'ın XAU işlemleri TP de SL de yapıyor; SL'leri engelleyen ya da TP'lere yoğunlaşan başarılı kurallar
bulunana kadar araştır; tüm decider işlemlerine bakılabilir.

Defter: DX-01 (geometri X, TP1,25/SL0,75 C), DX-02 (8 kural × 3 geometri; tek B R1×G2 +0,151R, p_FW 0,67), DX-03 (seçim
alfası X), IO-12 (decider kural araması X), M9 (BE/kilit bot'ta elendi), E29 (sahte WAIT dönem karışımı).
Bu klasör `decider_xau_tpsl_20261015`'in birebir kopyası (yalnız not yolu değişti), veri 2026-10-20'ye tazelendi:
journal OPEN 887, icra 94/94 eşleşti.

## A. İleri sınama (birincil) — kurallar DX-02 PROTOCOL'ünde 2026-10-15 04:41 UTC'de donduruldu
İleri küme = karar ts ≥ 2026-10-15 00:00 UTC (DX-01/02 verisi 10-14'te bitiyordu → hiç görülmedi).
Her R1–R8 × G1–G3: ileri kümede ortR(kural) vs ortR(kural-dışı) ve tüm küme; gün-blok bootstrap P(ortR>0), P(fark>0).
**Geçme (birincil aday R1, ön-kayıtlı tek B):** R1 ileri kümede G1 ve G2'de ortR > 0 ve kural-dışından büyük, P(fark>0) ≥ %80
(ileri n küçük olduğu için yön tutarlılığı ölçütü). Diğer 23 hücre bilgi amaçlı.

## B. Gerçek icra SL otopsisinden adaylar (keşif: icralar; sınama: gölge kararlar, aynı simülasyon)
`output/islem_otopsi/2026-10-20_2348_xau_decider/` (94 icra): giriş rastgeleden +0,16R iyi (P %95); SL'lerin %50'si
"yön doğru" (stop sonrası TP'ye gitti), %56'sı ≤10 dk; 5. dk ayrışma AUC 0,81; `KOVALAMA` bayrağı SL %18 vs %36.
- B1 erken kesme: girişten 5 (ve 10) dk sonra R ≤ −0,5 ise çık (yalnız o an bilinen bar kapanışı).
- B2 KOVALAMA = otopsi etiketi (son 15 dk lehte ≥ +1,5 ATR5 vb.) — R1 ile aynı aileden; yalnız gölgede sınanır.
- B3 giriş gecikmesi: karar + 3 dk (ilk 3 dk'nın gürültüsünü atla) — DX-02 yalnız +1 dk'yı ölçmüştü.
Sınama kümesi: gölge BUY kararları (icra edilmemiş; 583 + yinelenmeyen), G1 geometrisi; gün-blok P, iki yarı, ayrıca ileri
alt küme. **Geçme:** gölgede ortR farkı > 0, P ≥ %90, iki yarıda > 0 ve ileri alt kümede işaret aynı.
Geometri ızgarası tekrarlanmaz (DX-01). Geçen aday yalnız GÖLGE → kart (2. KURAL).
