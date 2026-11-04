# NDX gece sürüklenmesi ("overnight drift / night effect") — literatür + ön-kayıtlı test (ON)

Kod ve ön-kayıt: `research/nasdaq_derin_20261013/overnight/` — `PROTOCOL.md` (sonuçlardan önce yazıldı; §7 uygulama
ayrıntısı da sonuçlardan önce eklendi), `axis_check.py`, `engine.py`, `run.py` (keşif), `cond_base.py` + `base_diff.py`
(taban A), `spread_audit.py` (icra denetimi, post-hoc), `lockbox.py` (kasa, bir kez açıldı). Çıktılar `results/`
(`discovery.txt/json`, `cond_baseA.json`, `base_diff.json`, `lockbox.txt/json`).
Python: `/opt/homebrew/opt/python@3.13/bin/python3.13 run.py` (≈1 dk). Canlı bot/backend/DB'ye dokunulmadı, commit yok.

**Tek cümlelik verdikt:** 10 ön-kayıtlı varyantın hiçbiri LIVE adayı değil. Koşulsuz gece/Avrupa-açılışı pencereleri
ya maliyet sonrası negatif (01–04, 02–03 ET) ya da yalnız piyasa betası (18:00→09:30, aynı sürede başka saatte tutmaktan
iyi değil); "düşüş günü sonrası" koşullu sürümler kartı geçiyor ama kenarın çoğu gecenin değil, ertesi günün tamamının
("korku döner" — GF-05/GF-10/CAPREV ile aynı mekanizma), 2021 sonrası yarıya iniyor, DAX'ta anlamlı değil ve DAX kasası
negatif. En iyi ihtimalle S10 (Avrupa penceresi | dün ≤ −%0,5 ∧ VIX ≥ 18,4) **GÖLGE adayı (C/B−)**.

---

## 1. Literatür ne diyor (büyüklük, saatler, yayın sonrası kalıcılık, koşullama, vadeli vs ETF)?

### Takeaway
Gece getirisi ABD endekslerinde gerçek bir tarihsel olgu; S&P e-mini'de 1998–2020 boyunca tek "özel saat" 02:00–03:00 ET
(Avrupa açılışı) idi, satış günlerinden sonra ve yüksek VIX'te güçleniyordu — ama spread sonrası koşulsuz strateji
negatifti ve yazarların kendi Temmuz 2026 takibi bu saatin 2021'den beri ≈0 olduğunu (NQ dahil) söylüyor.

