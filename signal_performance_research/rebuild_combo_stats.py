"""Task 20 — Rebuild meta_combination_stats on HONEST 1m outcomes.

Runs the (corrected-aware) CombinatorialAuditor end-to-end:
  fetch_signal_matrix  -> attach_corrections (latest replay batch) -> honest is_win
  mine_combination_rules
  sync_combination_stats -> writes meta_combination_stats (select-then-update/insert,
                            NOT the broken .upsert wrapper)

Non-destructive to prediction_logs; only refreshes the derived stats table that
feeds the Meta-Intelligence Engine combos. Prints a before/after diff so the
honest rebuild is auditable.
"""
import os, sys, asyncio

for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from services.combinatorial_auditor import CombinatorialAuditor  # noqa: E402
from utils.safe_supabase import safe_get_data  # noqa: E402


async def main():
    aud = CombinatorialAuditor()
    if not aud.client:
        raise SystemExit("Supabase client unavailable — check .env")

    # Snapshot BEFORE
    before = safe_get_data(
        aud.client.table("meta_combination_stats")
        .select("combo_key,symbol,regime,total_signals,wins,win_rate")
        .execute()
    ) or []
    before_map = {(r["combo_key"], r["symbol"], r["regime"]): r for r in before}
    print(f"[before] meta_combination_stats rows: {len(before)}")

    print("[fetch] building corrected-aware signal matrix (days=45, limit=5000)...")
    df = await aud.fetch_signal_matrix(days=45)
    if df is None or df.empty:
        raise SystemExit("No signal matrix — nothing to mine.")
    print(f"[fetch] matrix rows: {len(df)}  symbols: {sorted(df['symbol'].unique())}")
    print(f"[fetch] overall honest win_rate: {df['is_win'].mean():.4f}")

    print("[mine] mining combination rules...")
    stats = aud.mine_combination_rules(df)
    print(f"[mine] mined {len(stats)} combo/symbol/regime rules")

    print("[sync] writing meta_combination_stats...")
    await aud.sync_combination_stats(stats)

    # Snapshot AFTER
    after = safe_get_data(
        aud.client.table("meta_combination_stats")
        .select("combo_key,symbol,regime,total_signals,wins,win_rate")
        .execute()
    ) or []
    print(f"[after] meta_combination_stats rows: {len(after)}")

    # Diff: show notable win_rate changes (honest vs prior)
    print("\n=== win_rate changes (|Δ| >= 0.03), top 30 by |Δ| ===")
    diffs = []
    for s in stats:
        k = (s["combo_key"], s["symbol"], s["regime"])
        old = before_map.get(k)
        old_wr = float(old["win_rate"]) if old else None
        new_wr = s["win_rate"]
        if old_wr is not None and abs(new_wr - old_wr) >= 0.03:
            diffs.append((abs(new_wr - old_wr), s["symbol"], s["combo_key"],
                          s["regime"], old_wr, new_wr, s["total_signals"]))
    diffs.sort(reverse=True)
    for d in diffs[:30]:
        _, sym, ck, reg, owr, nwr, n = d
        print(f"  {sym:12s} {ck:28s} {reg:16s} {owr:.3f} -> {nwr:.3f}  (n={n})")
    print(f"\n[done] {len(diffs)} combos shifted >=3pp under honest 1m outcomes")


if __name__ == "__main__":
    asyncio.run(main())
