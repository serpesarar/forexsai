"""
backfill_exits.py — geçmiş kararları YENİ çıkış politika setiyle yeniden grade et.
=============================================================================
NEDEN: exits.py'a 2026-07-27'de be30_runner (ölçülmüş NDX BUY yönetimi) + XAU sembol-özel
politikalar eklendi, ama `exit_grades` yalnız YENİ kayıtlar için o setle doluyor; eski
kayıtlar 6-politikalık eski setle grade edilmişti. Ayrıca `exit_grades_real` (GERÇEK OPEN
trade'lerin çıkış kıyası) hiç geriye dönük hesaplanmamıştı.

Çıkış grade'i DETERMİNİSTİK yeniden oynatmadır (aynı barlar → aynı sonuç), yani haftalarca
veri beklemeye gerek yok: MT5'ten geniş bar penceresi çekilip tüm geçmiş yeniden grade
edilebilir. SIZINTI YOK — her kayıt yalnız KENDİ entry_bar_time'ından SONRAKİ barlarla
grade edilir (outcomes.resolve_path ile aynı kural).

KULLANIM (kutuda, MT5 açıkken):
    python backfill_exits.py            # dry-run: kaç kayıt, kaç politika, örnek
    python backfill_exits.py --apply    # yaz (önce .backup_<ts> alır)

outcome/pnl_r'a DOKUNMAZ — yalnız exit_grades / exit_grades_real alanlarını doldurur.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import decider_config as config  # noqa: E402
import exits  # noqa: E402
from decide import JOURNAL_JSONL, journal_lock  # noqa: E402
from outcomes import MAX_HORIZON_H  # noqa: E402

BARS_N = 20000            # ~69 gün 5m — tüm canlı journal dönemini kapsar
MAX_FWD_BARS = int(MAX_HORIZON_H * 12)   # 48h × 12 bar/saat


def _load_bars() -> dict:
    """Sembol başına geniş 5m bar penceresi (MT5)."""
    import MetaTrader5 as mt5
    if not mt5.initialize(config.PEPPERSTONE_TERMINAL_PATH):
        print("❌ MT5 bağlanamadı:", mt5.last_error())
        return {}
    out = {}
    for fx_sym, cands in config.SYMBOL_CANDIDATES.items():
        real = next((s for s in cands if mt5.symbol_info(s) is not None), None)
        if not real:
            continue
        mt5.symbol_select(real, True)
        rates = mt5.copy_rates_from_pos(real, mt5.TIMEFRAME_M5, 0, BARS_N)
        if rates is None or len(rates) == 0:
            print(f"  {fx_sym}: bar yok, atlandı")
            continue
        out[fx_sym] = [{"high": float(r["high"]), "low": float(r["low"]),
                        "close": float(r["close"]), "time": int(r["time"])} for r in rates]
        b = out[fx_sym]
        print(f"  {fx_sym:14s} {len(b)} bar | "
              f"{datetime.fromtimestamp(b[0]['time'], timezone.utc):%Y-%m-%d} → "
              f"{datetime.fromtimestamp(b[-1]['time'], timezone.utc):%Y-%m-%d}")
    return out


def _fwd(bars: list, since: float) -> list:
    """entry_bar_time'dan SONRAKİ barlar, 48h ufkuyla sınırlı (grading ile aynı kural)."""
    i = 0
    lo, hi = 0, len(bars)
    while lo < hi:                                   # ikili arama (20k bar × 2.5k kayıt)
        mid = (lo + hi) // 2
        if bars[mid]["time"] <= since:
            lo = mid + 1
        else:
            hi = mid
    i = lo
    return bars[i:i + MAX_FWD_BARS]


def backfill(apply: bool = False) -> None:
    if not JOURNAL_JSONL.exists():
        print("journal yok."); return
    print("MT5'ten bar penceresi çekiliyor...")
    bars_by = _load_bars()
    if not bars_by:
        return
    rows = [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    now = datetime.now(timezone.utc).timestamp()
    n_cf = n_real = n_skip = 0
    pol_counts: dict = {}
    for e in rows:
        sym = e.get("symbol")
        bars = bars_by.get(sym)
        if not bars:
            n_skip += 1
            continue
        mature = now - datetime.fromisoformat(e["ts"]).timestamp() > MAX_HORIZON_H * 3600
        if not mature:                                # olgunlaşmamış → tam pencere yok
            n_skip += 1
            continue
        # 1) karşı-olgu grade'i (eski set → yeni set)
        cf = e.get("counterfactual")
        if cf and cf.get("atr") and cf.get("entry_bar_time"):
            fwd = _fwd(bars, cf["entry_bar_time"])
            if fwd:
                eg = exits.grade_all(cf["dir"], cf["entry_price"], cf["atr"], fwd, symbol=sym)
                if eg:
                    e["exit_grades"] = eg; n_cf += 1
                    for p in eg:
                        pol_counts[p] = pol_counts.get(p, 0) + 1
        # 2) GERÇEK OPEN trade grade'i
        tr = e.get("trade")
        dec = e.get("decision") or {}
        if tr and tr.get("atr") and tr.get("entry_bar_time") and \
                str(dec.get("action", "")).upper() == "OPEN" and dec.get("direction"):
            fwd = _fwd(bars, tr["entry_bar_time"])
            if fwd:
                eg = exits.grade_all(dec["direction"], tr["entry_price"], tr["atr"], fwd, symbol=sym)
                if eg:
                    e["exit_grades_real"] = eg; n_real += 1
                    pol = tr.get("exit_policy")
                    if pol and pol in eg:
                        e["policy_pnl_atr"] = eg[pol]
                        e["policy_pnl_r"] = round(eg[pol] / 1.5, 3)
    print(f"\nkarşı-olgu grade: {n_cf} | gerçek-OPEN grade: {n_real} | atlanan: {n_skip}")
    print("politika kapsamı:", json.dumps(pol_counts, ensure_ascii=False))
    if not apply:
        print("\n(DRY-RUN — yazmak için --apply)")
        return
    bak = JOURNAL_JSONL.with_suffix(f".backup_{datetime.now():%Y%m%d_%H%M}.jsonl")
    shutil.copy2(JOURNAL_JSONL, bak)
    with journal_lock(timeout=30.0):
        with open(JOURNAL_JSONL, "w", encoding="utf-8") as f:
            for e in rows:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"✅ YAZILDI (yedek: {bak.name})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    backfill(ap.parse_args().apply)
