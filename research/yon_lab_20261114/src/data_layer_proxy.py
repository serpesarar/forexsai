"""NOM data_layer kapalı-saat maskesi (R1) — taşıma barları için aynı kural."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'nom_20261113/src'))
from data_layer import closed_mask as closed  # noqa: E402,F401
