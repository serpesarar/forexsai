# Claude Decider — tam geçmiş denetimi, kapı madenciliği ve rejim ölçümü
**Tarih:** 2026-09-14 · **Veri:** `decider_journal` tamamı (5.297 karar, 2026-06-30 → 2026-09-14)
**Kapsam:** 1.531 OPEN kararı / 1.515 grade edilmiş · 4.350 karşı-olgu (mekanik) grade

---

## 0. Yönetici özeti

1. **Bir tane gerçek "yanlış → doğru" var, ama Temmuz'da ve WR'a bakarak görülemez:**
   XAU'nun stop geometrisi (2026-07-27) RR 0.40 → 0.67 düzeltildi; başabaş %71.4'ten
   %59.9'a indi, EV −0.081R → +0.004R. Dikkat: **WR %65.0'ten %60.1'e DÜŞTÜ.** Sistem
   yön tahmininde değil GEOMETRİDE yanlıştı (bkz. §1-B).
   Bunun dışında sistem 11 haftadır başabaşın etrafında salınıyor: toplam WR %61.1,
   başabaş %59.9 → **EV +0.006R**.
2. **%73.2'lik hafta tek haftalık bir sıçramaydı ve hemen geri döndü:** ertesi hafta
   (09-07 → 09-13) **%52.8 / −0.118R**.
3. **Decider'ın seçim alfası yok.** Karşı-olgu (her kayıtta "primary_dir açsaydı" mekanik
   sonucu) 11 haftanın 10'unda decider'ın ±4pp'si içinde. Yani sonuçları belirleyen
   decider'ın seçiciliği değil, piyasanın o haftaki hâli.
