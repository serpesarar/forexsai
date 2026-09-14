"""entry_quality kapısının CANLI gölge karnesi.

Kullanım (kutuda):  python claude_decider/entry_quality_report.py [--gun 14]

Kapı gölge modda (`ENTRY_QUALITY_BLOCK=False`) karara dokunmaz, yalnız her karara
`entry_quality` damgası basar. Bu script o damgayı gerçekleşen sonuçlarla eşleştirip
"kapı açık olsaydı ne olurdu"yu ölçer.

BLOK MODA GEÇME ÖLÇÜTÜ (offline kanıtla aynı çıta):
  · elenen kümede n ≥ 100 VE EV < 0 VE her iki kronolojik yarıda da EV < 0
  · kalan kümenin EV'si eleme öncesine göre YÜKSELMİŞ olmalı
Tutmuyorsa kapı gölgede kalır — offline kanıt canlıda tekrarlanmadan açılmaz.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOURNAL = HERE / "memory" / "journal.jsonl"
BREAKEVEN_WR = 59.9        # RR 0.67 → 1/(1+0.67)


def _ts(rec: dict):
    try:
        return datetime.fromisoformat(str(rec.get("ts")).replace("Z", "+00:00"))
    except Exception:
        return None


def _load(days: int) -> list[dict]:
    if not JOURNAL.exists():
        sys.exit(f"journal yok: {JOURNAL}")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for line in JOURNAL.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        t = _ts(rec)
        if t and t >= cutoff and rec.get("entry_quality"):
            out.append(rec)
    return out


def _samples(rows: list[dict]) -> tuple[list, list]:
    """(gerçek OPEN sonuçları, karşı-olgu sonuçları) — her biri (blocked, win, r)."""
    real, cf = [], []
    for rec in rows:
        q = rec.get("entry_quality") or {}
        blocked = bool(q.get("blocked"))
        if q.get("counterfactual_dir"):
            if rec.get("cf_outcome") in ("WIN", "LOSS"):
                cf.append((blocked, rec["cf_outcome"] == "WIN", rec.get("cf_pnl_r") or 0.0))
        elif rec.get("outcome") in ("WIN", "LOSS"):
            real.append((blocked, rec["outcome"] == "WIN", rec.get("pnl_r") or 0.0))
    return real, cf


def _stat(rows: list) -> tuple[int, float, float]:
    if not rows:
        return 0, 0.0, 0.0
    return (len(rows),
            100 * sum(1 for _, w, _ in rows if w) / len(rows),
            sum(r for _, _, r in rows) / len(rows))


def _report(label: str, rows: list) -> bool:
    n, wr, ev = _stat(rows)
    print(f"\n### {label}  (n={n}, başabaş WR %{BREAKEVEN_WR})")
    if n < 10:
        print("   veri birikiyor — henüz yorum yok")
        return False
    blocked = [x for x in rows if x[0]]
    kept = [x for x in rows if not x[0]]
    for nm, g in (("TÜMÜ (kapısız)", rows), ("ELENECEK", blocked), ("KALACAK", kept)):
        gn, gw, ge = _stat(g)
        if not gn:
            print(f"   {nm:16s} n=0")
            continue
        flag = "✅" if gw >= BREAKEVEN_WR else "⛔"
        print(f"   {nm:16s} n={gn:4d} WR=%{gw:5.1f} EV={ge:+.3f}R {flag}")
    if len(blocked) < 10:
        print("   → elenen küme henüz küçük, karar için erken")
        return False
    half = len(blocked) // 2
    _, _, e1 = _stat(blocked[:half])
    _, _, e2 = _stat(blocked[half:])
    _, _, ev_all = _stat(rows)
    _, _, ev_kept = _stat(kept)
    print(f"   elenen yarılar: EV1={e1:+.3f} EV2={e2:+.3f} | kalan EV {ev_all:+.3f} → {ev_kept:+.3f}")
    ok = (len(blocked) >= 100 and _stat(blocked)[2] < 0 and e1 < 0 and e2 < 0
          and ev_kept > ev_all)
    print("   VERDİKT: " + ("✅ blok moda geçme ölçütleri SAĞLANDI"
                            if ok else "⏳ ölçütler henüz sağlanmadı — gölgede kal"))
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description="entry_quality canlı gölge karnesi")
    ap.add_argument("--gun", type=int, default=21, help="kaç günlük pencere (varsayılan 21)")
    a = ap.parse_args()
    rows = _load(a.gun)
    print(f"entry_quality damgalı kayıt: {len(rows)} (son {a.gun} gün)")
    if not rows:
        print("Kapı yeni bağlanmış olabilir — decider'ın bir sonraki turunu bekleyin.")
        return
    real, cf = _samples(rows)
    ok_real = _report("GERÇEK OPEN kararları", real)
    ok_cf = _report("KARŞI-OLGU (WAIT'lerin 'açsaydı'sı)", cf)
    print("\n" + "=" * 70)
    print("ÖZET: " + ("her iki sette de ölçütler sağlandı → decider_config.py'ye "
                      "ENTRY_QUALITY_BLOCK=True yazılabilir"
                      if (ok_real and ok_cf) else
                      "gölgede kalmalı (offline kanıt canlıda henüz tekrarlanmadı)"))


if __name__ == "__main__":
    main()
