# Ön kayıt — Korku gecesi (K1) ayı çağlarında da çalışır mıydı? Günlük vekil ile 1993–2017 (2026-11-18)

Sonuçlara bakılmadan yazıldı. Gerekçe: W2 haftalık korku 1999–2017'de çöktü (dot-com, 2008). Canlı/aday korku kuralları yalnız 2018–26
verisiyle doğrulandı. Gün içi veri 2016 öncesinde yok. Günlük OHLC'den vekil kurulur, önce 2018–26'da K1'i yeniden ürettiği kanıtlanır.

## Vekil (günlük ETF; QQQ ana, SPY/DIA/IWM tekrar)
- **V1:** C ≤ ((H + L) / 2) × (1 − %0,5) ∧ C < O (günün orta noktasının altında, düşüşle kapanış). K1'in "TWAP altı ∧ son saat aşağı"
  tanımına en yakın günlük karşılık.
- İşlem: d kapanışında AL → d+1 kapanışı. Maliyet 2 bp + finansman (taban da öder). Taban: V1 olmayan günler.

## Doğrulama aşaması (önce)
2018-04 → 2026-11 QQQ'da V1 ile NDX Duka K1 gecelerinin örtüşmesi ve V1 getirisi raporlanır. **Geçerlilik:** QQQ V1 fark > +20 bp ve K1
gecelerinin ≥ %50'si V1. Geçmezse vekil geçersiz, çalışma durur (X değil, "ölçülemedi").

## Asıl soru (vekil geçerliyse)
1993/1999 → 2017 alt dönemler: 1993–98, 1999–2002 (dot-com), 2003–07, 2008–09 (kriz), 2010–17.
- Her alt dönemde V1 fark ve ort, en kötü işlem, birikimli en büyük düşüş.
- **Hüküm (risk etiketi, kural değil):** ayı alt dönemlerinin (99–02, 08–09) ikisinde de fark > 0 → "K1 ayı çağında da çalışıyor (sağlam)".
  Biri eksi → "çağa bağlı risk" (canlı lot için uyarı). İkisi de eksi → "boğa çağına bağlı" (ciddi uyarı).

## EK-1 — Vekil ile iki C+ adayının bağımsız eski dönem sınaması (vekil geçerli çıktıktan sonra yazıldı; adayların tanımları değiştirilmeden)
Dönem: **1993/1999 → 2017-12** (aday sonuçlarını üreten 2018–26 verisiyle örtüşmez). ETF: QQQ ana, SPY/DIA/IWM tekrar.
- **GN-05 art arda korku:** V1(d) ∧ (V1(d−1) ∨ d−1 açılış→kapanış ≤ −%1) vs V1(d) ∧ değil. Ölçüt: QQQ'da ardışık > değil ∧ SPY/DIA/IWM'nin
  ≥ 2'sinde aynı → GN-05 **B**'ye yükselir; tersi → X'e düşer; karışık → C+ kalır.
- **ZA-04 olay günü korkusu:** (takvim 2008 →) 2008–2017: V1 ∧ olay günü vs V1 ∧ habersiz (her grup kendi tabanıyla). Ölçüt: QQQ'da
  DD = fark(habersiz) − fark(olay) > 0 ∧ ≥ 2/3 öteki ETF'te aynı → ZA-04 **B**'ye yükselir; tersi → X; karışık → C+ kalır.