4. **Aranan "rejim" doğrulanmadı.** İyi/kötü haftayı ayırdığı sanılan ADX(1h) farkı
   (33.6 vs 17.1) tüm geçmişte tekrar etmiyor; rejim **kalıcı da değil** (geçmiş 50/100/200
   işlemin WR'ı sonraki işlemi öngörmüyor, r≈0.01-0.05). **Rejim zamanlanamaz.**
5. **Buna karşılık iki gerçek kapı bulundu ve OOS'ta ayakta kaldı** → `entry_quality.py`
   olarak GÖLGE modda canlıya bağlandı.

---

## 1. Haftalık tam döküm

| hafta | decider n | WR | EV | karşı-olgu n | WR | EV | ADX1h | VIX |
|---|---|---|---|---|---|---|---|---|
| 06-29 | 29 | %62.1 | +0.009 | 383 | %63.2 | +0.024 | 36.8 | 17.3 |
| 07-06 | 87 | %63.2 | +0.056 | 491 | %68.2 | +0.042 | 18.5 | 17.3 |
| 07-13 | 156 | %61.5 | +0.026 | 564 | %62.2 | −0.049 | 24.5 | 17.4 |
| 07-20 | 161 | %64.6 | +0.027 | 376 | %66.2 | +0.013 | 19.6 | 17.9 |
| 07-27 | 399 | %58.4 | −0.053 | 569 | %58.2 | −0.049 | 27.6 | 18.3 |
| 08-03 | 91 | %59.3 | −0.009 | 332 | %57.8 | −0.034 | 33.3 | 17.2 |
| 08-17 | 156 | %64.7 | +0.081 | 390 | %62.3 | +0.041 | 23.6 | 16.1 |
| 08-24 | 137 | %56.9 | −0.049 | 456 | %60.7 | +0.014 | 19.7 | 15.9 |
| **08-31** | 138 | **%73.2** | **+0.222** | 441 | %63.0 | +0.053 | 33.6 | 15.8 |
| **09-07** | 161 | **%52.8** | **−0.118** | 339 | %55.5 | −0.074 | 17.1 | 16.1 |

**Sembol bazında (tüm geçmiş, başabaş %59.9):**

| sembol | n | WR | EV | verdikt |
|---|---|---|---|---|
| GDAXI.INDX | 202 | %63.9 | **+0.066R** | tek net pozitif |
| NDX.INDX | 551 | %61.9 | +0.034R | hafif pozitif |
| XAUUSD | 532 | %61.3 | −0.015R | başabaş altı |
| USOIL.FOREX | 230 | %56.1 | **−0.063R** | başabaşın altında, kanayan taraf |

---

## 1-B. "Önceden yanlış yapıyordu, şimdi doğru yapıyor" — EVET, bir tane var

Haftalık WR serisinde bu GÖRÜNMEZ, çünkü müdahalede **WR düştü ama EV yükseldi**.
Epoch ayrılmadan bakmak (projenin `canonical-signal-metrics` kuralının yasakladığı şey)
tam olarak bu bulguyu gizliyor.

**XAU stop geometrisi müdahalesi** (2026-07-27, commit `85dc9b1`: 2.5 → 1.5 ATR):

| dönem | n | RR | başabaş WR | gerçekleşen WR | EV | verdikt |
|---|---|---|---|---|---|---|
| ÖNCE | 123 | 0.40 | **%71.4** | %65.0 | **−0.081R** | ⛔ yapısal −EV |
| SONRA | 409 | 0.67 | %59.9 | %60.1 | **+0.004R** | ✅ başabaşın üstü |

Yanlış olan **yön tahmini değil, geometriydi**: sistem, kazanması için %71.4 WR gereken
bir TP/SL ile oynuyordu ve %65 üretiyordu — yani iyi tahmin edip yine de para kaybediyordu.
Stop 1.5 ATR'ye çekilince başabaş %59.9'a indi ve aynı sistem artıya geçti.
**WR %65 → %60.1'e DÜŞTÜ, EV −0.081 → +0.004'e ÇIKTI.** Çıplak WR'ın neden yasak olduğunun
ders niteliğinde örneği.

⚠ Ama bu müdahale **Temmuz sonunda**; son iki haftadaki salınımın sebebi DEĞİL.

**Diğer epoch'lar — ölçüldü, etkisiz:**

| epoch | n | WR | kenar (WR−başabaş) | EV |
|---|---|---|---|---|
| Opus dönemi (08-21 öncesi) | 1055 | %61.0 | +1.2pp | −0.000R |
| Sonnet+effort dönemi | 460 | %61.1 | +1.2pp | +0.020R |

Model değişikliği karar kalitesini **ölçülebilir şekilde etkilememiş** (kenar birebir aynı:
+1.2pp). Kota tasarrufu bedavaya gelmiş — bu iyi haber.

XAU serbest-zekâ (`hybrid_v1`) n=435, kenar +0.1pp, EV −0.005R; kanıt-temelli akış n=1080,
kenar +1.6pp, EV +0.010R. Free mod hâlâ sistemin zayıf tarafı.

**🔴 gold_brain hiç değerlendirilmemiş:** 2026-07-29/30'da kurulan COT+FRED altın
zenginleştirmesi (`gold_brain.py`, `cot_gold.py`, `fred_macro.py`, git'e HİÇ commit
edilmemiş) 07-30 → 08-09 arası **290 karar üretmiş, 290'ı da WAIT**, karşı-olgusu da
hiç grade edilmemiş (`cf_outcome` 290/290 None). Yani: ne bir işlem açtı, ne ölçülebilir
tek bir çıktı verdi, ve 08-09'da sessizce durdu. Ölçülmemiş, terk edilmiş alt-sistem.

## 1-C. Epoch-düzeltilmiş haftalık kenar (WR − başabaş)

| hafta | n | kenar |
|---|---|---|
| 06-29 | 29 | +2.2pp |
| 07-06 | 87 | +3.3pp |
| 07-13 | 156 | +1.7pp |
| 07-20 | 161 | +4.7pp |
| 07-27 | 399 | −1.5pp |
| 08-03 | 91 | −0.5pp |
| 08-17 | 156 | +4.9pp |
| 08-24 | 137 | −2.9pp |
| **08-31** | 138 | **+13.3pp** |
| **09-07** | 161 | **−7.1pp** |

Trend yok. Son iki hafta, serinin **zıt yönlerdeki iki uç değeri** — küçük pozitif bir
kenar etrafında ders kitabı ortalamaya-dönüş.

## 2. Decider'ın çekirdek tezi veri tarafından çürütülüyor

Decider mean-reversion çalışır: `primary_dir` = "en güçlü aşırılık yönü", kanıt kapıları
`rev_chan`/`rev_vwap` aşırılıkta ateşler. Tez şudur: **ne kadar aşırı, o kadar iyi.**

`chz_dir` = fiyatın, işlem yönünün TERSİNE, 5m kanalında kaç sigma uzaklaştığı
(BUY'da kanal dibi, SELL'de kanal tepesi) — yani "söndürmeye çalıştığımız hareketin derinliği".

| chz_dir kovası | karşı-olgu n / WR / EV | decider n / WR / EV |
|---|---|---|
| < 0.5 | 1350 · %64.2 · −0.001 | 422 · %63.7 · +0.035 |
| 0.5–1.0 | 526 · %65.8 · +0.061 | 218 · %65.1 · +0.078 |
| 1.0–1.5 | 553 · %63.5 · +0.032 | 230 · %60.0 · −0.005 |
| 1.5–2.0 | 834 · %60.9 · +0.003 | 282 · %63.5 · +0.051 |
| 2.0–2.5 | 461 · %56.8 · −0.059 ⛔ | 226 · %57.5 · −0.044 ⛔ |
| ≥ 2.5 | 304 · %53.9 · −0.107 ⛔ | 121 · **%49.6** · **−0.174** ⛔ |

**Monoton düşüş, iki bağımsız veri setinde de.** Tez tam tersi yönde çalışıyor: en iyi bölge
sığ aşırılık (0.5–1.0), en kötü bölge derin aşırılık. Bu tam olarak botun `entry_gate.py`
kapısındaki **"bıçak yakalama"** (madde 8) koşulunun yasakladığı şey — decider'da bu kapı yoktu.

⚠ Not: VWAP aşırılığında (`vwz_dir`) aynı çöküş YOK (düz/hafif pozitif). Tehlikeli olan
spesifik olarak **kanal** aşırılığı.

---

## 3. Bot'un kapıları decider'da çalışıyor mu?

`yeni deneme/entry_gate.py` 8 koşullu skor = **trend-devam** felsefesi (EMA200/EMA50 tarafı,
ADX≥20, 1h momentum lehte, bıçak yakalama yasağı, hacim sakin). Decider ise **ortalamaya-dönüş**.
İkisi felsefe olarak zıt. Botun kapıları decider verisinde tek tek test edildi:

| bot kapısı | decider verisinde sonuç | verdikt |
|---|---|---|
| 5m/30m/1h/4h trend hizası | lehte %59.5-60.7 vs karşı %60.8-62.4 | ❌ fark yok — devretme |
| ADX(5m) ≥ 20 | ≥20 %60.9 vs <20 %62.5 | ❌ hatta hafif ters |
| **hacim < 1.5×** | **≥1.5 → %54.1 / −0.101R** | ✅ **birebir tekrarlandı** |
| bıçak yakalama (run30) | kanal karşılığı: chz_dir≥2.0 → %55-57 | ✅ **tekrarlandı** |
| 4/4 TF trend uyumu | %54.1 / −0.134R | ⛔ tümü hizalıyken KAYBEDİYOR (geç giriş) |

**Cevap:** Decider bot'un kurallarına göre çalışmıyordu; kendi koruyucuları (drift-nöbetçi,
hafta-sonu kapısı, sert yasaklar) var ama botun giriş-kalitesi kapıları yoktu. Botun 8
koşulundan **yalnız 2'si** decider'ın mean-rev doğasında da geçerli — ve ikisi de artık bağlandı.
Trend kapılarını devretmek yanlış olurdu: decider'ın işlem tipinde ölçülebilir katkısı yok.

