# BTC aile 05 — Trend / kırılım / momentum kenarları (XAU/NDX'ten taşınan kurallar, 5 yıllık sızıntısız backtest)

> Kapsam: yalnız bu aile (Golden Donchian, MAX10/MIN10, H4 Donchian, R0B_G1 + S2, momentum filtresi, H3 gün-içi momentum,
> 5m Donchian negatif kontrol). Veri: Binance BTCUSDT 1m/5m/15m/1h/4h/1d, 2021-06-01 → 2026-10-20 (UTC).
> Kaynaklar yereldir (dosya yolları `research/btc_5y_20261021/fam_trend/` altında):
> ön-kayıt [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/prereg.md) ·
> motor [lib_trend.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/lib_trend.py) ·
> koşucu [run_trend.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/run_trend.py) ·
> tüm hücreler [results/summary.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/summary.md),
> [results/cells.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/cells.json) ·
> ek ölçüt (P2 + swap) [results/amend_p2_swap.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/amend_p2_swap.json) ·
> testler `test_engine.py`, `test_prefix.py`, `diag_stop.py`, `diag_synth.py`.
> Repo'nun başka hiçbir dosyasına dokunulmadı; kutu/Supabase yok; commit yok. Evrim Paneli oturum notu ve deftere satır
> ekleme bu ajanın yetkisi dışında bırakıldı (taslak en altta).

---

## Yöntem ve doğrulama — sonuçlara güvenilebilir mi?

### Takeaway
Ön-kayıt sonuçlardan önce yazıldı (2026-10-21 22:05 UTC). Bir ek (A1) ilk koşudan sonra eklendi; yalnız ölçüt sıkılaştırdı ve gerekçesi yazıldı. Simülatör kaba taramayla birebir aynı, karıştırılmış-bar martingalinde yansız çıktı ve önek (sızıntı) testinden geçti. 36 ön-kayıtlı hücre ve 7 "DISCOVERY'de seçilen → OOS∪BLIND" kartı, yani 43 hücrelik tek bir aile koşuldu. Tamamı ~5 saniyede çalışıyor.

### Cited Findings
- **İcra modeli:** karar sinyal barının kapanışında verilir. Giriş bir sonraki 1m açılışında ve yarım spreadle yapılır (long ask = open + h). SL/TP bid seviyeleridir; long'da tetik mid_low − h ≤ SL koşuludur. Aynı 1m barda hem SL hem TP varsa SL sayılır. SL boşlukla atlanırsa açılıştan dolar. Spread %0,0185 alındı; stres senaryosunda %0,028, ayrıca sabit 15 $ varyantı koşuldu. Swap her gece 17:00 New York'ta işler (21:00 UTC yaz / 22:00 UTC kış): long −%14/365, short +%2/365. — [lib_trend.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/lib_trend.py)
- **Motor doğruluğu:** 3.000 rastgele sorguda (alt ve üst taraf) binary-lifting ilk-dokunuş kaba taramayla karşılaştırıldı, uyuşmazlık **0**. Elle hesaplanan bir LONG zaman çıkışı motorla birebir aynı çıktı (425,55 $). — `test_engine.py`
- **Sızıntı (önek) testi:** veri 2023-06-15 07:00 ve 2025-02-03 13:00'te kesilip tüm olay listeleri yeniden üretildi. Kesimden en az 2 gün önceki olayların (dec/dir/sl/tp) hepsi tam veriyle aynı çıktı, uyuşmayan hücre yok. — `test_prefix.py`
- **Yansızlık:** 1m barlar göreli o/h/l/c olarak bütün hâlinde karıştırıldı ve yol yeniden kuruldu (≈ martingal). Spread sıfırken long+short toplamı yalnız swap kadar negatif kaldı: R0B −0,025/−0,037, MOM ≈0. Swap'sız H3 penceresinde toplam ±0,06 gürültü içinde. Yani motor yön yanlılığı üretmiyor. — `diag_synth.py`
- **Plasebo (P1):** her olay için aynı takvim yılı × aynı UTC saat:dakikasından rastgele bir bar çekildi; yön ve geometri aynı tutuldu, 200 tekrar yapıldı. Bunu tüm uygun barlar üzerinde önceden simüle edilmiş tabandan çekmek, P1'i birebir ve hızlı hesaplıyor. **Holm** için tek yönlü gün-kümeli z kullanıldı (43 hücre, eşik 0,05/43 = 0,0012). **max-z:** hücre bazında sürüklenme-üstü z hesaplandı, boş dağılım her plasebo tekrarındaki hücre-maksimumu. — [run_trend.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/run_trend.py)
- **A1 eki (koşudan sonra, gerekçeli):** H4 trend filtreli hücreler için P2 (trend-koşullu taban + plasebo) eklendi. Girdi notu 01/H07 bunu "zorunlu" diye ön-kaydetmişti, prereg'e geçirilmesi unutulmuştu. — [prereg.md § Amendments](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/prereg.md)

