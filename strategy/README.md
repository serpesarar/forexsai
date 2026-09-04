# Strateji Laboratuvarı

2026-08-28 → 09-02 arasında NASDAQ üzerinde test edilen tüm stratejiler,
**aynı sembol-bağımsız arayüzle** yeniden koşulabilir hâlde. Amaç: aynı bataryayı
XAUUSD / USOIL / GDAXI üzerinde tekrarlamak.

## Çalıştırma

```bash
python3 strategy/kosu.py --sembol NAS100 \
  --barlar   nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv \
  --islemler nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv \
  --tam-izgara
```

`--sadece s08_geri_cekilme_limit` ile tek strateji, `--tam-izgara` ile bütün
parametre taraması + canlıya alma kartı.

## Yeni sembol nasıl eklenir

1. **İşlemler** — kutuda:
   `python backend/research/box_export_trades_30d.py --days 120`
   → çıkan CSV'yi ilgili sembol için süz (`symbol` sütunu).
2. **1m barlar** — kutuda `copy_rates_range(sembol, TIMEFRAME_M1, ...)`
   (MT5 terminali 1m'de ~100 gün geriye tutuyor).
3. `kosu.py`'yi o iki dosyayla çağır. Başka değişiklik gerekmez —
   tüm stratejiler `Veri` nesnesi üzerinden çalışır.

⚠️ Sembol adı MT5 adıdır: `NAS100`, `GER40`, `SpotCrude`, `XAUUSD`.

## KAPI 0 — zaman ekseni hizalaması (atlanamaz)

`kosu.py` her koşuda `hizalama_kontrol()` çalıştırır ve **lag≠0 ise durur.**
Sebep: 2026-08-29'da bir export +1230 dk kayık çıktı (bayat tick → yanlış broker
offset) ve üç ajanın analizini birden bozdu. Hizalama, işlem fiyatının ilgili
1m barın aralığına oturup oturmadığıyla ölçülür.

## Kabul protokolü

| kapı | ölçüt |
|---|---|
| 0 | zaman ekseni hizalı (lag=0, uyum >%90) |
| 1 | hacim: kalan n ≥ 150 |
| 2 | beklenti: ortR > 0 ve bootstrap %95 GA sıfırı içermiyor |
| 3 | kronolojik: 4 çeyreğin hepsi pozitif |
| 4 | hafta-çıkarma: çoğunlukta bazı geçiyor |
| 5 | permütasyon p < 0,05 (çok-hücre taramasında Bonferroni ile) |
| **6** | **GERÇEK DIŞ-ÖRNEKLEM: kural geliştirilirken kullanılmamış veri** |

**Kapı 6 olmadan hiçbir strateji "geçti" sayılmaz.**

## 🔴 Bu oturumda pahalıya öğrenilen dersler

1. **İç-örneklem dayanıklılığı dış-örneklemin yerini TUTMAZ.**
   S05 iç-örneklemde plato 9/9 + hafta 9/9 + p=0,0033 verdi; yeni haftada
   engellediği 3 işlemin 3'ü de TP çıktı, 4 SL'in dördünü de geçirdi.

2. **Kapı backtest'i yanlıdır.** Mevcut bir kapıdan (POS_SELL_MIN=0,40) GEÇMİŞ
   işlemlere daha sıkı eşik uygulamak, sıkı kapının canlıda BLOKLAYACAĞI
   popülasyonu ölçmez. S06'da backtest "+8.401$" dedi, botun gölge karnesi
   bloklananların %62 kazandığını gösterdi. **Gölge kanıtı backtest'i ezer.**

3. **Kozmetik WR tuzağı.** Kazanma oranı yükselirken paranın yatay/negatif
   kalması, hedefi küçültmenin/erken kilidin imzasıdır (S03, S04).

4. **Sınır artefaktı.** Bir parametre monoton iyileşiyorsa (plato yok), model
   ulaşılamaz bir ideale yakınsıyordur — S04'te "zirvenin %99'unda stop"
   = tepeden sat. S08'de X monoton artıyor → sonuç ÜST SINIR olarak okunmalı.

5. **Simülatör kalibre edilmeli.** İki ajan aynı CSV'den 4,8× farklı sonuç
   üretti; sebep çıkış ufku varsayımıydı. Baz simülasyon canlı P&L'e yakın
   değilse mutlak büyüklük iddiası yapılmaz.

6. **Giriş fiyatını bozan her kural kazananı keser.** S07'de gecikmeli giriş
   SL'i fiyata yaklaştırdı: 13 TP→SL çevrilme vs 3 kurtarma. S08 tam tersini
   yapıyor (daha iyi fiyat → SL uzaklaşır) ve tek dış-örneklem geçen strateji.

## Dosyalar

```
ortak/veri.py    Veri yükleme + resample + KAPI 0 hizalama kontrolü
ortak/sim.py     Sızıntısız TP/SL yarışı, ATR, sıkışma, pivotlar, konum
ortak/olcum.py   Özet, çeyrek, hafta-çıkarma, permütasyon, bootstrap, kart
s01..s08         Stratejiler (her biri calistir(v,**p) -> {id: usd})
kosu.py          Hepsini bir sembolde koşturan CLI
SONUCLAR.md      NASDAQ karnesi (tek tablo)
```
