# Ajan Tartışma Sistemi — Denetim + Karar Saati Analizi (2026-07-26)

**Soru (kullanıcı):** Tartışma sistemi ne kadar başarılı? Hangi saatlerde hangi
semboller daha iyi? Analizi NY 09:45 yerine Çin açılışı / 01:00 / 03:00 gibi
başka saatlerde koştursak daha mı iyi olur?

**Kısa cevap:**
1. Sistem şu an **yazı-tura** seviyesinde (n=32 yönlü çağrı, 60dk %53, 240dk %53).
2. En büyük kusur saat değil: **yapısal ayı yanlılığı** — 25 ayı / 7 boğa çağrısı,
   piyasa ise 29 yukarı / 28 aşağı. p=0.002. Ayı çağrıları negatif beklenen değerli.
3. **Saat seçimi yön açısından gürültü:** 2.4 yıllık 24 saatlik veride hiçbir
   sembolde hiçbir saat plaseboyu geçmiyor. Çin açılışı/01:00/03:00 dahil.
4. Saatin ölçülebilir tek gerçek etkisi **hareket büyüklüğü**. NDX ve USOIL
   zaten doğru saatte; DAX ve XAU biraz erken koşuyor.

---

## 1. Sistem ne yapıyor

`services/bias_debate_engine.py` — 8 ajan (boğa/ayı kanatları + 3 gerçek-yapı
ajanı + hedef-seviye ajanı + CIO), `DEBATE_ROUNDS=3` karşılıklı çürütme. Model
yönlendirmesi `llm_router.py` (CIO/debate → Kimi, veri ajanları → DeepSeek).
Çıktı `bias_test_log`'a yazılır, `fill_outcomes` 5m mumlardan +10dk…+6sa
getirileri notlar. Zamanlama `bias_auto_runner.tick()`:

| Sembol | Koşu (UTC) | run_label |
|---|---|---|
| NDX | 12:00, 13:45 | `0800_main`, `0945_confirm` |
| XAU | 08:00 | `xau_daily` |
| DAX | 08:10 | `dax_daily` |
| USOIL | 13:05 | `usoil_daily` |

---

## 2. Canlı karne — n çok küçük

