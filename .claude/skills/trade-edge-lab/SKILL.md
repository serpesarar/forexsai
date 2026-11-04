---
name: trade-edge-lab
description: MT5/bot işlem otopsisi ve karar-anı kesişim (confluence) araştırması — kazanan/kaybeden işlemleri giriş anındaki göstergelerle karşılaştır, aday filtreyi SONRAKİ dönemde doğrula. İşlem otopsisi, "hangi girişler kazandırıyor", strateji/filtre keşfi istendiğinde kullan; rutin UI/sinyal düzenlemesi için değil.
---

# Trade Edge Lab (Claude)

Codex ile ORTAK beceri. Araç ve veri sözleşmesi tek yerde durur, kopyalama:
- Script: `.agents/skills/trade-edge-lab/scripts/audit_trades.py`
- Veri sözleşmesi: `.agents/skills/trade-edge-lab/references/data_contract.md`
- Codex iş akışı: `.agents/skills/trade-edge-lab/SKILL.md` (aynı 6 adım geçerli)

Canlı kapıya/bot varsayılanına araştırmanın yan etkisi olarak DOKUNMA.
Aday → gölge → `go_live_gate.py` / canlı işlem kartı (CLAUDE.md 2. KURAL).

## Zorunlu sıra

1. **Saat ekseni önce.** Script her koşuda `Clock alignment` satırı basar.
   `MISALIGNED` ise DUR — tüm özellikler kaymış mumlardan hesaplanmıştır.
   (Bu projede iki kez yaşandı: broker +180 dk, export +1230 dk.) Sabit fiyat
   farkı (broker NAS100 ↔ backend NDX ≈27 puan) zaman hatası DEĞİLDİR; kontrol
   seviyeye değil fark dağılımına (IQR) bakar.
2. **Kovaya değil kombinasyona bak.** "2/3 uyumlu" gibi toplam skor, hangi
   koşulun eksik olduğunu gizler. Rapordaki `Condition combinations` tablosu
   (T/M/P büyük harf = uyumlu) asıl okunacak yerdir.
3. **n'e değil karar sayısına bak.** Aynı dakikada açılan bölünmüş bacaklar tek
   karardır; tablodaki parantez içi sayı budur.
4. **Keşfedilen her alt küme, keşfedildiği veride KANIT DEĞİLDİR.** Raporu okuyup
   bir kova seçtiysen test dönemi artık kirlidir. Doğrulama = hiç bakılmamış
   sonraki dönem: `--since <keşif verisinin bitişi>` ile yeni export'ta koş.
5. Sonucu WR ile değil **$/işlem veya R** ile raporla; `canonical-signal-metrics`
   kuralı: çıplak WR yasak.

## Veri kaynakları

| Kaynak | Dönem | Not |
|---|---|---|
| `research/trade_mgmt_ndx/trades.json` + `bars_1m.csv` | 06-15 → 07-09 | Cohort A broker saatinde (+3s) ama barlarla tutarlı; saat-bazlı analizde KULLANMA |
| `nasdaq_tam_veri_2026-08-29/islemler/*.csv` + `1m_veri/` | 07-01 → 08-27 | Gerçek MT5 UTC, düzeltilmiş; `sl_price` kapanıştaki stop (BE ile taşınmış olabilir → R hesaplanmaz) |
| Daha yenisi | — | Kutudan `scripts/remote.py sh` ile `box_export_trades_30d.py` çıktısı al |

```bash
python3 .agents/skills/trade-edge-lab/scripts/audit_trades.py \
  --trades nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv \
  --bars nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv \
  --symbol NDX.INDX --since 2026-07-10T00:00:00+00:00 \
  --out output/trade-edge-lab/ndx-forward-0710-0827
```

## Reddedilen fırsatlar (WAIT / kapı / veto)

`scripts/audit_skipped.py` botun kapı-atlama ve veto kayıtlarını 1m barlarla çözer ("kapı haklı mıydı?"). Önce simülatör botun gerçek TP/SL sonuçlarıyla kalibre edilir (<20 örnek ise durur). Logda TP/SL yok → 3 geometride (80/110, 80/60, 80/80) çözülür; aynı niyetin tekrar logları (neden, scope, yön) başına tek varsayımsal pozisyonla dedupe edilir. Yorum kuralı: **WR'ı başabaşla değil, "kapısız taban WR" ile kıyasla** (aynı tarih+saat dağılımında 5 dk'da bir giriş; rastgele yürüyüşte taban ≈ başabaş olduğu için sürüklenmeyi ayırır). Wilson CI başabaşı içeriyorsa "kanıtlı" deme.

```bash
python3 .agents/skills/trade-edge-lab/scripts/audit_skipped.py \
  --bars nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv \
  --gate-log nasdaq_tam_veri_2026-08-29/karar_gunlukleri/gate_skipped_NAS100.jsonl \
  --decision-log nasdaq_tam_veri_2026-08-29/karar_gunlukleri/demo_trades_TUM_NAS100.csv \
  --trades nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv \
  --out output/trade-edge-lab/ndx-rejected
```

## Emsal: 2026-09-30 "tMP %100" çöküşü

Pilot (06-15→07-09) 2/3 kovasında train %85,7 / test 6/6 gösterdi; kova tek bir
kombinasyondan geliyordu: **tMP** (yavaş trend ters, momentum+fiyat uyumlu) 19/19,
+3.691$ (~13 bağımsız karar). Önceden sabitlenmiş hipotezle bağımsız sonraki
dönemde (07-10→08-27, 172 işlem) tMP = **20 işlem, %50, −2.151$**; pilotta "en
kötü" görünen 0/3 kova **%63, +4.440$** çıktı. Bu üç basit 1m göstergesinin
mevcut bot işlemleri üzerinde kalıcı ayırt ediciliği YOK. Yeni aday önerirken
bu emsali hatırla.
