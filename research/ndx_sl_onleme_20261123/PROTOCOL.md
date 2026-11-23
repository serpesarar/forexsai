# NDX DAYCOMBO + REENTRY — SL önleme araştırması (ön kayıt, 2026-11-23, sonuçlar görülmeden)

**Soru (kullanıcı):** 2026-11-23'te NAS100'de 10 BUY (DAYCOMBO +4 / REENTRY +6, 30 lot, TP 80 / SL 110):
6 TP +14.325 $, 4 SL −13.242 $. Strateji nasıl geliştirilirse SL'lerin **en az %60'ı** engellenirdi —
farklı giriş noktası, bekleme taktiği, vb.

**Vaka (kanıt sayılmaz):** 13:45–14:00 UTC'de +750 p (+%2,9) şok; ardından 26.400–27.050 arası ±300 p
yönsüz çalkantı. UTC: DC 14:06 TP · RE 14:22 TP · DC 14:55 TP · RE 15:05 TP · **DC 15:21 SL** · **RE 15:47 SL**
(SL sonrası 1 dk) · **DC 17:06 SL** · RE 17:47 TP · DC 18:01 TP · **RE 18:31 SL**. Saat ekseni broker−2 s,
20/20 fiyat noktası 1m barla eşleşti.

## Defter ön taraması (3. KURAL) — TEKRARLANMAYACAKLAR
TD-01 (89 aday, 0 geçti: tepe kapıları, desteğe yakınlık/limit/teyit, ATR geri çekilme limiti, dönünce gir,
oynak stop, zaman çıkışı) · IO-09 (puan geri çekilme limiti) · IO-21 K1–K6 (fren, üst üste binme, SL sonrası
60 dk, DC günde 1, SQZ, RE yalnız TP sonrası) · IO-23 (aile içi tekil SL ayırıcı, 112 özellik) · IO-26 (tekil SL
girişte tanınmıyor) · M9/IO-07 (BE/kilit/erken çıkış) · CK-03/05 (DAYCOMBO/REENTRY kenarı 2026'ya özgü, C).
**Ön tahminim:** tekil giriş kapıları yine tutmaz (IO-26); gün düzeyi kurallar (kâr kilidi, geri verme freni)
pozitif sürüklenmeli bir akışta beklenen değeri düşürür — IO-21'de günün 2.+ DAYCOMBO'su daha iyiydi.

## Yeniden açma gerekçesi
1. **Yeni veri:** Dukascopy 1m 2018-01 → 2023-12 (`research/nom_20261113/data/ndx_1m_v3_duka.parquet`) bu
   kurallarda HİÇ koşulmadı (≈1.500 işlem günü). 2026-11-03 → 11-20 ileri broker verisi.
2. **Yeni tanımlar:** gün düzeyi durum kuralları, kırılım (buy-stop) teyidi, uzatılmış probasyon, SL sonrası
   geri alma koşullu REENTRY, çalkantı (verimlilik oranı), şok sonrası bekleme, gürültü/braket oranı.

## Veri ve dönemler
| ad | kaynak | dönem | geometri |
|---|---|---|---|
| ESKİ-A | v3 Duka | 2018-01-01 → 2020-12-31 | yüzde: TP/SL/spread × (fiyat/24.000) |
| ESKİ-B | v3 Duka | 2021-01-01 → 2023-12-31 | yüzde (aynı) |
| Y24 | TD-01 duka24 | 2024 | sabit 80/110 + 1,5 (TD-01 birebir) |
| Y25 | TD-01 bars_1m | 2025-01 → 2026-07-28 | sabit |
| Y26b | bars_1m + otopsi önbelleği + kutu MT5 | 2026-07-29 → 2026-11-20 | sabit |
| VAKA | kutu MT5 | 2026-11-23 | sabit (yalnız gösterim) |

Taban = TD-01 canlı akış taklidi birebir (`tepe_destek_20261104/engine.py`): DAYCOMBO sinyali (Cuma yok),
5 bar probasyon, sonraki M1 açılışı + spread, 3 gün tavan, aile başına tek pozisyon; REENTRY ana TP +5 / SL +1 dk,
tek sefer, 22–07 UTC ve Cuma yok. Kural iki akışa da uygulanır (aksi yazılmadıkça).

## Adaylar (eşikler sonuçlara bakılmadan sabit)
- **A gün kâr kilidi:** günün (DC+RE) gerçekleşmiş Σ R ≥ +X → o gün yeni giriş yok. X ∈ {2, 3, 4}.
- **B gün SL sayacı:** günde N. SL'den sonra yeni giriş yok. N ∈ {1, 2, 3}. *(K1/K3'e yakın; farkı sayım)*
- **C geri verme freni:** günün gerçekleşmiş Σ R'si gün içi tepesinden ≥ Y düştüyse (tepe > 0) dur. Y ∈ {1,5; 2; 3}.
- **D kırılım teyidi (buy-stop):** karar fiyatı + x·ATR5'e w dk içinde ulaşırsa o seviyeden gir; ulaşmazsa işlem yok.
  x ∈ {0,25; 0,5; 1,0}, w ∈ {15, 30}.
