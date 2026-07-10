"""
refresh_evidence.py — base-rate'leri YAŞANMIŞ deneyimle güncelle (Bayesyen blend).
=============================================================================
"Veteran hafızası" (evidence_tables.json) bir kez ESKİ araştırmadan kuruldu (prod log ~Haziran).
Piyasa değişiyor; kalibrasyon.py base'lerin şiştiğini gösterebiliyor. Bu modül decider'ın
KENDİ journal'ından (aynı feature uzayı: rev_chan/rev_vwap/adx/session × cf_outcome) canlı
WR'lar çıkarır, araştırma base'iyle BLEND eder → tablolar yaşayan gerçeğe yaklaşır.

BLEND (Bayesyen): araştırma base = prior (PRIOR_PSEUDO ~gözlem değerinde), canlı journal =
kanıt. posterior = (prior_wins + live_wins) / (PRIOR_PSEUDO + live_n). Canlı veri biriktikçe
BASKINLAŞIR; az veride araştırma korunur. Yalnız live_n ≥ MIN_LIVE hücreler güncellenir.

GÜVENLİK: VARSAYILAN DRY-RUN (sadece raporlar). `--apply` ile yazar (önce yedek alır).
NOT: 'base' (koşulsuz) güncellenmez — journal yalnız 'ilginç' kurulumları içerir (koşullu).
Win-tanımı: canlı cf (1×/1.5×ATR) — decider'ın gerçekte trade ettiği tanım (tutarlı).
"""
from __future__ import annotations
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL  # noqa: E402
from evidence import TABLES, REV_EDGES, ADX_EDGES, _bucket, _session  # noqa: E402

PRIOR_PSEUDO = 25     # araştırma base'i ~bu kadar gözleme bedel (canlı n bunu geçince baskın)
MIN_LIVE = 12         # bir hücreyi güncellemek için min canlı örnek
MIN_DIVERGE = 6       # rapor: araştırma↔canlı bu kadar pp ayrışan hücreler


def _load_journal():
    if not JOURNAL_JSONL.exists():
        return []
    from decide import load_journal
    return load_journal(clean=True)   # donuk-kopya karantinası (frozen kayıtlar base-rate'i zehirlemesin)


def collect_live(rows) -> dict:
    """Journal → {sym|dir: {gate:[w..], rev_chan:{bucket:[w..]}, rev_vwap, adx, session}}."""
    live = defaultdict(lambda: {"gate": [], "rev_chan": defaultdict(list), "rev_vwap": defaultdict(list),
                                "adx": defaultdict(list), "session": defaultdict(list)})
    for e in rows:
        cf = e.get("counterfactual") or {}
        if e.get("cf_outcome") not in ("WIN", "LOSS"):
            continue
        lf = cf.get("live") or (e.get("dirs_live") or {}).get(cf.get("dir")) or {}
        d = cf.get("dir")
        if not d:
            continue
        w = 1 if e["cf_outcome"] == "WIN" else 0
        key = f"{e['symbol']}|{d}"
        cell = live[key]
        if lf.get("gate_fired"):
            cell["gate"].append(w)
        for fld, edges in (("rev_chan", REV_EDGES), ("rev_vwap", REV_EDGES), ("adx", ADX_EDGES)):
            v = lf.get(fld)
            if v is not None:
                b = _bucket(v, edges)
                if b:
                    cell[fld][b].append(w)
        if lf.get("session"):
            cell["session"][lf["session"]].append(w)
    return live


def _blend(research_wr, live_wins, live_n):
    """Bayesyen posterior WR (%). research_wr None ise saf canlı."""
    rw = (research_wr / 100.0) if research_wr is not None else 0.5
    a = PRIOR_PSEUDO * rw
    post = (a + live_wins) / (PRIOR_PSEUDO + live_n)
    return round(post * 100)