### Inferences
- BTC 24/7 işlem gördüğü için "sonraki 1m açılışı ≈ sinyal kapanışı". Kart ölçütü 5'teki (icra) fark ≥1h TF'lerde 0,001–0,024R'de kalıyor. Bağlayıcı sürtünme spread + swap; ölçüt 5 yalnız 5m'de ısırıyor (aşağıda N5).
- Dondurulmuş birincil hücreler BTC'de hiç ayarlanmadı. Bu yüzden TAM dönem kartı onlar için örneklem dışıdır. DISCOVERY'de seçilen hücreler yalnız OOS∪BLIND'da kartlandı.

### Gaps
- Broker BTCUSD M1 kasası yalnız ~16 gün (not 02). İleri broker işareti (eski 10. ölçüt) bu turda sınanmadı.
- Stoch %K'nin "ham (fast) 14" olduğu ve SAR(0,02; 0,2) parametreleri varsayım. Projedeki `indicator_snapshots` formülü bu oturumda bulunamadı.
- Binance USDT fiyatı broker USD fiyatından ~%0,1 farklı. R tabanlı sonuçlar için önemsiz, mutlak seviye kuralı da yok.

---

## Hipotez tablosu — kart, plasebo, BLIND, taban (gerçek maliyet, FULL = 2021-06→2026-10; H3 ve "SEL:" = OOS∪BLIND)

### Takeaway
**43 hücrenin hiçbiri genişletilmiş kartın tamamını geçmedi. Holm'dan da max-z seçim düzeltmesinden de geçen hücre 0.** En güçlü aday **H4 Donchian + D1 EMA200 BUY** oldu. N=20 ve N=55'in ikisi de kartın 1–8. ölçütlerini ve A1'deki P2 trend kontrolünü geçiyor. Ancak bu hücre DISCOVERY'de seçildi, max-z p_sel 0,36–0,74, ve tek pozisyonda en iyi 20 gün çıkınca negatife dönüyor. Sonuç: **B, gölge adayı; LIVE değil**. XAU'dan dondurulmuş taşınan kurallar (Golden Donchian, R0B_G1, S2) BTC'de tutmadı: BLIND'da negatifler ya da n çok küçük. Momentum filtresi ve H3 X çıktı. 5m Donchian negatif kontrolü beklendiği gibi çöktü.

### Cited Findings (hepsi [summary.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/summary.md) ve [amend_p2_swap.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/amend_p2_swap.json))