- **E uzatılmış probasyon:** n ∈ {10, 15} bar, bant 1,28·ATR1·√n (E-n); ayrıca **E0-n**: n ∈ {5, 10} sonunda fiyat
  sinyal fiyatının altındaysa iptal (yalnız DAYCOMBO).
- **F SL sonrası geri alma:** SL'den doğan REENTRY yalnız 1m kapanış ≥ (durdurulan giriş − (1−f)·SL) olunca, w dk içinde;
  f ∈ {0,5; 1,0} (yarısını / tamamını geri aldıysa), w ∈ {30, 60}. TP sonrası REENTRY değişmez.
- **G çalkantı:** verimlilik oranı ER_n = |c−c₋ₙ| / Σ|Δc| (1m, n ∈ {60, 120}); ER < q → atla. q = KEŞİF (Y25) karar anı
  ER dağılımının %10 / %20 / %33 yüzdeliği (sonuç körü).
- **H şok sonrası:** son 180 dk içindeki herhangi kapanmış 15m mumun gövdesi ≥ k × (önceki 20 gün 15m |gövde| medyanı)
  → atla. k ∈ {3, 4, 6}.
- **I gürültü/braket:** SL / (ATR14(1m)·√30) < q → atla; q = Y25 dağılımının %10 / %20 / %33 yüzdeliği.
- **R (TD-01 yakın kalanları, yalnız yeni veride):** G8 probasyon kaçışı ≥30 / ≥50 p, PV −1 ATR5 limit (oynakta),
  G7 rejim ≥ 1,8 atla. ESKİ'de puan eşikleri × (fiyat/24.000).

## Geçme ölçütü (hepsi)
1. Δ Σ R > 0 **ve** Δ ort. R > 0: ESKİ-A, ESKİ-B, Y24, Y25 **her birinde** (Y26b ve VAKA raporlanır).
2. Havuz (dört dönem) gün-blok bootstrap P(gün başına Δ > 0) ≥ %90.
3. Plato: aynı aileden en az bir komşu eşik de 1. ölçütte aynı işarette (tek eşikliler hariç).
4. Plasebo: aynı dönemlerde aynı sayıda **rastgele** işlem atlama (gün kurallarında: aynı sayıda gün için rastgele saatte durma),
   500 tekrar; p × (1. ölçütü geçen aday sayısı) ≤ 0,10.
5. Stres: spread ×1,5 + 0,2 kayma (×ölçek) + 1 dk gecikme, havuz Δ > 0.
Geçen: **GÖLGE adayı** (2. KURAL kartı gerekir). Geçmeyen: raporlanır.

**Kullanıcı ölçüsü (her aday, her dönem):** engellenen SL oranı, kaybedilen TP oranı, atlanan kümenin kendi ort. R'si (E89),
E66 için dolmayan sinyallerin piyasa-R'si. "SL'nin %60'ını engelledi" ancak TP kaybı belirgin düşükse anlamlıdır.

