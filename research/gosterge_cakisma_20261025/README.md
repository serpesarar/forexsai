# Gösterge Çakışma Motoru (GÇM)

TradingView göstergelerini (resmî 127 teknik + topluluktaki 33.389 scriptin 55 ailesi) her sembolün tüm veri
geçmişine uygular. Göstergelerin **eş zamanlı tepkileri ve tepki kombinasyonlarının** bir sonraki 1…32 barın
yönünü saat-eşli tabandan daha iyi öngörüp öngörmediğini ölçer. Bunu dar ufuktan geniş ufka ve 1m'den 1d'ye her
zaman diliminde tekrarlar, bulunan kombinasyonun başka TF ve sembollerde tekrarlanıp tekrarlanmadığını sınar.

- Ön kayıt: [PROTOCOL.md](PROTOCOL.md)
- Sonuç tabloları: [SONUCLAR.md](SONUCLAR.md)
- Anlatı ve hüküm: [RAPOR.md](RAPOR.md)

## Hat

```
data.py        kaynak → temiz OHLC(V), segment (boşluk), KEŞİF/DOĞRULAMA/KASA bölmesi
indicators.py  133 nedensel gösterge → 353 ikili durum (boğa/ayı çiftleri) + 64 sürekli özellik
engine.py      tetik (durumun başladığı bar), yakın tetik (≤3 bar), örtüşme bastırma, etiket, taban,
               bloklu matris çarpımıyla kombinasyon sayımı, dairesel kaydırma plasebosu
miner.py       her ufuk: L1 tek tepki · L2 tepki ∧ durum / tepki ∧ yakın tepki · L3 üçlü → seçim → 3 bölme kararı
model.py       tüm göstergeler birlikte (HistGradientBoosting) → kasa AUC, en emin %10 isabeti
summarize.py   hücre tablosu, sistem hükmü, tekrarlanma (her aday tüm sembol × TF × h hücrelerinde)
rapor.py       SONUCLAR.md tabloları
inceleme.py    mum-mum inceleme hattı: inceleme/<SYM>_<TF>.html
coverage.py    topluluk scriptlerini kapsama oranı
test_causality.py  prefix + gelecek pertürbasyonu testi (geleceğe bakan gösterge yakalar)
```

## Çalıştırma

```bash
cd research/gosterge_cakisma_20261025
../../.venv/bin/python test_causality.py NDX 1h     # önce: geleceğe bakan gösterge yok mu?
../../.venv/bin/python run.py NDX                    # bir sembolün tüm TF'leri (madencilik + model)
../../.venv/bin/python run.py ALL                    # dört sembol
../../.venv/bin/python coverage.py && ../../.venv/bin/python summarize.py && ../../.venv/bin/python rapor.py
../../.venv/bin/python inceleme.py ALL               # HTML inceleme sayfaları
```

Süre (M-serisi, tek çekirdek):
- NDX 1h ≈ 2 dk, 1m ≈ 20–25 dk.
- DAX / XAU / USOIL tüm TF'ler ≈ 10–15 dk / sembol.

## Genişletme

- **Yeni gösterge:** `indicators.py` içinde `B.pair("AD", "<aile_kodu>", "<durum>", boga_kosulu, ayi_kosulu)`.
  Aile kodu `topluluk_taramasi/classify.py`'deki kodlardan biri olmalı, yoksa kapsama sayılmaz.
  Ardından `test_causality.py` çalıştırılmalı.
- **Yeni sembol / TF:** `config.py` → `SOURCES` ve `SPREAD`.
- **Yeni ufuk / bölme / eşik:** `config.py`. Ama ön kayıtlı değerleri değiştirmek PROTOCOL'e "EK" ister ve eski sonuçlar
  yeniden koşulmalıdır.

## Dürüstlük kuralları (kodda gömülü)

- Giriş sonraki barın açılışı (E7).
- Taban aynı bölmenin aynı UTC saati (E13/E15/E27).
- Örtüşen olaylar bastırılır (E6).
- Seçim eşiği aramanın tamamının plasebo max|z|'si (E24/E48).
- KASA yalnız sonda okunur.
- Ters yönde anlamlı sonuçlar da sayılır (E26/E28).