| hücre | n (tek-poz) | WR / başabaş | ortR [%95 GA] | P(EV>0) | yarı1 / yarı2 | stres ×1,5 | icra farkı | tek-poz | P1 yüzd. (P1 ort) | BLIND | taban | p_sel | verdikt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ★GD55-L (Golden Donchian) | 53 (24) | %50,9 / %41,6 | +0,208 [−0,103, +0,538] | 0,89 | +0,290 / +0,130 | +0,208 | 0,001 | +0,318 | 71 (+0,113) | −0,412 (n 8) | her gün BUY −0,011; P2 EMA-üstü +0,006 | 1,00 | SHADOW (mekanik) — kanıt yok |
| ★GD55-S (ayna) | 29 (17) | %44,8 / %46,0 | −0,024 | 0,43 | +0,053 / −0,097 | −0,025 | 0,055 | −0,038 | 37,5 | +0,230 | her gün SELL −0,058 | 1,00 | RED |
| ★MX10-L-1d (MAX10 long) | 353 (353) | %45,3 / %39,1 | +0,034 [−0,010, +0,077] | 0,94 | +0,062 / +0,006 | +0,033 | 0,003 | +0,034 | 91 (+0,009) | +0,026 | her gün BUY +0,004 | 0,95 | SHADOW (7,9,10 ✗) |
| ★MN10-S-1d | 293 | %42,7 / %42,3 | +0,002 | 0,52 | +0,005 / −0,001 | +0,001 | 0,002 | +0,002 | 71,5 | +0,004 | −0,012 | 1,00 | RED |
| ★MXMN10-LS-1d (iki yön) | 646 | %44,1 / %40,5 | +0,019 [−0,011, +0,052] | 0,89 | +0,034 / +0,005 | +0,018 | 0,003 | +0,019 | 92 | +0,014 | — | 0,945 | SHADOW |
| MX20-L-1d (plato) | 263 | %47,1 / %39,2 | +0,047 [−0,005, +0,099] | 0,96 | +0,064 / +0,030 | +0,046 | 0,003 | +0,047 | 96 (+0,010) | +0,023 | +0,004 | 0,785 | SHADOW (9,10 ✗) |
| MN10-L-1d (literatür dip kolu) | 293 | %56,0 / %57,9 | −0,010 | 0,32 | — | −0,011 | — | −0,010 | 26,5 | −0,017 | — | 1,00 | RED |
| MX10-L-H6 (10g-dip çıkışı; DISC-seçili) | 353 (79) | %39,1 / %29,6 | +0,227 [+0,064, +0,408] | 1,00 | +0,520 / −0,063 | +0,226 | 0,003 | +0,195 | 82,5 (+0,164) | −0,276 | +0,121 | 1,00 | SHADOW; **SEL OOS∪BLIND +0,029, P1 %8,5 → RED** |
| ★H4D20-L (filtresiz) | 560 (259) | %39,8 / %37,3 | +0,065 [−0,078, +0,200] | 0,82 | +0,150 / −0,020 | +0,064 | 0,010 | +0,100 | 93 (−0,013) | −0,107 | −0,019 | 0,91 | RED |
| ★H4D20-S | 460 | %37,8 / %37,6 | +0,004 | 0,52 | −0,002 / +0,011 | +0,004 | 0,011 | +0,041 | 48 | +0,005 | +0,001 | 1,00 | RED |
| **H4D20-T-L** (D1 EMA200 hizalı; DISC-seçili) | 305 (142) | %45,9 / %36,9 | **+0,236 [+0,027, +0,453]** | 0,99 | +0,254 / +0,218 | +0,236 | 0,005 | +0,205 | 97,5 (+0,073) | **+0,270 (62)** | −0,019; **P2 trend −0,020, P2-plasebo %100** | 0,39 | SHADOW (9,10 ✗) |
| SEL:H4D20-T-L (OOS∪BLIND kartı) | 224 (96) | %45,1 / %37,3 | +0,206 [−0,049, +0,466] | 0,94 | +0,270 / +0,142 | +0,206 | 0,007 | +0,114 | 96 (+0,055) | +0,270 | P2 +0,008, P2-plasebo %99,5 | 0,74 | SHADOW |
| H4D55-T-L (plato) | 200 (92) | %47,5 / %37,2 | +0,269 [+0,009, +0,519] | 0,98 | +0,218 / +0,319 | +0,268 | 0,007 | +0,257 | 98,5 (+0,062) | +0,481 (42) | P2 −0,020, P2-plasebo %100 | 0,36 | SHADOW (9,10 ✗) |
| H4D55-L / H4D20-T-S / H4D55-T-S | 343 / 217 / 140 | — | +0,140 / +0,029 / +0,166 | 0,93 / 0,57 / 0,88 | — | — | — | — | 97 / 33 / 83 | −0,070 / +0,143 / +0,247 | — | 0,67 / 1 / 1 | SHADOW / RED / RED (S'ler OOS'ta −0,72/−0,80) |
| ★R0B-L (1h yeni 20-bar tepesi, XAU R0B_G1) | 4.429 (1.371) | %33,3 / %30,8 | +0,078 [−0,027, +0,190] | 0,93 | +0,139 / +0,016 | +0,070 | 0,023 | +0,082 | 99,5 (+0,023) | **−0,054** | +0,020 | 0,40 | SHADOW (8,9,10 ✗) |
| R0B-S (ayna) | 4.051 | %32,1 / %31,5 | +0,019 | 0,61 | +0,036 / +0,002 | +0,011 | 0,024 | +0,013 | 89,5 | +0,028 | −0,014 | 0,98 | RED |
| ★R0B-L-S2σ (dün > +1σ ise atla) | 3.762 (1.230) | %33,3 / %30,3 | +0,093 [−0,022, +0,217] | 0,93 | +0,155 / +0,030 | +0,084 | 0,023 | +0,085 | 99,5 | −0,064 | +0,020 | 0,185 | SHADOW; SEL OOS∪BLIND +0,036, P1 %57 → RED |
| R0B-L-S2lit (literal +%1) | 3.006 | — | +0,067 | 0,86 | +0,078 / +0,057 | +0,058 | 0,023 | +0,064 | 94 | +0,032 | — | 0,935 | SHADOW |
| ★MOM-L-G1 (ATR 2/1) | 7.664 (3.032) | %33,4 / %34,4 | −0,028 [−0,077, +0,021] | 0,13 | −0,034 / −0,023 | −0,045 | 0,036 | −0,007 | 93 (−0,048) | −0,059 | −0,048 | 0,975 | RED |
| MOM-L-G2 (bot yakın hedef 0,73/1) | 7.665 | **%55,9 / %58,0** | −0,036 [−0,063, −0,009] | 0,00 | — | −0,054 | 0,035 | −0,031 | 65,5 | −0,072 | −0,039 | 1,00 | RED |
| MOM-S-G1 / MOM-S-G2 | 7.277 | — | −0,056 / −0,026 | 0,02 / 0,03 | — | — | — | — | 19,5 / 58 | +0,002 / −0,015 | −0,043 / −0,027 | 1 | RED |
| ★H3-L30 (ilk 30 dk yönü → son 30 dk; OOS∪BLIND) | 696 | %47,3 / %52,7 | −0,039 [−0,074, −0,005] | 0,01 | −0,025 / −0,052 | −0,051 | 0,028 | −0,039 | 22 (−0,027) | −0,054 | L −0,067 / S +0,012 | 1,00 | RED (ETF öncesi DISC +0,029) |
| H3-L30-HV (yüksek oynaklık günü) | 319 | — | −0,029 | 0,11 | — | −0,040 | — | — | 49,5 | −0,028 | — | 1,00 | RED |
| H3-ROD (bilgi: 10:00→16:00 ET) | 696 | %33,3 / %29,7 | +0,115 [−0,026, +0,261] | 0,94 | +0,117 / +0,114 | +0,100 | 0,021 | +0,115 | **71 (+0,078)** | +0,115 | **L +0,087 / S +0,067** | 1,00 | SHADOW (yön katkısı yok, aşağıya bak) |
| ★N5-L (5m Donchian48, negatif kontrol) | 5.544 | %39,9 / %50,1 | −0,204 [−0,232, −0,177] | 0,00 | −0,190 / −0,218 | −0,267 | **0,136** (iyimser −0,068) | −0,202 | **0,0** (−0,146) | −0,238 | −0,144 | 1,00 | RED (beklenen) |
| ★N5-S | 5.214 | %41,9 / %50,1 | −0,163 | 0,00 | — | −0,234 | 0,129 (iyimser −0,034) | −0,161 | 0,0 | −0,153 | −0,122 | 1,00 | RED (beklenen) |

