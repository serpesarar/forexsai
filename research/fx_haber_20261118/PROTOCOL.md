# Ön kayıt — FX'te habere dayanan ve habersiz büyük günlük hareket: ertesi gün dönüş mü, devam mı? (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "BTC ve döviz paritelerinde derin araştırma".

## Gerekçe
FX-01 H4 (§2.53): JPY çaprazlarında korku/coşku uçları **devam ediyor**, dönüş kuralları X (§3-34). §3-38 (bugün): habere dayanan hareket
sürer, habersiz hareket döner (petrol EIA, NDX korku gecesi, NDX gün içi düşüş). Hipotez: FX-01'deki "devam" iki zıt etkinin karışımı;
haber ayrımı yapılınca habersiz büyük hareketler dönmeli.

## Veri
Pepperstone D1 (sunucu günü = NY 17:00 → 17:00), `research/fx_secim_20261113/data/fx`, 2008-01 → 2026-10-02 (takvim sonu).
ABD makro takvimi (CPI/NFP/FOMC/JH) `research/xau_best_days_20261015/makro/out/calendar.csv`.
Maliyet: çiftin 2018+ H1 bar spread medyanı × 1,5 (bp, gidiş-dönüş) + gece swap'ı yok sayılır (tek gece, iki yönde simetrik kabul;
bilgi olarak meta swap raporlanır).

## Tanım
- r_d = C_d / C_{d−1} − 1; σ20 = önceki 20 günün r std'si (d hariç). Büyük gün: |r_d| ≥ k·σ20, k ∈ {1,5, 2,0}.
- **Dönüş işlemi:** d kapanışında (NY 17:00) r_d'nin tersine gir, d+1 kapanışında çık: f = −sign(r_d)·(C_{d+1}/C_d − 1)·1e4 − maliyet.
- Grup: d ABD olay günü (takvimde) mi, değil mi.
- **Ana evren:** USD'li 7 majör (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF).
- **Kör evren:** USD'siz 14 çapraz (AUDCAD, AUDJPY, AUDNZD, CADJPY, CHFJPY, EURAUD, EURCAD, EURCHF, EURGBP, EURJPY, GBPAUD, GBPCHF,
  GBPJPY, NZDJPY).
- Dönemler: KEŞİF 2008–2015, TEST 2016–2021-10, YENİ 2021-11 → 2026-10.

## Ölçütler (2 eşik; havuzlama gün-kümeli bootstrap)
- **H-dönüş (kural):** ana evren habersiz günler dönüş ort > 0 üç dönemde de ∧ tüm dönem P ≥ 1 − 0,05/2 = 0,975 ∧ kör evrende ort > 0 → B.
  Üç dönem + kör ama P altı → C+. Değilse X.
- **H-ilke:** DD = dönüş(habersiz) − dönüş(olay) > 0 üç dönemde de (ana evren) → ilke FX'te teyit (bilgi; kural değil).
- Bilgi: çift bazında, yön (risk-off/on) ayrımı, hafta sonu taşıması (Cuma) ayrı.

## EK-1 — Olay günü DEVAM kuralı (H-dönüş sonucu görüldükten sonra yazıldı; yeni hipotez, kör sınavlı)
Gözlem (görülen veri, kanıt sayılmaz): ana evrende olay günü dönüş işlemi üç dönemde eksi → devam.
- **Kural FX-OD:** d ABD olay günü (CPI/NFP/FOMC/JH) ∧ |r_d| ≥ k·σ20 → d kapanışında sign(r_d) yönünde gir, d+1 kapanışında çık.
  Net = devam getirisi − maliyet (spread × 1,5) − bugünkü swap (yaklaşık; E72 uyarısı).
- **Kör evren:** USDMXN, USDNOK, USDSEK, USDZAR (bu çalışmada hiç bakılmadı). USDTRY ön kayıtla dışarıda: aşırı carry/swap ve müdahale.
- **Ölçüt:** k ∈ {1,5, 2,0}. Kör havuz ort > 0 ∧ ≥ 3/4 çift > 0 ∧ havuz P ≥ 0,975 → B. Kör havuz > 0 ve ≥ 3/4 ama P altı → C+.
  Değilse X. Ayrıca kör evrende habersiz günlerin aynı devam işlemi (kontrol) raporlanır: olay > habersiz beklenir.