---

## 4. Rejim: ASIL SEBEP — örneklemde rejim çeşitliliği yok

**Tüm 2,5 aylık journal TEK bir düşük-oynaklık rejiminden ibaret:**

| gösterge | aralık | not |
|---|---|---|
| VIX | **15.1 – 19.6** (medyan 17.1) | VIX ≥ 20 olan kayıt: **0** |
| VIX ≥ 18.4 (panelin kanıtlı eşiği) | kayıtların **%7.3**'ü | rejim fiilen hiç oluşmadı |
| DXY | 98.6 – 101.6 | dar bant |

Tek rejimden rejim etkisi öğrenilemez. "Rejim yakaladı mı?" sorusunun cevabı:
**hayır — ortada yakalanacak bir rejim değişimi yok.** Denenen ve elenen adaylar:

| rejim adayı | sonuç |
|---|---|
| geçmiş performansın kalıcılığı | r=0.006–0.053 → öngörü yok |
| ADX(1h/4h) üst-TF trend gücü | train/test tutarsız (`<15` train %65.5 → test %57.3) |
| ATR%(4h) oynaklık | ⚠ **KONFOUND**: ham `≥1.2` kovasının **223/223'ü USOIL**; sembol-içi yüzdelikte test dönemi dejenere (175/183 XAU) |
| VIX bandı | aralık zaten yok (yukarıdaki tablo) |
| 4h hacim genişlemesi | 0.7–1.0 "ölü bant" iki sette de negatif; gerisi tutarsız |