### Cited Findings
- Boyarchenko-Larsen-Whelan (BLW), "The Overnight Drift": ABD hisse getirileri Avrupa piyasalarının açılış saatlerinde büyük ve pozitif; kapanıştaki emir dengesizliğiyle güçlü ilişki; satışlar sonrası gece geri dönüşü güçlü, rallilerden sonra çok zayıf (asimetri) — [NY Fed Staff Report 917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf); yayın: RFS 36(9), 2023, s. 3502–3547 — [IDEAS](https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html)
- En büyük pozitif getiri 02:00–03:00 ET: yıllık %3,7 (günde 1,48 bp); çoklu test (Bonferroni/BY) sonrası tam örneklem ve alt örneklemlerde sürekli anlamlı kalan TEK saat — [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- Kalıcılık: 23 yılın 20'sinde pozitif, 17'sinde anlamlı; haftanın her günü ve 12 ayın 9'unda anlamlı; 2020 en büyük yıl (%10,7 yıllık); 2002, 2008, 2019 hafif negatif. 1998–2010 ve 2011–2020 alt örneklemlerinde 24 saatlik profilin geri kalanı "oldukça farklı" (açılış saati ilk dönemde negatif, sonra düz; 17–18 yalnız ikinci dönemde anlamlı) — [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- 24:00–03:00 aralığındaki getirinin %50'si 02–03 saatinden; Tokyo DST doğal deneyi ve ABD-Avrupa DST uyumsuzluğu haftalarında öngörülebilirlik 04:00–05:00'e kayıyor (mekanizma = Avrupa likiditesinin gelişi) — [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- Strateji tablosu (2004–2020, ES): CTC (sürekli long) %8,95/yıl SR 0,42; CTO (16:15→09:30) %4,62; OTC %4,20; OD (02–03) %3,75 SR 1,10; OD+ (01:30–03:30) %6,21 SR 1,30; BtD (OD+ yalnız kapanış RSV<0 günleri) %6,07 SR 1,78. **Spread dahil:** CTO %0,38, OTC −0,05, OD −0,59 (SR −0,54), OD+ %1,91 (SR 0,26), BtD %4,04 (SR 1,10) — [SR917 Tablo IX](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- VIX etkileşimi: kapanış RSV'sinde 1 std düşüş VIX=20'de 2,6 bp, VIX 30'da 6,1 bp, VIX 12'de ≈0 gece getirisi üretir; negatif-RSV günlerinde VIX yükseldikçe OD getirisi artıyor (çift sıralama 6 farkın 5'i anlamlı) — [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- **Yayın sonrası (Temmuz 2026, aynı yazarlar):** 02–03 ET penceresi 1998–2020'de ES'in %5,9'luk kapanış-kapanış getirisinin %60'ından fazlasıydı; 2021–2025'te (1.245 gün) ortalaması "sıfıra yakın"; düz desen **NQ (Nasdaq-100 e-mini)** ve YM'de de geçerli. Açıklama: kapanış emir-dengesizliği dağılımı (RSV std %6,5 → %2,9) sıkıştı; VIX ortalaması yalnız 20,4 → 19,4; gece hacim payı %15 → %16. Yanlışlanabilir öngörü: dengesizlik dağılımı genişlerse sürüklenme geri gelir — [Liberty Street Economics, "The Disappearing Overnight Drift"](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- Bondarenko-Muravyev (ES tick, 2004–2018): 23:30–03:30 ET "EU-open" penceresi ortalama getirinin tamamını açıklıyor, yıllık %7,6, SR 1,67, t=6,4; günün geri kalanı ≈ −%0,8; her yıl/ay/gün pozitif (ikincil özet) — [Alpha Architect](https://alphaarchitect.com/market-return-around-the-clock/)
- Cliff-Cooper-Gulen (1993–2006): S&P 500 hisselerinde ortalama gece getirisi %0,028–0,048, gündüz −0,028…+0,002; endeks, vadeli ve ETF'lerde de var; büyük kısmı ilk işlem saatinde düşen yüksek açılış fiyatlarından — [CXO Advisory özeti](https://cxoadvisory.com/?p=1377). Ayrı makale: Kelly & Clark (2011) "Returns in trading versus non-trading hours: The difference is day and night" — [IDEAS](https://ideas.repec.org/a/pal/assmgt/v12y2011i2d10.1057_jam.2011.2.html)
- Bir 2016 çalışması dört büyük ABD ETF'inde gece-gündüz farkının 2006'dan itibaren belirgin azaldığını/kaybolduğunu bildiriyor (ikincil özet) — [CXO Advisory](https://cxoadvisory.com/?p=1377)
- Lou-Polk-Skouras (JFE 134(1), 2019): kesitte momentum kârlarının tamamı gece, diğer anomalilerin çoğu gündüz; "tug of war" = kurumlar gündüz momentuma karşı işlem yapıyor; aylık ~%2'lik gece-gündüz fark değişimi — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/87481) (kesit sonucu; endeks zamanlaması için doğrudan değil)
- Gerçek ürün: NightShares NSPY/NIWM (kapanışta vadeli al, açılışta sat) Haziran 2022'de açıldı, 31 Temmuz 2023'te kapandı; NSPY açılıştan beri −%6,9 (S&P +%22), NIWM −%10+; %0,55 yönetim ücreti + işlem maliyeti suçlandı. Başka bir kaynak −%4,6/−%4,7 diyor (tarih/baz farkı uzlaştırılamadı) — [WealthManagement/Bloomberg](https://www.wealthmanagement.com/etfs/night-effect-etfs-shut-down-overnight-stock-returns-elusive); [ETF Stream](https://www.etfstream.com:443/articles/blackout-for-night-effect-etfs)

### Inferences
- Literatür zaten "koşulsuz OD saati spread'i ödeyen için kârsız" diyor; tek maliyet-sonrası hayatta kalan, *dengesizlik/satış sonrası* koşullu sürümdü (BtD) — bizim S5/S6/S10'un mantığı bu. RSV verimiz yok; önceki gün getirisi vekil.
- 2021 sonrası koşulsuz etkinin NQ'da da sönmesi bizim 1h verimizle tutarlı (aşağıda: 02–03 saati 2016–20'de 1,19 bp t=2,07 → 2021–26'da 0,57 bp t=1,22).

### Gaps
- Bondarenko-Muravyev sayıları yalnız ikincil özetten; orijinal makale okunmadı.
- Liberty Street post'u koşullu (satış sonrası / yüksek VIX) sürüklenmenin 2021 sonrası durumunu raporlamıyor.
- Avrupa endeksleri (DAX) için yayımlanmış eşdeğer "gece sürüklenmesi" çalışması bulunamadı (arama yapılmadı/kaynak yok).

---

## 2. Bizim NDX verimizde saat-saat getiri: sürüklenme nerede, çağlar arası kararlı mı?

### Takeaway
2016–2020'de NDX CFD getirisinin büyük kısmı gece (18:00→09:00 ET ≈ 10,6 bp/gün vs gündüz 09–16 ≈ 1,9 bp), en güçlü saat
Globex yeniden açılışı 18:00 (3,4 bp, t=4,8) ve 02:00 (1,2 bp, t=2,1). 2021–2026H1'de bu tersine döndü (gece 2,9 bp vs
gündüz 3,5 bp); hiçbir gece saati t>2,1 değil; iki çağın 22 saatlik profili korelasyonu yalnız **0,17** (GF-03 teyidi).

### Cited Findings
- Saat ekseni doğru: 1m'de 2025-01…2026-09 her ay en büyük medyan aralık 09:30–09:31 ET (Şub–Nis 2025'te 10:00 makro verisi birinci, 09:31 ikinci); 30m'de 2021–26 her yıl 09:30; DAX 30m/1h 2019+ her yıl 09:00 Berlin — [axis_check.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/axis_check.py)
- Saatlik ortalama getiri (bp; bar açılışı → sonraki saat açılışı; NY saati), [results/discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt):

  | NY saat | 2016–20 bp (t) | 2021–26H1 bp (t) | 1m 2025-01→2026-06 bp (t) |
  |---|---|---|---|
  | 18 | **3,41 (4,78)** | 0,69 (1,29) | 2,49 (1,84) |
  | 23 | 0,01 | 0,63 (2,07) | 0,09 |
  | 00 | 0,93 (1,72) | 0,12 | −1,12 |
  | 01 | 0,76 (1,58) | 0,43 (1,09) | 0,31 |
  | **02** | **1,19 (2,07)** | 0,57 (1,22) | **2,09 (2,00)** |
  | 03 | 0,28 | 0,67 (1,06) | 2,08 (1,63) |
  | 05 | 1,09 (1,98) | 0,14 | −0,11 |
  | 11 | 1,28 (1,19) | 1,96 (1,87) | −0,61 |
  | 13 | −1,44 (−1,62) | 1,56 (1,39) | 4,34 (1,37) |
  | 22 | 0,09 | −0,51 (−1,35) | −1,63 (−2,04) |

- Gece (18→09) / 01–04 / gündüz (09→16) toplamları: 2016–20 10,58 / 2,23 / 1,92 bp; 2021–26 2,85 / 1,67 / 3,47 bp; 1m 2025–26 7,23 / 4,48 / 4,63 bp — [discovery.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.json)
- Çağlar arası saat profili korelasyonu: 0,168 (16/17 ET hariç; 17:00 bar'ı yalnız ~149 günde var — veri tuhaflığı, dışarıda); 1h 2021–26 ile 1m 2025–26 arası 0,22 — aynı dosya
- Aynı-süreli tüm başlangıç saatleri (taban A, brüt): 3 saatlik pencerede 01:00 başlangıcı 24'te **4.** (1,93 bp; diğerleri ort 1,27); 1 saatlikte 02:00 24'te **5.** (0,85 bp; diğerleri 0,17); 15 saatlikte 18:00 24'te **9.** (6,04 bp; diğerleri 5,82) — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)
- DAX 1h 2019–26 (ET saati): pozitif-anlamlı saatler 00:00 ET (1,11 bp, t=2,66), 02:00 ET (1,68, t=2,20), 05:00 ET (1,55, t=2,50); NDX 2021–26 profili ile korelasyon 0,28 — aynı dosya

### Inferences
- NDX'te klasik "gece etkisi" 2016–20'de güçlü, 2021+'da yok — Liberty Street'in ES/NQ için bulduğu sönmeyle aynı zamanlama. 02:00 saati 2025–26 1m'de yeniden pozitif (t=2,0) ama tek 18 aylık pencere; 2021–24 zayıf.
- Saat-saat profil çağlar arası taşınmıyor (0,17); tek-saat seçimine dayanan bir kural E17/E23 riskini taşır.

### Gaps
- 1h 17:00 ET satırı veri artefaktı (n≈149); 16:00→17:00 getirisi ölçülemiyor.

---

## 3. Ön-kayıtlı tutma stratejileri — her zaman long ve gün içi tabanına karşı, CFD maliyetleriyle

### Takeaway
Maliyet sonrası: Avrupa-açılışı pencereleri (S3 01→04, S4 02→03) **negatif/sıfır** (S4 net −0,012R, P(EV>0)=%0,02 —
anlamlı NEGATİF, BLW'nin spread-sonrası bulgusunun aynısı). Gece tutma S1 (18:00→09:30) kartı 6/6 geçiyor ama bu
**piyasa betası**: aynı uzunlukta başka saatte tutmakla aynı (24'te 9.), 2021+'da diğer yerleşimlerden kötü; her-zaman-long
(HOLD) da kartı 6/6 geçiyor (E13). 17:00 rollover'ını geçmeyen pencereler (18:00 girişi, 01→04) swap ödemiyor — CTO
(16:00→09:30) ödüyor ve 2021+'da swap getiriyi siliyor.

### Cited Findings
- Maliyet kalibrasyonu: Pepperstone endeks gece finansmanı = Nominal × (ARR ± %2,5)/360, rollover 17:00 New York; endeks CFD'lerinde Cuma üçlü swap; örnek uzun −%4,162 (= −1,66188 − 2,5) — [Pepperstone "Kosten und Gebühren" PDF](https://eu-assets.contentstack.com/v3/assets/bltaec35894448c7261/bltd4de9bfe319b6219/kosten-und-gebuhren.pdf)
- Kutunun gerçek NAS100 swap'ı: 5 lot BUY @29.503 → −25,16$/gece = −5,03 puan/lot ≈ yıllık %6,14 (→ ARR ≈ %3,64); SELL +0,93 puan/lot alıyor; GER40 SELL 10 lot −2,54$ → €STR ≈ %2,19 — [box_trades_40d.csv](/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/data/box_trades_40d.csv) (pozisyonlar 373421808, 384269483, 381310915)
- Spread: Dukascopy 2025 NDX bid/ask 1m — nakit seansta medyan 1,40 puan (09:31–16:01), seans dışında 3,4 puan (18:00 3,47; 01:00 3,42; 04:00 3,38); 18:00 yeniden açılışında bid getirisi mid'den ~0,8 puan şişik (18:00→19:00 bid +5,17 / mid +4,41 / ask +3,65 puan) — [spread_audit.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/spread_audit.py). Ön-kayıtlı 1,5 puan nakit seans spread'i; gece spread'i için "sp3" (3,0 puan) ayrıca raporlandı.
- Kart tablosu (NDX 1h 2016-05 → 2026-06, net = 1,5 p spread + swap; R = net puan / (σ20 günlük × fiyat); ölçüt 5 = 1m 2025-01→2026-06, gerçekçi T+1 dk + spread vs iyimser T) — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt):

  | Strateji | n | ortR | P(EV>0) | 1./2. yarı | ×1,5 spread | sp3 | brüt/net bp | swap p | yıllık % / Sharpe | kart |
  |---|---|---|---|---|---|---|---|---|---|---|
  | S1 NIGHT 18:00→09:30 | 2.419 | +0,044 | 1,000 | +0,060/+0,029 | +0,036 | +0,028 | 6,09/4,62 | 0 | 11,2 / 0,93 | 6/6 |
  | S2 CTO 16:00→09:30 | 2.495 | +0,021 | 0,960 | +0,025/+0,017 | +0,013 | +0,005 | 5,64/2,17 | 2,84 | 5,4 / 0,41 | 5/6 (icra ✗) |
  | S3 EU 01→04 | 2.490 | −0,003 | 0,303 | −0,013/+0,008 | −0,011 | −0,020 | 2,01/0,52 | 0 | 1,3 / 0,23 | 3/6 |
  | S4 OD 02→03 | 2.490 | −0,012 | 0,0002 | −0,019/−0,006 | −0,021 | −0,029 | 0,90/−0,59 | 0 | −1,5 / −0,50 | 2/6 |
  | S5 EU \| dün ≤−%0,5 | 619 | +0,007 | 0,727 | −0,006/+0,020 | +0,001 | −0,005 | 4,42/3,03 | 0 | 1,9 / 0,55 | 4/6 |
  | S6 EU \| dün ≤−%1 | 401 | +0,029 | 0,962 | +0,027/+0,031 | +0,023 | +0,018 | 7,21/5,85 | 0 | 2,4 / 0,76 | 6/6 |
  | S7 NIGHT \| dün ≤−%0,5 | 608 | +0,052 | 0,993 | +0,025/+0,078 | +0,046 | +0,040 | 10,07/8,70 | 0 | 5,3 / 0,66 | 6/6 |
  | S8 NIGHT \| dün ≤−%1 | 396 | +0,075 | 0,997 | +0,042/+0,109 | +0,070 | +0,065 | 13,88/12,53 | 0 | 5,0 / 0,67 | 6/6 |
  | S9 EU \| VIX ≥18,4 | 999 | +0,017 | 0,970 | +0,024/+0,010 | +0,013 | +0,009 | 4,20/2,92 | 0 | 2,9 / 0,61 | 6/6 |
  | S10 EU \| dün ≤−%0,5 ∧ VIX ≥18,4 | 388 | +0,035 | 0,993 | +0,044/+0,026 | +0,031 | +0,027 | 7,63/6,34 | 0 | 2,5 / 0,78 | 6/6 |
  | INTRA (1h vekil 10→16) | 2.495 | −0,002 | 0,466 | −0,009/+0,006 | −0,010 | −0,018 | 2,13/0,64 | 0 | 1,6 / 0,10 | 3/6 |
  | HOLD (her zaman long) | 2.495 | +0,044 | 0,983 | +0,055/+0,034 | +0,036 | +0,027 | 8,72/5,25 | 2,84 | 13,2 / 0,59 | 6/6 |

- İcra (ölçüt 5, 1m): S1 gerçekçi +0,031 vs iyimser +0,042 (fark 0,011 < 0,016 ✓); S2 +0,013 vs +0,021 (fark 0,008 > 0,0066 ✗); S7 +0,151 vs +0,220 (fark 0,069 < 0,076, sınırda ✓); S10 +0,103 vs +0,105 ✓ — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)
- Birebir 09:30 (NDX 30m, 2021-06→2026-06): S1 NIGHT +0,026R P=%95,2 ama **1. yarı −0,009** (ölçüt 3 ✗); S2 CTO +0,014 P=%81,6, 1. yarı −0,031, net −0,29 bp (swap 4,59 puan yiyor); INTRA +0,009 P=%64; HOLD +0,031 P=%84 — aynı dosya
- Çağlar (net R): S1 2016–20 +0,070 → 2021–26 +0,024; S3 −0,014 → +0,006; S4 −0,021 → −0,005; HOLD +0,056 → +0,034 — aynı dosya
- Taban A, 15 saatlik pencere (brüt, `base_diff.py`): 18:00 başlangıcı − aynı gün diğer başlangıçlar = +1,25 bp, P=%77,5; çağ 1 +5,17, **çağ 2 −1,75** — [base_diff.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/base_diff.json)

### Inferences
- S1 NIGHT'ın "6/6"sı zamanlama kenarı değil: aynı süreli rastgele yerleşim de aynı getiriyi veriyor; avantajı yalnız **varyans** (gece seansı oynaklığı düşük → Sharpe 0,93 vs HOLD 0,59) ve swap'tan kaçınma (18:00 girişi 17:00 rollover'ından sonra). 2021+'da bu avantaj bile kayboldu (çağ 2'de 18:00 yerleşimi diğerlerinden 1,75 bp kötü; 30m birebir 1. yarı negatif). Bot bağlamında "gece long tut" = beta almak; kart bunu ayırt edemiyor (HOLD da geçiyor) → taban A zorunluluğu doğru karar.
- Koşulsuz Avrupa-açılışı penceresi brütte gerçek ama küçük (02–03: ~0,9 bp ≈ 1,7–2 puan bugünkü fiyatta) — 1,5 puanlık spread'i karşılamıyor; gece spread'i (≈3,4 p Dukascopy) ile kesin negatif. BLW'nin "OD spread sonrası SR −0,54" bulgusu NDX CFD'de birebir tekrarlandı.
- CFD pratiği: 17:00 ET'yi geçen tutma (CTO, HOLD) 2023–26 faiz düzeyinde gecelik ~1,7 bp (5 puan) öder — CTO'nun 2021+ net getirisini sıfırlıyor. Gece stratejisi yapılacaksa giriş 18:00 sonrası olmalı.

### Gaps
- ARR tablosu 2016–2025 yıllık ortalama EFFR/€STR değerleri genel bilgiden yaklaşık (kaynaklanmadı); yalnız 2026 kutu swap'ından kalibre. Negatif EUR faizleri 0'a tabanlandı (muhafazakâr). Gerçek tarihsel Pepperstone swap serisi bulunamadı.
- Pepperstone NAS100 için saat-bazlı gerçek spread verisi yok; Dukascopy spread'i (seans dışı 3,4 p) muhtemelen Pepperstone'dan geniş.

---

## 4. Önceki gün getirisine ve VIX'e koşullu mu? (CAPREV "korku döner" ile bağ)

### Takeaway
Evet, koşul katkısı gerçek ve BLW yönünde: dün ≤ −%1 veya VIX ≥ 18,4 günlerinde Avrupa penceresi koşulsuzdan anlamlı iyi
(P %98,5–99,9). Ama bu koşullar **günün her saatini** yükseltiyor; Avrupa penceresinin aynı gündeki diğer 3 saatlik
pencerelere üstünlüğü yalnız +3,6–4,0 bp (P≈%95) ve 2021+'da +0,7–2,6 bp'ye iniyor. Gece (18:00→09:30) koşullu
sürümleri ise aynı gün yerleşimleri arasında **20'de 19.** — kenar ertesi günün tamamına yayılan "korku döner" etkisi.

### Cited Findings
- Taban B (koşullu − koşul-dışı, aynı pencere, net R, ay-blok bootstrap): S5 +0,013 (P %83,4); S6 +0,038 (P %98,5); S9 +0,033 (P %99,9); S10 +0,045 (P %99,7); S7 +0,010 (P %65,0); S8 +0,037 (P %87,6) — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)
- Taban A koşullu (aynı günler, 18:00 D−1 → 13:00 D arası 20 başlangıç; brüt bp): 3 saatlik 01:00 penceresi dn1.0 günlerinde 7,21 vs diğerleri 3,19 (2./20), VIX günlerinde 4,20 vs 2,10 (4./20), dn0.5∧VIX 7,63 vs 4,01 (5./20); 08:00 başlangıcı (nakit açılışı içerir) çoğu koşulda daha yüksek (dn1.0 10,43; dn0.5 7,23). 15 saatlik 18:00 penceresi dn0.5 10,20 vs 18,69 (19./20), dn1.0 14,11 vs 20,30 (19./20), VIX 7,32 vs 13,99 (20./20) — [cond_baseA.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/cond_baseA.json)
- Hedef − aynı gün diğer başlangıçlar ortalaması (brüt bp, ay-blok bootstrap): 01→04 | dn1.0 +4,03 (P %94,6; çağ1 +6,64 / çağ2 +2,59); | VIX +2,09 (P %89,0; +4,77 / +0,70); | dn0.5∧VIX +3,63 (P %95,0; +8,29 / +1,60); 02→03 | VIX +1,81 (P %98,2; +3,94 / +0,70); 18:00 15s | dn0.5∧VIX −9,96 (P %2,7) — [base_diff.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/base_diff.json)
- Çağlar (net R): S9 2016–20 +0,037 (P %97,9) → 2021–26 +0,007 (P %78); S10 +0,072 (P %99,5) → +0,019 (P %88); S6 +0,030 (P %82) → +0,028 (P %95); S8 +0,052 → +0,088 — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)
- Projede: VIX rejimi NDX yönünü öngörüyor ama genel girişlerde işlem başına ≈0,01R (GF-05); stres sonrası satış yasağı K5/K5b; CAPREV (stres ∧ VIX ≥ 18,4 → dip kırılımında al, seans kapanışı çıkışı) NDX+DAX 6/6 LIVE (GF-22); CAPREV gece taşıması M1/15m'de daha kötüydü (CP) — [KAPI_KAYIT_DEFTERI.md](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- BLW'nin asimetrisi (satış sonrası geri dönüş) NDX'te de görünüyor ama bizim veride bu, Avrupa saatine özgü küçük bir öne-yığılma + ertesi günün tamamına yayılan "korku döner" sürüklenmesi. Gece tutma, korku-dönüşünün en kötü yerleşimi (CP bulgusuyla tutarlı: CAPREV pozisyonunu gece taşımak kötüleştiriyordu).
- S10 ≈ CAPREV'in koşul hücresinin (stres ∧ VIX) gevşek bir sürümü; aynı günlerde CAPREV ile çakışır → portföye bağımsız ek değil, aynı faktöre ikinci maruziyet (E19).
- 2021 sonrası koşullu etkinin de yarıya inmesi Liberty Street'in "kapanış dengesizliği sıkıştı" açıklamasıyla tutarlı (dengesizlik küçülünce dealer'ın talep ettiği prim de küçülür).

### Gaps
- Kapanış emir-dengesizliği (RSV) verisi yok; önceki gün getirisi kaba vekil. CFD tick hacmiyle imzalı hacim kurulamadı.
- 10 varyantlık aile + 4+ tur NDX geçmişi (E23/E24): Bonferroni (%99) eşiğini yalnız S7, S8, S10 geçiyor; seçim-düzeltmeli maks. istatistik koşulmadı.

---

## 5. Kasa (2026-07-01 → 10-02) ve DAX bağımsız kontrol

### Takeaway
DAX'ta aynı tanımlar aynı işaretli ama anlamsız (P %68–81), kasada DAX Avrupa penceresi belirgin negatif. NDX kasasında
koşulsuz Avrupa penceresi negatif; koşullu S5/S6 küçük pozitif (n 21/12), VIX'li S9/S10 neredeyse hiç tetiklenmedi (n 6/4).
Bağımsız teyit yok.

### Cited Findings
- DAX keşif (spread 1,5 p, EUR swap): DX-EU (01→04 ET) +0,007R n=1.859 P %74, yarılar −0,008/+0,022; DX-PRE (08→09 Berlin) +0,003 P %68; DX-EU|dn0.5 +0,022 n=459 P %79; DX-EU|dn1.0 +0,038 n=245 P %81; DX-NIGHT (17:30→09:00 Berlin, 30m 2021+) +0,006 P %63 (swap 3,29 p) — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)
- Kasa NDX 1m (T+1 dk + 1,5 p): S1 +0,016R (n 63, bp −2,0); S2 +0,021; S3 −0,007; S4 −0,003; S5 +0,019 (21); S6 +0,016 (12); S7 −0,033 (21); S8 +0,089 (12); S9 +0,005 (6); S10 +0,006 (4); INTRA +0,018; HOLD +0,044 (bp −0,8). NDX 30m birebir benzer (S5 +0,040, S6 +0,055, S8 +0,206, S7 +0,040) — [lockbox.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/lockbox.txt)
- Kasa DAX: DX-EU −0,061R (n 67, P %15); DX-PRE −0,017; DX-EU|dn0.5 −0,121 (n 14); DX-EU|dn1.0 −0,055 (n 7); DX-NIGHT +0,001 — aynı dosya

### Inferences
- Kasa n'leri karar verdirecek büyüklükte değil (≈65 gün); ön-kayda göre kasa yalnız düşürebilir: DAX tarafı negatif → "DAX karşılığı aynı işaret ve kasada negatif değil" şartı sağlanmadı.

### Gaps
- DAX 1h 2019 öncesi seyrek (yılda <2.200 bar) → DAX yalnız 2019–2026; bağımsız örneklem NDX'in 10 yılının yarısı.

---

## 6. Hangi varyant 6 ölçütlü canlıya alma kartını geçiyor? Verdikt

### Takeaway
Kartı 6/6 geçenler: S1, S6, S7, S8, S9, S10 (+ kıyas HOLD). Ön-kayıtlı ek şartlarla (taban A, DAX, kasa) hiçbiri LIVE
adayı olamıyor. Sınıflama: S1/S7/S8 = beta/korku-dönüşü, geceye özgü değil → **RED**; S3/S4/S5 → **RED** (maliyet);
S2 → **RED** (icra + swap); S6/S9/S10 → **SHADOW adayı (C/B−)**, en iyisi S10.

### Cited Findings
- Verdikt gerekçeleri ön-kayıt §6'ya göre: (a) taban A — S1 15s yerleşim 24'te 9., S7/S8 20'de 19.; (b) Bonferroni — S6 %96,2, S9 %97,0 < %99; (c) çağ 2 — S9 +0,007 (P %78), S10 +0,019 (P %88); (d) DAX — aynı işaret, P %74–81; (e) kasa — DAX negatif, S9/S10 n 6/4 — [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/PROTOCOL.md), [results/](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/)
- Ekonomik büyüklük: S10 yılda ~39 olay × net ~6,3 bp ≈ nominalin %2,5'i/yıl (Sharpe 0,78); HOLD %13,2/yıl (Sharpe 0,59); S1 %11,2/yıl (Sharpe 0,93) — [discovery.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/overnight/results/discovery.txt)

### Inferences
- **Deftere önerilen satır (§2, yeni ön ek "ON"):**
  `| ON-01 | 2026-10-13 | Gece sürüklenmesi (BLW 2023; Avrupa açılışı 01→04/02→03 ET, gece 18:00→09:30, CTO 16:00→09:30; dün ≤−%0,5/−%1 ve VIX≥18,4 koşullu; spread 1,5 p + Pepperstone swap; ön-kayıt research/nasdaq_derin_20261013/overnight/PROTOCOL.md) | Koşulsuz Avrupa penceresi maliyet sonrası negatif (02→03 −0,012R P %0,02; 2021+ brüt ≈0 — Liberty Street 2026 ile aynı); gece tutma 6/6 ama aynı süreli rastgele yerleşimden farksız (beta; 2021+ kötü); koşullu sürümler kartı geçiyor (S10 388 olay +0,035R P %99,3) ama koşul günün tamamını yükseltiyor (Avrupa penceresi aynı gün diğer saatlerden +3,6 bp, 2021+ +1,6), gece koşullu 20'de 19., DAX anlamsız (P %74–81), DAX kasası negatif | X (koşulsuz/gece) · C (S10 gölge adayı) |`
- **§1 için yeni kanıt hatası önerisi (E27):** "Canlıya alma kartı her-zaman-long'u da geçirir": yükselen piyasada pasif long pencereler 6/6 alır (HOLD 6/6); kartın yanına **aynı süreli, aynı günlü, her başlangıç saati tabanı** (taban A) zorunlu olmalı — aksi hâlde beta kenar diye canlıya girer.
- S10 gölgeye bağlanacaksa: CAPREV ile aynı günlerde çakıştığı için ayrı etiketle, karar portföy katkısıyla (E19) verilmeli; 1. KURAL oturum notu ve deftere satır ekleme bu araştırmayı başlatan ajana bırakıldı (paralel araştırmacılar aynı dosyalara yazmasın diye).

### Gaps
- Seçim-düzeltmeli maks. istatistik (E24) koşulmadı; 10 varyant + taban testleri için yapılmalı.
- Pepperstone NAS100 gerçek gece spread'i ve 18:00 yeniden açılış dolum kalitesi canlıda ölçülmedi.
