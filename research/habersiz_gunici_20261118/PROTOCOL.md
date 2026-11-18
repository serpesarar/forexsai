# Ön kayıt — Habersiz gün içi sert düşüş → dönüş (2026-11-18)

Sonuçlara bakılmadan yazıldı. Gerekçe: §3-38 (habere dayanan hareket sürer, habersiz döner). GI-01 gün içi korkuyu haber ayrımı yapmadan
sınadı (X); yeni tanım haber ayrımı.

## Tanım
- NDX nakit seansında 30 dk'lık barlar (10:00 → 15:30 kapanışları). Bar getirisi ≤ −e, e ∈ {%0,6, %1,0}.
- Günde yalnız ilk tetik. Giriş bar kapanışından sonraki 1m açılışı (ask); çıkış aynı gün 16:00 veya ertesi gün 16:00 (bid).
- Grup: habersiz gün (takvimde CPI/NFP/FOMC/JH yok) vs olay günü. Analiz → 2026-10-02.
- Taban: aynı gruptaki günlerde aynı saatte rastgele bir 30 dk barı kapanışından giriş (gün başına 1, tohum sabit).

## Ölçüt
Habersiz grupta NDX Duka ESKİ ve YENİ'de ikisinde de ort > 0 ∧ > taban ∧ tüm dönem P ≥ 0,975 (2 eşik × 2 çıkış = 4 hücre, Bonferroni
0,05/4 → 0,9875); kör MT5 US30 ve US2000 (M30, giriş sonraki bar açılışı) habersiz grupta ort > taban → B. P hariç → C+.
Yalnız NDX → C. Değilse X. Olay grubu bilgi olarak raporlanır.

## EK-1 — Bağımsız eski dönem ve besleme teyidi (ZA-05 sonuçları görüldükten sonra; kural ve parametreler değiştirilmeden)
- **Bağımsız dönem:** Dukascopy NDX M30 2016-04 → 2017-12 + EET30 2016-11 → 2017-12 (Duka 1m'den önce; bu soruda hiç bakılmadı).
- **Besleme teyidi (veri sağlamlığı, bağımsız kanıt değil):** MT5 NAS100 M30 2018 →, NQ 5m 2019–24, MT5 US500 M30 2021 →.
- Hücre: e %0,6 ve %1, ertesi 16:00 çıkışı, habersiz grup; taban aynı (rastgele 30 dk bar).
- **Yükseltme ölçütü:** 2016–17'de iki beslemenin ikisinde de ort > taban (n küçük, işaret yeter) ∧ MT5 NAS100 ve NQ'da ort > taban
  → ZA-05 B'ye yükselir (P eşiği orijinal veride 0,983 kaldığı için "B (bağımsız dönem teyitli)" yazılır). 2016–17'de eksi → C+ kalır.
