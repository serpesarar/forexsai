# Piyasa gün içi momentumu (market intraday momentum) — ön-kayıt protokolü

Tarih: 2026-10-13. **Bu dosya sonuçlara bakılmadan yazıldı.** Sonradan değişiklik olursa §9'a tarihli, gerekçeli
ek olarak yazılır; bu bölümler değiştirilmez.

## 0. Defter kontrolü (3. KURAL)

- **GF-02 / H1 "kapanış akışı" (Baltussen+ 2021)** zaten denendi: ama orada (a) sinyal = gün getirisi |r| ≥ %1,
  (b) ürün = *kapı* — 15:00–15:50 ET arasındaki rastgele 1m girişlerinde "güne KARŞI yönü blokla", (c) ölçü =
  TP/SL braketli (G80, GS) R'nin gün-içi U-ortalamasından farkı (ilk sürüm E15 yüzünden yanıltıcıydı),
  (d) veri 2025–2026 1m. Sonuç: "saat-eşlemeli tabanla dört dönemde tutarsız" → X.
- **Bu çalışma neden yeni (tanım + veri + gerekçe):**
  1. Ürün bir *kapı* değil, **zamanlanmış strateji**: her işlem günü tek karar, giriş sabit saatte, çıkış 16:00 ET
     (braket yok — §3 meta-ders 5 "braket ≠ zaman": literatürdeki etki tam olarak zaman-çıkışlı son 30 dk getirisidir).
  2. Sinyaller literatürün kendi tanımları: Gao+ 2018 `r_ONFH` (önceki 16:00 → 10:00), ilk 30 dk tek başına,
     Baltussen+ 2021 `r_ROD` (önceki 16:00 → 15:30), geç-gün `r(12:00→15:30)`, ikinci-son yarım saat `r_SLH`.
  3. Veri: NDX 1h **10 yıl** (2016–2026) yıl-yıl, 30m 5 yıl, 1m icra kontrolü, **DAX bağımsız piyasa**, kasa.
- E15 (aynı gün ortalaması) kullanılmaz: tabanlar = aynı pencerede hep-AL ve rastgele yön (işaret permütasyonu).
- E23: NDX geçmişine bu proje 4+ tur baktı → kasa + DAX zorunlu, ana hipotez TEK ve önceden seçili.

## 1. Veri ve saat ekseni

| Kod | Kaynak | Dönem | Kullanım |
|---|---|---|---|
| N1h | `load_long('1h')` (UTC) | 2016-05 → 2026-06-30 | son-60 dk varyantları, 10 yıl yıl-yıl |
| N30 | `load_long('30m')` 2021-06 → 2023-09 + `bars_30m.parquet` 2023-10 → | keşif 2021-06 → 2026-06-30; kasa 2026-07-01 → 10-02 | **ana kart** (15:30–16:00) |
| N1m | `bars_1m.parquet` | 2025-01-02 → 2026-06-30 (2026-01-01→02-10 boşluk); kasa 07-01 → 10-02 | 5. ölçüt (icra), 1m ile aynı kuralların tekrarı |
| D30 | `dax_30m.parquet` | 2021-03 → 2026-10-02 | bağımsız piyasa |
| MAC | `macro_daily_patched.csv` | VIX_close, NDXCASH_close | **yalnız ÖNCEKİ gün** değeri |

- UTC → America/New_York (DAX: Europe/Berlin) `zoneinfo`/pandas ile; DST doğal.
- **Saat ekseni testi (zorunlu, sonuçtan önce):** her veri × yıl için medyan bar aralığının en büyük olduğu NY
  dakikası; 1m/30m'de 09:30, 1h'te 09:00 barı (09:30 içerir) olmalı; DAX'ta Berlin 09:00 (veya 15:30 ABD açılışı) civarı.
  Tutmazsa analiz durur.
- Gün kümesi: NYSE işlem günü = MAC'te `NDXCASH_close` olan günler (tatiller düşer). **Yarım günler** (Şükran
  Günü ertesi Cuma; 24 Aralık Pzt–Per; 4 Temmuz Sal–Cum ise 3 Temmuz) dışarıda. Gerekli barlardan biri yoksa gün dışarıda.
- DAX gün kümesi: verideki Berlin 09:00 ve 17:30 sınır barları olan hafta içi günler; 24/31 Aralık dışarıda.

