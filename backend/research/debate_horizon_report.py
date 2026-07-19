"""Agregasyon: ufuk-bazlı isabet, sembol/saat/ajan/kalibrasyon kırılımları."""
import json, os, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(HERE, "debate_records.json")))
HORIZONS = [10, 20, 30, 60, 120, 240]

def signed(rec, ret):
    """Tahmin yönünde işaretli getiri (%). bullish→+ret, bearish→−ret."""
    if ret is None:
        return None
    if rec["bias"] == "bullish":
        return ret
    if rec["bias"] == "bearish":
        return -ret
    return None  # neutral/choppy ayrı ele alınır

def fmt_bucket(rows, label):
    parts = [f"{label:<28} n={len(rows):>2}"]
    for m in HORIZONS:
        s = [signed(r, r[f"ret_{m}"]) for r in rows]
        s = [x for x in s if x is not None]
        if not s:
            parts.append(f" {m:>3}m: --")
            continue
        wins = sum(1 for x in s if x > 0)
        parts.append(f" {m:>3}m:{wins}/{len(s)}({wins/len(s)*100:.0f}%) r={st.mean(s):+.3f}")
    day = [r for r in rows if r["day_correct"] is not None]
    dayw = sum(1 for r in day if r["day_correct"])
    parts.append(f" | gün:{dayw}/{len(day)}")
    return "".join(parts)

directional = [r for r in recs if r["bias"] in ("bullish", "bearish")]
neutralish = [r for r in recs if r["bias"] not in ("bullish", "bearish")]
print(f"TOPLAM {len(recs)} koşu — yönlü {len(directional)}, nötr/choppy {len(neutralish)}")
print("\n== GENEL (yönlü çağrılar): ufuk-bazlı isabet + ort. işaretli getiri % ==")
print(fmt_bucket(directional, "TÜMÜ"))

print("\n== SEMBOL bazında ==")
by = defaultdict(list)
for r in directional:
    by[r["symbol"]].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== RUN LABEL (karar saati) ==")
by = defaultdict(list)
for r in directional:
    by[r["run_label"]].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== YÖN bazında ==")
by = defaultdict(list)
for r in directional:
    by[r["symbol"] + " " + r["bias"]].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== CONFIDENCE kovası ==")
by = defaultdict(list)
for r in directional:
    c = r["confidence"] or 0
    b = "low<60" if c < 60 else ("med60-75" if c < 75 else "high>75")
    by[b].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== AGENT AGREEMENT ==")
by = defaultdict(list)
for r in directional:
    by[str(r["agreement"])].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== DEBATE WINNER ==")
by = defaultdict(list)
for r in directional:
    by[str(r["winner"])].append(r)
for k in sorted(by):
    print(fmt_bucket(by[k], k))

print("\n== NÖTR/CHOPPY çağrılar: |hareket| gerçekleşmesi ==")
for r in neutralish:
    moves = {m: r[f"ret_{m}"] for m in HORIZONS}
    print(f" id={r['id']:>2} {r['symbol']:<12} {r['run_label']:<14} bias={r['bias']:<8} "
          f"60m={moves[60]} 240m={moves[240]} gün={r['day_change_pct']} doğru={r['day_correct']}")

print("\n== UZMAN AJAN stance'ları — ufuk isabeti (yönlü stance verenler) ==")
ag = defaultdict(lambda: defaultdict(list))  # agent -> horizon -> signed rets
agn = defaultdict(int)
for r in recs:
    for name, stance in (r.get("agents") or {}).items():
        if stance not in ("bullish", "bearish"):
            continue
        agn[name] += 1
        for m in (30, 60, 240):
            ret = r[f"ret_{m}"]
            if ret is None:
                continue
            ag[name][m].append(ret if stance == "bullish" else -ret)
for name in sorted(agn, key=lambda x: -agn[x]):
    line = f"{name:<18} n={agn[name]:>2}"
    for m in (30, 60, 240):
        s = ag[name][m]
        if s:
            w = sum(1 for x in s if x > 0)
            line += f" {m:>3}m:{w}/{len(s)}({w/len(s)*100:.0f}%) r={st.mean(s):+.3f}"
    print(line)

print("\n== MFE/MAE (ilk 60dk, tahmin yönüne göre lehte/aleyhte maksimum) ==")
for grp, rows in sorted({s: [r for r in directional if r["symbol"] == s] for s in {r["symbol"] for r in directional}}.items()):
    fav, adv = [], []
    for r in rows:
        if r["mfe60_up"] is None:
            continue
        f_, a_ = (r["mfe60_up"], r["mfe60_dn"]) if r["bias"] == "bullish" else (r["mfe60_dn"], r["mfe60_up"])
        fav.append(f_); adv.append(a_)
    if fav:
        print(f"{grp:<12} n={len(fav)} lehte-maks ort={st.mean(fav):+.3f}%  aleyhte-maks ort={st.mean(adv):+.3f}%")

print("\n== EXPECTED_CLOSE hata analizi ==")
errs = []
for r in recs:
    ec, day = r.get("expected_close"), r.get("day_change_pct")
    if ec and r["p0"] and day is not None:
        try:
            pred_pct = (float(ec) - r["p0"]) / r["p0"] * 100
            errs.append((r["symbol"], r["run_label"], round(pred_pct, 2), day, round(abs(pred_pct - day), 2),
                         (pred_pct > 0) == (day > 0)))
        except (TypeError, ValueError):
            pass
if errs:
    dir_ok = sum(1 for e in errs if e[5])
    print(f"n={len(errs)} yön-tutarlılık={dir_ok}/{len(errs)} ort |hata|={st.mean(e[4] for e in errs):.2f}pp")
    for e in errs:
        print("  ", e)

print("\n== KOŞU-BAZLI DETAY (yönlü) ==")
for r in sorted(directional, key=lambda x: (x["symbol"], x["ny_date"])):
    print(f" id={r['id']:>2} {r['ny_date']} {r['symbol']:<12} {r['run_label']:<14} {r['bias']:<7} "
          f"c={r['confidence']:.0f} agr={str(r['agreement'])[:5]:<5} win={str(r['winner'])[:8]:<8} "
          f"10m={r['ret_10']} 30m={r['ret_30']} 60m={r['ret_60']} 240m={r['ret_240']} gün={r['day_change_pct']} ok={r['day_correct']}")
