"""Read-only canlı lifecycle/geometri/filtre/feed monitörü.

Prod backend'in HTTP API'sinden (gerçek MT5->Redis->DataHub feed'i) canlı
fiyat okur, Supabase'den aktif sinyalleri ve son filtre istatistiklerini
çeker, dört başlığı doğrular ve raporlar. HİÇBİR ŞEY YAZMAZ.

Doğrulananlar:
  1) Lifecycle TP/SL  - canlı fiyat kanonik TP/SL'i geçtiği halde sinyal hâlâ
                        active mi? (prod lifecycle 2dk'da bir koşar; gecikme bayrağı)
  2) Kanonik geometri - target_config'ten yeniden hesaplanan TP/SL, DB'de saklı
                        targets/stop ile uyuşuyor mu? (inflated geometri tespiti)
  3) Filtreleme       - son penceredeki resolution_reason/status dağılımı
                        (market_closed_invalid oranı vb.)
  4) Fiyat akışı      - /api/data/cached taze (cached=False) mi, yoksa Supabase
                        fallback'e (bayat) mı düşmüş?

Çalıştırma (repo kökünden, venv aktif):
    python research/live_lifecycle_monitor.py
Ortam değişkenleri:
    BACKEND_URL          (default: prod Railway URL)
    MONITOR_INTERVAL_S   (default: 120)
    MONITOR_CYCLES       (default: 0 = sonsuz)
    FILTER_WINDOW_HOURS  (default: 6)
    SUPABASE_URL / SUPABASE_KEY  (yoksa .env'den okunur)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env()

from services.target_config import (  # noqa: E402
    calculate_stoploss_price,
    calculate_target_prices,
    get_effective_config,
)

BACKEND_URL = os.getenv(
    "BACKEND_URL", "https://upbeat-flow-production.up.railway.app"
).rstrip("/")
INTERVAL_S = int(os.getenv("MONITOR_INTERVAL_S", "120"))
CYCLES = int(os.getenv("MONITOR_CYCLES", "0"))
FILTER_WINDOW_HOURS = int(os.getenv("FILTER_WINDOW_HOURS", "6"))
TRACKED = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

# Kanonik geometri karşılaştırma toleransı (bağıl). Saklı geometri bu eşiğin
# üstünde saparsa "inflated/yanlış" olarak işaretlenir.
GEOM_REL_TOL = 0.02
# Sinyal en az bu kadar eskiyse lifecycle'ın (2dk) koşmuş olması beklenir;
# daha taze sinyalleri "gecikme" sanmayalım.
LIFECYCLE_GRACE_MIN = 3.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _age_min(value: Optional[str]) -> Optional[float]:
    dt = _parse_dt(value)
    return None if dt is None else (_now() - dt).total_seconds() / 60.0


def _http_get_json(path: str, timeout: int = 15) -> Optional[dict]:
    url = f"{BACKEND_URL}{path}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"    [HTTP HATA] {path}: {exc}")
        return None


def _coerce_targets(raw: Any) -> Dict[str, float]:
    """targets alanı dict / JSON string / çift-encode string olabilir."""
    for _ in range(3):
        if isinstance(raw, dict):
            out: Dict[str, float] = {}
            for k, v in raw.items():
                try:
                    out[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
            return out
        if isinstance(raw, str) and raw.strip():
            try:
                raw = json.loads(raw)
            except Exception:
                return {}
        else:
            return {}
    return {}


def _supabase_client():
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise SystemExit("SUPABASE_URL / SUPABASE_KEY tanımlı değil (.env).")
    return create_client(url, key)


# ── 4) Fiyat akışı sağlığı ──────────────────────────────────────────────────
def check_price_flow() -> Dict[str, dict]:
    print(f"[1/4] Fiyat akışı sağlığı  ({BACKEND_URL})")
    status = _http_get_json("/api/data/scheduler/status")
    if status:
        print(
            f"    scheduler running={status.get('running')} "
            f"tracked={status.get('tracked_symbols')}"
        )
    out: Dict[str, dict] = {}
    for sym in TRACKED:
        resp = _http_get_json(f"/api/data/cached/{sym}")
        if not resp or not resp.get("success"):
            print(f"    {sym:<12} ❌ fiyat alınamadı")
            out[sym] = {"price": None, "stale": True}
            continue
        data = resp.get("data") or {}
        price = data.get("current_price")
        stale = bool(resp.get("cached"))  # cached=True => Supabase fallback = bayat
        flag = "⚠ FALLBACK(bayat)" if stale else "✓ canlı"
        age = _age_min(data.get("updated_at"))
        age_s = f"{age:.1f}dk" if age is not None else "?"
        print(f"    {sym:<12} {flag:<18} price={price} updated={age_s} önce")
        out[sym] = {"price": price, "stale": stale}
    return out


# ── 2+1) Aktif sinyaller: geometri + lifecycle ──────────────────────────────
def check_active_signals(client, prices: Dict[str, dict]) -> None:
    print(f"\n[2/4] Kanonik geometri  &  [3/4] Lifecycle TP/SL  (aktif sinyaller)")
    resp = (
        client.table("prediction_logs")
        .select(
            "id, symbol, model_type, ml_direction, ml_entry_price, timeframe, "
            "targets, stop_loss_pips, created_at, status"
        )
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )
    rows = resp.data or []
    print(f"    aktif sinyal: {len(rows)}")

    geom_mismatch = 0
    lifecycle_lag = 0
    checked = 0
    for r in rows:
        sym = r.get("symbol")
        direction = (r.get("ml_direction") or "").upper()
        entry = r.get("ml_entry_price")
        tf = r.get("timeframe") or "15m"
        if sym not in TRACKED or direction not in ("BUY", "SELL") or not entry:
            continue
        try:
            entry = float(entry)
        except (TypeError, ValueError):
            continue
        checked += 1

        canon_tp = calculate_target_prices(entry, direction, sym, tf)
        canon_sl = calculate_stoploss_price(entry, direction, sym, tf)
        stored = _coerce_targets(r.get("targets"))

        # (2) Geometri: saklı TP1 vs kanonik TP1
        if stored.get("TP1") and canon_tp.get("TP1"):
            rel = abs(stored["TP1"] - canon_tp["TP1"]) / max(abs(canon_tp["TP1"]), 1e-9)
            if rel > GEOM_REL_TOL:
                geom_mismatch += 1
                if geom_mismatch <= 5:
                    print(
                        f"    [GEOMETRİ] {sym} {direction} {r.get('model_type')} "
                        f"saklıTP1={stored['TP1']:.4f} kanonikTP1={canon_tp['TP1']:.4f} "
                        f"(Δ{rel*100:.1f}%)"
                    )

        # (3) Lifecycle: canlı fiyat kanonik TP4/SL'i geçtiyse ve sinyal yeterince
        # eskiyse, prod lifecycle çözmüş olmalıydı.
        live = (prices.get(sym) or {}).get("price")
        age = _age_min(r.get("created_at"))
        if live is None or age is None or age < LIFECYCLE_GRACE_MIN:
            continue
        live = float(live)
        tp_hit = (
            (direction == "BUY" and live >= canon_tp.get("TP1", float("inf")))
            or (direction == "SELL" and live <= canon_tp.get("TP1", float("-inf")))
        )
        sl_hit = (
            (direction == "BUY" and live <= canon_sl)
            or (direction == "SELL" and live >= canon_sl)
        )
        if tp_hit or sl_hit:
            lifecycle_lag += 1
            kind = "TP≥1" if tp_hit else "SL"
            if lifecycle_lag <= 8:
                print(
                    f"    [LIFECYCLE] {sym} {direction} {r.get('model_type')} "
                    f"canlı={live} {kind} geçildi ama hâlâ ACTIVE "
                    f"(yaş {age:.0f}dk, entry={entry}, SL={canon_sl:.4f})"
                )

    print(
        f"    → kontrol edilen {checked} | geometri sapması {geom_mismatch} | "
        f"lifecycle gecikme şüphesi {lifecycle_lag}"
    )


# ── 3) Filtreleme istatistikleri ────────────────────────────────────────────
def check_filtering(client) -> None:
    cutoff = (_now() - timedelta(hours=FILTER_WINDOW_HOURS)).isoformat()
    print(f"\n[4/4] Filtreleme  (son {FILTER_WINDOW_HOURS}s)")
    resp = (
        client.table("prediction_logs")
        .select("status, resolution_reason, model_type, created_at")
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(5000)
        .execute()
    )
    rows = resp.data or []
    total = len(rows)
    if not total:
        print("    pencerede kayıt yok")
        return
    by_status: Dict[str, int] = {}
    mci = 0
    for r in rows:
        st = r.get("status") or "?"
        by_status[st] = by_status.get(st, 0) + 1
        if r.get("resolution_reason") == "market_closed_invalid":
            mci += 1
    print(f"    toplam {total} | " + " ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print(f"    market_closed_invalid: {mci} ({mci/total*100:.1f}%)")


def run_cycle(client, cycle: int) -> None:
    ts = _now().strftime("%Y-%m-%d %H:%M:%S UTC")
    print("=" * 72)
    print(f"DÖNGÜ {cycle}  @ {ts}")
    print("=" * 72)
    prices = check_price_flow()
    check_active_signals(client, prices)
    check_filtering(client)
    print()


def main() -> None:
    client = _supabase_client()
    print(
        f"Read-only canlı monitör başladı | backend={BACKEND_URL} | "
        f"interval={INTERVAL_S}s | cycles={'∞' if CYCLES == 0 else CYCLES}"
    )
    cycle = 1
    while True:
        try:
            run_cycle(client, cycle)
        except KeyboardInterrupt:
            print("durduruldu.")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[DÖNGÜ HATASI] {exc}")
        if CYCLES and cycle >= CYCLES:
            return
        cycle += 1
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
