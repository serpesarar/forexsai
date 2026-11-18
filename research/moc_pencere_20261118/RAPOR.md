# Kapanış müzayedesi (MOC) penceresi: 15:50 → 16:00 düşüşü ve korku gecesi (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/moc.py` (`kesif`, `dogrula`). Bağımsız besleme: MT5 NAS100 2m (2017–2026) ve NQ 5m.

## Soru
Korku gecesi ABD'ye özgü (Avrupa'da yok, bkz. `korku_kuresel_20261118`). Aday açıklama: 15:50'de yayımlanan kapanış müzayedesi
dengesizliği fiyatı kapanışa doğru iter, baskı ertesi gün geri döner. Bu doğruysa 15:50 → 16:00 düşüşü korku gecesini güçlendirmeli.

## Sonuç: X (ön kayıt); 09:30 çıkışlı tek iz C

| hücre | ESKİ | YENİ (kör) | MT5 2m | NQ 5m | hüküm |
|---|---|---|---|---|---|
| K1 ∧ son 10 dk ≤ −%0,1 vs K1 ∧ değil (ertesi 16:00) | +96,9 vs +4,0 (P 0,996) | **+41,6 vs +48,2** (fark −6,6) | fark +23,2 | +11,5 | X |
| K1 ∧ son 10 dk ≤ −%0,2 vs değil | +105,5 vs +17,6 | +42,7 vs +45,2 | +34,8 | −5,1 | X |
| son 10 dk ≤ −%0,3 → ertesi 09:30 | +46,4 vs −0,7 | +18,7 vs −2,7 (P 0,951 < 0,967) | +25,5 vs −0,2 (P 0,988) | +29,0 vs −0,5 (P 0,975) | X; iz C |

- **Doz yok.** ESKİ'deki büyük fark (+93 bp) kör dönemde tamamen kayboluyor. Son 10 dakikanın düşüp düşmemesi K1 gecesinin sonucunu
  değiştirmiyor. Müzayede baskısı korku gecesinin açıklaması değil, en azından 2021 sonrasında.
- **Tek iz:** son 10 dakikada ≥ %0,3 düşüşten sonra gece tutuşu (16:00 → ertesi 09:30) üç beslemede de +19…+29 bp. Ama Bonferroni
  eşiğinin altında, K1 gecelerinden ayrıldığında zayıflıyor (K1 dışı P 0,87) ve zaten korku gecesi kuralının gece kısmı.
- Bilgi (ESKİ): son saati "müzayede yukarı döndü" ve "düşüş sürdü" diye ayırınca sürdüğünde +32, döndüğünde +13 bp. Yön sezgiyle
  uyumlu ama anlamlı değil.

## Sonuç
Korku gecesinin ABD'ye özgülüğü müzayede penceresinden gelmiyor. Kalan adaylar: ABD'de günlük risk azaltımının (kaldıraçlı/oynaklık
hedefli fonlar) kapanışa yığılması ve ertesi gün yeniden alım. MA-04 "kaldıraçlı akış yoğunluğu" daha önce X'ti. Mekanizma açık
kalıyor; kural yine de doğrulanmış (B).