2026-07-06 → 07-24, `_dup` satırları hariç **58 koşu, bunun 32'si yönlü**
(kalan 26'sı nötr/choppy = çekimser).

| Sembol | yönlü n | 10dk | 30dk | 60dk | 240dk | ort. getiri 240dk |
|---|---|---|---|---|---|---|
| NDX | 13 | 54% | 46% | 54% | 69% | +0.25% |
| XAUUSD | 9 | 67% | 56% | 56% | 44% | −0.01% |
| GDAXI | 3 | 67% | 67% | 67% | 33% | −0.15% |
| USOIL | 7 | 71% | 43% | 43% | 43% | −0.35% |
| **TOPLAM** | **32** | **63%** | **50%** | **53%** | **53%** | **+0.01%** |

**Hiçbiri anlamlı değil.** NDX'in 240dk %69'u (9/13) → p=0.27. Panelde "birincil
ufuk" olarak NDX 240dk kullanılıyor ama bu n=13'lük bir gözlem; kanıt değil.
10dk'daki %63 muhtemelen kısa vadeli momentum sürekliliği — tartışma o anki
hareketi okuyup uzatıyor, öngörü değil.

Çekimserlik oranı: DAX %70, NDX %50, XAU %25, USOIL %30. DAX'ta 10 koşunun
7'si "karar yok" — token harcanıyor, çıktı üretilmiyor.

---

## 3. ANA KUSUR — yapısal ayı yanlılığı

| | çağrı | 60dk isabet | 240dk isabet | ort. getiri 240dk |
|---|---|---|---|---|
| **bearish** | **25** | 13/25 (52%) | 12/25 (48%) | **−0.077%** |
| bullish | 7 | 4/7 (57%) | 5/7 (71%) | **+0.316%** |

Sistem **3.6 kat daha fazla ayı** çağırıyor. Aynı dönemde piyasa 29 yukarı /
28 aşağı kapadı — yani ayı yanlılığı piyasadan gelmiyor, modelden geliyor.

Binom testi: 25/32 ayı, %50 beklentiye karşı **p = 0.0021**. Bu tesadüf değil.

Ve yanlılık pahalı: ayı çağrıları negatif beklenen değerli, az sayıdaki boğa
çağrısı pozitif. LLM'ler risk anlatısına doğal olarak meyleder ("değerleme
yüksek", "gap kapanır", "direnç var") — `SYMBOL_PROFILES` içindeki NDX uyarısı
("stres rejimi olmadan yüksek güvenli ayı çağırma") bu yanlılığı **durduramamış**:
NDX'te 10 ayı / 3 boğa.

Ayrıca güven kalibrasyonu yok: ortalama güven 57, isabet 53. Güven ile isabet
arasında ilişki görünmüyor (CLAUDE.md'de zaten "LLM confidence ters-kalibre"
notu var — bu veri onu doğruluyor).

---

## 4. Saat sorusu

### 4a. Yön öngörülebilirliği — hiçbir saatte yok

`research/debate_hour_lab.py`. Mantık: bir tartışma o saatte ancak **o saatte
mevcut olan bilgi** kadar iyi olabilir. Tavanı ölçtük.

* Veri: yfinance 1h, ~2.4 yıl. NQ=F→NDX, GC=F→XAU, CL=F→USOIL (vadeliler 24
  saat işlem görür → Asya/Çin saatleri ölçülebilir), ^GDAXI→DAX (nakit seans).
* `candle_cache` bu iş için **kullanılamaz**: kapsama delikli (NDX'te US seansı
  saatleri ~133 bar, diğer saatler ~76) — saatler arası kıyası bozar.
* Skor = **beceri** = koşullu kuralın test isabeti − en iyi SABİT yönün test
  isabeti. Gerekçe: `always_long` bir saatte %65 tutuyorsa tartışmaya gerek
  yoktur; tartışmanın değeri sabit yönü geçtiği kadardır.
* Kural + sabit yön kronolojik train'de (ilk %60) seçilir, test'te (son %40)
  raporlanır. 24 saat × 4 ufuk × 6 kural taranıyor → **plasebo**: 150 tur
  karıştırılmış ileri getiri, aynı seçim prosedürü.

| Sembol | zirve beceri | plasebo p95 | sonuç |
|---|---|---|---|
| NDX | +16.9pp | +20.0pp | ❌ geçemedi |
| GDAXI | +9.4pp | +25.5pp | ❌ geçemedi |
| XAUUSD | +12.8pp | +19.9pp | ❌ geçemedi |
| USOIL | +19.3pp | +19.0pp | ⚠ sınırda (+0.3pp) |

**Hiçbir saat gerçek yön edge'i taşımıyor.** USOIL'in sınırdaki geçişi bulgu
değil: 4 sembol p95 eşiğinde test edilirse en az birinin şans eseri geçme
olasılığı 1−0.95⁴ = **%18.5**. Tam olarak beklenen sonuç.

Kullanıcının özel olarak sorduğu saatler de dahil — Çin/HK açılışı (01:00),
Asya öğleden sonrası (03:00), Tokyo kapanışı (06:00) — hiçbiri ayrışmıyor.

### 4b. Saatin ölçülebilir tek gerçek etkisi: hareket büyüklüğü

Bu betimsel bir istatistik, plasebo gerektirmez: karar saatinden sonraki 4
saatte medyan mutlak hareket (o anki 1h ATR'ye oranla). 4 saatlik yönlü bir
karar, önünde 4 saatlik yol kalmayan bir saatte verilirse tanım gereği ölüdür.

| Sembol | mevcut koşu | hareket sırası | en hareketli saat | değerlendirme |
|---|---|---|---|---|
| **NDX** | 12:00 + 13:45 UTC | **1/24 ve 3/24** | 12:00 (2.27 ATR) | ✅ zaten optimal |
| **USOIL** | 13:05 UTC | **4/24** (1.49 ATR) | 11:00 (1.65 ATR) | ✅ iyi, marj %11 |
| **XAUUSD** | 08:00 UTC | **8/24** (0.76 ATR) | 10:00 (1.28 ATR) | ⚠ %68 daha fazla hareket 10:00'da |
| **GDAXI** | 08:10 UTC | **5/6** (0.67 ATR) | 11:00 (0.80 ATR) | ⚠ seansının alt sırasında, marj %19 |

NDX için mevcut 12:00 UTC koşusu 24 saatin en hareketlisi — çünkü sonraki 4
saat ABD nakit açılışını kapsıyor, ama o anki ATR hâlâ küçük. Yani "önümüzde
ne kadar yol var" oranı zirvede. **NDX'i oynatmaya gerek yok.**

⚠ Metodoloji notu: ilk koşuda DAX'ın geç seans saatleri sahte biçimde en
hareketli görünüyordu — ileri pencere seans kapanışını atlayıp ertesi sabaha
uzanıyordu. İleri pencere guard'ı sıkılaştırıldı (`h*1.5+1` saat); düzeltme
sonrası DAX'ın en hareketli saati 14:00 değil 11:00 ve marj 2.2× değil %19.

### 4c. Neden canlı A/B testi yapılamaz

"Aynı tartışmayı 5 farklı saatte koştur, hangisi tutuyor bak" fikri
istatistiksel olarak imkânsız:

| Ayırt edilecek fark | gereken n | süre (0.55 yönlü çağrı/gün) |
|---|---|---|
| %55 vs %50 | ~784 | ~5.5 yıl |
| %60 vs %50 | ~196 | ~17 ay |
| %65 vs %50 | ~87 | ~7.5 ay |

(tek örneklem binom, α=0.05, güç %80). **Sembol başına, saat başına.** 5 aday
saat × 4 sembol = 20 hücre. Şu anki tüm veri seti 32 yönlü çağrı — tek bir
hücrenin gereksiniminin bile altında.

Bu yüzden "en iyi saati bulmak için hepsini koşturalım" yaklaşımı yıllar sürer
ve o sürede toplanan veri de yeni saat kararlarını haklı çıkarmaz.

---

## 5. Öneriler — öncelik sırasıyla

**1) Ayı yanlılığını düzelt (en yüksek etki).** Saat değişikliği değil, asıl
sorun bu. Somut seçenekler:
   - CIO promptuna simetri zorlaması: "son 20 çağrının yön dağılımı" enjekte
     edilsin; %70'i tek yöndeyse CIO'dan gerekçelendirme istensin.
   - `recent_track_record` zaten sembol bazlı karne veriyor — içine **yön
     dağılımı + yöne göre isabet** eklenirse ajan kendi yanlılığını görür.
   - Ya da doğrudan: ayı çağrısı için boğa çağrısından daha yüksek kanıt eşiği.

**2) DAX'ın çekimserliğini ele al.** 10 koşunun 7'si karar üretmiyor. Ya
   koşuyu 11:00 UTC'ye al (hem %19 daha fazla hareket hem Londra öğle yapısı
   oturmuş olur), ya da DAX'ı tamamen durdur — şu haliyle token yakıyor.
   `BIAS_SYMBOL_RUNS_UTC` içinde `08:10=dax_daily:GDAXI.INDX` → `11:00=...`

