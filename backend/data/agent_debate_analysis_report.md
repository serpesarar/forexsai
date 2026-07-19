# Agent Tartışma Sistemi — Çok-Ufuklu Başarı Analizi ve Geliştirme Raporu

**Tarih:** 2026-07-18 · **Veri:** `bias_test_log` 39 koşu (2026-07-06 → 2026-07-16) + `candle_cache` 5m mumlar
**Araçlar:** `backend/research/debate_horizon_analysis.py` (veri çıkarma) + `debate_horizon_report.py` (agregasyon)
**Metodoloji:** Her tartışma koşusu, karar fiyatından (`price_at_decision`) itibaren **+10/20/30/60/120/240 dk** ve gün-kapanışı ufuklarında yeniden notlandı. "İşaretli getiri" = tahmin yönünde gerçekleşen % hareket (bearish çağrıda düşüş pozitif sayılır).

> ⚠️ **İstatistiksel dürüstlük:** Yönlü çağrı örneklemi n=18 (tekilleştirilmiş ~14). Bu boyutta güven aralığı ±20-25 puan — aşağıdaki her bulgu "erken kanıt"tır, kanıtlanmış edge değildir. Rapor bu yüzden hem bulguları hem de örneklemi büyütecek enstrümantasyon planını içerir.

---

## 1. Veri Envanteri ve Operasyonel Sorunlar (önce bunlar düzelmeli)

| Tespit | Detay | Etki |
|---|---|---|
| **Çift yazar** | 9 koşu çifti aynı (sembol, tarih, label) ile 2 kez loglanmış — 07-15/16'da TÜM koşular çift. Model denetimi notundaki "Railway'de eski-kod yazar hâlâ aktif" bulgusuyla tutarlı: iki backend aynı pencerede debate koşuyor. | İstatistikler şişiyor; token 2× harcanıyor |
| **Notlama durmuş** | 14/39 satır (07-15 ve 07-16) `was_correct=NULL`. 16:15 ET / 22:20 UTC filler koşmamış; catch-up (`fill_pending`) da tetiklenmemiş. | Öğrenme döngüsü (öz-kalibrasyon bloğu) 3 gündür kör |
| **07-17'de hiç koşu yok** | Son kayıt 07-16. Auto-runner durmuş veya backend kapalıydı. | Veri toplama kesintili — n büyümüyor |
| **`agent_agreement` ölü alan** | 18/18 yönlü koşuda değer "mixed". CIO prompt'u pratikte hep aynı değeri üretiyor. | En değerli potansiyel filtre (konsensüs) ölçülemiyor |
| **`expected_close` kategorik** | Sayısal fiyat değil, "negative/uncertain" gibi metin. | Hedef-fiyat hata analizi yapılamıyor |

---

## 2. Ana Bulgu — Kullanıcı Hipotezi DOĞRULANDI: Gün-kapanışı metriği ajanların gerçek isabetini gizliyor

Yönlü (bullish/bearish) 18 çağrının ufuk karnesi:

| Ufuk | İsabet | Ort. işaretli getiri |
|---|---|---|
| +10dk | 10/18 (%56) | **+0.178%** |
| +20dk | 11/18 (%61) | +0.092% |
| +30dk | 8/18 (%44) | +0.063% |
| +60dk | 11/18 (%61) | **+0.152%** |
| +120dk | 8/18 (%44) | +0.121% |
| +240dk | 10/17 (%59) | **+0.138%** |
| **Gün kapanışı** | **6/12 (%50)** | — |

**NDX çarpıcı örnek:** bearish çağrılar gün-kapanışında **0/4** (yani "ajan %20-30 isabetli" görünümünün kaynağı) ama:
- +60dk: 4/6 isabet, ort **+0.29%**
- +240dk: 4/5 isabet, ort **+0.24%**

