# Sonuç — sıkışma (SQZ, B14) filtresi derin sınama (2026-10-20)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) + her turun dosya başı ekleri (exp2–exp5) + [ileri_kart.py](ileri_kart.py) başlığı.
Raporlar: `results/rapor.md` (ana tablo), `rapor2.md` (bot öncesi panel, mekanizma, ML), `rapor3.md` (veri kaynağı, aylık,
uyarlanabilir, rejim), `rapor4.md` (bot dış örneklem, güç), `rapor5.md` (H1 doğrudan, lot ağırlığı), `rapor6.md` (saat içi).
Kart: `backend/data/evolution/go_live_cards/sqz_filter_ndx.json` (verdikt **GÖLGE**).
Bot kümeleri DECIDER (ayrı süreç, filtre uygulanmaz) ve MANUEL hariçtir. Doğruluk: hesaplanan ATR14/ATR100 değerleri
2026-10-19 bot logundaki SIKIŞMA satırlarıyla birebir (0,677 / 0,694 / 0,903 / 0,896).

## Örnekler (≈70.000 olay)
Bot gerçek işlemleri 06-30 → 10-20 (NDX 318, DAX 70, USOIL 156) · botun engellenen NDX SELL sinyalleri 949 · panel NDX
sinyalleri 06-15 → 10-09 1.457 · **bot öncesi panel 02-18 → 06-12 5.018 (yeni)** · decider 874 · DAYCOMBO 2025-26 356 ·
NDX 5m kırılım-devam / dönüş 2025-01 → 2026-09 14.441 + 14.441 · DAX/USOIL/XAU kırılım 3.000'er ×2 · rastgele yön
plasebosu NDX 5.893 + 3 sembol.

## Algoritmalar
10 sıkışma ölçüsü (ATR 14/100, 5/60, 30/240; getiri std oranı; 15 dk aralık/ATR100; 5m BB genişlik yüzdeliği; TTM
BB∈Keltner; **gün-içi mevsimsellikten arındırılmış ATR14**; tick hacim oranı) × 31 eşik; lojistik ve LightGBM yürüyen
doğrulama; uyarlanabilir filtre (son W günde sıkışık kötüyse engelle); risk-sabit lot ağırlıklandırma; aynı SL'le RR
0,73/1/1,5/2 mekanizma taraması; saat-içi tabakalı fark.

## Bulgular
| soru | cevap | kanıt |
|---|---|---|
| Botta sıkışık işlemler daha mı kötü? | **Evet, geçmişte tutarlı** | dış örneklem (türetme penceresi hariç) 285 işlem Δ −0,24R, P(Δ<0) %99,5, saat-eşli %94, 4/4 ay; VIXREG/SELL'de güçlü |
| İleri dönemde (08-28 →, hiç görülmemiş) tutuyor mu? | **Hayır** | 45 işlem: sıkışık **+0,096R** vs +0,297R; engellemek **−2,0R** (P %37); saat içi fark **ters** (+0,10, P %28) |
| Genel bir piyasa kuralı mı? | **Hayır** | bot öncesi panel 5.018 sinyalde **TERS** (sıkışık +0,066 vs −0,015, saat-eşli plasebo ters yönde anlamlı); kırılım olaylarında aydan aya işaret değiştiriyor; rastgele yönde zayıf |
| Mekanizma geometrik mi (yakın TP)? | **Hayır** | RR büyüyünce Δ işaret değiştirmiyor; sıkışma sonrası 60 dk aralık daha DAR (genişleme yok, oynaklık kümelenmesi) |
| Saatin vekili mi? | **Kısmen** | 15–17 UTC işlemlerinin %83'ü sıkışık (ABD açılışı sonrası oynaklığın doğal sönmesi); mevsimsellikten arındırılınca botta etki tersine dönüyor; ileri dönemde fark tamamen saatle açıklanıyor |
| Başka bir ölçü/algoritma işe yarıyor mu? | **Hayır** | seçim düzeltmeli p 0,075 (tüm dönem), 0,20 (ileri); ML botta 0/3–2/3 ay; uyarlanabilir filtre yalnız panelin son çeyreğinde kazanıyor |
| Veri kaynağı etkisi? | **Var** | aynı panel olayları iki farklı 1m tablosuyla Δ −0,152 vs −0,063; sıkışık etiketi %81 örtüşüyor |
| Diğer semboller? | DAX zayıf aynı yön (Δ −0,13, P %81), USOIL ters | — |

## Yedinci tur — VIXREG vekili (botun asıl sinyal tipi, bot öncesi bağımsız dönem) — `rapor7.md`, `yon_ayrimi.csv`
Vekil = önceki gün VIX rejiminin lehte yönündeki pulse1/2/3 sinyalleri, Asya/Cuma hariç, sabit 80/110 puan.
| küme | n | Δ (sıkışık − diğer) | P(Δ<0) | saat-içi P |
|---|---|---|---|---|
| vekil bot dönemi 06-15→10-09 | 250 | −0,209 | %95 | %95 |
| gerçek bot VIXREG | 207 | −0,260 | %99 | %97 |
| **vekil bot öncesi 02-18→06-12** | 393 | **+0,075** | %22 | %31 |
| vekil bot öncesi · SELL / · BUY | 84 / 309 | −0,09 / **+0,13** | %69 / %12 | %64 / %24 |
| panel bot öncesi tüm model · SELL / · BUY | 1.363 / 2.547 | −0,002 / **+0,123** | %49 / %1,5 | %53 / %3 |
Vekil bot döneminde gerçek botun etkisini birebir üretiyor → etki botun koduna değil sinyal tipine ve **döneme** ait;
aynı sinyal tipi şubat–haziranda etki göstermiyor (BUY'da ters). Yön ayrımı da kurtarmıyor (ön-kayıtlı ölçüt 3: bot öncesi
vekilde P(Δ<0) ≥ %90 → %22, GEÇMEDİ).

## Hüküm: KULLANILAMAZ (şimdilik) — GÖLGE kalır, ileri kartla izlenir
Ön-kayıtlı 4 ölçütten 1'i (ileri dönem) açıkça düştü. Geçmişteki güçlü etki keşif ve geri doğrulama dönemine
(06-29 → 08-27) yoğunlaşmış. Kural donduruluktan sonra görülen tek dönemde (08-28 →) engel para kaybettirirdi. Bağımsız
veride genel bir mekanizma yok. Güç hesabı: ileri dönemin etkisi sürerse eşik 1,00 hiçbir n'de kart geçemez; eşik 0,9
(post-hoc) için ≈400 işlem (haftada ~6,6 → ~14 ay) gerekir.
**Yapma:** SQZ_FILTER_BLOCK=True; eşiği ileri dönem sonucuna bakarak 0,9'a çekmek (E24); dünkü 4/4 isabeti kanıt saymak.
**Yap:** `python3 research/sikisma_derin_20261020/ileri_kart.py` ayda bir; 150 ileri işlemde ön-kayıtlı 5 ölçüt.
