"""Sızıntı / eksen doğrulamaları (çıktı: results/leak_checks.txt).
1) Zaman ekseni: journal 'price' (karar anındaki MT5 5m kapanışı = o anki bid) ile düzeltilmiş 1m
   kapanışı, dönem bazında (07-28 öncesi kaymış satırlar / sonrası) ve dakika kayması (−5..+5) ile.
2) İcra edilen 68 işlemde simülatörün orijinal TP/SL sonucu gerçek MT5 sonucuyla örtüşüyor mu.
3) ATR yalnız kapalı barlardan mı: atr_closed(t) hesaplamasında kullanılan son barın bitişi ≤ giriş."""
import numpy as np
import pandas as pd
import core

HERE = core.HERE
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
lines = []
d = pd.read_pickle(HERE / "data" / "trades_full.pkl")
b = core.load_1m().set_index("t_utc").close
cut = pd.Timestamp("2026-07-28 18:00", tz="UTC")
for name, m in [("07-28 öncesi (kaymış etiketler düzeltildi)", d.decision_time_utc < cut),
                ("07-28 sonrası (UTC etiketli)", d.decision_time_utc >= cut)]:
    s = d[m]
    for off in (-180, -60, -3, -2, -1, 0, 1, 60, 180):
        diffs = [abs(b[t]-p) for t, p in zip((s.decision_time_utc + pd.Timedelta(minutes=off)).dt.floor("min"), s.j_price) if t in b.index]
        lines.append(f"{name:45s} offset {off:+4d} dk  medyan|Δ|={np.median(diffs):7.3f}  n={len(diffs)}")
x = d[d.executed]
ct = pd.crosstab(x.exec_outcome, x.sim_outcome)
lines.append("\nİcra (68) gerçek sonuç × simülasyon sonucu:\n" + ct.to_string())
r5 = core.resample(core.load_1m(), "5min")
viol = 0
for t in d.entry_time_utc.dropna().sample(200, random_state=1):
    ends = r5.t_end[r5.t_end <= t]
    viol += int(ends.max() > t)
lines.append(f"\nATR kapalı-bar kontrolü: 200 örnekte ihlal = {viol}")
lines.append(f"Giriş gecikmesi (karar→ilk yol barı, dk) gölge: {d[~d.executed & d.usable.astype(bool)].entry_delay_min.describe().round(2).to_dict()}")
(OUT / "leak_checks.txt").write_text("\n".join(lines))
print("\n".join(lines))