Sebep net: ölçüm dönemindeki 5 notlanmış NDX günü **hepsi yeşil kapandı** (+0.59% → +1.01%). Boğa sürüklenmesinde herhangi bir bearish gün-kapanış çağrısı otomatik kaybediyor — ama ajanlar **ilk 1-4 saatin yönünü** çoğu kez doğru okuyor (07-08: bearish çağrı, 60dk'da −1.56% ve −0.68% gerçekleşme; gün +0.76% kapanıp "yanlış" sayılmış). Ajanların ürettiği bilgi **intraday bias**, notlama ise onu **günlük bias** gibi sınıyor.

**MFE/MAE kanıtı (ilk 60dk, tahmin yönüne göre):**
| Sembol | Lehte maks. ort | Aleyhte maks. ort | R:R |
|---|---|---|---|
| NDX | +0.48% | −0.25% | ~1.9 |
| USOIL | +1.09% | −0.14% | ~7.8 |
| XAUUSD | +0.16% | −0.22% | **<1 (edge yok)** |

---

## 3. Sembol Karnesi

| Sembol | Yönlü n | 60dk | 240dk | Gün | Değerlendirme |
|---|---|---|---|---|---|
| **USOIL** | 3 | 3/3, +0.73% | 2/3, +0.45% | 1/2 | En güçlü — bearish çağrılar tüm ufuklarda pozitif. n çok küçük ama tutarlı. |
| **NDX** | 9 | 5/9, +0.12% | 6/8, +0.21% | **2/6** | İntraday değerli, gün-kapanışı yanıltıcı. Bearish alt-küme 60-240dk'da net pozitif. |
| **XAUUSD** | 6 | 3/6, −0.08% | 2/6, −0.12% | 3/4 | **Sistematik sorun:** 6/6 çağrı bearish (tek yön!), ≥30dk tüm ufuklar negatif. Altında intraday edge YOK (hafıza notlarıyla tutarlı: XAU intraday edge defalarca reddedildi). Gün 3/4 "doğru" görünümü küçük n + şanslı günler. |
| **GDAXI** | **0** | — | — | — | **5 koşunun 5'i neutral/choppy** — DAX tartışması hiç yönlü karar üretmiyor. Mevcut haliyle token israfı. |

## 4. Karar Saati (run_label) Karnesi

| Pencere | Yönlü/Nötr | Gözlem |
|---|---|---|
| `0800_main` (NDX 08:00 ET) | 1 / 7 | Neredeyse hep neutral — premarket'te ajanlar taahhütten kaçınıyor. Tek yönlü çağrısı (07-08 bearish) 60dk'da −1.56% ile mükemmeldi. |
| `0945_confirm` (NDX 09:45 ET) | 9 / 4 | Yönlü karar üreten pencere. 30dk'da zayıf (%33 — açılış volatilitesi), **240dk'da 6/8 (%75)**. Açılış sonrası ilk yarım saatte fiyat çağrıya ters gidip sonra dönüyor. |
| `xau_daily` (08:00 UTC) | 5 / 2 | 10-20dk'da fena değil (%60-80), ≥30dk çöküyor — XAU'da öğle-sonrası ters dönüş baskın. |
| `dax_daily` (08:00 UTC) | 0 / 5 | Hiç yönlü karar yok. |
| `usoil_daily` (13:05 UTC) | 3 / 3 | Yönlü çağrılar tüm ufuklarda güçlü; 13:05 UTC (NY sabahı, EIA sonrası) iyi seçilmiş pencere. |

## 5. Kalibrasyon ve Filtre Alanları

- **Confidence TERS kalibre:** `low<60` kovası 60dk'da 6/6 ve +0.45%; `med 60-75` kovası 4/11 (%36) ve −0.06%. LLM'in confidence sayısı (55-65 bandında kümelenmiş) sinyal taşımıyor — hatta hafif ters. Canlı kullanımda LLM confidence'ına **ağırlık verilmemeli**; yerine bu tablodan türetilen ampirik (sembol × ufuk) taban oranları kullanılmalı.
- **`debate_winner` en bilgilendirici alan:** `bear` kazandığında 60dk 10/13 (%77), +0.32%. `balanced` → 30-60dk 0/3 (kaçınılmalı sinyali).
- **Nötr/choppy aşırı kullanımı:** 39 koşunun 21'i nötr (%54). Notlanmış 13 nötr gününün 9'unda |gün hareketi| > 0.5% (ort. 0.71%) — ±0.15% "flat" bandı pratikte hiç tutmuyor, nötr çağrılar otomatik "yanlış" sayılıp genel isabeti eziyor. Nötr = "trade yok" (abstain) olarak ayrılmalı, doğruluk istatistiğine karıştırılmamalı.

## 6. Uzman Ajan Karnesi (context_notes stance çıkarımı — regex, gürültülü; yapılandırılmış alan gerekli)

| Ajan | n | 60dk | 240dk | Not |
|---|---|---|---|---|
| chart_patterns | 18 | %56, +0.13% | **%67, +0.26%** | Tek tutarlı pozitif ajan |
| technical_structure | 30 | %47, −0.10% | %43, −0.13% | En sık konuşan, katkısı negatif |
| smc_structure | 18 | %39, −0.18% | %33, −0.27% | Belirgin negatif — ters gösterge adayı |
| macro | 15 | %33, −0.06% | %33, −0.15% | Negatif |
| trend_channel | 13 | %31, −0.19% | %38, −0.18% | Negatif |
| price_targets | 10 | %40, −0.22% | %40, −0.18% | Negatif |
| volatility | 9 | %33, −0.03% | %44, +0.00% | Nötr |

CIO sentezinin (%59-61) tek tek ajanların çoğundan iyi olması debate mimarisinin lehine — ama ajan stance'ları serbest metinden regex ile çıkarıldığı için bu tablo **yönlendirici**, kesin değil.

---

## 7. Geliştirme Planı — Öncelik Sırasıyla

### P0 — Ölçüm altyapısı (bunlar olmadan hiçbir karar güvenilir değil)
1. **Çok-ufuklu notlama kalıcılaşsın:** `bias_test_log`'a `ret_10m, ret_30m, ret_60m, ret_240m, mfe_60m, mae_60m` kolonları (migration) + `fill_outcomes` bunları 5m mumlardan doldursun. Gün-kapanışı metriği legacy olarak kalsın; panel ve öz-kalibrasyon bloğu **60dk + 240dk** isabetini birincil göstersin.
2. **Çift yazarı kapat:** Railway'deki eski-kod auto-runner'ı durdur veya `already_logged` kontrolünü `record_run` içine (insert öncesi, tüm çağrı yolları için) taşı. Mevcut 9 çift kayıt temizlensin/işaretlensin.
3. **Notlama sürekliliği:** `fill_pending` catch-up'ı startup'ta da koşsun (şu an 3 gün birikmiş); 07-15/16 geriye dönük notlansın.
4. **Yapılandırılmış ajan çıktısı:** Her uzman ajan serbest metnin yanına `{"stance": "bullish|bearish|neutral", "conviction": 1-5}` JSON'u döndürsün, `raw_payload._debate.agent_stances` olarak saklansın → ajan karnesi regex'siz, kesin ölçülür. `agent_agreement` bu alandan hesaplansın (LLM'e sorulmasın — ölü alan sorunu çözülür).

### P1 — Karar → uygulama stratejisi (mevcut kanıtla)
5. **Ufuk-sınırlı bias:** Tartışma çıktısı "günlük bias" değil **"4 saatlik intraday bias"** olarak tüketilsin: Precision Veto / claude_decider'a verilirken `valid_until = karar + 240dk` damgası; NDX'te kapanışa doğru (son 2 saat) bias etkisi sıfırlansın (boğa-drift ters çeviriyor).
6. **Sembol politikası:** USOIL çağrıları en yüksek ağırlık; NDX intraday (özellikle `debate_winner=bear` iken); **XAU yönlü çağrıları gölgede kalsın** (6/6 bearish tek-yön kilitlenmesi + negatif getiriler — prompt'a XAU için "bearish çağrı ancak stress-rejim kanıtıyla" kuralı eklenmeli); **DAX debate'i askıya al veya prompt'unu yönlü karara zorla** (5/5 nötr = maliyet, sinyal yok).
7. **Zamanlama:** NDX 09:45 çağrısında ilk 30dk **girişten kaçın** (isabet %33 — açılış gürültüsü), 30dk sonrasında pozisyon al, 240dk'da kapat. 08:00 penceresi nötr üretiyorsa loglanıp geçilsin (maliyet düşürme: nötr üretimi yüksek pencereler haftalık gözden geçirilsin).
8. **Confidence yerine ampirik taban oranı:** Öz-kalibrasyon bloğuna (recent_track_record) ufuk-bazlı sembol karnesi eklensin; canlı tüketicide LLM confidence çarpanı kaldırılıp (sembol × winner × ufuk) tablosundan gelen taban oranı kullanılsın.

### P2 — Örneklem ve doğrulama kapısı
9. **Canlıya bağlama eşiği:** Sembol başına ≥30 tekil yönlü çağrı VE hedef ufukta ≥%55 isabet (bootstrap CI alt sınırı >%50) sağlanana kadar tüm tüketim GÖLGE modda kalsın. Mevcut n bunun çok altında.
10. **Nötr kalite metriği:** Nötr çağrılar için ayrı gösterge — "nötr denen günlerin |hareket| yüzdeliği". Nötr, doğruluk oranına dahil edilmesin.
11. **Ajan ağırlıklandırma deneyi (yapılandırılmış stance geldikten sonra):** chart_patterns'a CIO prompt'unda "geçmiş isabeti yüksek" etiketi; smc_structure/trend_channel stance'ları ters-gösterge hipoteziyle ayrıca izlensin (şu an ikisi de negatif ama n küçük).

---

## 8. Özet Karar Matrisi (bugünkü kanıtla "ajan dedi → ne yapmalı")

| Durum | Aksiyon |
|---|---|
| USOIL yönlü çağrı | 60-120dk ufkunda takip et (en güçlü kanıt) |
| NDX `winner=bear` + bearish | 09:45+30dk'dan itibaren intraday kısa, 240dk'da kapat; gün-kapanış beklentisi KURMA |
| NDX bullish | Zayıf ama pozitif (240dk 2/3); düşük ağırlık |
| NDX/`winner=balanced` | İşlem yok (30-60dk 0/3) |
| XAU bearish | Uygulama YOK — gölgede izle (negatif getiri + tek-yön kilitlenmesi) |
| DAX herhangi | Uygulama YOK — debate yönlü karar üretmiyor |
| Herhangi nötr/choppy | Trade yok; istatistiğe katma |
| LLM confidence | Karar girdisi olarak KULLANMA (ters kalibre) |

---

## EK A — Taze-Bakış Bulguları (2026-07-18, ikinci geçiş)

1. **Placebo/baseline kontrolü (kritik düzeltme):** Koşu anlarında sembollerin ham drift'i ölçüldü. **USOIL'in "3/3, +0.73%" başarısı büyük ölçüde dönem trendi** — aynı anlarda koşulsuz-bearish de +0.74% kazanırdı; ajan katma değeri ≈ 0. NDX bearish ise koşulsuz-bearish baseline'ını **+0.14pp (60dk) / +0.11pp (240dk)** geçiyor — mütevazı ama gerçek seçicilik. XAU'da baseline +0.04% (hafif yukarı drift) iken ajanlar 6/6 bearish → net negatif katkı. Ders: ufuk karnesi her zaman **baseline-farkıyla** raporlanmalı, ham isabetle değil.
2. **`invalid_if` tüketilmiyordu:** Notlanan vakalarda XAU 4/4, USOIL 2/2 geçersizlik seviyesi delinmiş — bias'ın kendi "iptal şartı" gerçekleşiyor ama hiçbir tüketici bakmıyordu. Yeni `debate_bias_gate` seviye delinmişse bias'ı etkisiz sayıyor.
3. **Karar gecikmesi ölçülemiyor:** `_debate.generated_at_utc` var ama insert anına/`price_at_decision` tazeliğine karşı fark loglanmıyor — debate ~dakikalar sürüyor, slippage enstrümantasyonu eksik (P1 adayı).
4. **08:00→09:45 flip bilgisi:** 07-16'da 08:00 choppy → 09:45 bearish (doğru yön). En taze koşu esas alınmalı — gate `latest` satırı okuyarak bunu doğal yapıyor.
5. **Öz-kalibrasyon bloğu BAŞTAN BERİ ÖLÜYDÜ:** `recent_track_record` özel REST wrapper'da olmayan `.not_` zincirini çağırıyor, exception fail-open'a düşüp hep `""` dönüyordu — yani "model kendi karnesini görsün" mekanizması hiç çalışmamış. Düzeltildi + sembol-bazlı + ufuk karnesi eklendi. (2026-07-09 "%30.8 doğruluk" otopsisinden sonra eklenen mekanizmanın kendisi de sessizce kırıktı — fail-open'ların da izlenebilirliği gerekiyor.)
6. **Aynı-gün çapraz-sembol korelasyonu:** 07-13/15'te XAU+USOIL birlikte bearish (ortak makro ajan girdisi) — ortak-hata riski; sembol başına bağımsız kanıt şartı prompt'lara eklenebilir (P2).

## EK B — Uygulama Durumu (2026-07-18)

| P0 maddesi | Durum |
|---|---|
| Çok-ufuklu kolonlar + doldurma | ✅ `20260718_bias_test_multi_horizon.sql`; `fill_outcomes` 5m mumlardan dolduruyor; 39/39 satır geri-dolduruldu |
| Çift-yazar | ✅ `record_run` insert-önü idempotensi; 9 gerçek çift `*_dup` işaretli (07-08'de aynı etiketle loglanmış GDAXI/XAU koşuları çift DEĞİL — geri alındı). ⚠ Railway'deki eski kod yeniden deploy edilene kadar oradaki yazar da bu korumadan geçmez |
| Notlama sürekliliği | ✅ startup `fill_pending` catch-up (`BIAS_FILL_CATCHUP_ENABLED`); 07-15/16 notlandı |
| Yapılandırılmış ajan stance | ✅ 7 uzman ajan `STANCE:/CONVICTION:` satırı veriyor → `_debate.agent_stances`; `agent_agreement` beyanlardan hesaplanıyor |
| Tüketici katman | ✅ `signal_gates.debate_bias_gate` — NDX+USOIL, pulse+smc karşıt-sinyal freni, ≤240dk, NDX 14:00 ET kesimi, winner=balanced/invalidation etkisiz, default GÖLGE (`DEBATE_BIAS_GATE_BLOCK=0`) |
| Öz-kalibrasyon | ✅ ölü `.not_` düzeltildi; sembol-bazlı + `+60/+240dk` ufuk karnesi CIO prompt'una akıyor |
