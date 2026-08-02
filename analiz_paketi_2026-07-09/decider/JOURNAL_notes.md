# Decider JOURNAL — ham deneyim (append-only)

> Her karar burada `journal.jsonl` olarak saklanır (bu .md insan/Obsidian görünümü).
> Bu **ham deneyim** — henüz "ders" değil. Bir desen ancak kanıt-kapısını geçince
> `LESSONS.md`'e terfi eder (aşağıdaki kural). Hurafe öğrenmemenin tek koruması bu.

## Kayıt formatı (`journal.jsonl`, her satır bir karar)
```json
{
  "ts": "2026-06-27T14:30:00Z",
  "symbol": "NDX.INDX", "dir": "BUY",
  "gate": {"source": "channel", "z": 2.4},
  "vix": {"value": 21.3, "favored": "BUY", "aligned": true},
  "context": {"open_positions": 1, "net_exposure": "...", "session": "NY", "near_event": false},
  "decision": {"action": "APPROVE", "size_factor": 0.7, "reason": "...", "management": "..."},
  "model": "sonnet",
  "outcome": null            // sonradan doldurulur: "WIN"|"LOSS"|"BE"|"VETOED" + pnl
}
```

## 📈 Kanıt-kapısı — bir desen LESSONS'a NE ZAMAN terfi eder
Haftalık re-damıtma (`distill_journal.py`) bir aday dersi yalnız şu durumda terfi ettirir:
- **min 20 örnek** (deduped, 60dk/kurulum) — küçük-örnek hurafesini engeller
- **WR base'i ≥ +8pp geçiyor** VE breakeven (%60) üstünde
- **placebo p < 0.05** (permütasyon testi) — şans değil
- Aksi halde aday `LESSONS.md`'de "⏳ izleniyor" kalır, kararı ETKİLEMEZ.

> Decider bu dosyayı her kararda OKUMAZ; yalnız `LESSONS.md` (damıtılmış) + son ~10
> kayıt (yakın bağlam) okunur. Ham journal = re-damıtma yakıtı.
