# ForexSAI Analiz Paketi — 2026-07-09

Bu klasör, "Claude Decider" (Opus/Fable karar katmanı) ile gerçek MT5 (Pepperstone)
sonuçlarını karşılaştırmalı analiz etmek için tek yerde toplanmış veri setidir.
Amaç: nerede yanlış yapılmış, hangi kararlar/sinyaller kazandırmış/kaybettirmiş.

## Klasör yapısı

### `decider/` — Opus/Fable karar katmanı verileri
| Dosya | İçerik |
|---|---|
| `journal.jsonl` | **Ham veri, en önemli dosya** (2026-07-09, backlog TAMAMEN eritildi). Her satır bir karar anı: sembol, canlı özellikler (rev_chan/rev_vwap/adx/vix), kullanılan kanıt (WR/n/OOS), Opus'un kararı (action/direction/size/reason/management), counterfactual (açsaydı ne olurdu), gerçek `outcome`/`cf_outcome` (WIN/LOSS/EXPIRE), `exit_grades` (6 farklı çıkış stratejisinin R sonucu), `forensics` (çok-TF S/R + trend anlık görüntüsü), `batch_eval` (Fable+Opus toplu değerlendirme işareti — **tüm 1043 grade'li kayıtta dolu**, hem Fable hem Opus tarafından). |
| `LESSONS.md` | Decider'ın öğrendiği/terfi ettirdiği kurallar (kanıt-kapılı). |
| `REGIME.md` | Güncel piyasa rejimi notları (VIX eşiği, sembol trend bağlamı, aktif yasaklar). |
| `PLAYBOOK.md` | Doğrulanmış priorlar. |
| `JOURNAL_notes.md` | Serbest-metin günlük notlar (varsa). |
| `_kod_*.py` | Karar mantığının kendisi (decide.py=prompt+guardrail, decider_config.py=sembol/eşik ayarları, run_decider.py=ana döngü, gates.py=mean-reversion kapı mantığı, forensics.py=çok-TF snapshot). Kararların NEDEN böyle verildiğini anlamak için. |
| `01-07_*.txt` | Mevcut analiz araçlarının (post_mortem/analyze_missed/calibration/exit_compare/baseline_compare/model_compare/outcomes) bu tarihte alınmış çıktıları — aşağıda özet var. |
| `00_BLOKER_login_gerekli.txt` | Fable/Opus toplu analiz ilk denemelerde CLI login eksikliğiyle başarısız oldu; dosyanın sonunda **ÇÖZÜLDÜ** notu ve nihai sonuçlar var. |
| `batch_eval_fable_run.log` | İlk başarılı Fable turu (70 kayıt, $0.46, WR %62) — sonraki turlar `backlog_turlari/`'de. |
| `batch_eval_opus_run.log` | İlk başarılı Opus turu (aynı 70 paket, $1.17, WR %83) — sonraki turlar `backlog_turlari/`'de. |
| `batch_eval_kumulatif_rapor.txt` | **NİHAİ** Fable + Opus kümülatif skorbord — backlog'un TAMAMI (1043/1043 kayıt) işlendikten sonraki tam tablo. |
| `backlog_turlari/tur{2-15}_{fable,opus}.log` | Backlog'u eritmek için çalıştırılan 14 ek tur × 2 model = 28 log dosyası (her biri kendi WR/EV/maliyetini içerir). |

### `trades/` — Gerçek MT5 işlem geçmişi
- `mt5_deals_son_14gun.csv` — Pepperstone hesabındaki (61551449, Demo) son 14 günün TÜM deal
  kayıtları (BALANCE hariç asıl işlemler dahil): ticket, order, zaman (UTC + broker-epoch),
  sembol, BUY/SELL, IN/OUT, hacim, fiyat, **profit**, position_id (aynı pozisyonun giriş+çıkışını
  eşlemek için), magic (hangi bot/scope açtığını ayırt eder), comment (`forexsai-sr`, `fxs NDX.INDX:...`,
  `[sl ...]`, `[tp ...]` gibi etiketler kaynağı gösterir). 326 deal.
- Tarih aralığı: 2026-06-25 → 2026-07-09 (UTC, "şimdi"den geriye 14 gün).

### `prices/` — Aynı tarih aralığının 1 dakikalık OHLCV verisi
- `NDX_INDX_1m_son_14gun.csv`, `GDAXI_INDX_1m_son_14gun.csv`, `USOIL_FOREX_1m_son_14gun.csv`,
  `XAUUSD_1m_son_14gun.csv` — sütunlar: time_utc, open, high, low, close, tick_volume, spread, real_volume.
  ~12-14 bin bar/sembol. `trades/` ile `time_utc` üzerinden hizalanabilir (deal zamanına en yakın barı bul).

## Fable/Opus TOPLU analiz sonuçları (batch_eval.py) — BACKLOG TAMAMEN ERİTİLDİ

İlk denemeler CLI login eksikliğiyle başarısız oldu (bkz. `00_BLOKER_login_gerekli.txt`),
kullanıcı `claude /login` ile giriş yaptıktan sonra başarıyla tamamlandı. Ardından 14 ek tur
daha çalıştırılarak **journal'daki TÜM 1043 grade'li kayıt** (70/tur kapasiteyle) hem Fable
hem Opus'a **sızıntısız** protokolle (fiyat/zaman/sonuç/karar sıyrılmış + shuffle) soruldu —
adil A/B, tam kapsam:

