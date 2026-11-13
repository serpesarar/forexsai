# FX-01 — Döviz çifti seçimi ve zorunlu akış kapıları (2026-11-13)

Ön kayıt: `PROTOCOL.md` (+ EK-1…5, hepsi sınamadan önce yazıldı). Veri: Pepperstone-Demo MT5 (kutu, salt-okuma), 27 çift × D1/H1/M15/M5/M1
(terminal tavanı 100.000 bar → H1 2010-10→, M15 2022-11→). Maliyet: bar spread'i ile 2026-11-11…13 tick spread'inin büyüğü + Razor
komisyonu (≈ $7/lot gidiş-dönüş, 0,53–1,07 bp). KEŞİF ≤ 2021, KÖR 2022 →.

## 1. Hangi çift? (soru: az riskli, oynak, tahmin edilebilir)
| Ölçüt (son 3 yıl) | Sonuç |
|---|---|
| Maliyet / oynaklık (κ) | **USDJPY 0,0010** (σ 68 bp/gün) · GBPJPY 0,0017 · USDCAD 0,0021 · … EURUSD 0,013 (18.) · USDTRY 0,18 (son) |
| Gecelik swap | TRY çiftleri iki yönde de −35…−52 bp/gece → gece taşınamaz; majörler ±1 bp |
| Öngörülebilirlik vekilleri | Günlük AC1 tüm çiftlerde ±0,1 içinde, VR5 0,8–1,0 → **yön için ölçülebilir bellek yok** |

Hüküm: "En tahmin edilebilir döviz" diye bir çift yok; FX majörleri verimli piyasa. İşlem edilebilirlik + belgelenmiş zorunlu akış
birlikte **USDJPY**'yi öne çıkarıyor: en ucuz oynaklık ve Tokyo fiksi (gotobi) gibi takvime kilitli bir alıcı. EURTRY/USDTRY swap ve
spread nedeniyle elenir.

## 2. Hipotez sonuçları (net = gerçek maliyet sonrası, bp/olay)
| ID | Kural | Sonuç | Sınıf |
|---|---|---|---|
| H1 | Ay sonu 10→16 Londra, ABD−DAX ay-içi farkına göre USD sepeti (hedge akışı) | n 192, +1,30 (P 0,72), KEŞİF −1,21 | X |
| H1b | Ay sonu 16→20 ters (hedge sinyali) | −0,55 | X |
| H2 | Gün içi mevsimsellik (kendi saatinde değer kaybı), 6 hücre | EURUSD Avrupa kısa KÖR'de sönüyor (+0,16); USDJPY işaret ters | X |
| H3 | FOMC günü USD sepeti kısa (önceki 18:00 ET → 16:00 ET) | n 128, +5,85 (P 0,88), kontrol −1,52 | C+ |
| H3b | FOMC duyuru öncesi (→14:00 ET) | +4,36 (P 0,95), olay isabeti %50,8, ilk 5 çıkınca +2,45, 2025–26 eksi | C+ |
| H4 | Stres (VIX ≥ 18,4) ∧ RSI2 < 10 → taşıma çifti uzun (korku dönüşü aktarımı) | 6/6 çift ≤ 0 (AUDJPY −31,5; NZDUSD −30,4); ayna da eksi | X |
| H5 | Benzer ekonomili çapraz çiftte z ≥ 2 ortalamaya dönüş | görülen 3/4 +, kör AUDNZD −17,6 / EURCHF −3,9 | X |
| H8a | Gotobi 08:00→10:00 JST USDJPY uzun | +0,45 (P 0,84), kontrol −0,43 | C |
| H8b | Gotobi 10:00→15:00 JST kısa | USDJPY +1,72 (P 0,965), kontrol +0,05; kör havuz P 0,71 | C+ |
| **H8c** | **Gotobi sabahı (23→01 UTC) yükseldiyse 01→06 UTC USDJPY kısa** | **n 657, +1,79 (P 0,946), KEŞİF +1,40 / KÖR +2,75, ×1,5 +1,09; kontrol −0,73; 4/4 JPY çifti brüt +; aile max-t p 0,08; doz-tepki tekdüze** | **B−** (kart 5/6, GÖLGE) |
| **H9** | **Ay sonu: 10→16 Londra hareketinin tersine 16→20 Londra, 6 çift sepet** | **n 182, +1,93 (P 0,968), KEŞİF +2,28 / KÖR +1,09; kontrol −1,24 (fark P 0,999); 5/6 çift +; doz-tepki tekdüze; ilk 5 çıkınca +0,39** | **B−** (kart 5/6, GÖLGE) |