- **Holm:** en küçük tek yönlü p = 0,0147 (H4D20-T-L), eşik 0,0012. **0/43 geçti.** max-z p_sel'in en iyisi R0B-L-S2σ'da 0,185, ardından H4D55-T-L 0,36 ve H4D20-T-L 0,39. **Hiçbiri ≤0,10 değil.** — [cells.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/cells.json)
- **Yıl bazında (ortR, n):**
  - H4D20-T-L: 2022 −1,04 (3), 2023 +0,37 (78), 2024 +0,26 (111), 2025 +0,17 (99), 2026 +0,05 (14).
  - R0B-L: 2022 −0,03, 2023 +0,31, 2024 +0,12, **2025 −0,07**, 2026 +0,07.
  - MX10-L-1d: 4/6 yıl +.
  - GD55-L: 2024 +0,69 (21), **2025 −0,42 (11)**.
  - [summary.md "Yıl bazında"](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/summary.md)
- **Kuyruk yoğunlaşması (tek-poz seti, giriş UTC günü; E31):**
  - H4D20-T-L FULL: en iyi 5 gün hariç +0,084, **20 gün hariç −0,157**. SEL penceresinde 5 gün hariç +0,011, 20 gün hariç −0,376.
  - R0B-L: 5 gün hariç +0,031, 20 gün hariç −0,064.
  - GD55-L: 5 gün hariç −0,118.
- **Nominal % (E32):** H4D20-T-L işlem başına net **+%0,54**, R0B-L +%0,030, MX10-L-1d +%0,145, GD55-L +%1,15. İşaretler R ile tutarlı.