### NİHAİ KÜMÜLATİF SONUÇ (1043/1043 kayıt, her iki model de aynı paketleri gördü)
| Kaynak | Değerlendirdiği | OPEN | WR | EV(R) |
|---|---|---|---|---|
| **claude-fable-5** | 1043 | 234 | **%48 (112/234)** | **−0.231R** |
| **opus** | 1043 | 224 | **%46 (102/224)** | **−0.259R** |
| (canlı Opus kararı — gerçekte çalışırken verdiği kararlar) | — | 78 | **%62 (48/78)** | — |
| (naive-gate: kapı ateşleyen HER şeyi aç, hiç muhakeme yok) | 1043 | 1043 | **%60** | — |

**⚠️ EN ÖNEMLİ BULGU:** Tam veri setinde hem Fable'ın hem Opus'un **kör toplu muhakemesi
(batch_eval)**, hem **canlı Opus kararlarından (%62)** hem de **hiçbir akıl yürütmeden kapı
ateşleyen her şeyi açan naive stratejiden (%60)** DAHA KÖTÜ çıktı (%48 / %46). Yani bu özel
görevde ("bu kurulumda işlem açar mısın, hangi yön?") LLM'in seçiciliği DEĞER KATMIYOR —
tam tersi, rastgele/naive kabul etmekten daha kötü sonuç veriyor. Olası açıklamalar:
- Batch prompt'unun sağladığı bağlam (yalnız ATR-göreli z-skorlar, mutlak fiyat/S-R yok)
  canlı kararda kullanılan zengin bağlamdan (VIX taze mi, korelasyon, session, LESSONS/REGIME
  metni) daha fakir — modelin "kör" değerlendirmesi daha az bilgiyle yapılıyor.
  → **Adil olmayabilir**: canlı karar LESSONS/REGIME/PLAYBOOK metnini okuyor, batch_eval
  sadece whitelist edilmiş sayısal alanları görüyor.
- Ya da: canlı Opus'un asıl değeri "WAIT" deme kararında (gate ateşlese bile açmama) —
  batch_eval'da bu oran daha düşük WAIT/OPEN dengesi üretiyor olabilir (fable 234/1043=%22
  OPEN, opus 224/1043=%21 OPEN — ikisi de canlıdaki orana yakın ama sonuç WR'ları daha düşük).
- Turlar arasında (bkz. `backlog_turlari/`) WR **çok değişken**: bazı turlarda her iki model
  de %0 WR verdi (tur 7-8, ~93 OPEN hepsi kayıp), bazılarında %80-100 — bu, journal'ın
  kronolojik olarak biriktiği ve bazı dönemlerin (örn. güçlü trend/rejim flip) sistematik
  olarak modele YANLIŞ göründüğünü düşündürüyor. Diğer analiz oturumunun bu tur-bazlı
  varyansı `backlog_turlari/tur*.log` dosyalarından inceleyip hangi sembol/dönem/rejimde
  toplandığını (journal.jsonl'deki ts/symbol ile eşleştirerek) araştırması önerilir.

**Toplam maliyet (login sonrası, tüm 15 tur × 2 model):** ~$24.61 (28 başarılı API çağrısı;
1 tur geçici parse hatasıyla başarısız oldu, otomatik sonraki turda kendini düzeltti).

## Bilinen sorunlar (bu paket hazırlanırken bulundu)

1. **`model_compare.py` çöküyor (gerçek kod hatası).** `SHADOW_MODEL = None` yapıldıktan
   (canlı gölge-model kapatıldı, 2026-07-03 commit) sonra script'in başlık formatlama satırı
   (`model_compare.py:98`) `None` model adını `%d`/`.0f` gibi formatlamaya çalışıp
   `TypeError: unsupported format string passed to NoneType.__format__` ile çöküyor.
   Çökmeden ÖNCE ürettiği kısmi veri kaydedildi (`07_model_kiyas_opus_fable.txt`):
   son gölge-etkin dönemden **196 karşılaştırmalı karar**, %97 karar-anlaşması,
   Opus kendi OPEN'larında **WR %20 (1/5), EV −0.666R**.

## Hızlı okuma sırası önerisi (diğer analiz için)
1. `decider/journal.jsonl` — ham gerçek; `outcome`/`cf_outcome` alanlarına göre WIN/LOSS filtrele.
2. `decider/batch_eval_kumulatif_rapor.txt` — Fable vs Opus vs canlı-karar vs naive-gate kıyası.
3. `decider/02_sl_otopsi.txt` — kaybı kazançtan ayıran istatistiksel koşullar (n=419 grade'li).
4. `decider/03_kacirilan_analiz.txt` — açılmayan ama kazanacak işlemler (recall/aşırı-temkin analizi).
5. `decider/04_kalibrasyon.txt` — Opus'un verdiği WR tahminleri gerçekte tutuyor mu.
6. `decider/05_cikis_optimizasyon.txt` — hangi çıkış stratejisi (sabit/trailing/breakeven/time) en karlı.
7. `trades/mt5_deals_son_14gun.csv` + `prices/*.csv` — journal'daki kararları gerçek MT5 sonuçlarıyla
   çapraz doğrulamak / journal dışı (recorder/bot) etkiyi görmek için.
