"""Veri katmanı — Supabase'ten işlemler, giriş parmak izleri ve broker 1m mumları.

Kaynaklar (salt-okuma; hiçbir tabloya YAZMAZ):
  * ``bot_trades``             MT5 kapanış deal'leri (evolution_agent yazar). Zamanlar
                               BROKER saatinde (UTC+2/+3) UTC etiketli → align.py düzeltir.
                               ``sl``/``tp`` = pozisyonu açan emrin İLK planı.
  * ``bot_entry_fingerprints`` giriş anı bağlamı (yalnız MOMSR ailesi yazıyor).
  * ``indicator_snapshots``    broker 1m OHLC + TICK hacmi (data_recorder). 2026-07-28
                               öncesi broker saatinde → ``normalize_snapshot_clock``.
  * yfinance ^VIX              günlük kapanış (fail-open; yalnız ÖNCEKİ gün kullanılır).
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from . import settings as S

log = logging.getLogger("islem_otopsi.data")

BAR_COLS = ["open", "high", "low", "close", "volume"]


def get_client() -> Any:
    """Service-role Supabase istemcisi (anahtar keşfi scripts/remote.py ile ortak)."""
    from scripts.remote import _client
    return _client()


def fetch_table(client: Any, table: str, select: str, filters: list[tuple[str, str, Any]],
                order_col: str) -> list[dict]:
    """Sayfalı tam okuma (PostgREST 1000 satır tavanı)."""
    rows: list[dict] = []
    start = 0
    while True:
        q = client.table(table).select(select)
        for col, op, val in filters:
            q = getattr(q, op)(col, val)
        batch = q.order(order_col).range(start, start + S.SUPABASE_PAGE - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < S.SUPABASE_PAGE:
            return rows
        start += S.SUPABASE_PAGE


# ── İşlemler ─────────────────────────────────────────────────────────────────

def family_of(magic: int | None) -> str:
    """Magic numarasından strateji ailesi."""
    if magic is None or int(magic) == S.MANUAL_MAGIC:
        return "MANUEL"
    return S.FAMILY_BY_OFFSET.get(int(magic) - S.MAGIC_BASE, f"MAGIC_{int(magic)}")


def load_trades(client: Any, since_utc: pd.Timestamp) -> pd.DataFrame:
    """Kapanmış pozisyonlar (position_id başına tek satır, kısmi kapanışlar toplanır).

    Zamanlar HAM broker etiketinde döner (``open_raw``/``close_raw``); gerçek UTC
    align.py'de fiyat eşleştirmesiyle bulunur.
    """
    since_raw = (since_utc - timedelta(days=1)).isoformat()
    rows = fetch_table(client, "bot_trades", "*", [("close_time", "gte", since_raw)], "close_time")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["pid"] = df["raw"].map(lambda r: int((r or {}).get("position_id") or 0))
    df["reason"] = df["raw"].map(lambda r: int((r or {}).get("reason", -1)))
    df["net"] = df["profit"].fillna(0) + df["commission"].fillna(0) + df["swap"].fillna(0)
    df = df[df["pid"] > 0].sort_values("close_time")
    return _aggregate_positions(df)


def _aggregate_positions(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("pid", sort=False)
    out = pd.DataFrame({
        "pid": g["pid"].first(),
        "broker_symbol": g["symbol"].first(),
        "symbol": g["normalized_symbol"].first(),
        "direction": g["direction"].first(),
        "magic": g["magic"].first(),
        "volume": g["volume"].sum(),
        "open_raw": pd.to_datetime(g["open_time"].min(), utc=True),
        "open_price": g["open_price"].first(),
        "close_raw": pd.to_datetime(g["close_time"].max(), utc=True),
        "close_price": g["close_price"].last(),
        "sl0": g["sl"].first(),
        "tp0": g["tp"].first(),
        "net": g["net"].sum(),
        "swap": g["swap"].sum(),
        "reason": g["reason"].last(),
        "comment": g["comment"].last(),
        "n_closes": g["pid"].size(),
    }).reset_index(drop=True)
    out["symbol"] = out["symbol"].fillna(out["broker_symbol"].map(
        lambda s: S.SYMBOL_ALIASES.get(str(s).upper())))
    out["family"] = out["magic"].map(family_of)
    return out.dropna(subset=["open_raw", "open_price", "symbol"]).reset_index(drop=True)


def load_fingerprints(client: Any, since_utc: pd.Timestamp) -> dict[int, dict]:
    """ticket(=position_id) → giriş parmak izi (raw JSON alanları dahil)."""
    rows = fetch_table(client, "bot_entry_fingerprints", "ticket,scope,entry_type,tp_source,voters,raw",
                       [("ts", "gte", (since_utc - timedelta(days=2)).isoformat())], "ts")
    out: dict[int, dict] = {}
    for r in rows:
        raw = r.get("raw") or {}
        voters = r.get("voters") or raw.get("voters") or []
        out[int(r["ticket"])] = {
            "fp_scope": r.get("scope"), "fp_entry_type": r.get("entry_type"),
            "fp_tp_source": r.get("tp_source"), "fp_voters_n": len(voters),
            "fp_voters": ",".join(sorted(map(str, voters))),
            "fp_backend_conf": raw.get("backend_conf"), "fp_mom_stretch": raw.get("mom_stretch"),
            "fp_zone_touches": raw.get("entry_zone_touches"), "fp_n_zones": raw.get("n_zones"),
            "fp_priority": raw.get("priority"), "fp_session": raw.get("session"),
            "fp_backend_action": raw.get("backend_action"), "fp_sl": raw.get("sl"), "fp_tp": raw.get("tp"),
        }
    return out


# ── Mumlar (önbellekli) ──────────────────────────────────────────────────────

def _cache_paths(symbol: str) -> tuple:
    safe = symbol.replace(".", "_")
    return S.CACHE_DIR / f"{safe}_1m_raw.parquet", S.CACHE_DIR / f"{safe}_1m_meta.json"


def _fetch_bars_raw(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    client = get_client()
    rows = fetch_table(client, "indicator_snapshots", "candle_time,open,high,low,close,volume",
                       [("symbol", "eq", symbol), ("timeframe", "eq", "1m"),
                        ("candle_time", "gte", start.isoformat()), ("candle_time", "lt", end.isoformat())],
                       "candle_time")
    df = pd.DataFrame(rows, columns=["candle_time"] + BAR_COLS)
    df["candle_time"] = pd.to_datetime(df["candle_time"], utc=True)
    return df


def _missing_ranges(cov: dict | None, need_start: pd.Timestamp, need_end: pd.Timestamp) -> list:
    if not cov:
        return [(need_start, need_end)]
    c0, c1 = pd.Timestamp(cov["start"]), pd.Timestamp(cov["end"])
    ranges = []
    if need_start < c0:
        ranges.append((need_start, c0))
    tail = c1 - timedelta(hours=S.CACHE_REFRESH_TAIL_H)
    if need_end > tail:
        ranges.append((max(tail, need_start), need_end))
    return ranges


def load_bars_raw(symbol: str, need_start: pd.Timestamp, need_end: pd.Timestamp,
                  refresh: bool = False) -> pd.DataFrame:
    """Ham (normalize edilmemiş) 1m mumlar; yalnız eksik aralıklar indirilir."""
    S.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pq, meta_p = _cache_paths(symbol)
    cached = pd.read_parquet(pq) if (pq.exists() and not refresh) else pd.DataFrame(columns=["candle_time"] + BAR_COLS)
    cov = json.loads(meta_p.read_text()) if (meta_p.exists() and not refresh) else None
    parts = [cached]
    for a, b in _missing_ranges(cov, need_start, need_end):
        log.info("%s 1m indiriliyor: %s → %s", symbol, a, b)
        parts.append(_fetch_bars_raw(symbol, a, b))
    df = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else cached
    if len(df):
        df["candle_time"] = pd.to_datetime(df["candle_time"], utc=True)
        df = df.drop_duplicates("candle_time", keep="last").sort_values("candle_time").reset_index(drop=True)
        df.to_parquet(pq, index=False)
        new_cov = {"start": min(need_start, pd.Timestamp(cov["start"])) if cov else need_start,
                   "end": max(need_end, pd.Timestamp(cov["end"])) if cov else need_end}
        meta_p.write_text(json.dumps({k: pd.Timestamp(v).isoformat() for k, v in new_cov.items()}))
    return df


def normalize_snapshot_clock(raw: pd.DataFrame) -> pd.DataFrame:
    """Ham etiket → gerçek UTC (2026-07-28 kohort ayrımı); UTC indeksli çerçeve döner."""
    if raw.empty:
        return pd.DataFrame(columns=BAR_COLS, index=pd.DatetimeIndex([], tz="UTC"))
    t = pd.to_datetime(raw["candle_time"], utc=True)
    broker_until = pd.Timestamp(S.SNAPSHOT_BROKER_UNTIL)
    ambiguous_until = pd.Timestamp(S.SNAPSHOT_AMBIGUOUS_UNTIL)
    keep = ~((t >= broker_until) & (t < ambiguous_until))
    shift = np.where(t < broker_until, -S.SNAPSHOT_BROKER_SHIFT_H, 0)
    true_t = t + pd.to_timedelta(shift, unit="h")
    df = raw.loc[keep, BAR_COLS].astype(float).copy()
    df.index = pd.DatetimeIndex(true_t[keep])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df[(df["high"] >= df["low"]) & (df["close"] > 0)]


def load_bars(symbols: list[str], need: dict[str, tuple], refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Sembol başına normalize edilmiş 1m mumlar (paralel indirme)."""
    def one(sym: str) -> tuple[str, pd.DataFrame]:
        a, b = need[sym]
        return sym, normalize_snapshot_clock(load_bars_raw(sym, a, b, refresh))
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, symbols))