## Sınırlar
- Duka bid + sabit/ölçekli spread; canlı 0–2 dk gecikme stres ölçütünde.
- REENTRY canlıda diğer ailelerin kapanışından da doğar; taklit yalnız DAYCOMBO'dan doğurur.
- Buy-stop dolum barında SL kontrolü barın dip noktası dolumdan önce gelmiş olsa da sayılır (muhafazakâr).

## EK-1 (taban regresyonu ve kutu logu görüldükten sonra, HİÇBİR aday koşulmadan önce)
Taban: ESKİ-A +0,053R (1.228), ESKİ-B +0,026R (1.309), Y24 +0,031R, Y25 −0,004R, Y26b +0,116R; TD-01 ile tutarlı.
Kutu logu (yerel saat UTC−5): probasyon canlı; bugün girişler sinyalin +138 / +56 / **+171** p üstünden; bant 274 / 276 / 180 p —
**bant SL'den (110 p) geniş olunca probasyon aleyhe hareketi de süzmüyor.** Canlı giriş replay'den ≈1 dk geç.
Ek aday (aynı ölçütler):
- **E-cap:** probasyon bandı = min(1,28·ATR1·√5, c × SL), c ∈ {0,5; 1,0} (aleyhe c×SL'den fazla düşerse iptal).

## EK-2 (taramanın ilk yarısı görüldükten sonra — kısmen POST-HOC, şeffaflık için)
Kullanıcının bu oturumdan ÖNCE (2026-11-23 07:12, başka oturum) koyduğu kalıcı ölçüt: *kural son 3–4 takvim yılının her birinde
artıysa aday; eski dönem eksiliği elemez* (`feedback-son-yillar-olcutu`). İkincil hüküm olarak uygulanır:
**S4: 2023, 2024, 2025, 2026 her yılda Δ Σ R > 0 + havuz P ≥ %90 + stres Δ > 0.** Birincil (ön kayıtlı) hüküm değişmez; ikisi
yan yana raporlanır. Uyarı: DAYCOMBO 2026'da tasarlandı (2026 örneklem içi), TD-01'in KEŞİF'i 2025–26/07 — temiz yakın yıllar
2023 ve 2024'tür. Tarama ilk yarısında ESKİ-A (2018–20) çoğu adayda tersti; bu ek bunu gördükten sonra yazıldı.

## EK-3 (yazılı kayıt) — gecikme taraması ve lag-1 tabanı
Gecikme plasebosundan doğdu (post-hoc, RAPOR §3). Bekleme türü kurallar bundan sonra **lag 1 tabanına** karşı ölçülür (E152).

## EK-4 (kullanıcı hedefi sürdüğü için, hiçbir V sonucu görülmeden) — oynaklığa göre braket + eşit $ risk
Yeniden açma gerekçesi: TD-01 V1–V3 yalnız 2024–26 ve lag 0'da sınandı (+3,9 / +17,1 / −0,5R); 2018–23 ve lag 1 yeni.
SL_p = max(110, k × ölçü), TP_p = SL_p × 80/110, **lot = 30 × 110 / SL_p** (R zaten lot-normalize). ESKİ'de 110 × ölçek.
- **V1** ölçü = ATR5, k ∈ {2; 2,5; 3}
- **V3** ölçü = ATR(1h), k ∈ {0,75; 1}
- **V4 (yeni, gürültü-normalize)** ölçü = ATR14(1m)·√30, k ∈ {1; 1,5; 2}
Ölçüt: lag 1 tabanına karşı 2023–2026 her yıl Δ Σ R > 0 (S4) + havuz P ≥ %90 + stres (spread ×1,5, kayma 0,2) Δ > 0;
ayrıca ön kayıtlı 1. ölçüt (ESKİ-A/B, Y24, Y25). Kullanıcı ölçüsü: bugünkü **canlı** 4 SL'den kaçı aynı girişte stopsuz TP'ye ulaşırdı
(canlı giriş fiyatı/saatiyle) ve canlı 6 TP'den kaçı korunur; tarihsel SL-engel / TP-kayıp.
