# Pine Motoru — TradingView topluluk scriptlerini birebir çalıştırma

TradingView'deki kaynağı açık topluluk scriptleri (gösterge + strateji) kendi Pine v1–v6 motorumuzla dört sembolün
1h verisinde çalıştırılır. Çıktıları (plot, şekil, alarm, renk, strateji girişi) ikili "tepki durumlarına" çevrilir.
Her tepkinin ve tepki çiftinin ileri yön isabeti, Gösterge Çakışma Motoru'nun (`../gosterge_cakisma_20261025`) etiket,
taban, plasebo ve ölçütleriyle sınanır. Ön kayıt: `PROTOCOL.md` (EK-P1…P6). Hüküm: `RAPOR.md` — PN-01 X (2026-10-28).

## Boru hattı (sırayla)

| Adım | Komut | Çıktı |
|---|---|---|
| 1. Kaynak indir | `python download_sources.py` | `data/src/sources.jsonl.gz` |
| 2. Eksik kütüphaneler | `python fetch_libs.py` | `data/src/libs_extra.jsonl.gz`, `data/lib_index_v2.json` |
| 3. Derleme taraması (tanı) | `python compile_scan.py [motor_dizini] [çıktı]` | `data/compile_scan*.json` |
| 4. Tam koşu | `python batch.py recent 0 7` | `data/runs/recent/part_*.pkl.gz` (+ `engine_log.txt`) |
| 5. Eski motor kayıtlarını yenile | `python batch.py retry recent 7 stale` | parçalar yerinde, `retry_log_stale.json` |
| 6. Eşitlik testi (motor değiştiyse) | `python equiv_check.py <motor> 500 <eski_tarama> <yeni_tarama>` | konsol |
| 7. Değerlendirme (A1+A2) | `python eval_scripts.py` | `results/<SYM>/cells.csv`, `meta.json` |
| 8. Tekrarlanma | `python replicate_pine.py` | `results/tekrar_pine.csv` |
| 9. Tablolar | `python pine_rapor.py` | `SONUCLAR.md`, `results/hukum_pine.json` |
| 10. Mum mum inceleme | `python pine_inceleme.py ALL` | `inceleme/<SYM>.html`, `inceleme/index.html` |

`batch.py` ve `replicate_pine.py` multiprocessing (spawn) kullanır; **dosyadan** çalıştırılmalıdır (stdin'den değil).
`data/` git'e girmez (kaynaklar, koşu parçaları).

## Motor

| Dosya | Görev |
|---|---|
| `pine_parser.py` | Girinti tabanlı lexer + ayrıştırıcı (v1–v6, yumuşak anahtar kelimeler, çok satırlı string, satır devamı) |
| `pine_transpile.py` | AST → Python `__run` bar döngüsü; kütüphaneler, UDT, metotlar, aşırı yükleme |
| `pine_runtime.py` | na mantığı, seriler, dizi/harita/matris, çizim nesneleri, renk, UDT |
| `pine_ta.py` | `ta.*` artımlı karşılıkları (çağrı yeri × bağlam başına durum) |
| `pine_builtins.py` | Yerleşik fonksiyon tabloları, v4 eşlemeleri, çıktı yakalama |
| `pine_broker.py` | `strategy.*` broker emülatörü (sonraki açılışta dolum, OHLC yolu, braketler) |
| `pine_run.py` | Çalışma zamanı (RT), `request.security` çok geçişli (üst/alt TF, Heikin Ashi), kütüphane yükleme |
| `signals.py` | Çıktı kanalları → tepki durumları (sabit kurallar) |

## Bilinen sınırlar

- Başka sembol verisi (`request.security("TVC:DXY", …)`), footprint, ekonomik veri ve renko/kagi grafikleri desteklenmez. Bunlar "uygulanamadı" sayılır, kenarsız sayılmaz.
- Script başına sembol başına 60 sn sınırı vardır.
- A1/A2 araması son 12.000 1h barında yapılır. Tüm tarih ve diğer zaman dilimleri yalnız adayların tekrar sınamasında kullanılır (EK-P1, EK-P3).
