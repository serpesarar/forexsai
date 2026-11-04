"""Ortak veri seçimi — mum eşleştirme fizibilite ölçümleri (2026-10-12).

Yalnız EŞLEŞME SAYIMI yapılır; hiçbir betik sonuçlara (gelecek fiyat) bakmaz → ön-kayıt temiz kalır.
Kaynaklar (hepsi UTC, bar başlangıcı damgalı; ayrıntı: docs/MUM_ESLESTIRME_ALGORITMASI.md §5):
  NDX 5m/15m  : research/ndx_pattern_motifs/data   (Dukascopy 2025 + Pepperstone 2026)
  NDX 30m/1h  : research/ndx_gate_forge/data       (Pepperstone, broker saatinden UTC'ye çevrilmiş)
  DAX         : research/ndx_gate_forge/data
  XAU / OIL   : research/pinbar_20261010/data      (candle_cache; src=='yahoo' satırları ATILIR, E21)
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PIP = {"NDX": 1.0, "DAX": 1.0, "XAU": 0.1, "OIL": 0.01}   # meta_analysis_engine ile aynı
YEARS = 5


def sources(root: Path = ROOT) -> dict:
    gf, pm, pb = root / "research/ndx_gate_forge/data", root / "research/ndx_pattern_motifs/data", root / "research/pinbar_20261010/data"
    src = {
        ("NDX", "5m"): pm / "bars_5m.parquet", ("NDX", "15m"): pm / "bars_15m.parquet",
        ("NDX", "30m"): gf / "long_30m_utc.parquet", ("NDX", "1h"): gf / "long_1h_utc.parquet",
        ("DAX", "15m"): gf / "dax_15m.parquet", ("DAX", "30m"): gf / "dax_30m.parquet", ("DAX", "1h"): gf / "dax_1h.parquet",
        ("XAU", "5m"): pb / "XAUUSD_5m.parquet", ("XAU", "15m"): pb / "XAUUSD_15m.parquet",
        ("XAU", "30m"): pb / "XAUUSD_30m.parquet", ("XAU", "1h"): pb / "XAUUSD_1h.parquet",
        ("OIL", "5m"): pb / "USOIL_5m.parquet", ("OIL", "15m"): pb / "USOIL_15m.parquet",
        ("OIL", "30m"): pb / "USOIL_30m.parquet", ("OIL", "1h"): pb / "USOIL_1h.parquet",
    }
    only = os.environ.get("FEAS_ONLY")            # duman testi: FEAS_ONLY="NDX:15m,XAU:1h"
    if only:
        keep = {tuple(x.split(":")) for x in only.split(",")}
        src = {k: v for k, v in src.items() if k in keep}
    return src


def load(path: Path) -> pd.DataFrame:
    """Broker satırları, zamana göre sıralı, son YEARS yıl."""
    d = pd.read_parquet(path)
    if "src" in d.columns:
        d = d[d.src == "broker"]
    d = d.sort_values("ts").reset_index(drop=True)
    return d[d.ts >= d.ts.max() - pd.Timedelta(days=int(365.25 * YEARS))].reset_index(drop=True)


def nq(default: int) -> int:
    return int(os.environ.get("FEAS_NQ", default))