⚠ **BU, `entry_quality` KAPISI İÇİN DE BİR UYARIDIR:** kapı eşikleri (chz_dir≥2.0,
vol≥1.5) bu TEK rejim içinde ölçüldü. VIX 25'te aynı eşiklerin geçerli olduğu
kanıtlanmadı. Bu yüzden `regime_meter.py` her karara rejim damgası basar ve koşul
gözlenen zarfın dışına çıkarsa **"kapı kanıtı burada geçerli değil"** uyarısı verir.

### 4-EK. Eski başlık: kalıcılık testi

**4a. ADX hipotezi (iyi hafta ADX1h=33.6 vs kötü hafta 17.1) doğrulanmadı.**
Tüm geçmişte ADX(1h) kovaları train/test arasında tutarsız (`<15` train %65.5 → test %57.3).
Haftalık korelasyon r=+0.40 (n=10 hafta — anlamlı değil), karşı-olguda r=−0.11 (ters işaret).

**4b. Rejim kalıcı değil — bu belirleyici test.**
"Son N işlemin WR'ı sonraki işlemi öngörüyor mu?"

| pencere | karşı-olgu (iyi−kötü rejim farkı) | decider |
|---|---|---|
| son 50 | +5.5pp (r=+0.053) | +1.4pp (r=+0.013) |
| son 100 | +3.5pp (r=+0.031) | +2.5pp (r=+0.029) |
| son 200 | +5.1pp (r=+0.028) | +0.8pp (r=+0.006) |

Decider'ın kendi işlemlerinde sinyal fiilen sıfır. **Sonuç: "rejim iyiyken gir, kötüyken
dur" kuralı bu veriyle kurulamaz.** Haftalık salınım öngörülebilir değil — %73'lük haftayı
önceden bilmenin bir yolu yok, nitekim ertesi hafta %52.8'e düştü.

Zamanlanabilen şey rejim değil, **karar anındaki giriş kalitesi** (bölüm 5).

---

## 5. YENİ KAPI — `entry_quality.py` (giriş kalitesi)

**Kural:** `chz_dir(5m) ≥ 2.0` **VEYA** `vol_ratio(5m) ≥ 1.5` → OPEN açma.

**Doğrulama bataryası:**