### Inferences
- **H4 Donchian + D1 EMA200 BUY** XAU'daki H4_DONCH30 varyantının (+0,33R) BTC karşılığı. Şu açılardan ayakta:
  - DISCOVERY, OOS ve BLIND'ın üçünde de pozitif (+0,32 / +0,18 / +0,27).
  - N=20 ve 55'te plato var.
  - Trend-koşullu taban P2 ≈ −0,02. Yani MK-07'nin "trend filtresi yalnız sürüklenmeyi seçiyor" uyarısı burada **tutmuyor**: kırılım tetiği trendli rastgele girişten ayrışıyor (P2-plasebo %99,5–100).
  - Swap'a dayanıklı (swap maliyeti 0,033R).

  Zayıf yanları:
  - DISC'te seçildi, ön-kayıtlı birincil hücre filtresiz H4D20-L'ydi ve o RED çıktı.
  - 43 hücrelik aile düzeltmesini geçmiyor.
  - 2022 ayı piyasasında filtre kapalı kaldı (3 işlem). Kenar fiilen 2023–2025 boğa dönemlerinde ölçüldü.
  - Kazanç en iyi ~20 güne dayanıyor.
  - Yılda ~26 tek-pozisyon işlem → ileri gölgede n=100'e ~4 yıl gerekir.
- **XAU'dan dondurulmuş kurallar taşınmadı.** R0B_G1'in BTC'deki P1 farkı (+0,078 vs +0,023) XAU'dakine (+0,102 vs +0,049) benziyor, ama BLIND'da işaret dönüyor (−0,054) ve p_sel 0,40. Golden Donchian'da n=53, P1 yüzdeliği 71, BLIND −0,41 (n=8): kanıt yok. Bu MK-03'ün "yeni-tepe davranışı piyasaya özgü" bulgusunu destekliyor.
- **MAX10/MAX20 (literatür)** küçük ama tutarlı: +0,03…+0,05R/gün (≈ +%0,15–0,21 nominal), üç bölmede de +. P1 yüzdeliği 91–96. Seçim düzeltmesinden geçmiyor. Literatürdeki büyük Sharpe iddiası, gerçek spread + swap ve R ölçüsünde "her gün al" tabanının yalnız birkaç baz puan üstünde kalıyor. MIN10 kolu (dip alımı ve dipte satış) sıfır/negatif, yani literatürün "ikisi birlikte" kazancı BTC 2021–26'da yok.
- **Momentum filtresi BTC'de kenar değil.** G1 (ATR 2/1) −0,028R; bu, NDX'teki +0,079'un tersi. G2'de WR %55,9 ama başabaş %58,0 (OLD-20 deseni: yüksek WR ≠ kenar). P1 yüzdeliği 93'ün nedeni filtrenin rastgele girişten biraz az kaybetmesi; mutlak beklenti negatif.
- **H3 (Shen-Urquhart-Wang) ETF sonrasında işlemiyor:** OOS∪BLIND −0,039, P 0,01. ETF öncesi DISC'te +0,029 idi. Bu, literatür bulgusunun eski örnekleme ait olduğu ve çürüdüğü yorumuyla tutarlı.
- **Negatif kontrol N5** kart ölçütü 5'in BTC'deki duyarlılığını kalibre ediyor. İyimser (kapanış girişi, spread 0) −0,07 iken gerçek −0,20 (fark 0,136 > 0,5·|R|). USOIL'deki −0,005 → −0,125 deseni BTC 5m'de birebir tekrarlıyor. Kırılım barından sonra giriş rastgeleden de kötü (P1 yüzdeliği 0).

### Gaps
- Holm/max-z ailesine SEL tekrar kartları da dahil (43 hücre). Bu muhafazakâr bir seçim. Yalnız 36 ön-kayıtlı hücreyle bile en iyi p (0,0147) Holm eşiğinin (0,0014) çok üstünde, karar değişmez.
- H4-T-L kenarının 2022 gibi bir ayı yılında ne yapacağı bilinmiyor; filtre o yıl 3 işlem açtı.

---

## R0B_G1 S2 kovalama atlaması BTC'ye taşınıyor mu?