**3) XAU'yu 08:00 → 10:00 UTC'ye al.** Sonraki 4 saatte %68 daha fazla hareket.
   Yön edge'i yok ama en azından kararın üzerine düşeceği bir hareket olur.

**4) NDX ve USOIL'e dokunma.** İkisi de hareket sıralamasında zirvede (1/24,
   3/24, 4/24). Yeni saat eklemek yalnızca token maliyeti ekler.

**5) Yeni saat EKLEME.** Çin açılışı / 01:00 / 03:00 koşuları için hiçbir kanıt
   yok; Asya saatleri hem yön becerisi göstermiyor hem de hareket açısından
   alt sıralarda (NDX 01:00 = 0.39 ATR vs 12:00 = 2.27 ATR).

**6) Karar ufkunu dürüstçe yeniden türet.** `PRIMARY_HORIZON_MIN` NDX için 240dk
   diyor ama dayanağı n=13. n≥30 olana kadar panelde "erken gözlem" etiketiyle
   gösterilmeli.

**7) Veri hijyeni (küçük).** 2026-07-08'de iki satır yanlış `run_label` ile
   yazılmış: GDAXI ve XAUUSD `0945_confirm` etiketiyle 21:49/22:05 UTC'de.
   Saat bazlı raporlamayı kirletir (`run_label` zaman kovası olarak okunuyor).

---

## Üretilen dosyalar
- `research/debate_hour_lab.py` — saat tavanı laboratuvarı (yeniden koşulabilir)
- `backend/data/debate_hour_report.md` — sembol × saat tam tablolar