# ── VIX (opsiyonel bağlam) ───────────────────────────────────────────────────

def load_vix(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """^VIX günlük kapanış (tarih → kapanış). Hata → boş seri (fail-open, raporda yazılır)."""
    path = S.CACHE_DIR / "vix_daily.csv"
    try:
        if path.exists():
            s = pd.read_csv(path, index_col=0, parse_dates=True)["close"]
            lo_ok = s.index.min() <= (start - timedelta(days=3)).tz_localize(None).normalize()
            hi_ok = s.index.max() >= (end - timedelta(days=3)).tz_localize(None).normalize()
            if lo_ok and hi_ok:
                return s
        import yfinance as yf
        h = yf.Ticker("^VIX").history(start=(start - timedelta(days=10)).strftime("%Y-%m-%d"),
                                      end=(end + timedelta(days=1)).strftime("%Y-%m-%d"), auto_adjust=False)
        s = h["Close"].rename("close")
        s.index = pd.DatetimeIndex(s.index.tz_localize(None) if s.index.tz is not None else s.index).normalize()
        S.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        s.to_frame().to_csv(path)
        return s
    except Exception as exc:  # pragma: no cover - ağ bağımlı
        log.warning("VIX alınamadı (fail-open): %s", exc)
        return pd.Series(dtype=float)


def utc_now() -> pd.Timestamp:
    return pd.Timestamp(datetime.now(timezone.utc))
