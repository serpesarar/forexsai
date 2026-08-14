# NASDAQ faz uygulaması — 2026-08-14

Kaynak: 133 NASDAQ işlemi + 33.353 adet 1m bar üzerinde bar-bar karşı-olgusal
denetim (iki bağımsız model + iki tur çapraz hakemlik). Uygulama kuralları
`phase_rules.py`'de topludur; bot yalnız "veri topla → kurala sor → logla/uygula".

> ⚠️ **Kanıtın sınırı:** tüm eşikler TEK AYIN verisinden çıkarıldı ve aynı ay
> üzerinde optimize edildi. Aşağıdaki WR/net rakamları **örneklem içi**dir;
> canlıda bu seviyeler beklenmemelidir. Bayrakların amacı canlı ölçümü mümkün
> kılmaktır. Faz-1'in seçtiği alt küme n=71 — yani ayın yarısı; küçük örneklemde
> %80'lik oranların güven aralığı geniştir.

---

## 1. Etki haritası (hangi kural nereye dokundu)

| Faz | Kural | Dosya · fonksiyon | Bayrak (varsayılan) |
|---|---|---|---|
| 0.1 | Koşullu başabaş (MFE ≥ 0.5R) | `trade_manager.manage_positions` | `MGMT_BE_MODE='conditional_mfe'` **açık** |
| 0.2 | Zaman stopu | `trade_manager._time_stop_pass` + `_close_at_market` | `MGMT_TIME_STOP_MIN=240` **açık** |
| 0.3 | TP = 2.5×ATR70(1m) | `forexsai_demo_bot._fixed_distances` + `open_trade_v2`; hesap `phase_rules.tp_distance` | `TP_MODE='atr'` **açık** |
| 0.3b | TP tabanı = 0.3×SL (**plan dışı ekleme**) | `phase_rules.tp_distance` | `TP_ATR_MIN_R=0.3` **açık** |
| 1.1 | ASIA 22–07 UTC yasağı | `_entry_window_blocks` → `check_scope` / `check_vix_regime` / `check_channel_reversion` / `check_daycombo` | `NDX_SESSION_BLOCK_ENABLED=False` |
| 1.2 | Cuma yasağı + Cuma 20:45 sonrası | aynı fonksiyon | `NDX_FRIDAY_BLOCK=False`, `NDX_WEEKEND_HOLD_BLOCK=False` |
| 1.3 | S/R-limit kolunu kapat | `_route_open` | `NDX_SR_ENTRY_ENABLED=True` |
| 1.4 | SCOUT oyu sayma + zone çıtası 4 | `_confirm_required`, `open_trade_sr` | `PHASE1_CONFIG_RESTORE=False` |
| 2.1 | Sıkı dalga konumu (SELL ≥0.60 / BUY ≤0.40) | `_position_gate_blocks` | `POS_TIGHT_ENABLED=True`, `POS_TIGHT_BLOCK=False` (**gölge**) |
| 2.2 | SELL için 5m RSI>55 | aynı yerde, gölge logu | `SELL_RSI_SHADOW_ENABLED=True` |
| 3 | MOD-E probasyon (5 bar) | `_shadow_probation` → `shadow_log.record_probation` | `PROBATION_SHADOW_ENABLED=True`, `PROBATION_LIVE=False` (**gölge**) |
| — | Ardışık SL soğuması | `phase_rules.loss_streak_cooldown_active` | **bağlanmadı** (etkisi nötr, backlog) |

Teslim sözleşmesi: **Faz-0 açık, Faz-1 kapalı, Faz-2/3 gölge.** Faz-1, Faz-0'ın
go/no-go'sundan (2 hafta) sonra tek komutla açılır.

## 2. Mevcut kodla çakışma analizi

