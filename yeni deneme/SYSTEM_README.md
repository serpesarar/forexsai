# ForexSAI Bot Makinesi — KOMPLE SİSTEM (kurtarma + çalıştırma rehberi)

> Bu klasör (`yeni deneme/`) + yan klasör (`../claude_decider/`) = bot makinesinde çalışan
> HER ŞEY. Bir daha silinirse panik yok: **tamamı GitHub'da** (`serpesarar/forexsai`).
> `git clone` ile geri gelir (aşağıda). Tek elle koyulacak şey: 2 config dosyası (şifreler).

---

## 🗺️ Veri akışı (sistem haritası)
```
                ┌─ data_recorder.py ──→ Supabase (candle_cache + indicator_snapshots)
   MT5          │   (OHLC + 28 indikatör, sürekli kayıt)
 (IC Markets) ──┤
                └─ forexsai_demo_bot.py ──→ MT5 emirleri (kural-bazlı: momentum, S/R,
                    channel-reversion, VIX-regime scope'ları)

 Pepperstone   ┌─ claude_decider/run_decider.py ──→ Opus kararı (shadow journal)
   MT5       ──┤   (NASDAQ/DAX/Altın/Petrol + VIX, evidence-temelli)
                └─ claude_decider/vix_recorder.py ──→ Supabase vix_live (canlı VIX)
```

## ⚙️ 4 süreç — ne çalıştırılır
| # | Komut | Ne yapar |
|---|---|---|
| 1 | `python data_recorder.py` | MT5 → Supabase OHLC+indikatör kaydı (sürekli) |
| 2 | `python forexsai_demo_bot.py` | Kural-bazlı forex botu (IC Markets) |
| 3 | `python run_decider.py` *(claude_decider/ içinden)* | Opus evidence-decider (Pepperstone, shadow) |
| 4 | `python vix_recorder.py --terminal "C:/.../Pepperstone/terminal64.exe"` | Pepperstone VIX → Supabase |

> 1+2 IC Markets terminaline, 3+4 Pepperstone terminaline bağlanır. İki terminal ayrı kurulu olmalı.

## 📁 Dosyalar — `yeni deneme/`
| Dosya | Rol |
|---|---|
| `forexsai_demo_bot.py` | Ana bot: tarama döngüsü, scope'lar, MT5 emir gönderme |
| `data_recorder.py` | Sürekli MT5→Supabase OHLC+indikatör kaydı (1m freeze'in kalıcı çözümü) |
| `sr_zones.py` | 1m destek/direnç kümeleme + S/R giriş planı (pending limit) |
| `channel_filter.py` | Linreg-kanal + VWAP mean-reversion filtresi (channel_reversion scope) |
| `indicators.py` | 29 indikatör hesabı (VWAP z dahil) |
| `combo_filter.py` · `discrimination.py` | Araştırma motorları (nested-CV + placebo, edge keşfi) |
| `sl_forensics.py` · `sl_indicator_analysis.py` | SL post-mortem analizi (gelişim) |
| `config.py` | ⚠️ ŞİFRELER — git'te YOK, elle koy (aşağı bak) |

## 📁 Dosyalar — `../claude_decider/`
| Dosya | Rol |
|---|---|
| `run_decider.py` | Canlı shadow döngü (Pepperstone → gate → Opus → journal → outcome) |
| `decide.py` | Opus kararı (`claude -p`, evidence-temelli özerk) + per-sembol stop |
| `evidence.py` + `evidence_tables.json` | Koşullu base-rate "veteran hafızası" |
| `gates.py` | 5m mean-rev kapısı + allow-list + VIX-regime |
| `outcomes.py` | WIN/LOSS grading (broker-saat tutarlı) |
| `distill_journal.py` | Haftalık kanıt-kapılı öğrenme (journal → LESSONS) |
| `vix_recorder.py` | Pepperstone VIX → Supabase vix_live |
| `memory/` | PLAYBOOK · LESSONS · REGIME (Opus'un okuduğu) |
| `decider_config.py` | ⚠️ Pepperstone yolu + Supabase — git'te YOK, elle koy |

---

## 🆘 KURTARMA (her şey silinirse — bot makinesinde)
```bat
git clone --filter=blob:none --no-checkout https://github.com/serpesarar/forexsai.git forexsai-bot
cd forexsai-bot
git sparse-checkout init --cone
git sparse-checkout set "yeni deneme" claude_decider
git checkout main
pip install -r "yeni deneme/requirements.txt"
pip install MetaTrader5 numpy requests
```
→ Tüm kod geri gelir (~400K). Sonra **2 config dosyasını** koy (bunlar git'te YOK):

### `yeni deneme/config.py` içermesi gerekenler
- `MT5_ACCOUNT` / `MT5_PASSWORD` / `MT5_SERVER` (IC Markets demo)
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY`
- `FOREXSAI_API` (Railway backend URL)
- `SYMBOL_MAP`, `ROBUST_SCOPES`, `CHANNEL_REVERSION`, `VIX_REGIME_*` (scope ayarları)

### `claude_decider/decider_config.py` içermesi gerekenler
- `PEPPERSTONE_TERMINAL_PATH` (Pepperstone terminal64.exe yolu)
- `SYMBOL_CANDIDATES`, `VIX_CANDIDATES`, `VIX_REGIME_THRESHOLD`, `BLOCKED_SYMBOL_DIRECTIONS`
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` (vix_recorder için)

> Bu 2 dosyanın güncel/dolu hali Mac'teki `panel/yeni deneme/config.py` ve
> `panel/claude_decider/decider_config.py`'de DURUYOR — oradan kopyalanır.

## 🔄 Güncelleme (WhatsApp YOK)
Mac'te değişiklik yapılınca → bot makinesinde `forexsai-bot` klasöründe: `git pull`. Bitti.
