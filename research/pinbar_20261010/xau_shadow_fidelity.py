"""xau_shadow.py (canlı mantık) ↔ xau_card_sl.py (araştırma) sadakat testi — XAU 1h, 2016 → 2026-09-02.
⚠️ ESKİ: 2026-10-16'da xau_shadow mekanik R0B_G1 tanımına geçti (atr_before/is_signal/resolve API'si kalktı) →
bu betik artık çalışmaz; güncel parite: research/xau_best_days_20261015/golge_parite/parity.py"""
import sys, importlib.util as u
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "yeni deneme"))
import xau_shadow as xs
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
sp2 = u.spec_from_file_location("deep", HERE / "deep.py"); D = u.module_from_spec(sp2); sp2.loader.exec_module(D)
d = pd.read_parquet(HERE / "data/XAUUSD_1h.parquet"); d = d[d.ts < "2026-09-03"].reset_index(drop=True); F = S.features(d)
o, h, l, c, seg, atr = F["o"], F["h"], F["l"], F["c"], F["seg"], F["atr"]; n = len(o); H, K, SPR = 20, 1.5, 0.25
# araştırma: tek pozisyon, giriş o[e]+0.25
ref, busy = {}, -1
for i in np.where(D.pin_mask(F, kind="hepsi"))[0]:
    e = i + 1
    if i <= busy or e + H - 1 >= n or seg[e] != seg[i] or seg[e + H - 1] != seg[i]: continue
    A = atr[i]; ent = o[e] + SPR; stop = ent - K * A; out = None
    for j in range(e, e + H):
        if l[j] <= stop: out = (min(o[j], stop) if j > e else stop); last = j; break
    if out is None: out, last = c[e + H - 1], e + H - 1
    ref[i] = (out - ent) / (K * A); busy = last
# canlı mantık: aynı barlar, sırayla; olay açıksa overlap
ts = (d.ts.astype("int64") // 10**9).to_numpy()
bars = [{"t": int(ts[k]), "open": o[k], "high": h[k], "low": l[k], "close": c[k]} for k in range(n)]
live, openev = {}, None
for i in range(xs.LOOK + xs.ATR_N + 2, n):
    cur = bars[:i + 1][-300:]; ii = len(cur) - 1
    fresh = False
    if openev is None and xs.is_signal(cur, ii):               # önce sinyal (poll sırası): açık olay varsa overlap
        A = xs.atr_before(cur, ii)
        if A is None or i + 1 >= n: continue
        ent = o[i + 1] + SPR; sd = K * A
        openev = {"i": i, "ev": {"sig_t": cur[ii]["t"], "entry_ask": ent, "stop": ent - sd, "stop_dist": sd,
                                 "paper_close": cur[ii]["close"], "spread_assumed": SPR}}
        fresh = True
    if openev is not None and not fresh:
        r = xs.resolve(openev["ev"], cur)
        if r is not None:
            live[openev["i"]] = r["R_research"]; openev = None
            continue
common = sorted(set(ref) & set(live)); diff = [abs(ref[i] - live[i]) for i in common]
print(f"araştırma {len(ref)} işlem (ort {np.mean(list(ref.values())):+.4f}R) | canlı mantık {len(live)} işlem (ort {np.mean(list(live.values())):+.4f}R)")
print(f"ortak {len(common)}; yalnız araştırmada {len(set(ref)-set(live))}, yalnız canlıda {len(set(live)-set(ref))}; "
      f"ortak işlemlerde max |ΔR| {max(diff):.2e}, ΔR>1e-6 olan {sum(x>1e-6 for x in diff)}")
