"""
Adım 1b — 5m mean-reversion edge'in per-sembol/yön DÜRÜST base rate'leri (PLAYBOOK v2 için).
Sabit kapı: 5m_rev_chan>2.0 VEYA 5m_rev_vwap>1.5 (aşırı mean-reversion, yön-hizalı).
Dedup + zaman-bazlı OOS (son %40). XAU SELL yasağı / USOIL SELL-only doğrulansın.
"""
import json, sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
sys.path.insert(0, str(ROOT / "yeni deneme"))

recs = [json.loads(l) for l in open(ROOT / "sr_rejection_research" / "data" / "features.jsonl")]
recs.sort(key=lambda r: r["t"])


def gate(r):
    """yön-hizalı 5m aşırı mean-reversion kapısı → (geçti?, rev_chan, rev_vwap)"""
    buy = r["dir"] == "BUY"; f = r["f"].get("5m")
    if not f:
        return None
    rc = rv = None
    c = (f.get("chan") or {}).get("50") or (f.get("chan") or {}).get(50)
    if c and c["spp"] > 1e-9:
        z = c["pm"] / c["spp"]; rc = (-z) if buy else z
    if f.get("vwap"):
        vz = f["vwap"]["vwap_z"]; rv = (-vz) if buy else vz
    passed = (rc is not None and rc > 2.0) or (rv is not None and rv > 1.5)
    return passed, rc, rv


# dedup 60dk/kurulum
last = {}; rows = []
for r in recs:
    k = (r["model"], r["symbol"], r["dir"]); t = datetime.fromisoformat(r["t"]).timestamp()
    if k in last and t - last[k] <= 3600:
        continue
    last[k] = t
    g = gate(r)
    if g is None:
        continue
    rows.append({**r, "_pass": g[0], "_t": t})
rows.sort(key=lambda x: x["_t"])
split = rows[int(0.6 * len(rows))]["_t"]  # son %40 = OOS


def stats(sel):
    n = len(sel); w = sum(x["win"] for x in sel)
    return n, (w / n * 100 if n else 0)


print("Per (sembol, yön) — sabit kapı: 5m rev_chan>2.0 OR rev_vwap>1.5\n")
hdr = f"{'sembol':<14}{'yön':<5}{'base_n':>7}{'base_WR':>9}{'kapı_n':>8}{'kapı_WR':>9}{'lift':>7}{'OOS_n':>7}{'OOS_WR':>8}"
print(hdr); print("-" * len(hdr))
by = defaultdict(list)
for r in rows:
    by[(r["symbol"], r["dir"])].append(r)
for (sym, d), sel in sorted(by.items()):
    bn, bwr = stats(sel)
    g = [x for x in sel if x["_pass"]]
    gn, gwr = stats(g)
    oos = [x for x in g if x["_t"] >= split]
    on, owr = stats(oos)
    lift = gwr - bwr
    flag = ""
    if gn >= 25:
        flag = "  ✅" if (gwr >= 65 and lift >= 8) else ("  ⚠️" if gwr >= 58 else "  ❌")
    print(f"{sym:<14}{d:<5}{bn:>7}{bwr:>8.0f}%{gn:>8}{gwr:>8.0f}%{lift:>+6.0f}{on:>7}{owr:>7.0f}%{flag}")
