# Ön-kayıt — "20 puan geri çekilme limiti" ve "%80'de %30 kilit" (2026-10-07)

Kullanıcı soruları: (1) NDX işlemlerinde girişten sonra ~20–30 puanlık ters hareket her seferinde geliyor mu;
sinyalde girmek yerine 20 puan daha iyi fiyata limit konsaydı oran ne olurdu. (2) Fiyat TP mesafesinin
%80'ine ulaşınca SL TP mesafesinin %30'u kâra çekilseydi (ör. DAYCOMBO 06.10: %95'e gidip SL) ne olurdu.
Sonuçlara bakmadan sabitlendi. Defter öncülleri: S08 (geri_cekilme_limit_2026-09-02.md: X=20/30dk,
dolmazsa market +19.606$ vs taban +5.023$, monoton → şüpheli), OLD-21 (limit = ters seçilim), M9 (BE/kilit elendi).

## Veri
`bot_trades` tüm kapanmış işlemler (2026-06-30 → 10-07), broker 1m `indicator_snapshots`, saat ekseni
`scripts/islem_otopsi` fiyat eşleştirmesi. Karar başına ilk bacak; yalnız ilk SL/TP geometrisi geçerli (R).
Karşılaştırma tabanı: aynı girişin YÖNETİMSİZ 1m yeniden oynatması (gerçek sonuçla kalibrasyon %98,5).

## A. Girişten sonraki ters hareket (betimsel)
MAE (puan) — TP'ye ulaşana / çıkışa kadar; ve ilk 30/60/120 dk içinde. Pay: ≥10/20/30/40 puan. TP vs SL ayrı.

## B. Limit girişi (NDX, puan)
Sinyal = botun gerçek giriş anı ve fiyatı. Limit = giriş − s·X. Dolum: BUY ise bar düşüğü ≤ limit − spread
(ASK limitin altına inmeli), SELL ise bar yükseği + spread ≥ limit + ... (ASK ≥ limit). Dolum barında SL
kontrol edilir, TP bir sonraki bardan (muhafazakâr).
- **Ana hipotez (S08'den ön-kayıtlı):** X=20, pencere 30 dk.
- Izgara (dayanıklılık, seçim YOK): X ∈ {10, 20, 30, 40}, pencere ∈ {30, 120} dk.
- Dolmazsa: (i) **atla** (ii) **pencere sonunda piyasadan gir** (S08 varyantı).
- Geometri: (G1) aynı mesafe (dolumdan TP/SL orijinal puan mesafesi) (G2) aynı seviye (orijinal TP/SL fiyatı).
- Metrik: sinyal başına puan (dolmayan = 0), dolum oranı, dolanların WR'ı, kaçırılan kazananlar.
- Geçme ölçütü: ana hipotez **2026-09-02 sonrası** (S08'in görmediği dönem) VE kronolojik iki yarıda tabandan
  iyi; X ızgarasında monoton-artış (plato yok) görülürse "sınır artefaktı şüphesi" yazılır.

## C. Kâr kilidi (tüm semboller, R)
Tetik: bar yükseği (BUY) giriş + f·TP_mesafe'ye ulaştı → SONRAKİ bardan itibaren SL = giriş + L·TP_mesafe.
Aynı barda SL ve TP → SL (muhafazakâr). Kilit stopu kaymasız dolar (iyimser — not edilir).
- **Ana hipotez (kullanıcı):** f=0,80, L=0,30.
- Izgara: f ∈ {0,6, 0,7, 0,8, 0,9}, L ∈ {0,0, 0,1, 0,3, 0,5}.
- Metrik: toplam ΔR vs taban, kurtarılan kaybeden (taban SL → kilit), öldürülen kazanan (taban TP → kilit).
- Geçme ölçütü: ΔR > 0 her iki yarıda ve 2026-09-02 öncesi/sonrası ayrımında; NDX/USOIL/DAX ayrı.
Not: canlı botta NDX BUY'da BE30+koştur (M3) var — taban yönetimsizdir; etkileşim ayrıca yazılır.
