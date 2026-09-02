# Çıkış geometrisi araması + kârı artırma denemesi (kullanıcı hedefi)

**Veri:** 282 NAS100 işlemi + 100.000 adet 1m bar (doğrulanmış eksen) · sürtünme 2pt
**Denenen:** 120 çıkış-geometrisi hücresi + 2 filtre + kombinasyonlar

## 1. Kullanıcının kuralı genelleştirildi — çalışmıyor (48 hücre)

`MFE ≥ tau×TP_mesafesi → SL = giriş + phi×zirve` (takipli)

| tau \ phi | %20 | %30 | %40 | %50 | %60 | %70 | %80 | %90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| %30 | −3.098 | −1.841 | −338 | +775 | +738 | +1.588 | +2.854 | +5.198 |
| **%50** | −1.531 | −791 | −1.126 | **−379** | −885 | +94 | +2.135 | +4.359 |
| %70 | +2.503 | +3.318 | +2.636 | +2.813 | +3.439 | +2.527 | +3.686 | **+5.339** |
| BAZ | +4.997 | | | | | | | |

**48 hücrenin 46'sı bazın altında.** Kullanıcının sorduğu gevşetme yönü
(%50 → %40 → %30 → %20) sistematik olarak **daha kötü** — sol sütunlar en negatif.

## 2. phi sınır kontrolü — görünen "kazanan" bir sınır artefaktı

TP kaldırılmış, tau=%70: phi=%85 → +4.984 · %90 → +6.301 · %95 → +7.901 · **%99 → +9.187**

Sıkılaştırdıkça monoton iyileşiyor, **optimum yok — sınıra kaçıyor.** phi=%99
"stop zirvenin %99'unda" = *tepeden sat* demek; gerçekleştirilemez. Yani
phi=%90 sütunundaki artılar bir mekanizma değil, bu ideale yaklaşmanın gölgesi.

## 3. Diğer aileler de geçemedi

| aile | en iyi | bazı geçen hücre |
|---|---:|---|
| A: takipli kâr-stop | +5.339 (+342) | 2/48 |
| B: TP kaldır, sadece takip | +6.301 (+1.304) | 3/48 |
| C: kısmi kapatma (%25/50/75) | +3.582 (−1.415) | **0/24** |

**120 hücrenin 5'i (%4) bazı geçiyor — şans seviyesi.** Medyan hücre −4.266$.
Gerçek mekanizma olsaydı hücrelerin çoğu geçer ve etrafında plato olurdu.

## 4. ASIL BULGU — çıkışta değil GİRİŞTE (gerçekleşen para, simülasyon değil)

Bu oturumda **plasebo testi geçmiş** iki filtre birleştirildi:
Cuma ≥12 UTC bloğu (p=0,015) + ATR sıkışma ≥1,0 (p=0,043)

| | n | gerçekleşen USD |
|---|---:|---:|
| filtresiz | 282 | **+4.290** |
| **filtreli** | **141** | **+11.243** |
| elenen | 141 | **−6.953** |

İki filtre birlikte **kaybeden yarıyı ayıklıyor.** Bu, tüm çıkış aramasından
elde edilen en iyi sonucun (+1.304) 5 katı — ve simülasyon değil, gerçek para.

## 5. Canlıya alma kartı (CLAUDE.md 6 ölçüt)

| # | ölçüt | sonuç |
|---|---|---|
| 1 | hacim ≥150 | **n=141 — KIL PAYI KALDI** |
| 2 | ortR>0 & P(EV>0)≥%90 | ortR=+0,172 · %95GA=[+0,034,+0,311] · **P=%99,4 GEÇTİ** |
| 3 | iki yarı da ≥0 | +0,197 / +0,148 **GEÇTİ** |
| 4 | spread ×1,5 stresi | ×1,5=+10.966 · ×3,0=+8.947 **GEÇTİ** |
| 5 | icra gerçekçiliği | gerçek MT5 dolumları **GEÇTİ** |
| 6 | sıra-bağımlı (tek pozisyon) | filtre slot serbestleştirir, ihlal 5→1 **GEÇTİ** |

**5/6 geçti.** Ama iki ciddi çekince:
1. **Hacim 141 < 150** (eşiğin altında).
2. **İyileştirmenin kendisi** bootstrap'te %95 GA=[−3.156, +16.860] → **sıfırı
   içeriyor** (P(fark>0)=%90,4). Yani filtreli kümenin kârlı olduğu çok güçlü
   (P=%99,4) ama *baza göre daha iyi olduğu* %95 çıtasını geçmiyor.
3. **Seçim yanlılığı:** iki filtre de aynı 2 aylık pencerede bulundu; kombinasyon
   sonuçlar görüldükten sonra seçildi.

## 6. Uygulanan

`FRIDAY_BLOCK_*` bayrakları eklendi (`phase_rules.py`) + `_friday_blocks` kapısı
`open_trade`/`open_trade_sr` içine bağlandı. **Varsayılan GÖLGE**
(`FRIDAY_BLOCK_LIVE=False`) — hiçbir emri değiştirmez, "engelleseydim" kaydı tutar.
Sıkışma filtresi zaten 2026-08-28'de aynı şekilde gölgeye alınmıştı.
Saf çekirdek `friday_blocks()` + 5 yeni test (toplam 11, hepsi geçiyor).

**Sonraki adım:** iki gölge bayrağı 2 hafta birlikte ölçülür → elenen kümenin
gerçek sonuçları 1m replay ile doğrulanır → hacim 150'yi aşar ve iyileştirme
GA'sı sıfırın üstüne çıkarsa `LIVE=True`.

## Ders
Kullanıcının sezgisi (SL'leri önle) mekanik olarak çalışıyordu — kaybedenlerin
%33'ünü kurtarıyor — ama kazanandan aldığı daha fazlaydı. **Çıkışı oynatarak
değil, girişi eleyerek** kâra geçiliyor: aynı emek girişte 5 kat getiri verdi.