def refresh(apply: bool = False):
    rows = _load_journal()
    tables = json.loads(TABLES.read_text(encoding="utf-8")) if TABLES.exists() else {}
    live = collect_live(rows)
    graded = sum(1 for e in rows if e.get("cf_outcome") in ("WIN", "LOSS"))

    print("=" * 70)
    print("EVIDENCE TAZELEME — base-rate'leri yaşanmış deneyimle güncelle")
    print("=" * 70)
    print(f"Journal: {len(rows)} | grade'li: {graded} | PRIOR_PSEUDO={PRIOR_PSEUDO} MIN_LIVE={MIN_LIVE}\n")

    changes = []        # (cellkey, sub, bucket, research, livewr, live_n, blended)
    new_tables = json.loads(json.dumps(tables))   # derin kopya

    for key, cell in sorted(live.items()):
        t = new_tables.get(key)
        if t is None:
            continue
        # gate hücresi
        for sub in ("gate", "rev_chan", "rev_vwap", "adx", "session"):
            if sub == "gate":
                ws = cell["gate"]
                if len(ws) >= MIN_LIVE:
                    rwr = (t.get("gate") or {}).get("oos_wr") or (t.get("gate") or {}).get("wr")
                    lwr = round(100 * sum(ws) / len(ws)); bl = _blend(rwr, sum(ws), len(ws))
                    if rwr is None or abs(lwr - rwr) >= MIN_DIVERGE:
                        changes.append((key, "gate", "-", rwr, lwr, len(ws), bl))
                    t.setdefault("gate", {})["wr"] = bl; t["gate"]["live_n"] = len(ws)
            else:
                for b, ws in cell[sub].items():
                    if len(ws) < MIN_LIVE:
                        continue
                    rcell = (t.get(sub) or {}).get(b) or {}
                    rwr = rcell.get("oos_wr") or rcell.get("wr")
                    lwr = round(100 * sum(ws) / len(ws)); bl = _blend(rwr, sum(ws), len(ws))
                    if rwr is None or abs(lwr - rwr) >= MIN_DIVERGE:
                        changes.append((key, sub, b, rwr, lwr, len(ws), bl))
                    t.setdefault(sub, {})[b] = {**rcell, "wr": bl, "live_n": len(ws)}

    # 2 — CERRAHİ YÜKSEK-İDDİA KAPAĞI (temiz kalibrasyon 2026-07-10): şişiklik DAR bölgede —
    # yalnız ≥%80 iddialı hücreler canlıda ~%60-61 verdi (−25/−32pp); 50-80 bandı kalibre.
    # Yeterli canlı teyidi (live_n≥20 ve hâlâ ≥80) olmayan her ≥80 iddia 72'ye kapaklanır.
    # oos_wr DAHİL — tüketiciler (evidence_pack/calibration) oos_wr'ı tercih eder, bypass olmasın.
    CAP_AT, CAP_MIN_LIVE, CAP_FROM = 72, 20, 80
    capped = 0

    def _cap_cell(c):
        nonlocal capped
        if not isinstance(c, dict):
            return
        strong_live = (c.get("live_n") or 0) >= CAP_MIN_LIVE and (c.get("wr") or 0) >= CAP_FROM
        for fld in ("wr", "oos_wr"):
            v = c.get(fld)
            if isinstance(v, (int, float)) and v >= CAP_FROM and not strong_live:
                c[fld] = CAP_AT
                c["capped"] = True
                capped += 1

    for _k, _t in new_tables.items():
        for _sub, _val in _t.items():
            if _sub in ("gate", "base"):
                _cap_cell(_val)
            elif isinstance(_val, dict):
                for _b, _c in _val.items():
                    _cap_cell(_c)
    if capped:
        print(f"🔒 Cerrahi kapak: canlı-teyitsiz ≥{CAP_FROM}% iddialı {capped} alan {CAP_AT}%'e indirildi.")

    if not changes and not capped:
        upd = sum(1 for k, c in live.items() if len(c["gate"]) >= MIN_LIVE)
        print(f"Güncellenecek belirgin hücre YOK (live_n≥{MIN_LIVE} & ≥{MIN_DIVERGE}pp sapan).")
        print(f"  ({graded} grade'li örnek henüz hücre başına az; veri biriktikçe dolacak.)")
        return

    print(f"DEĞİŞECEK HÜCRELER ({len(changes)}) — araştırma → canlı → blend:")
    print(f"  {'sembol|yön':<18} {'hücre':<9}{'bucket':<8}{'arş':>5}{'canlı':>7}{'n':>5}{'blend':>7}")
    for key, sub, b, rwr, lwr, n, bl in sorted(changes, key=lambda x: -abs((x[4] or 0) - (x[3] or x[4] or 0))):
        rs = f"{rwr}%" if rwr is not None else "yok"
        print(f"  {key:<18} {sub:<9}{b:<8}{rs:>5}{lwr:>6}%{n:>5}{bl:>6}%")

    if apply:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        backup = TABLES.with_name(f"evidence_tables.backup_{ts}.json")
        shutil.copy(TABLES, backup)
        TABLES.write_text(json.dumps(new_tables, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n✅ YAZILDI: {TABLES.name}  (yedek: {backup.name})")
        print("   Decider sonraki başlangıçta yeni base-rate'leri okuyacak.")
    else:
        print(f"\n[DRY-RUN] Yazılmadı. Uygulamak için: python refresh_evidence.py --apply")
        print("   (önce yedek alır; geri almak için yedeği evidence_tables.json'a kopyala)")


if __name__ == "__main__":
    refresh(apply="--apply" in sys.argv)