### Takeaway
**Hayır.** σ-birimli S2 (dün > +1·dvol20 → atla) DISCOVERY'de güçlüydü (fark −0,232) ama OOS'ta zayıfladı (−0,048) ve BLIND'da işaret değiştirdi (+0,074). Tek-pozisyon toplamını üç bölmenin üçünde de **azaltıyor**. Literal +%1 eşiği DISC ve OOS'ta ters işaretli (+0,118 / +0,115). Plato (×0,75 / ×1,25) işaret tutarlılığı göstermiyor. XAU'daki A sınıfı filtre (MK-13) BTC'de geçerli değil.

### Cited Findings
- Atlanan vs kalan (R0B-L), sırayla DISC / OOS / BLIND:
  - **S2σ:** −0,068 vs +0,164 / +0,075 vs +0,123 / +0,011 vs −0,064. Tek-pozisyon Σ R filtresiz → filtreli: 51,6 → 49,9 / 53,0 → 50,3 / 8,3 → 4,6.
  - **S2σ×0,75:** farklar +0,079 / +0,126 / −0,222.
  - **S2σ×1,25:** +0,021 / −0,026 / +0,449.
  - **Literal %1:** +0,118 / +0,115 / −0,358.
  - **SELL aynası** (dün < −1σ ise SELL'i atla): +0,381 / −0,404 / +0,168.
  - — [summary.md § S2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/summary.md)

### Inferences
- Bölmeler arasında işaret değiştiren, eşiğe duyarlı bir bayrak, E17/E34 türü post-hoc bir kalıptır. BTC'nin günlük σ'sı (~%3) XAU'nunkinin birkaç katı. Literal +%1 BTC'de "sıradan gün" sayılır (olayların ~%32'sini atlıyor). E25'in öngördüğü gibi σ-ölçekleme gerekli, ama ölçeklenmiş hâli de tutmuyor.

### Gaps
- Bayraklı olay sayıları bölme başına 147–308. Daha ince ayrım (S1 seri kırılım vb., E34 2×2) bu turda koşulmadı.

---

## Swap maliyeti ve uzun tutuş

### Takeaway
Gece başına −%14/365 long swap, çok günlü BUY'ları belirgin vuruyor ama hiçbir hücrenin işaretini tek başına çevirmiyor. Golden Donchian'ın ortR'sinin ~%27'sini, H4-T-L'nin ~%12'sini yiyor.

### Cited Findings
| hücre | swap'lı ortR | swap'sız ortR | swap maliyeti (R) |
|---|---|---|---|
| GD55-L | +0,208 | +0,284 | 0,075 |
| MX10-L-H6 | +0,227 | +0,294 | 0,067 |
| H4D20-T-L | +0,236 | +0,269 | 0,033 |
| H4D55-T-L | +0,269 | +0,301 | 0,033 |
| R0B-L | +0,078 | +0,097 | 0,020 |
| MX10-L-1d | +0,034 | +0,040 | 0,006 |

— [amend_p2_swap.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/amend_p2_swap.json)

### Inferences
- Swap modeli, broker spesifikasyonundaki INTEREST_CURRENT oranından alındı (not 02; 360/365 bölücü ve tahakkuk anı doğrulanmadı). Pepperstone PDF'indeki −%22,5 kullanılırsa maliyetler ~1,6× olur. GD bu durumda ~+0,16R'ye iner, H4-T-L ~+0,21R'de kalır.

### Gaps
- Gerçek swap tahakkuk anı ve hafta sonu davranışı canlı hesapta ölçülmedi.

---

## Yan gözlem (ön-kayıtlı değil, C): ABD seansında stop + zaman çıkışı iki yönde de pozitif

### Takeaway
10:00→16:00 ET penceresinde, 1×ATR(H1) stop ve zaman çıkışıyla rastgele long ve rastgele short **ikisi de** pozitif çıkıyor (net +0,087 / +0,067R). Stop sonrası fiyat ortalama 0,24–0,25R aynı yönde devam ediyor. Martingal yolda bu etki sıfır. Yani BTC'nin ABD saatlerinde ≥1 ATR(H1) hareketlerinde devam (trend) davranışı var. H3-ROD'un +0,115'i büyük ölçüde bu yönsüz etkiden geliyor (P1 +0,078); ilk-30-dk yönünün katkısı ~+0,04 ve plasebo yüzdeliği 71.

### Cited Findings
- Stop payı %58–61. Stop sonrası kalan hareket long'da −0,249R, short'ta −0,240R. R0B-L'de −0,003, H4'te −0,023. Karıştırılmış-bar martingalinde (ATR yolla uyumsuz ilk denemede) bu değer anlamsızdı; doğru kurulmuş sentetik testte long+short toplamı ≈ 0. — `diag_stop.py`, `diag_synth.py`

### Inferences
- Bu etki "volatilite kırılımı / straddle" ailesinin (başka ajanın kapsamı olabilir) ön-kayıtlı sınamasına aday. Burada yalnız C olarak not edildi; kart uygulanmadı.

### Gaps
- Saat ve gün dağılımı, ETF öncesi/sonrası ayrımı ve maliyet duyarlılığı bu turda ölçülmedi.

---

## Defter satırı taslağı (docs/KAPI_KAYIT_DEFTERI.md §6 biçimi; yeni bölüm önerisi "§2.11 BTC aile trend — `research/btc_5y_20261021/fam_trend/`")

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-T01 | 2026-10-21 | **XAU Golden Donchian BTC'ye dondurulmuş taşıma** (D1 kapanış ≥ önceki 55 high ∧ > EMA200 → ertesi 00:00 UTC BUY, SL 2/TP 4 ATR14, 20 gün, swap −%14/yıl; ayna SELL; plato N 40/70) | Binance 2021-06→2026-10: 53 işlem (tek-poz 24) +0,208R [−0,10, +0,54], P 0,89, P1 yüzd. 71, BLIND −0,41 (n 8), en iyi 5 gün hariç −0,12; swap 0,075R yiyor; SELL aynası −0,024. Hacim yapısal olarak geçilemez ve plasebo üstü değil | C (taşındığına kanıt yok) |
| BTC-T02 | 2026-10-21 | **Literatür MAX10/MIN10 günlük** (kapanış = 10g max → 24 s BUY; MIN10 → SELL; MIN10 BUY kolu; MAX20 plato; "10g dip kapanışında çık" H6 varyantı), SL 2×ATR14 felaket stopu | MX10-L 353 olay +0,034R P 0,94 P1 %91, üç bölmede + (+0,040/+0,032/+0,026); MX20 +0,047 P1 %96; MIN10 SELL +0,002, MIN10 BUY −0,010; iki yön +0,019. H6 DISC'te +0,47, OOS∪BLIND +0,029, P1 %8,5. Holm/max-z ✗ | B− (küçük, tutarlı, seçim düzeltmesiz) / H6: X |
| BTC-T03 | 2026-10-21 | **H4 Donchian kırılımı** (H4 kapanış ≥ önceki N high / ≤ N low; SL 2/TP 4 ATR14(H4), 30 bar; N 20/55 × filtre {yok, D1 EMA200 hizalı}) | Filtresiz birincil H4D20-L +0,065 P 0,82, BLIND −0,11 → RED; SELL'lerin hepsi ≈0/−. **D1-hizalı BUY**: N20 305 olay +0,236 [+0,03, +0,45] P 0,99, yarılar +0,25/+0,22, P1 %97,5, BLIND +0,27; N55 +0,269 P1 %98,5, BLIND +0,48; **P2 (trendli rastgele BUY) −0,02, P2-plasebo %100** → trend sürüklenmesi değil. OOS∪BLIND kartı (DISC-seçili) 224 olay +0,206 P 0,94, kart 1–8 ✓. **Holm ✗ (p 0,015 vs 0,0012), max-z p_sel 0,39/0,74 ✗**, tek-poz en iyi 20 gün hariç −0,16; 2022'de 3 işlem | **B** (gölge adayı; LIVE değil) |
| BTC-T04 | 2026-10-21 | **R0B_G1 BTC'ye dondurulmuş taşıma** (H1 high ≥ önceki 20 high → BUY, SL 1,5×ATR14(H1), 20 s; ayna SELL) | 4.429 olay +0,078R [−0,03, +0,19] P 0,93 vs P1 +0,023 (yüzd. 99,5), yarılar +0,14/+0,02, tek-poz +0,082; **BLIND −0,054**, 2025 −0,07; p_sel 0,40. SELL aynası +0,019 | B− (DISC/OOS'ta XAU desenini tekrarlıyor, BLIND'da dönüyor) |
| BTC-T05 | 2026-10-21 | **S2 kovalama atlaması** (R0B-L içinde dün > +1·dvol20 ise atla; ×0,75/×1,25 plato; literal +%1; SELL aynası dün < −1σ) | Atlanan−kalan farkı DISC −0,23 / OOS −0,05 / BLIND +0,07; filtre tek-poz Σ R'yi üç bölmede de düşürüyor; literal %1 DISC/OOS'ta ters işaret; plato tutarsız | X (BTC'ye taşınmıyor; MK-13 XAU'ya özgü) |
| BTC-T06 | 2026-10-21 | **Bot momentum filtresi** (15m stoch>70 ∧ dist(EMA20)/ATR>0,8 ∧ H1 SAR altta, ilk geçiş; G1 TP 2/SL 1 ATR(H1), G2 TP 0,73/SL 1; SELL aynası) | BUY G1 7.664 olay −0,028R P 0,13; G2 WR %55,9 < başabaş %58,0, −0,036; SELL −0,056 / −0,026; BLIND hepsi ≤0. NDX'teki +0,079 (ATR 2/1) BTC'de yok | X |
| BTC-T07 | 2026-10-21 | **Literatür H3 gün-içi momentum ETF sonrası** (BTC 09:30–10:00 ET getirisi yönünde 15:30→16:00 ET, SL 1×ATR(H1); HV günleri; 10:00→16:00 bilgi kolu) | OOS∪BLIND 696 gün −0,039R P 0,01, P1 %22; ETF öncesi +0,029; HV −0,029. 10:00→16:00 kolu +0,115 ama P1 +0,078 (yüzd. 71): rastgele long da short da pozitif → yön katkısı ≈ +0,04 | X (H3) / C (ABD seansında stop+zaman yönsüz devam etkisi, ön-kayıtsız) |
| BTC-T08 | 2026-10-21 | **Negatif kontrol 5m Donchian48 + EMA200 + aşım ≤0,5 ATR** (TP=SL=1×ATR14(5m), 24 s; ayna) | BUY 5.544 olay −0,204R, iyimser −0,068 (icra farkı 0,136 ✗), P1 yüzd. 0; SELL −0,163 (iyimser −0,034). USOIL deseni birebir | X (beklenen; kart 5 duyarlılığı BTC 5m'de doğrulandı) |

---

## Yeni yöntem tuzakları

| ID önerisi | Tuzak | Vaka | Önlem |
|---|---|---|---|
| E40 | **Motor yansızlık sınamasında yalnız kapanış getirilerini karıştırıp OHLC'yi kapanış oranıyla taşımak**, bar-içi uçlarla açılışların sürekliliğini bozar. Sahte stop dokunuşları ve "stop sonrası geri dönüş" üretir. Olay ATR'si gerçek yoldan kalınca ölçek de uyumsuzlaşır | fam_trend `diag_stop.py` ilk sentetik denemesi: martingalde ortR −0,41, stop payı %83 (anlamsız) | Barları göreli (o, h, l, c)/önceki kapanış dörtlüsü olarak BÜTÜN hâlinde karıştır; SL/TP'yi fiyat oranıyla yeni yola ölçekle (`diag_synth.py`) |
| E41 | **Stoplu + zaman çıkışlı tabanın kendisi yönsüz kenar taşıyabilir** (devam eden piyasada iki yön de +). "ortR > 0" yön sinyalinin kanıtı sanılır | BTC 10:00→16:00 ET, 1×ATR(H1) stop: rastgele long +0,087, short +0,067; H3-ROD +0,115'in ~%70'i bu | Yön sinyalini hep hücre − P1 (aynı saat, aynı yön) ve hem long hem short tabanıyla oku; long+short taban toplamı ≈ −maliyet değilse yol dinamiğini ayrıca raporla |
| E42 | **7/24 piyasada ≥1h TF'de kart ölçütü 5 (icra farkı) neredeyse boş**: sonraki 1m açılışı ≈ sinyal kapanışı, fark yalnız spread kadar kalıyor | BTC D1/H4/H1 hücrelerinde fark 0,001–0,024R; yalnız 5m'de 0,13R | 7/24 varlıklarda sürtünmeyi spread stresi + swap ile değerlendir; ölçüt 5'i yalnız ≤15m TF'lerde ayırt edici say |
| E43 | **Trend filtreli kuralların DISCOVERY'si ayı yılını içerse bile filtre o yılı boşaltır**: DISCOVERY'de seçim fiilen tek bir boğa yılına (2023) dayanır | H4D20-T-L DISCOVERY 81 olayın 78'i 2023'te; 2022'de 3 | Bölme başına olay sayısını yıl bazında raporla; ayı rejiminde hiç sınanmamış trend filtresini "bölmeler arası tutarlı" sayma |
