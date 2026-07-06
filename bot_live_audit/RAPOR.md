# MT5 Bot — Son 1.5 Hafta Canlı İşlem Analizi (2026-06-13 → 06-24)

**Hesap:** 52890969 (ICMarketsSC-Demo) · **Bakiye:** 89,581 → **Equity:** 87,946
**Round-trip işlem:** 445 · **WR:** %53.7 · **Net P/L:** **−16,059** · **Kaynak:** `sonislemler/mt5_islemler_20260624_120317.csv`

---

## 0. TL;DR (yöneticinin 30 saniyesi)

1. **Kayıp tek bir yerden geliyor: XAUUSD.** XAU −16,843; diğer 3 sembol toplam ≈ **+785**. XAU'yu çıkar → bot başabaş-artı.
2. **XAU'nun kaybı tek bir stratejiden: `flip` (pulse inversiyon).** XAU'nun 153 işleminin 149'u `flip`, net **−11,113**. Tüm `flip` (tüm semboller) = **−11,440**.
3. **Sorun "model mi, TP/SL mi?" → İKİSİ DE, ve birbirine kenetli:** Her config'de payoff < 1 (SL mesafesi TP'den geniş). Bu yapı, YÜKSEK-WR sinyalle hayatta kalır; DÜŞÜK-WR sinyalle (flip %52, emel %38-48, XAU yazı-tura) kanar. Felaket = `RR<1` × `düşük-WR sinyal`.
4. **Senin "XAU'da tersine çevir" hipotezin — test edildi:** Yön'ü ters çevirmek İŞE YARAMAZ (XAU her iki yönde de %48 = sinyal bilgi taşımıyor). TP/SL mesafesini takaslamak (TP=5/SL=3) in-sample kârlı görünüyor ama sadakat açığı + maliyet kırılganlığı + önceki OOS araştırmayla çelişki → **doğrulanmamış bahis, deploy etme.**
5. **İyi haber:** Bu kayıplar botun ESKİ fazından. `yeni deneme` config'in XAU'yu zaten kaldırmış + doğrulanmış pulse scope'lara daralmış. En büyük hata zaten düzeltilmiş. Kalan iş: config'i sağlamlaştırmak + filtrenin canlıda WR'ı gerçekten tutturduğunu doğrulamak.

---

## 1. Veri & Metot (dürüst sınırlar)

