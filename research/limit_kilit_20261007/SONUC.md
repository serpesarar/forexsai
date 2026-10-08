# Sonuç — "20 puan geri çekilme limiti" ve "%80'de %30 kâr kilidi" (2026-10-07)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · kod: `run.py` · ham: `results/*.csv`.
Veri: 548 bağımsız bot kararı (2026-06-30 → 10-07), 311'i NDX; broker 1m; yönetimsiz yeniden oynatma
(gerçek sonuçla %98,5 uyum). Dolum muhafazakâr: BUY limiti ASK limitin altına inince dolar; dolum barında TP
sayılmaz; aynı barda iki bariyer → kötü olan.

## A. Girişten sonra 20–30 puanlık düşüş her zaman geliyor mu?

| NDX (306 TP/SL karar) | SL ile bitenler | TP ile bitenler |
|---|---:|---:|
| ilk 30 dk'da ≥20 puan ters | %89 | %57 |
| çıkışa / TP'ye kadar ≥20 puan ters | %96 | %64 |
| aynısı — DAYCOMBO + REENTRY (11 SL / 38 TP) | %100 | %55 |
| aynısı — NDX BUY (23 SL / 49 TP) | %87 | %49 |
| TP öncesi medyan ters hareket (DAYCOMBO) | — | 26 puan |

**Hayır, her zaman değil:** 20 puanlık düşüş kaybedenlerin neredeyse hepsinde, kazananların ancak yarısında var.
20 puan HİÇ düşmeyen NDX işlemlerinin %92'si TP; düşenlerin %51'i.

## B. 20 puan daha iyi fiyattan limitle girilseydi

NDX (SL ≥80 puan olan 270 karar), tabana (sinyalde piyasadan giriş) göre toplam puan farkı:

| varyant | dolum | fark (puan) | kaçan TP |
|---|---:|---:|---:|
| **X=20, 30 dk, dolmazsa atla** (aynı mesafe) | %73 | **−2.320** | 68 |
| X=20, 30 dk, dolmazsa atla (aynı TP/SL seviyesi) | %73 | −1.630 | 68 |
| **X=20, 30 dk, dolmazsa piyasadan gir — S08 ana hipotezi** | %73 | **−551** | 0 |
| X=20, 120 dk, dolmazsa atla | %83 | −1.218 | 46 |
| ızgaranın tamamı (X 10/20/30/40 × 30/120 dk × atla/piyasa × 2 geometri) | | 32 varyantın 30'u negatif; en iyi +209 | |

- DAYCOMBO + REENTRY (49 karar): 16 varyantın 15'i negatif, biri 0; X=20/30 dk/atla **−1.429 puan**.
- S08 hipotezi her iki yarıda ve 2026-09-02 sonrası (S08'in görmediği dönem) negatif → **S08'in +19.606$'ı tekrarlanmadı**
  (olası nedenler: iyimser dolum — BID dokunuşunu dolum saymak, dolum barında TP; "monoton/plato yok" uyarısı zaten yazılıydı).
- Mekanizma: limit, düşüş vermeyen (%92 kazanan) işlemleri kaçırıyor, kaybedenlerin hemen hepsini dolduruyor —
  OLD-21'deki ters seçilimin aynısı. Dolan işlemler iyileşiyor (NDX BUY: −130 → +630 puan) ama kaçan kazananlar daha pahalı.

## C. TP'nin %f'i dolunca SL'yi TP mesafesinin %L'sine çek

548 karar, tüm semboller, R (fark = kilitli − taban):

| f | L | fark R | 1. yarı | 2. yarı | 09-02 sonrası | NDX | USOIL | P(fark>0) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **0,8** | **0,3** (kullanıcı) | **−0,3** | +5,1 | **−5,5** | −2,5 | −3,0 | +6,1 | %48 |
| 0,6 | 0,5 | +18,4 | +19,7 | −1,3 | −1,0 | +1,3 | +16,1 | %93 |
| 0,9 | 0,3 | +10,0 | +10,7 | −0,7 | −2,3 | +4,0 | +6,0 | %96 |

- %80/%30: 23 SL kurtarıyor, **57 TP'yi öldürüyor** → sıfır. NDX'te −3,0R, DAYCOMBO +0,2R (1 kurtarılan / 2 öldürülen).
- **16 varyantın 16'sı da 2. yarıda ve 09-02 sonrasında negatif.** Pozitif toplamlar ilk yarıdan ve çoğunlukla USOIL'den
  geliyor; defter M9'daki "USOIL kilidi örneklem içi +10R, bağımsızda −8,1R" ile aynı desen.
- DAYCOMBO 06.10 (#397377651) bu kuralla kurtulurdu (+24 puan ≈ +720$ yerine −3.297$) — ama tek vaka; aynı kural
  geçmişte bu vakanın 2,5 katı kazananı kesiyor.

## Hüküm
İki fikir de ön-kayıtlı ölçütü geçemedi → **ELENDİ** (B: S08 tekrarlanmadı, C: M9 teyidi). Kilit tablosundaki
f=0,6 / f=0,9 hücreleri "ikinci yarıda negatif" olduğu için aday DEĞİL; yeniden açmak için yeni veri gerekir.
Not: kilit stopu kaymasız varsayıldı (iyimser); canlıda NDX BUY'da zaten BE30+koştur (M3) var.