## 2. Tanımlar (NDX, NY saati; fiyat = ilgili sınırdaki bar kapanışı)

- `P(t)` = bitişi t olan barın kapanışı. `C0` = önceki işlem gününün P(16:00).
- `r_ON` = P(09:30)/C0 − 1 (09:30 = 09:29 1m barının / 09:00–09:30 30m barının kapanışı).
- `r_FH` = P(10:00)/P(09:30) − 1 (ilk 30 dk). `r_ONFH` = P(10:00)/C0 − 1 (Gao+ 2018'in "ilk yarım saat"i budur).
- `r_ROD` = P(15:30)/C0 − 1 (Baltussen+ 2021). `r_ROD60` = P(15:00)/C0 − 1.
- `r_LATE` = P(15:30)/P(12:00) − 1 (geç-gün devamı). `r_SLH` = P(15:30)/P(15:00) − 1.
- Hedef pencereler: **LH** = 15:30 → 16:00; **L60** = 15:00 → 16:00.
- Yön = sign(sinyal) (0 → işlem yok). Giriş: karar barının (bitişi 15:30 / 15:00) **SONRAKİ 1m barının açılışı**
  (30m/1h veride: sonraki barın açılışı); çıkış: bitişi 16:00 olan barın kapanışı.
- Maliyet: **1,5 puan / işlem (gidiş-dönüş)**, stres ×1,5 = 2,25 puan. DAX: aynı 1,5 puan.
- **R birimi:** `R = (yön·(çıkış − giriş) − maliyet) / (giriş · dvol)`, `dvol` = NDXCASH günlük getirilerinin
  20 günlük std'si, **önceki gün** itibarıyla (CAPREV kartıyla aynı: "1× günlük oynaklık stopu" birimi;
  stop konmaz). DAX: kendi 17:30 kapanışlarından 20g std, önceki gün. Ayrıca puan ve bp raporlanır.
- Regresyon: `r_hedef = a + b·r_sinyal` (b×100, R², Newey-West yok — yalnız literatürle kıyas için).

## 3. Hipotezler (sabit, ayar YOK)

| ID | Sinyal | Hedef | Veri | Rol |
|---|---|---|---|---|
| **P1** | sign(r_ROD) | LH | N30 | **ANA HİPOTEZ — kart bunun üzerine** |
| S1 | sign(r_ONFH) | LH | N30 | Gao+ (ikincil) |
| S2 | sign(r_FH) (yalnız ilk 30 dk) | LH | N30 | ikincil |
| S3 | r_ONFH ve r_ROD aynı işaretse o yön, değilse işlem yok | LH | N30 | Baltussen η(ONFH,ROD) |
| S4 | sign(r_LATE) | LH | N30 | geç-gün devamı |
| S5 | sign(r_SLH) | LH | N30 | Gao r12 |
| S6 | sign(r_ROD60) | L60 | N1h (10 y) + N30 | son-60 dk, 10 yıl yıl-yıl |
| S7 | sign(r_ONFH) | L60 | N1h + N30 | son-60 dk |

Toplam 8 hipotez → ikincillerde Holm düzeltmesi (permütasyon p-değerleri üzerinden).

### Ön-kayıtlı koşullandırma bölmeleri (yalnız P1, S1, S6 için)
- **V1:** önceki gün VIX ≥ 18,4 vs < 18,4.
- **V2:** ilk-30 aralığı yüksek: (H−L)(09:30–10:00) / (P(09:30)·dvol) ≥ **yalnız ÖNCEKİ 250 günün** %67'lik kantili
  (nedensel tertil) vs diğerleri.
