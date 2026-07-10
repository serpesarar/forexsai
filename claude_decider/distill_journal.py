"""
distill_journal.py — kanıt-kapılı öğrenme: decider'ın KENDİ geçmişini re-damıt.
=============================================================================
"Görüp analiz eden öğrenen" döngüsünün kapanışı. JOURNAL'ın grade edilmiş kararlarını
(WIN/LOSS) aynı titizlikle (dedup 60dk + min örnek + placebo) tarar; bir deseni ancak
KANIT-KAPISINI geçince LESSONS'a terfi ettirir. Erken dönemde veri azken HİÇBİR ŞEY
terfi etmez — LLM'in 5 işlemden hurafe öğrenmesini engelleyen disiplin budur.

Ayrıca ölçer: (1) genel EV, (2) per-sembol kalibrasyon (canlı WR vs kanıt base'i — rejim
drift), (3) Opus yargısı değer katıyor mu (konviksiyon→WR? kapı-dışı öneriler tutuyor mu?).
Haftalık (veya elle) çalıştır. Opus istenirse derin analiz için kullanılabilir; bu çekirdek
istatistik saf Python (bedava).
"""
from __future__ import annotations
import json
import random
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL  # noqa: E402
from evidence import load_tables, REV_EDGES, ADX_EDGES, _bucket  # noqa: E402

LESSONS = HERE / "memory" / "LESSONS.md"
MIN_N = 20          # bir desen terfi için min örnek (deduped)
MIN_LIFT = 0.08     # base'e göre min +8pp
PLACEBO_M = 300
DEDUP_SEC = 3600
AUTO_START = "<!-- AUTO-LESSONS START (distill_journal.py üretir) -->"
AUTO_END = "<!-- AUTO-LESSONS END -->"


def _load_graded():
    if not JOURNAL_JSONL.exists():
        return [], []
    from decide import load_journal
    rows = load_journal(clean=True)   # donuk-kopya karantinası (öğrenme zehirlenmesin)
    graded = [r for r in rows if r.get("outcome") in ("WIN", "LOSS")]
    graded.sort(key=lambda r: r["ts"])
    last, out = {}, []          # dedup 60dk/sembol/yön (autocorrelation engeli)
    for r in graded:
        k = (r["symbol"], (r.get("decision") or {}).get("direction"))
        t = datetime.fromisoformat(r["ts"]).timestamp()
        if k in last and t - last[k] <= DEDUP_SEC:
            continue
        last[k] = t; out.append(r)
    return rows, out


def _wr(items):
    n = len(items)
    return (sum(1 for x in items if x["outcome"] == "WIN") / n, n) if n else (0.0, 0)


def _placebo_best_split(vals, wins, M=PLACEBO_M):
    """En iyi tek-eşik lift'i + placebo p (permütasyon). Dönüş: (op, thr, lift_pp, p)."""
    base = sum(wins) / len(wins)
    svals = sorted(vals)
    cands = []
    for q in (0.2, 0.35, 0.5, 0.65, 0.8):
        cands.append(svals[int(q * (len(svals) - 1))])

    def best(w):
        bl, bop, bt = -1.0, None, None
        for thr in cands:
            for op in (">", "<"):
                sel = [w[i] for i, v in enumerate(vals) if (v > thr if op == ">" else v < thr)]
                if len(sel) >= MIN_N:
                    lift = sum(sel) / len(sel) - base
                    if lift > bl:
                        bl, bop, bt = lift, op, thr
        return bl, bop, bt
    obs, op, thr = best(wins)
    if obs < 0:
        return None, None, 0.0, 1.0
    ge = 0
    for _ in range(M):
        sh = wins[:]; random.shuffle(sh)
        if best(sh)[0] >= obs:
            ge += 1
    return op, thr, obs * 100, (ge + 1) / (M + 1)


def _feat(r, key):
    live = r.get("live") or {}
    if key == "vix_aligned":
        fav = (r.get("vix") or {}).get("favored_ndx")
        d = (r.get("decision") or {}).get("direction")
        return 1.0 if (fav and fav == d) else 0.0
    if key == "size_factor":
        return (r.get("decision") or {}).get("size_factor")
    return live.get(key)