| ölçüt | decider (n=1515) | karşı-olgu (n=4350, bağımsız) |
|---|---|---|
| elenen küme | n=434 · %56.0 · **−0.069R** | n=1010 · %56.6 · **−0.068R** |
| elenen, kronolojik yarılar | −0.078 / −0.061 (ikisi de −) | −0.105 / −0.031 (ikisi de −) |
| elenen, P(EV>0) bootstrap | **%4.2** | **%0.4** |
| elenen, sembol kırılımı | 4/4 sembolde negatif (USOIL −0.226R) | 4/4 sembolde negatif |
| kalan küme | n=1081 · %63.1 · **+0.036R** · P(EV>0)=%93.7 | n=3340 · %63.5 · +0.017R · P=%90.2 |
| kapsam | %71 | %77 |
| **plasebo** (aynı kapsamda rastgele kapı, 2000 tur) | **p=0.0085** | — |

Sızıntı kontrolü: `forensics` snapshot'ı `fetch_multi_tf()` ile karar anında üretiliyor,
outcome sonradan çözülüyor → yapısal olarak sızıntısız (CLAUDE.md `_bars_upto` tuzağı yok).

**⚠ DÜRÜSTLÜK NOTU — kapı sihirli değnek değil.** Hafta hafta etkisi:

| hafta | kapısız | kapılı | elenen küme |
|---|---|---|---|
| 07-06 | %63.2 / +0.056 | %71.4 / +0.193 | %48.4 / −0.192 |
| 08-17 | %64.7 / +0.081 | %67.9 / +0.133 | %56.8 / −0.051 |
| **08-24** | %56.9 / −0.049 | **%67.4 / +0.126** | %39.2 / −0.345 |
| 08-31 | %73.2 / +0.222 | %73.1 / +0.220 | nötr |
| **09-07** | %52.8 / −0.118 | **%50.9 / −0.150** ❌ | %57.1 / −0.046 |

10 haftanın 8'inde iyileştiriyor, **en kötü haftada (09-07) iyileştirmiyor, hafif kötüleştiriyor.**
Ortalamada gerçek ve istatistiksel olarak sağlam bir kazanç, ama haftalık varyansı yenmiyor.

**Durum: GÖLGE** (`ENTRY_QUALITY_BLOCK=False`). Proje geleneği gereği ≥2-3 hafta canlı
gölge ölçümünden sonra açılmalı. `entry_quality` alanı artık her journal kaydına yazılıyor.

---

## 6. Önerilen sonraki adımlar

1. **2-3 hafta gölge ölçümü** → kutuda karneyi çalıştır:
   ```
   python claude_decider/entry_quality_report.py --gun 21
   ```
   Script gerçek OPEN ve karşı-olgu setlerini ayrı raporlar ve blok moda geçiş
   ölçütünü (elenen kümede n≥100, EV<0, iki kronolojik yarıda da EV<0, kalan
   kümenin EV'si yükselmiş) kendisi denetler. "SAĞLANDI" derse kutunun
   `decider_config.py`'sine `ENTRY_QUALITY_BLOCK = True` yazılır (dosya
   gitignore'da, elle eklenmeli).
   Not: kapı WAIT kararlarında da karşı-olgu yönüyle ölçüldüğü için örneklem
   ~3 kat hızlı birikir.
2. **USOIL'i decider'da askıya al** — 230 işlem, %56.1 WR, −0.063R; elenen alt kümesi
   −0.226R. Sembolün kendisi başabaşın altında.
3. **Derin aşırılığı prompt'ta da söyle** — kapı OPEN'ı kesiyor ama model hâlâ "ne kadar
   aşırı o kadar iyi" diye muhakeme ediyor; PLAYBOOK'a monoton düşüş tablosu girmeli.
4. **4/4 TF uyumu bulgusunu araştır** (n=137, %54.7) — "her şey hizalı" = geç giriş
   hipotezi ayrı bir kapı adayı, n büyüyünce tekrar ölç.