| Sembol | medyan tutuş | 1m kapsama (06-13→24) | kullanılan fiyat kaynağı |
|---|---|---|---|
| NDX (USTEC) | 8.2 dk | ❌ yok (06-12'de dondu) | temiz 1h + işlem fill'leri |
| GDAXI (DE40) | 11.9 dk | ❌ yok | temiz 1h + fill'leri |
| USOIL (XTIUSD) | 175 dk | ✓ 06-22'ye dek | 1m + 5dk snapshot + fill |
| XAUUSD | 5.9 dk | ✓ 06-22'ye + ~3dk snapshot 06-24'e dek | 1m + 3dk snapshot + fill |

- **Bot scalp yapıyor (medyan 6-12dk).** 1h/5m barlar bu işlemler için yetersiz; 1m şart ama endekslerde candle_cache 1m donmuş (MT5 köprüsü 1m yayınlamıyor — `mt5_pull_missing_1m.py` ile elle dolduruluyor, son: endeks 05-21).
- **Boşluğu kapatan kaynak:** Yoğun günlerde botun kendi fill'leri (06-23'te 61, 06-24'te 55 XAU işlemi) ~5-15dk'da bir gerçek piyasa fiyatı + XAU "1h" snapshot'ları (~3dk) 06-24'e kadar.
- Tüm simülasyonlar **muhafazakâr** (sparse veride favorable-reach alt sınır; first-touch'ta adverse önce). Config-A (mevcut) simülasyonu gerçek P/L'i birebir tutturuyor (sim −90.7$/lot × 153 × ~1.2 lot ≈ gerçek −16,843) → motor sadık.

---

## 2. Ekonomi — sembol bazında (kesin, fiyat verisi gerekmez)

| Sembol | n | WR | payoff (avgW/avgL) | başabaş-WR | **net P/L** | yorum |
|---|---|---|---|---|---|---|
| **NDX** | 122 | 53.3% | 0.86 | 53.7% | **+374** | ≈başabaş; BUY +510 / SELL −137 |
| **USOIL** | 38 | 65.8% | 0.60 | 62.5% | **+783** | kârlı; SELL +1048 / BUY −265(n=2) |
| **GDAXI** | 132 | 53.8% | 0.78 | 56.3% | **−372** | hafif zarar; BUY −329 / SELL −43 |
| **XAUUSD** | 153 | 51.0% | 0.80 | 55.5% | **−16,843** | ☠️ BUY −9,260 / SELL −7,583 |
| **TOPLAM** | 445 | 53.7% | 0.74 | 57.5% | **−16,059** | WR>%50 ama payoff<1 |

> **Teşhis cümlesi:** WR %53.7 (%50 üstü → model yönünde hafif edge VAR) ama payoff 0.74 → başabaş için %57.5 gerekiyor. **3.8 puanlık açık = öncelikle TP/SL oran problemi.** Ama bu ortalama; XAU çıkınca tablo tersine döner.

---

## 3. Gerçek TP/SL oranları (senin sorduğun — config'inle karşılaştır)

Tetiklenen `[tp X]`/`[sl X]` seviyelerinden, entry'ye mesafe:

| Sembol/yön | TP medyan | SL medyan | **gerçek RR** | not |
|---|---|---|---|---|
| NDX BUY | 78.1 pt | 35.3 pt | **2.21** | geniş TP — momentum config'i (config NDX:BUY tp80 ✓) |
| NDX SELL | 19.0 pt | 24.2 pt | 0.78 | |
| GDAXI (her iki) | 18.2 pt | 29.5 pt | 0.62 | |
| USOIL SELL | 0.79 (%1.04) | 1.14 (%1.49) | 0.69 | config USOIL tp1.04%/sl1.49% ✓ birebir |
| **XAUUSD (her iki)** | 3.03 | 5.03 | **0.60** | TP yakın / SL uzak — gürültüde kanama reçetesi |

**Çıkarım:** Geçmişte fiilen uygulanan oranlar yöne göre değişiyor; çoğu RR<1. XAU'da TP=3(yakın)/SL=5(uzak), sıfır-drift ±5 oynayan enstrümanda **mümkün olan en kötüye yakın** ayar.

---

## 4. Model/strateji atfı — "modelsel mi?" sorusunun net cevabı

Giriş yorumlarındaki kombo metadata'sından (`FX|S|flip|50`, `FX|W|emel+pulse1` …):

| Strateji/kombo | n | WR | **net P/L** | exp/işlem |
|---|---|---|---|---|
| `legacy_demo` (baseline pulse) | 113 | 60.2% | **+1,951** | +17.3 ✓ TEK kârlı |
| `flip` (pulse inversiyon) | 241 | ~54% | **−11,440** | −51 ☠️ |
| `emel+pulse1` | 49 | 47% | **−5,405** | −110 |
| `emel+ml` | 42 | 38% | **−1,165** | −28 |

**Sembol × strateji:** `XAUUSD flip` = n149, net **−11,113** (XAU kaybının ~%66'sı). `legacy_demo` her sembolde +EV (NDX +989, GDAXI +567, USOIL +395).

> **Cevap:** Sorun saf "TP/SL" değil; **strateji seçimi** baskın ve düzeltilebilir lever. `flip` ve `emel`-combo'lar canlıda −EV; baseline pulse (`legacy_demo`) +EV. Kötü payoff (RR<1) ikincil, evrensel bir sürükleyici — ama yüksek-WR baseline onu taşıyor, düşük-WR flip taşıyamıyor.

---

## 5. SL sonrası fiyat yolu — SL çok mu dar, yön mü yanlış?

SL olduktan sonra, fiyat entry yönünde would-be TP'ye dönüyor mu?

| Sembol | reachTP +60dk | reachTP +240dk | advExt +240dk | yorum |
|---|---|---|---|---|
| NDX | 49% | 64% | +2.45R | chop — geri de dönüyor, ileri de gidiyor |
| GDAXI | 40% | 54% | +2.06R | chop |
| USOIL | 31% | 38% | +0.69R | SL'ler "haklı" — trend gerçekten dönmüş |
| **XAUUSD** | **68%** | **79%** | **+5.45R** | saf whipsaw: ±5R çırpınma, yön bilgisi yok |

**SL-genişletme testi (NDX/GDAXI):** SL'i 1.5×/2×/3× yapmak net'i İYİLEŞTİRMİYOR (NDX BUY −12 → −35). Yani "SL çok dar" değil; geniş SL sadece chop kayıplarını büyütüyor. İndekslerde çözüm stop genişletmek değil, **sinyal kalitesi** (momentum filtresi).

---

## 6. İNVERSİYON — senin ana hipotezin, titizce test edildi

**A) Yön'ü ters çevir (aynı TP/SL):**

| Sembol | orig WR | INV WR | INV beklenti | verdict |
|---|---|---|---|---|
| NDX | 54.2% | 53.4% | −0.011R | etkisiz |
| GDAXI | 55.6% | 58.4% | −0.056R | WR artar ama hâlâ −EV (payoff 0.62) |
| USOIL | 64.9% | 38.2% | −0.350R | **felaket** — gerçek SELL edge'ini öldürür |
| XAUUSD | 48.6% | 47.9% | −0.232R | **işe yaramaz** — sinyal bilgi taşımıyor |

> XAU'yu yön olarak ters çevirmek çözüm DEĞİL: %48 → %49, gürültü gürültü kalır. **Gürültüyü ters çevirerek kâr çıkmaz.**

**B) TP/SL mesafesini takasla (yön aynı, TP=5/SL=3) — config C:**

| Sembol | net$/lot | OOS-split | maliyet duyarlılığı | verdict |
|---|---|---|---|---|
| XAUUSD | +88.9 | in +111 / OOS +66 (✓çökme yok) | spread×3'te +27, ×5'te −34 | **doğrulanmamış bahis** |
| USOIL | +36.6 | in +24.7 / OOS +50 | ×5'te bile +24.6 (sağlam) | gerçek SELL edge'i geliştirme adayı |

> **XAU inv-tpsl uyarısı:** Sim config-A'da gerçeği tutturuyor AMA realize WR %48.6 vs sim %55.2 → **+6.5pt iyimser**. Derate + gerçekçi maliyet → kâr +20-35$/lot'a iner; 1.5 hafta tek vol rejimi; önceki OOS+friction+bootstrap araştırman "XAU intraday edge yok" diyor. **Sorumlu yol: önce kanamayı durdur, sonra uzun geçmişte friction'la doğrula. Tek switch'le deploy etme.**
> **USOIL inv-tpsl:** Çok daha sağlam (her iki yarı +, maliyete dayanıklı) ama n=34 küçük — daha çok veriyle test edilmeli, "USOIL SELL'i tut" çekirdek kararından daha düşük güven.

---

## 7. ADLİ BULGU — analiz edilen işlemler ≠ mevcut `yeni deneme` botu

İşlemlerin giriş yorumları (`FX|S|flip|50`, `emel+ml`, `ForexSAI_demo`, lot 3-5, XAU ağır) **mevcut `yeni deneme/forexsai_demo_bot.py` koduyla uyuşmuyor** (o `forexsai-demo {scope}` yazıyor, XAU yok, lot 0.10, `LIVE_TRADING=False`, sadece pulse-momentum scope).

→ **−16k, botun ÖNCEKİ deneysel fazından** (XAU+flip+emel meta). Mevcut config en büyük hatayı (XAU+flip) zaten kaldırmış.

**AÇIK SORU:** XAU-flip üreten o eski bot HÂLÂ canlı mı çalışıyor (06-24'e dek işlem var)? Yoksa `yeni deneme`ye (LIVE_TRADING=False) tam geçildi mi? Bu, acil aksiyonu belirler (acil durdur vs yeni config'i doğrula).

---

## 8. Mevcut `yeni deneme/config.py` denetimi (ileriye dönük)

| Scope | TP/SL (RR) | kanıt | verdict |
|---|---|---|---|
| NDX.INDX:BUY | 80/110 (0.73) | hafıza: tek +EV; tarihsel NDX BUY +510 | ✓ TUT |
| USOIL.FOREX:SELL | 1.04%/1.49% (0.70) | hafıza + tarihsel +1048 | ✓ TUT |
| GDAXI.INDX:BUY | 67/119 (0.56) | hafıza: momentum-filtreli +EV | ⚠ koşullu (filtreye bağlı) |
| USOIL.FOREX:BUY | 1.04%/1.49% | hafıza: momentum-filtreli +EV | ⚠ ince örnek |
| **GDAXI.INDX:SELL** | 67/119 (0.56) | **config notu kendisi "OOS'ta çöktü, bilerek YOK" diyor** ama ROBUST_SCOPES'ta VAR ve MOMENTUM_FILTERED'da YOK | ❌ **TUTARSIZ — kaldır veya filtreye al** |

**Yapısal riskler:**
- 5 scope'un 4'ü backend momentum filtresine (`/api/bot/trade-signal` → `should_trade`) bağlı. Backend düşerse bunlar atlanıyor (iyi) — ama **GDAXI:SELL momentum-filtreli değil**, backend yoksa naked `open_trade` ile açılıyor (kötü).
- Tüm config RR<1 — bu sorun DEĞİL, çünkü momentum filtresi WR'ı %78-96'ya çıkarıyor (hafıza). **Ama bu yüksek WR bu pencerede canlıda doğrulanmadı** (filtreli scope'lar fiilen işlem açmadı; +EV olan `legacy_demo` en yakın proxy).

---

## 9. Sembol bazında reçete

- **NDX:** NDX:BUY (momentum, tp80/sl110) tut — tek net +EV index yönü. NDX SELL açma (−137, marjinal). Stop genişletme.
- **USOIL:** USOIL:SELL tut (en sağlam +EV, +1048). inv-tpsl (TP'yi 1.49'a genişlet) bir sonraki test adayı ama önce daha çok veri. USOIL:BUY momentum-filtreli kalsın, ince örnek.
- **GDAXI:** GDAXI:BUY momentum-filtreli koşullu tut. **GDAXI:SELL config tutarsızlığını çöz** (kendi notun "çöktü" diyor).
- **XAUUSD:** **Intraday'i kapalı tut.** Yön de TP/SL takası da doğrulanmış değil. Altının gerçek edge'i daily-swing (Donchian breakout + EMA200, hafıza: 64.5% WR, +0.69R) — istersen onu ayrı, düşük-frekans bir scope olarak kuralım. Intraday scalp XAU = kanama.

---

## 10. Sıradaki adımlar (öneri)

1. **Doğrula:** XAU-flip bot hâlâ canlı mı? (Bölüm 7 açık soru)
2. **config.py:** GDAXI:SELL tutarsızlığını gider.
3. **Canlı doğrulama:** `yeni deneme`yi LIVE_TRADING=False'da birkaç gün izle → momentum-filtreli scope'ların gerçek WR'ı %58 başabaşı geçiyor mu? (geçmiş veride bu scope'lar açılmadığı için bu canlıda test edilmeli)
4. **Opsiyonel araştırma:** XAU inv-tpsl ve USOIL inv-tpsl'i 1.5 hafta yerine 2-3 aylık 1m + friction ile doğrula (overfit mi gerçek mi).
