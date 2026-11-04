"""GÇM sabitleri — PROTOCOL.md §2, §5, §6, §7 ile birebir. Sonuç sonrası değiştirilmez (EK gerekir)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
import os
LIB = os.environ.get("GCM_LIB", "main")          # EK-6: "variants" → parametre varyantı kütüphanesi
RES = HERE / ("results" if LIB == "main" else "results_V")
R = ROOT / "research"

# (sembol, TF) → (dosya, başlangıç kesimi | None). "derive:<tf>" = o TF'den yeniden örnekle.
SOURCES: dict[str, dict[str, tuple[str, str | None]]] = {
    "NDX": {
        "1m": (str(R / "ndx_pattern_motifs/data/bars_1m.parquet"), None),
        "5m": (str(R / "ndx_pattern_motifs/data/bars_5m.parquet"), None),
        "15m": (str(R / "ndx_gate_forge/data/long_15m_utc.parquet"), None),
        "30m": (str(R / "ndx_gate_forge/data/long_30m_utc.parquet"), None),
        "1h": (str(R / "ndx_gate_forge/data/long_1h_utc.parquet"), None),
        "4h": ("derive:1h", None),
        "1d": (str(R / "ndx_buy_lab/data/long_1d.csv"), None),
    },
    "DAX": {
        "1m": (str(HERE / "data/DAX_1m.parquet"), None),             # EK-5
        "5m": ("derive:1m", None),                                    # EK-5
        "15m": (str(R / "ndx_gate_forge/data/dax_15m.parquet"), None),
        "30m": (str(R / "ndx_gate_forge/data/dax_30m.parquet"), None),
        "1h": (str(R / "ndx_gate_forge/data/dax_1h.parquet"), "2020-01-01"),
        "4h": ("derive:1h", None),
        "1d": ("derive:1h", None),
    },
    "XAU": {
        "1m": (str(HERE / "data/XAU_1m.parquet"), None),             # EK-5
        "5m": (str(R / "pinbar_20261010/data/XAUUSD_5m.parquet"), None),
        "15m": (str(R / "pinbar_20261010/data/XAUUSD_15m.parquet"), None),
        "30m": (str(R / "pinbar_20261010/data/XAUUSD_30m.parquet"), None),
        "1h": (str(R / "pinbar_20261010/data/XAUUSD_1h.parquet"), None),
        "4h": ("derive:1h", None),
        "1d": ("derive:1h", None),
    },
    "USOIL": {
        "1m": (str(HERE / "data/USOIL_1m.parquet"), None),           # EK-5
        "5m": (str(R / "pinbar_20261010/data/USOIL_5m.parquet"), None),
        "15m": (str(R / "pinbar_20261010/data/USOIL_15m.parquet"), None),
        "30m": (str(R / "pinbar_20261010/data/USOIL_30m.parquet"), None),
        "1h": (str(R / "pinbar_20261010/data/USOIL_1h.parquet"), None),
        "4h": ("derive:1h", None),
        "1d": ("derive:1h", None),
    },
}
TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
SPREAD = {"NDX": 1.2, "DAX": 1.2, "XAU": 0.25, "USOIL": 0.03}   # fiyat birimi, gidiş-dönüş tek spread

HORIZONS = (1, 2, 4, 8, 16, 32)          # bar
SPLITS = (0.60, 0.20, 0.20)               # KEŞİF / DOĞRULAMA / KASA
GAP_FACTOR = 3                            # boşluk > 3×TF → yeni segment
RECENT_W = 3                              # "yakın tetik" penceresi (bar)
N_MIN = {"1m": 200, "5m": 200, "15m": 200, "30m": 200, "1h": 200, "4h": 100, "1d": 60}
TOP_K = 30
L3_EXPAND = 300
DEDUP_OVERLAP = 0.80
NULL_SHIFTS = 20
NULL_MIN_OFFSET = 0.05
Z_PASS = 1.645
LIFT_MIN = 0.02
SEED = 20261025
