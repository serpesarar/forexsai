"""Task 21 — Verify the 3 panels render HONEST (1m GT-corrected) data.

Exercises each corrected-aware backend code path directly (no HTTP, so no prod
lifecycle side effects):
  1. Signals / accuracy-by-model  -> routers.learning.get_accuracy_by_model
  2. Permutation Analysis         -> services.permutation_analysis_service.analyze_model_permutations
  3. Meta Signal Analysis         -> reads meta_combination_stats (rebuilt in Task 20)

Pass criteria: each path runs without exception, attaches corrections, and the
per-model win rates land in the honest band (well below the inflated 5m numbers,
consistent with the leak-audited ground-truth memory).
"""
import os, sys, asyncio

for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))


async def main():
    from database.supabase_client import get_supabase_client
    from utils.safe_supabase import safe_get_data
    client = get_supabase_client()

    print("=" * 64)
    print("PANEL 1 — Signals / accuracy-by-model (honest)")
    print("=" * 64)
    from routers.learning import get_accuracy_by_model
    res = await get_accuracy_by_model(symbol=None, days=30)
    models = res.get("models") or res.get("data") or res
    if isinstance(models, dict) and "models" in models:
        models = models["models"]
    rows = models if isinstance(models, list) else (
        res.get("by_model") or res.get("accuracy") or [])
    if not rows and isinstance(res, dict):
        # dump top-level keys for shape discovery
        print("  keys:", list(res.keys()))
        rows = []
    for m in rows:
        name = m.get("model") or m.get("model_type") or m.get("name")
        wr = m.get("win_rate") or m.get("accuracy") or m.get("target_hit_rate")
        tot = m.get("total") or m.get("total_signals") or m.get("resolved")
        print(f"  {str(name):20s} wr={wr}  n={tot}")

    print()
    print("=" * 64)
    print("PANEL 2 — Permutation Analysis (honest)")
    print("=" * 64)
    from services.permutation_analysis_service import analyze_model_permutations
    import inspect
    sig = inspect.signature(analyze_model_permutations)
    print("  signature:", sig)
    try:
        perm = await analyze_model_permutations(symbol="USOIL.FOREX", days=30)
    except TypeError:
        perm = await analyze_model_permutations("USOIL.FOREX")
    perms = perm.get("permutations") or perm.get("data") or perm.get("combos") or []
    if isinstance(perm, dict) and not perms:
        print("  keys:", list(perm.keys()))
    for p in (perms[:12] if isinstance(perms, list) else []):
        lbl = p.get("combo") or p.get("label") or p.get("models")
        wr = p.get("win_rate") or p.get("accuracy")
        n = p.get("total_signals") or p.get("total") or p.get("n")
        print(f"  {str(lbl):34s} wr={wr}  n={n}")

    print()
    print("=" * 64)
    print("PANEL 3 — Meta Signal Analysis source (meta_combination_stats)")
    print("=" * 64)
    stats = safe_get_data(
        client.table("meta_combination_stats")
        .select("symbol,combo_key,regime,win_rate,wins,total_signals,last_updated")
        .order("last_updated", desc=True)
        .limit(20)
        .execute()
    ) or []
    fresh = sum(1 for s in stats if str(s.get("last_updated", "")).startswith("2026-05-30"))
    print(f"  rows shown: {len(stats)}  refreshed-today: {fresh}")
    for s in stats[:12]:
        print(f"  {s['symbol']:12s} {s['combo_key']:30s} {s['regime']:16s} "
              f"wr={s['win_rate']}  n={s['total_signals']}")

    print("\n[done] all 3 panel paths executed without exception")


if __name__ == "__main__":
    asyncio.run(main())