M15 ayrıştırması (2022-11→, dört JPY çifti): gotobi sabahı yükseliş artık 08:00→08:45 JST'de bitiyor; fiks çevresi eksi (piyasa akışın önüne
geçiyor). Yeni zamanlama KÖR veriden görüldüğü için hüküm verilmedi (Dukascopy 2012–21 ile sınanmalı; indirme engele takıldı, 92 gün).

## 3. Mekanizma ve ortak ders
Ayakta kalan iki parça aynı mekanizma: **zorunlu fiks akışı fiyatı fiksten önce iter, geçici etki fiksten sonra geri döner** (Tokyo 09:55
gotobi fiksi; Londra 16:00 ay sonu WM/R fiksi). İkisinde de: (i) kontrol günlerinde aynı kural ≈ 0 veya eksi (normal günde hareket
devam ediyor), (ii) fiks öncesi itme büyüdükçe dönüş büyüyor, (iii) ön-kayıtlı kör çift/sepet ölçütleri geçiyor. "Kim işlem yapmak
zorunda?" sorusunun FX cevabı fiks alıcısı; NASDAQ'taki korku-dönüşü FX'e taşınmıyor (taşıma çözülmesi devam ediyor).

Zayıf yanlar: kenar maliyete ince (brüt ≈ 3,2–3,3 bp, maliyet ≈ 1,4 bp → kart 5. ölçütü geçmiyor); H9 kuyruğa bağımlı; H8c bir ana
hücrenin KÖR verisi görüldükten sonra yazıldı (E53). İkisi de **GÖLGE**; canlıya alma kararı kullanıcıda.

Büyüklük (bilgi): USDJPY H8c 1 lot ($100k) ≈ +$18/olay, ~41 olay/yıl; olay başı std ≈ 29 bp → yıllık Sharpe ≈ 0,4–0,5. H9 sepeti 6 bacak × 12 ay.

**Son yıl uyarısı (E59):** 2026 (Oca–Kas) H8c USDJPY 33 olay brüt −5,65 bp (2025 +8,4); H9 2026 60 bacak brüt +4,48. Gotobi
etkisi bu yıl zayıf; gölge karnesi bunu izlemeli.

## 4b. Gölge modülü (hazır, bota BAĞLANMADI)
`yeni deneme/fx_fiks_shadow.py` + `test_fx_fiks_shadow.py` (8/8). Kural dondurulmuş; geçmiş H1 üzerinde `step()` tekrar oynatması
araştırmayla birebir (2026: GOTOBI 33 / −5,65, AYSONU 60 / +4,48). EMİR GÖNDERMEZ. Bağlamak için `forexsai_demo_bot.py` ana döngüsüne
dax_fomc_shadow kalıbıyla `fx_fiks_shadow.poll(mt5, log, _daycombo_offset, cfg=config)` + main push gerekir (kullanıcı onayı).

## 4. Yöntem notları (deftere)
- Hesap Razor (EURUSD tick medyan spread 0): MT5 bar `spread` alanı komisyonu içermez ve son yıllarda 0,1 pip'e iner → komisyonsuz maliyet
  modeli FX kenarlarını ≈ 0,6–1,1 bp şişirir.
- Terminal "max bars" 100.000: `copy_rates_from_pos` döngüsü bundan derine inemez; H1 ≈ 16 yıl, M15 ≈ 3 yıl, M1 ≈ 70 gün.
- Kutu ajanı zaman aşımında kabuğu öldürür ama `python -c` alt süreci yaşamaya devam eder (yetim süreç MT5 terminalini meşgul eder);
  büyük çekimleri zaman bütçeli yaz.

## 5. Dosyalar
`PROTOCOL.md` · `fx_core.py` (yükleme/saat/maliyet) · `hyp.py` (H1/H2/H3/H8) · `h4.py` · `h5.py` · `h8_perm.py` · `h8c_saglamlik.py` · `kart.py` ·
`h9_kart.py` · `secim.py` · gölge `yeni deneme/fx_fiks_shadow.py` · `probe.py`/`export.py`/`tick_spread.py`/`kutu.py` (kutu, salt-okuma) · `results/` · kartlar
`backend/data/evolution/go_live_cards/usdjpy_gotobi_fiks_donus.json`, `fx_aysonu_fiks_donus.json`.