| Mevcut mekanizma | Yeni kuralla ilişkisi |
|---|---|
| **4h dalga konum kapısı** (SELL ≥0.40 / BUY ≤0.60, VIXREG'de BLOK) | Korundu. Sıkı eşik (0.60/0.40) ONUN ÜSTÜNE gölge katman olarak eklendi; mevcut kapı bloklamışsa sıkı katman zaten devreye girmez (çift log yok). |
| **VIXREG ATR-uyarlamalı SL** (2.0×ATR(5m), 60–200) | **Dokunulmadı.** Faz-0.3 yalnız TP'yi değiştirir. Sonuç: VIXREG'de RR artık TP(ATR70)/SL(ATR5m) — ikisi de oynak. Log satırı (`[TP-ATR] … RR x.xx`) bunu her girişte yazar. |
| **Momentum-continuation filtresi** (backend) | Değişmedi; Faz-1.3 yalnız girişin İCRA kolunu (limit → yok) kapatır, filtreyi değil. |
| **Claude Decider istisnası** (TQ çukurunda onay) | Faz-1 zaman yasakları decider istisnasının **ÖNÜNDE** çalışır: ASIA/Cuma penceresinde decider onayı olsa da giriş yok (kapı `check_*` başında). Bilinçli: TQ "çıtayı yükselt", Faz-1 "tamamen kapat" demektir. |
| **`ATR_GEOMETRY` (NDX BUY, kapalı)** | Bağımsız. Açılırsa SL'i o belirler, TP'yi yine Faz-0.3 ezer. |
| **DAYCOMBO** | TP değişiminden muaf (`TP_ATR_EXCLUDE_SCOPES`); zaman stopu ve BE kapsamı dışında değil (BE zaten yalnız yönetilen magic'ler). |
| **Kazananı-koştur (runner)** | Zaman stopu `phase='run'` pozisyona dokunmaz — koşan kazanan kesilmez. |
| **`fxs-v2` backend geometrisi** | TP'si de ATR70'e çekilir; yoksa aynı scope iki farklı hedefle çalışır ve ölçüm bozulur. |

## 3. Karşı-olgusal doğrulama (kod = analiz mi?)

`1MDATA/mt5_islem_analizi/04_phase_replay.py` botun **gerçek kural modülünü**
kullanarak aynı 133 işlemi yeniden çözer. Referans rakamlar birebir tutuyor:

| Senaryo | Analiz | Bu koddaki replay |
|---|---|---|
| Simülatör kalibrasyonu (mevcut kural, BE'siz) | WR %60.2 | **WR %60.2** ✓ |
| Faz-1 filtrelerinin seçtiği küme | n=71 | **n=71** ✓ |
| Faz 0+1 | WR %81.7 · +4.512$ | WR %80.3 · +4.764$ (zaman stopsuz) |
| MOD-E (probasyon + TP80, Faz-1 filtreli) | n=65 · WR %75.4 · +8.537$ | **n=65 · %75.4 · +8.537$** ✓ |
| Probasyon + küçük TP (yasak) | daha kötü | **daha kötü** (+2.478$ vs +6.383$) ✓ |

Regresyon testi: `tests/test_phase_replay_equivalence.py` (veri yoksa atlanır) +
`tests/test_phase_rules.py` (32 birim testi).

### Plandan tek sapma — zaman stopu 120 → 240 dk
Aynı replay'de 120 dk **zararlı** çıktı: işlemleri erken kesiyor (TP tabanı
devredeyken WR %72,2→%67,7, net +4.110$ → +1.816$). 240 dk ise aynı "zombi"
korumasını verirken net'i +4.716$'a **yükseltiyor**. Varsayılan 240 yapıldı. Plandaki değere dönmek için:
```
python3 scripts/bot_flags.py set MGMT_TIME_STOP_MIN 120 --restart
```

### Plan dışı EKLEME — ATR TP'ye alt taban (`TP_ATR_MIN_R=0.3`)
Kutuda canlı veriyle koşulan duman testi (`box_phase_smoke.py`, Cuma 22:02 UTC,
piyasa ölü) şunu gösterdi: **ATR70(1m)=4,8pt → TP 12pt / SL 110 = RR 0,11**.
Başabaş kazanma oranı %90; üstüne spread hedefin ~%15'ini yer. Örneklemde de
133 işlemin 35'i RR<0,30 ile açılmış (min RR 0,07).

Taban taraması (aynı 133 işlem, TP = max(2,5×ATR70, taban×SL)):

| taban | WR | net | 1,5pt spread ile | 3pt spread ile |
|---|---|---|---|---|
| yok (plandaki hâli) | %73,7 | +2.678$ | +1.788$ | +899$ |
| 0,2×SL | %73,7 | +3.827$ | — | — |
| **0,3×SL (seçilen)** | **%72,2** | **+4.110$** | **+3.220$** | — |
| 0,4×SL | %69,2 | +3.793$ | +2.904$ | +2.014$ |
| 0,5×SL | %66,2 | +500$ | — | — |
| 0,6×SL (= yasak listesindeki 66pt) | %60,2 | **−6.219$** | — | — |

Yani yasak listesindeki "min TP 66pt" maddesi **doğru** — ama sebebi tabanın
kendisi değil, tabanın yüksekliği. 0,3 tabanı her spread varsayımında tabansız
hâlden iyi. Kapatmak için: `python3 scripts/bot_flags.py set TP_ATR_MIN_R 0.0`.

### TP=ATR70'in tek başına etkisi (taban dahil, bu ayın verisinde)
| Kural | n | WR | net |
|---|---|---|---|
| eski (TP 80 sabit, BE'siz sim) | 133 | %60.2 | +1.643$ |
| **TP = 2.5×ATR70 + 0,3 taban** | 133 | **%72.2** | **+4.110$** |
| yukarısı + zaman stopu 240 | 133 | %72.2 | **+4.716$** |
ATR70 hedefi medyan **46pt** üretiyor (min 17 / maks 108) — sabit 80pt yerine;
taban devredeyken 33pt'nin altına inmiyor.

## 4. Gölge log şeması

`gate_skipped.jsonl` (karar anı, sızıntısız):
`ts, scope, symbol, mt5_symbol, direction, reason='shadow:<kural>', rule,
decision('would_block'|'would_wait'), price, sl, tp, shadow=true` + kurala özel
alanlar (`pos`, `sell_min`, `buy_max`, `rsi5m`, `rsi_gate_pass`, `atr_1m`, `band`).

`shadow_followup.jsonl` (sonuç, 10 bar / probasyon çözümü sonrası):
`decided_at, rule, decision, price, next10_high, next10_low, next10_close,
mfe, mae` — probasyonda ayrıca `entry, slippage_vs_signal, adverse, band,
outcome(WIN|LOSS|TIMEOUT|cancelled), minutes`.

Durum dosyası: `shadow_pending.json` (restart-dayanıklı).

## 5. Geri alma planı (tek komut)

```
python3 scripts/bot_flags.py revert-all --restart   # her şey eski davranışa
python3 scripts/bot_flags.py phase0 off --restart   # yalnız Faz-0'ı geri al
python3 scripts/bot_flags.py phase1 on  --restart   # Faz-1'i aç (go/no-go sonrası)
python3 scripts/bot_flags.py phase2 block --restart # sıkı konum kapısını BLOK yap
python3 scripts/bot_flags.py show                  # etkin değerler
```
Kill-switch (plan): haftalık net < −1.500$ → `revert-all`.

## 6. Canlı ölçüm karnesi (doldurulacak)

| Aşama | Beklenen (örneklem içi sim) | Canlı ölçüm | Karar |
|---|---|---|---|
| Mevcut (referans) | n=133 · %56.4 · −907$ | — | — |
| Faz 0 (taban + stop 240) | %72.2 · +4.716$ | … | 2 hafta sonra go/no-go: WR farkı ≤5 puan → Faz-1 |
| Faz 0+1 | n=71 · %80.3 · +4.970$ | … | … |
| Faz 0+1+2 (MOD-W) | n=36 · %88.9 | … | 2 hafta gölge → BLOK |
| MOD-E (Faz 3) | n=65 · %75.4 · +8.537$ | … | 4. hafta: işlem başına net MOD-E ≳ MOD-W ise ana motor |

## 7. Yapılmayanlar (bilerek)

- **Faz 4** (Beta-Binomial/SPRT scope sağlık monitörü, EWMA rejim alarmı, DAYCOMBO
  lot artışı, Kelly) — 2. ay planı, backlog'a yazıldı.
- **Ardışık SL soğuması** — kural motoru var, bota bağlanmadı (etkisi nötr).
- **Yasak listesi** — hiçbiri uygulanmadı (min TP 66pt, MFE-zemin, Hurst router,
  5m teyit mumu, EMA50 trend kapısının SELL'e yayılması, kovalama yasağı).
