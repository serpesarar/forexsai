# Ön-kayıt — sembol başına TP/SL optimizasyonu (2026-10-08)

Kullanıcı: "her sembolün son 1,5 aylık performansını incele, TP/SL değiştirerek en iyi kazancı bul,
sonra önceki işlemlerle test et." Defter: IO-08 (havuzda 15 çarpan ≈0), OLD-20 (NDX BUY sorun geometri;
ATR 2,0/1,0 +0,079R), M8 (TP 2,5×ATR: WR↑ para↓), M11 (USOIL RR 1,0 kapalı).

## Veri
`bot_trades` tüm kapanmış bot işlemleri (MANUEL hariç), karar başına ilk bacak, broker 1m.
Her işlem kendi GİRİŞİYLE yönetimsiz yeniden oynatılır (BE30/koştur yok); (1,1) kalibrasyonu gerçek
TP/SL'yi ≥%85 tutmazsa sonuç güvenilmez sayılır.

## Bölme (kullanıcının istediği yön)
EĞİTİM = son 45 gün (2026-08-24 → 10-08) — en iyi geometri burada seçilir.
TEST = daha önceki işlemler (2026-06-30 → 08-23) — seçilen geometri burada sınanır (geriye doğru).

## Izgara (her işlemin kendi SL/TP mesafesinin çarpanı)
SL × {0,5, 0,75, 1, 1,25, 1,5, 2, 2,5} · TP × {0,5, 0,75, 1, 1,25, 1,5, 2, 2,5, 3} = 56 hücre.

## Metrik
- `aynı lot R` = sonuç × SL çarpanı (orijinal risk birimi = aynı lotla para).
- `aynı risk R` = sonuç (lot SL'ye göre küçültülür, $ risk sabit).
Seçim: eğitimde **aynı lot toplam R** en yüksek hücre (kullanıcının "en iyi kazanç" tanımı); ayrıca
3×3 komşuluk ortalaması (tepe mi plato mu) raporlanır.

## Kapsam ve geçme
Sembol-yön başına (eğitimde ≥20 karar) + sembol başına. Geçme: seçilen hücre TEST'te mevcut geometriden
(1,1) iyi VE eğitim-en-iyinin test sırası ilk %25'te. Eğitim ↔ test hücre sıralaması Spearman ile raporlanır.
Geçen hücre yalnız GÖLGE adayıdır (≥150 olay + canlıya alma kartı, 2. KURAL).
