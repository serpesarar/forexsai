"""
allocator.py — META-ALLOCATOR: sermayeyi modele değil, MOTORA tahsis et (D perspektifi).
=============================================================================
Teşhis (2026-07-09 paketi): sorun tek motorun kusuru değil, TAHSİSİN SABİT olması.
07-01/02'de reversion +6099$ kazandı, rejim döndü, AYNI motor 07-03→09 −5136$ kanadı —
çünkü sermaye kaymadı. VIXREG (+3101$) tek +EV koldu ama payı artmadı.

Bu araç GERÇEK MT5 deal geçmişinden (CSV export) motor bazlı rolling performansı ölçer ve
ÖNERİLEN lot çarpanları üretir (tavsiye niteliğinde — config'e elle uygulanır):
 - Kanayan motor (EV<0, n≥5)  → 0.25× (sıfırlanmaz: rejim dönünce sinyal kaybolmasın)
 - Nötr (±)                   → 0.50-1.00×
 - Kazanan motor              → 1.00-1.50× (EV payıyla orantılı)

Kullanım: python allocator.py --deals <mt5_deals.csv> [--days 7]
CSV formatı = paketteki export (ticket,order,time_utc,...,position_id,magic,comment).
"""
from __future__ import annotations
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

MAG = {"52890969": "momentum/SR", "52890970": "CHREV", "52890971": "VIXREG"}
BLEED_MULT, MAX_MULT = 0.25, 1.5
MIN_N = 5


def load_positions(path: str) -> list[dict]:
    """Deal'leri position_id ile eşle → kapanmış pozisyon listesi (motor, sembol, pnl, kapanış zamanı)."""
    pos = defaultdict(lambda: {"in": None, "out_t": None, "pnl": 0.0})
    for d in csv.DictReader(open(path)):
        if d.get("type") == "BALANCE":
            continue
        p = pos[d["position_id"]]
        if d.get("entry") == "IN":
            p["in"] = d
        else:
            p["out_t"] = d["time_utc"]
        p["pnl"] += float(d.get("profit") or 0) + float(d.get("swap") or 0) + float(d.get("commission") or 0)
    out = []
    for p in pos.values():
        if p["in"] and p["out_t"]:
            out.append({"engine": MAG.get(p["in"]["magic"], f"magic:{p['in']['magic']}"),
                        "symbol": p["in"]["symbol"], "pnl": p["pnl"],
                        "closed": datetime.fromisoformat(p["out_t"].replace("Z", "+00:00"))})
    return out


def allocate(positions: list[dict], days: int = 7):
    if not positions:
        print("pozisyon yok"); return
    ref = max(p["closed"] for p in positions)
    cutoff = ref - timedelta(days=days)
    recent = [p for p in positions if p["closed"] >= cutoff]
    print("=" * 66)
    print(f"META-ALLOCATOR — son {days} gün ({cutoff:%m-%d} → {ref:%m-%d}), {len(recent)} pozisyon")
    print("=" * 66)
    eng = defaultdict(lambda: [0, 0, 0.0])          # engine → [win, n, pnl]
    for p in recent:
        e = eng[p["engine"]]
        e[0] += p["pnl"] > 0
        e[1] += 1
        e[2] += p["pnl"]
    # öneri: kanayan 0.25×; kazananlar pozitif-EV payına göre 1.0-1.5×
    pos_ev = {k: v[2] / v[1] for k, v in eng.items() if v[1] >= MIN_N and v[2] > 0}
    tot_pos = sum(pos_ev.values()) or 1.0
    print(f"  {'motor':<14}{'n':>4}{'WR':>7}{'net$':>9}{'EV$/işlem':>11}   önerilen lot çarpanı")
    print("  " + "-" * 62)
    for k, (w, n, pnl) in sorted(eng.items(), key=lambda x: -x[1][2]):
        ev = pnl / n
        if n < MIN_N:
            mult, note = 1.0, "(n az — değiştirme)"
        elif ev < 0:
            mult, note = BLEED_MULT, "🩸 kanıyor → küçült (sıfırlama)"
        else:
            mult = round(min(MAX_MULT, 1.0 + 0.5 * (pos_ev.get(k, 0) / tot_pos)), 2)
            note = "⭐ kazanan → büyüt" if mult > 1.05 else "koru"
        print(f"  {k:<14}{n:>4}{100*w/n:>6.0f}%{pnl:>9.0f}{ev:>11.1f}   ×{mult:.2f}  {note}")
    print("\n  Uygulama: 'yeni deneme/config.py' scope LOT çarpanlarına elle yansıt")
    print("  (öneri niteliğinde — otomatik yazmaz). Haftada 1 koş; rejim dönünce tahsis döner.")


if __name__ == "__main__":
    deals, days = None, 7
    for a in sys.argv[1:]:
        if a.startswith("--deals="):
            deals = a.split("=", 1)[1]
        elif a.startswith("--days="):
            days = int(a.split("=", 1)[1])
    if not deals:
        print("kullanım: python allocator.py --deals=<mt5_deals.csv> [--days=7]"); sys.exit(1)
    allocate(load_positions(deals), days)