def distill():
    rows, g = _load_graded()
    tables = load_tables()
    lines = []
    waits = [r for r in rows if r.get("outcome") == "WAIT"]
    opens = [r for r in rows if r.get("outcome") is None]
    cost = sum((r.get("cost_usd") or 0) for r in rows)
    lines.append(f"_Son güncelleme: {datetime.now():%Y-%m-%d %H:%M} · journal {len(rows)} kayıt "
                 f"({len(g)} grade-deduped, {len(waits)} WAIT, {len(opens)} açık) · ~${cost:.2f} quota_\n")

    if len(g) < MIN_N:
        lines.append(f"⏳ **Yetersiz veri** ({len(g)}/{MIN_N} grade-deduped işlem). Kanıt-kapısı için "
                     "daha çok shadow gerek — bu DOĞRU davranış (az veriden ders çıkarma yok).")
        _write_block(lines); print("\n".join(lines)); return

    # 1) genel sağlık
    wr, n = _wr(g)
    ev = sum(r.get("pnl_r", 0) for r in g) / n
    verdict = "✅ +EV" if ev > 0 else "❌ −EV"
    lines.append(f"**Genel:** WR {wr*100:.0f}% (n={n}) · EV {ev:+.3f}R/işlem → {verdict} "
                 f"(breakeven ~%60 @ RR0.67)")

    # 2) per-sembol kalibrasyon (canlı vs kanıt base)
    lines.append("\n**Kalibrasyon (canlı vs kanıt base):**")
    by = {}
    for r in g:
        by.setdefault((r["symbol"], (r["decision"] or {}).get("direction")), []).append(r)
    for (sym, d), items in sorted(by.items()):
        lwr, ln = _wr(items)
        ev_base = (tables.get(f"{sym}|{d}", {}) or {}).get("gate") or {}
        ref = ev_base.get("oos_wr") or ev_base.get("wr")
        drift = f" (kanıt %{ref})" if ref else ""
        flag = ""
        if ref and ln >= 8 and lwr * 100 < ref - 15:
            flag = " ⚠️ DRIFT — REGIME.md güncelle / güveni düşür"
        lines.append(f"  {sym} {d}: canlı %{lwr*100:.0f} (n={ln}){drift}{flag}")

    # 3) Opus yargısı değer katıyor mu
    lines.append("\n**Opus yargı değeri:**")
    sf = [(r, _feat(r, "size_factor")) for r in g if _feat(r, "size_factor") is not None]
    if len(sf) >= MIN_N:
        med = sorted(x[1] for x in sf)[len(sf) // 2]
        hi = [r for r, v in sf if v > med]; lo = [r for r, v in sf if v <= med]
        hw, hn = _wr(hi); lw, ln2 = _wr(lo)
        verdict = "konviksiyon GERÇEK (büyük→daha çok kazanıyor)" if hw - lw >= 0.08 else \
                  "konviksiyon zayıf sinyal" if abs(hw - lw) < 0.08 else "ters (küçük daha iyi!)"
        lines.append(f"  size>med %{hw*100:.0f}(n={hn}) vs size≤med %{lw*100:.0f}(n={ln2}) → {verdict}")
    gf = [r for r in g if (r.get("live") or {}).get("gate_fired")]
    ngf = [r for r in g if not (r.get("live") or {}).get("gate_fired")]
    if gf and ngf:
        gw, _ = _wr(gf); nw, _ = _wr(ngf)
        lines.append(f"  gate-içi %{gw*100:.0f}(n={len(gf)}) vs kapı-dışı %{nw*100:.0f}(n={len(ngf)}) "
                     f"→ {'kapı-dışı öneriler ZAYIF, gate kal' if nw < gw - 0.08 else 'kapı-dışı tutuyor — özerklik değer katıyor'}")

    # 4) koşullu edge madenciliği (kanıt-kapılı terfi)
    lines.append("\n**Aday dersler (placebo-kapılı):**")
    promoted = []
    for key, label in [("rev_chan", "mean-rev aşırılığı"), ("adx", "ADX"), ("size_factor", "Opus konviksiyon")]:
        pairs = [(_feat(r, key), 1 if r["outcome"] == "WIN" else 0) for r in g if _feat(r, key) is not None]
        if len(pairs) < MIN_N:
            continue
        vals = [p[0] for p in pairs]; wins = [p[1] for p in pairs]
        op, thr, lift_pp, p = _placebo_best_split(vals, wins)
        if op and lift_pp >= MIN_LIFT * 100 and p < 0.05:
            msg = f"✅ {key} {op} {thr:.2g} → +{lift_pp:.0f}pp WR (n≥{MIN_N}, placebo p={p:.3f}) [{label}]"
            promoted.append(msg); lines.append(f"  {msg}")
        elif op and lift_pp >= MIN_LIFT * 100:
            lines.append(f"  ⏳ {key} {op} {thr:.2g} → +{lift_pp:.0f}pp ama placebo p={p:.2f} (≥0.05) — izleniyor")
    if not promoted and "⏳" not in "".join(lines[-4:]):
        lines.append("  (kanıt-kapısını geçen yok — terfi yok)")

    _write_block(lines)
    print("\n".join(lines))
    if promoted:
        print(f"\n→ {len(promoted)} ders LESSONS.md auto-bloğuna terfi etti.")
    candidate_lifecycle(rows)


def candidate_lifecycle(rows):
    """S1 — BİRLEŞİK ADAY YAŞAM DÖNGÜSÜ (kill-protokollü): post_mortem ayırıcılarını her
    distill'de TAZE veriyle yeniden test et. ≥2 ARDIŞIK koşuda FDR-geçen → ✅ KANIT-TEYİTLİ
    (LESSONS'ta karara görünür). Geçmeyen → SİLİNİR (terfiliyse DÜŞÜRÜLÜR) — bayat aday
    birikmez, hurafe LESSONS'ı kirletemez. S2 — terfi tarihli önce/sonra OPEN WR etkisi."""
    import post_mortem as pm
    from datetime import datetime
    hist_p = LESSONS.parent / "candidate_history.json"
    hist = json.loads(hist_p.read_text(encoding="utf-8")) if hist_p.exists() else {}
    results, used = pm.analyze(rows)
    passed = pm.bh_pass(results) if results else set()
    by_key = {r[0]: r for r in results}
    today = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 60)
    print(f"ADAY YAŞAM DÖNGÜSÜ — forensik'li kayıt: {used}, FDR-geçen: {len(passed)}")
    print("=" * 60)
    # 1) geçenler: teyit sayacı (aynı gün mükerrer koşu sayılmaz)
    for k in passed:
        _, nw, nl, mw, ml, p = by_key[k]
        h = hist.get(k) or {"first_seen": today, "confirms": 0}
        if h.get("last_seen") != today:
            h["confirms"] = h.get("confirms", 0) + 1
        h.update(last_seen=today, last_p=p,
                 yon="düşük" if ml < mw else "yüksek",
                 stats=f"W {mw:.2f} vs L {ml:.2f}")
        if h["confirms"] >= 2 and not h.get("promoted"):
            h["promoted"] = today
            print(f"  ✅ TERFİ: {k} ({h['confirms']}× ardışık FDR)")
        hist[k] = h
    # 2) KILL: bu koşuda geçmeyen her aday silinir (terfili olsa bile düşürülür)
    for k in [k for k in hist if k not in passed]:
        note = " (terfiliydi → DÜŞÜRÜLDÜ)" if hist[k].get("promoted") else ""
        print(f"  ✂ SİLİNDİ: {k}{note} — taze veride FDR geçemedi")
        del hist[k]
    hist_p.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")

    conf = [f"{k}: kayıplarda {h['yon']} ({h['stats']}, p={h['last_p']:.3f}, "
            f"{h['confirms']}× teyit, ilk {h['first_seen']})"
            for k, h in sorted(hist.items()) if h.get("promoted")]
    pend = [f"{k}: kayıplarda {h['yon']} ({h['stats']}, p={h['last_p']:.3f}, "
            f"{h['confirms']}/2 teyit)"
            for k, h in sorted(hist.items()) if not h.get("promoted")]
    pm.write_candidates_block(pend, confirmed=conf, title_extra=" · distill-yönetimli")
    print(f"  → LESSONS bloğu: {len(conf)} teyitli, {len(pend)} izlenen (tek kaynak, replace).")

    # S2 — DERS-ETKİ: terfi tarihinden önce/sonra gerçek OPEN WR (düşük güç, dürüst trend)
    opens = [(r["ts"][:10], r["outcome"]) for r in rows
             if str((r.get("decision") or {}).get("action", "")).upper() == "OPEN"
             and r.get("outcome") in ("WIN", "LOSS")]
    for k, h in hist.items():
        pd = h.get("promoted")
        if not pd:
            continue
        bef = [o for d, o in opens if d < pd]
        aft = [o for d, o in opens if d >= pd]
        if len(bef) >= 5 and len(aft) >= 5:
            bw = 100 * sum(1 for o in bef if o == "WIN") / len(bef)
            aw = 100 * sum(1 for o in aft if o == "WIN") / len(aft)
            print(f"  📈 ETKİ [{k}] terfi {pd}: önce WR {bw:.0f}% (n={len(bef)}) → "
                  f"sonra {aw:.0f}% (n={len(aft)})  {'▲' if aw > bw else '▼'}")


def _write_block(lines: list[str]):
    """LESSONS.md'nin AUTO bloğunu güncelle (insan-tohumu dersleri bozmadan)."""
    block = AUTO_START + "\n## 🤖 Auto-dersler (decider geçmişinden, kanıt-kapılı)\n" + "\n".join(lines) + "\n" + AUTO_END
    txt = LESSONS.read_text(encoding="utf-8") if LESSONS.exists() else "# Decider LESSONS\n"
    if AUTO_START in txt and AUTO_END in txt:
        pre = txt[:txt.index(AUTO_START)]; post = txt[txt.index(AUTO_END) + len(AUTO_END):]
        txt = pre + block + post
    else:
        txt = txt.rstrip() + "\n\n" + block + "\n"
    LESSONS.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    distill()
