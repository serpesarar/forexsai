"""NASDAQ mum kaynaklarının yükleyicileri — hepsi aynı biçime getirilir.

Ortak biçim (DataFrame):
    t     int64   bar AÇILIŞI, gerçek UTC epoch (saniye)
    open/high/low/close  float64
    vol   float64  tik hacmi (yoksa NaN)
    spr   float64  fiyat biriminde spread (yoksa NaN)

İki bağımsız besleme var ve KARIŞTIRILMAZ (seviye farkı IQR ~29 puan, FAZ_0 §2):
    DUKA  Dukascopy USATECHIDXUSD BID 1m (UTC)
    MT5   Pepperstone NAS100 (kutu terminali). Sunucu saati = New York + 7 sa
          (yeni deneme/broker_time.py); csv.gz dosyalarındaki `t` sunucu duvar saatidir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
NY = "America/New_York"
SERVER_MINUS_NY_H = 7
MT5_POINT = 0.1  # NAS100 point (data/mt5/meta.json)
COLS = ["t", "open", "high", "low", "close", "vol", "spr"]

DUKA_1M = ROOT / "research/nom_20261113/data/ndx_1m_v3_duka.parquet"
MT5_DIR_A = ROOT / "research/c1_turev_20261105/data/mt5"
MT5_DIR_B = ROOT / "research/yon_lab_20261114/data/mt5"
MT5_UTC_CSV = [
    ROOT / "nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv",
    ROOT / "islem_paketi_2026-08-27/NASDAQ/1m_veri/NAS100_1m_MT5_2026-08-13_2026-08-27.csv",
]
CANDLE_CACHE_1M = [
    ROOT / "nasdaq_1m_candle_cache_2026-02-10_2026-08-29/nasdaq_1m_candle_cache_TAM_2026-02-10_2026-08-29.csv",
    ROOT / "backend/data/nom_cache/ndx_1m.parquet",
]


def server_to_utc(t_server: np.ndarray) -> np.ndarray:
    """MT5 sunucu duvar saati epoch'u → gerçek UTC epoch.

    Sunucu = NY + 7 sa. NY duvar saatine indirip America/New_York ile yerelleştiririz;
    DST geçişi Pazar 02:00 NY'de, piyasa kapalıyken olur → belirsiz/olmayan saat beklenmez.
    """
    wall_ny = pd.to_datetime(t_server, unit="s") - pd.Timedelta(hours=SERVER_MINUS_NY_H)
    loc = wall_ny.tz_localize(NY, ambiguous="NaT", nonexistent="NaT")
    if loc.isna().any():
        raise ValueError(f"{int(loc.isna().sum())} bar DST geçiş saatine düştü — beklenmiyordu")
    return (loc.tz_convert("UTC").asi8 // 10**9).astype(np.int64)


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    for c in COLS:
        if c not in df:
            df[c] = np.nan
    df = df[COLS].copy()
    df["t"] = df["t"].astype(np.int64)
    for c in COLS[1:]:
        df[c] = df[c].astype(np.float64)
    return df.sort_values("t").reset_index(drop=True)


DUKA_RAW_BI5 = ROOT / "research/nom_20261113/data/duka_m1"
DUKA_V1 = ROOT / "research/nom_20261113/data/ndx_1m_v1.parquet"


def _duka_tail_after(t_last: int) -> pd.DataFrame:
    """Ana dosyanın bitişinden sonraki Dukascopy barları — ham bi5'ten, ana dosyayla AYNI temizlik kurallarıyla
    (nom_20261113/src/data_layer.load_bi5_range: R1 kapalı saat, R2 OHLC, R3 düz sıfır-hacim dolgu).
    İkinci kopya ndx_1m_v1 ile birebir aynı olması dayatılır. Spread modeli bu barlarda yok (spr = NaN)."""
    import datetime as _dt
    import importlib
    sys.path.insert(0, str(ROOT / "research/nom_20261113/src"))
    DL = importlib.import_module("data_layer")
    start = _dt.datetime.fromtimestamp(t_last, _dt.timezone.utc).date()
    b, _ = DL.load_bi5_range(DUKA_RAW_BI5, start, _dt.date.today(), "duka_bi5_ext")
    b = b[b["t"] > t_last][["t", "open", "high", "low", "close"]].reset_index(drop=True)
    v1 = pd.read_parquet(DUKA_V1, columns=["t", "open", "high", "low", "close"])
    v1 = v1[v1["t"] > t_last].reset_index(drop=True)
    if len(b) != len(v1) or not np.allclose(b.to_numpy(), v1.to_numpy(), atol=1e-9, rtol=0):
        raise AssertionError("Dukascopy ek günleri: ham bi5 ile ndx_1m_v1 ayrışıyor")
    return b


DUKA_M1_EXPORT = Path.home() / "Downloads/USATECHIDXUSD_M1.csv"   # Dukascopy M1 dışa aktarımı (3 ondalık, UTC)
DUKA_M30_EXPORT = Path.home() / "Downloads/USATECHIDXUSD30.csv"   # Dukascopy M30 dışa aktarımı (2 ondalık, UTC, 2016-03 →)
EXPORT_TOL = 1e-6


def _read_export(path: Path) -> pd.DataFrame:
    sys.path.insert(0, str(Path(__file__).parent))
    import dis_okuyucu as R
    x = R.read_ohlc(path)
    return _finish(pd.DataFrame({"t": x["wall"].astype("int64") // 10**9, "open": x["open"], "high": x["high"],
                                 "low": x["low"], "close": x["close"]}))


def load_duka_1m(extend: bool = True, export: bool = True) -> pd.DataFrame:
    """Ana Dukascopy 1 dk + ham bi5 kuyruğu + M1 dışa aktarımının ana dosyada OLMAYAN dakikaları.

    M1 dışa aktarımı ortak dakikalarda ana dosyayla birebir olmak zorunda (değilse durur); 2025-06 → 10 arasında
    tik indirmesindeki saat boşluklarına düşen 16.772 gerçek dakikayı ekler.
    """
    d = _finish(pd.read_parquet(DUKA_1M)[["t", "open", "high", "low", "close", "spr"]].copy())
    if extend:
        tail = _duka_tail_after(int(d["t"].iloc[-1]))
        d = _finish(pd.concat([d, tail], ignore_index=True)) if len(tail) else d
    if export and DUKA_M1_EXPORT.exists():
        e = _read_export(DUKA_M1_EXPORT)
        m = e.merge(d, on="t", suffixes=("_e", "_d"))
        diff = np.abs(m[["open_e", "high_e", "low_e", "close_e"]].to_numpy() - m[["open_d", "high_d", "low_d", "close_d"]].to_numpy())
        if len(m) == 0 or float(diff.max()) > EXPORT_TOL:
            raise AssertionError(f"Dukascopy M1 dışa aktarımı ana dosyayla ayrışıyor (max {diff.max() if len(m) else 'çakışma yok'})")
        d = _finish(pd.concat([d, e[~e["t"].isin(d["t"])]], ignore_index=True))
    if export and DUKA_2025_BI5.exists():
        d = _union_checked(d, _bi5_folder(DUKA_2025_BI5), "Dukascopy 2025 günlük 1 dk (yeniden indirilen)",
                           allow_superset=True)
    return d


UNION_LOG: dict[str, dict] = {}
REPLACED: list[str] = []          # resmi mumla değiştirilen dakikalar (UTC)
OFFICIAL_MAX_SHARE = 0.001        # resmi mum ↔ tik kurgusu ayrışması ortak dakikaların ‰1'ini aşamaz


DUKA_2025_BI5 = Path(__file__).resolve().parents[1] / "out/duka_m1_2025"  # s11 (kullanıcı onayıyla indirildi)


def _bi5_folder(folder: Path) -> pd.DataFrame:
    """Klasördeki YYYYMMDD_BID.bi5 günleri — ana dosyayla AYNI temizlik (data_layer.load_bi5_range: R1/R2/R3)."""
    import datetime as _dt
    import importlib
    sys.path.insert(0, str(ROOT / "research/nom_20261113/src"))
    DL = importlib.import_module("data_layer")
    days = sorted(p.name[:8] for p in folder.glob("*_BID.bi5"))
    if not days:
        return pd.DataFrame(columns=COLS)
    a = _dt.date(int(days[0][:4]), int(days[0][4:6]), int(days[0][6:]))
    b = _dt.date(int(days[-1][:4]), int(days[-1][4:6]), int(days[-1][6:]))
    x, _ = DL.load_bi5_range(folder, a, b, "duka_bi5_2025_yeniden")
    return _finish(x[["t", "open", "high", "low", "close"]].copy())


def _union_checked(d: pd.DataFrame, extra: pd.DataFrame, name: str, allow_superset: bool = False) -> pd.DataFrame:
    """Ortak dakikalar birebir olmalı. allow_superset (yalnız Dukascopy'nin resmi 1 dk mumu için): ayrışan dakikada
    resmi mum geçer (ana 2025 dosyası eksik tik indirmesinden kurulmuştu), ayrışma ortak dakikaların ‰1'ini aşmamak şartıyla."""
    m = extra.merge(d, on="t", suffixes=("_e", "_d"))
    replace_t = np.array([], dtype=np.int64)
    if len(m):
        diff = np.abs(m[["open_e", "high_e", "low_e", "close_e"]].to_numpy() - m[["open_d", "high_d", "low_d", "close_d"]].to_numpy()).max(axis=1)
        bad = diff > EXPORT_TOL
        if bad.any():
            b = m[bad]
            # Resmi Dukascopy 1 dk mumu, bizim (eksik/sınır tikli) tik kurgumuzdan yetkili; ama ayrışma ‰1'i aşarsa
            # yanlış dosya/saat ekseni şüphesi → dur.
            if not allow_superset or bad.mean() > OFFICIAL_MAX_SHARE:
                raise AssertionError(f"{name} ana dosyayla {int(bad.sum())} dakikada ayrışıyor (max {diff.max():.3f})")
            replace_t = b["t"].to_numpy()
            REPLACED.extend(pd.to_datetime(replace_t, unit="s").strftime("%Y-%m-%d %H:%M").tolist())
    UNION_LOG[name] = {"ortak": int(len(m)), "eklenen": int((~extra["t"].isin(d["t"])).sum()), "resmi_mumla_degisen": int(len(replace_t))}
    d = d[~d["t"].isin(replace_t)]
    return _finish(pd.concat([d, extra[~extra["t"].isin(d["t"])]], ignore_index=True))


def load_duka_m30_export() -> pd.DataFrame:
    return _read_export(DUKA_M30_EXPORT)


def load_mt5_native(tf: str, folder: Path = MT5_DIR_A) -> pd.DataFrame:
    """tf ∈ M1, M5, M15, M30, H1 — sunucu saatinden UTC'ye çevrilmiş."""
    x = pd.read_csv(folder / f"NAS100_{tf}.csv.gz")
    out = pd.DataFrame({
        "t": server_to_utc(x["t"].to_numpy()),
        "open": x["o"], "high": x["h"], "low": x["l"], "close": x["c"],
        "vol": x["v"], "spr": x["sp"] * MT5_POINT,
    })
    return _finish(out)


def load_mt5_utc_csv(path: Path) -> pd.DataFrame:
    x = pd.read_csv(path)
    t = pd.to_datetime(x["time_utc"], utc=True).astype("int64") // 10**9
    out = pd.DataFrame({
        "t": t, "open": x["open"], "high": x["high"], "low": x["low"], "close": x["close"],
        "vol": x["tick_volume"], "spr": x["spread"] * MT5_POINT,
    })
    return _finish(out)


def load_candle_cache(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return _finish(pd.read_parquet(path))
    x = pd.read_csv(path)
    t = pd.to_datetime(x["time_utc"], utc=True).astype("int64") // 10**9
    return _finish(pd.DataFrame({"t": t, "open": x["open"], "high": x["high"], "low": x["low"],
                                 "close": x["close"], "vol": x.get("volume")}))


# ── 2026-11-17 EK: kutudan taze çekim + önceki broker beslemesi (USTEC) ─────────
KUTU_TAZE = Path(__file__).resolve().parents[1] / "out/kutu_taze"  # calistir/arac_nas100_mum_export.py çıktısı
USTEC_JSON = [ROOT / "1MDATA/mt5_ustec_1m_bars.json", ROOT / "RECOVER/mt5_ustec_1m_bars.json"]


def load_ustec_json(path: Path) -> pd.DataFrame:
    """Önceki broker hesabının USTEC 1m dışa aktarımı. `t` sunucu duvar saati (NY+7), s05'te ölçüldü:
    Dukascopy'ye karşı her hafta en iyi gecikme 0 (çevrimden sonra). Bugünkü NAS100'den AYRI besleme."""
    import json as _json
    bars = pd.DataFrame(_json.loads(path.read_text())["bars"])
    out = pd.DataFrame({"t": server_to_utc(bars["t"].to_numpy()), "open": bars["o"], "high": bars["h"],
                        "low": bars["l"], "close": bars["c"], "vol": bars.get("v")})
    return _finish(out)
