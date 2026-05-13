"""Manual smoke demo — not a pytest. Run with:
    PYTHONPATH=backend .venv/bin/python backend/tests/_psi_smoke_demo.py
Shows how the PSI overlay would affect meta-engine confidence under
different simulated PSI regimes. Safe to delete; kept here because it's
handy when tuning the bias matrix."""
from dataclasses import fields

from services import pandemic_sensitivity_service as psi
from services.meta_analysis_engine import MetaSignal


def main() -> None:
    field_names = {f.name for f in fields(MetaSignal)}
    for need in ("raw_confidence", "psi_adjustment", "psi_context"):
        assert need in field_names, f"missing MetaSignal field: {need}"
    print("OK: MetaSignal has raw_confidence, psi_adjustment, psi_context fields")

    scenarios = [
        ("CRITICAL", 88.0),
        ("HIGH_RISK", 70.0),
        ("WARNING", 50.0),
        ("ELEVATED", 30.0),
        ("NORMAL", 13.2),
    ]
    for label, score in scenarios:
        psi._last_snapshot = {"psi_score": score, "risk_level": label, "baskets": []}
        print(f"\n=== Simulated {label} PSI ({score}) ===")
        for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"):
            for direction in ("BUY", "SELL"):
                adj = psi.compute_meta_adjustment(sym, direction)
                mark = "*" if adj["applied"] else " "
                print(
                    f" {mark} {sym:14s} {direction:4s}  "
                    f"delta={adj['adjustment']:+6.2f}  applied={adj['applied']}"
                )


if __name__ == "__main__":
    main()