- **V3:** güçlü sinyal: |sinyal| ≥ 1,0 × dvol (Rosa 2022 eşik fikri; GF-02 H1'in |%1| eşiğinin vol-normalize hâli).
Literatür iddiası (önceden yazılı): yüksek VIX / yüksek ilk-30 aralığı / güçlü sinyal kovasında ortR daha büyük.
Bölme sonucu kart DEĞİLDİR; bir kova ancak kendi başına 6 ölçütü geçerse ayrı scope adayı olur ve yine kasa+DAX ister.

## 4. Tabanlar ve plasebo

- **Hep-AL** aynı pencerede (NDX sürüklenmesi), aynı maliyet.
- **İşaret permütasyonu:** sinyal işaretleri günler arasında 2.000 kez karıştırılır → stratejinin ortR'si için
  boş dağılım; p = P(boş ≥ gözlenen). Bu "rastgele yön / aynı yön sayısı" tabanıdır.
- **Saat plasebosu:** aynı r_ROD-benzeri sinyal (önceki 16:00 → t) ile t → t+30 dk penceresi, t = 11:00…15:00
  (30 dk adım). LH özel değilse etki tüm gün sürer (genel trend) — bilgi amaçlı.

## 5. Canlıya alma kartı (CLAUDE.md 2. KURAL) — P1 üzerinde, keşif verisi N30 (2021-06 → 2026-06-30)

1. hacim ≥ 150 olay; 2. ortR > 0 ve gün-blok bootstrap P(EV>0) ≥ %90; 3. kronolojik iki yarı ≥ 0;
4. spread ×1,5'te ortR > 0; 5. icra: sinyal barı kapanışı/spreadsiz giriş ile sonraki 1m açılışı + spread arasındaki fark
   < ortR/2 (N1m'de ölçülür; N30 için sonraki 30m barın açılışı); 6. aynı anda tek pozisyon (günde tek işlem, yapısal) ile pozitif.
Ek (karar ölçütü, karta ek): **hep-AL tabanını geçmeli** (fark > 0, permütasyon p ≤ 0,10).

## 6. Bağımsız kontroller (bir kez, en sonda)

- **Kasa:** 2026-07-01 → 2026-10-02, N30 + N1m, yalnız P1 ve S6 — **bir kez** açılır. Ölçüt: ortR > 0 (n ≈ 60 → yalnız işaret).
- **DAX:** P1'in DAX karşılığı (Berlin): r_ROD = P(17:00)/C0(17:30 dün) − 1 → hedef 17:00 → 17:30; S1/S2 karşılığı
  ilk 30 dk = 09:00 → 09:30 (ONFH = dün 17:30 → 09:30). Ölçüt: ortR > 0 ve P(EV>0) ≥ %90.
- **10 yıl yıl-yıl (S6):** yılların ≥ %70'inde ortR > 0.

## 7. Verdikt eşlemesi (önceden)

- **LIVE adayı:** P1 kartı 6/6 + hep-AL'ı geçer + kasa > 0 + DAX > 0 (P ≥ %90). (Yine de önce GÖLGE.)
- **SHADOW:** kart 6/6 ama bağımsız kontrollerden biri başarısız; veya 5/6 ve eksik ölçüt yalnız hacim.
- **RED:** kart ≤ 5/6 (hacim dışı bir ölçüt) veya hep-AL'ı geçmiyor.

## 8. Çıktılar
`intraday_momentum/run_*.py`, `results/*.json|csv`, notlar
`research_notes/NASDAQ gün içi kenar araştırması/intraday_momentum.md`. Canlı bot/backend/DB'ye dokunulmaz, commit yok.

## 9. Ekler (sonradan)

**Ek-1 (2026-10-13, saat ekseni testi sonrası, HİÇBİR sonuç görülmeden):**
- NDX 1m ve 30m: her ay açılış sıçraması 09:30 ET'de (1m'de 2025 Şub–Nis 10:00 tepe = 10:00 makro verileri; 09:30
  ikinci); CFD 16:00 kapanışı ↔ NDXCASH kapanışı aylık medyan farkı tüm aylarda en küçük 16:00'da (30m 64/64, 1m 20/20).
- NDX 1h uzun veri: 122 ayın 119'unda 16:00 en iyi eşleşme; **2017-12, 2018-01, 2018-02 aylarında 17:00 eşleşiyor**
  (etiketler 60 dk geç; 2017 kış saati dönemi). Karar: N1h'ten **2017-11-05 → 2018-03-11** (o kışın tüm ABD standart
  saati dönemi) çıkarılır. Düzeltme denenmez.
- DAX 30m: ABD standart saatinde (NY DST değil) açılış sıçraması Berlin 08:00 etiketinde (436 gün), ABD yaz saatinde
  09:00'da (984 gün) → kaynak dönüşümü ABD DST kuralıyla 60 dk erken etiketlemiş. Karar: **NY DST değilken DAX ts +60 dk**
  düzeltilir; düzeltme sonrası saat ekseni testi yeniden koşulur (`run_0_axis.py` çıktısına eklenir).
