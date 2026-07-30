"""Core logic for the bias-accuracy measurement harness (shared).

Both the HTTP router (``routers.bias_test_router``) and the scheduled
auto-runner (``services.bias_auto_runner``) call these functions, so the
recording / grading / reporting rules live in exactly one place.

Writes to bias_test_log only — isolated from the live daily_bias / veto engine.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from services import daily_bias_service as bias_svc
from services import session_context_service as sc

logger = logging.getLogger(__name__)

NDX = "NDX.INDX"
_FLAT_PCT = 0.15

# Multi-symbol (2026-07-08): rows are attributed to a symbol via the payload's
# `symbol` field (set by the debate engine) or the run_label prefix. The DB
# table has no symbol column — run_label carries it, raw_payload records it.
LABEL_SYMBOLS = {"xau": "XAUUSD", "dax": "GDAXI.INDX", "usoil": "USOIL.FOREX",
                 "ndx": NDX}

# Per-symbol grading windows (DST-safe): (tz, start_min, end_min).
# start=None → whole day up to the cutoff. Grading = session open→close for
# NDX (unchanged legacy behaviour); decision-price→session close for others.
_SESSION_WINDOWS = {
    NDX: ("America/New_York", 9 * 60 + 30, 16 * 60),
    "GDAXI.INDX": ("Europe/Berlin", 9 * 60, 17 * 60 + 30),
    "XAUUSD": ("America/New_York", None, 17 * 60),
    "USOIL.FOREX": ("America/New_York", None, 14 * 60 + 30),   # NYMEX settle
}


def symbol_for_row(row: dict) -> str:
    """Resolve which instrument a bias_test_log row belongs to."""
    raw = row.get("raw_payload") or {}
    if isinstance(raw, dict) and raw.get("symbol") in _SESSION_WINDOWS:
        return raw["symbol"]
    label = (row.get("run_label") or "").lower()
    for prefix, sym in LABEL_SYMBOLS.items():
        if label.startswith(prefix):
            return sym
    return NDX   # legacy default — all pre-multi-symbol rows are NASDAQ


class BiasTestError(RuntimeError):
    """Recoverable harness error (bad payload, missing candle, db down)."""


def _client():
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return None
    return get_supabase_client()


def direction_from_pct(pct: Optional[float]) -> Optional[str]:
    if pct is None:
        return None
    if pct > _FLAT_PCT:
        return "positive"
    if pct < -_FLAT_PCT:
        return "negative"
    return "flat"


def predicted_matches_actual(predicted: str, actual: Optional[str]) -> Optional[bool]:
    if actual is None:
        return None
    predicted = (predicted or "").lower()
    if predicted == "bullish":
        return actual == "positive"
    if predicted == "bearish":
        return actual == "negative"
    if predicted in ("neutral", "choppy"):
        return actual == "flat"
    return None


async def record_run(payload: dict, run_label: str = "manual",
                     run_ts: Optional[datetime] = None) -> dict:
    """Normalise a bias payload, attach session context, insert a log row.

    Raises :class:`ValueError` on an unparseable payload, :class:`BiasTestError`
    if the DB is unavailable or the insert fails.
    """
    parsed = bias_svc.normalize_cio_payload(payload)   # may raise ValueError
    run_ts = run_ts or datetime.now(timezone.utc)
    if run_ts.tzinfo is None:
        run_ts = run_ts.replace(tzinfo=timezone.utc)

    ctx = await sc.enrich_price_context(run_ts)

    # İdempotensi ARTIK insert yolunda (2026-07-18): auto-runner'ın kendi
    # already_logged kontrolü iki AYRI süreç (ör. Railway + lokal) aynı pencerede
    # koşunca yarışıyordu — 07-15/16'daki tüm koşular çift loglandı. Zamanlanmış
    # pencere etiketleri gün başına 1 kayıt; "manual" etiketi bilinçli tekrar
    # koşulara açık bırakılır.
    if run_label != "manual" and already_logged(ctx["ny_time"][:10], run_label):
        logger.info("[bias-test] duplicate run skipped: %s %s",
                    ctx["ny_time"][:10], run_label)
        return {"ok": False, "duplicate": True, "run_label": run_label,
                "ny_date": ctx["ny_time"][:10],
                "predicted_bias": parsed["nasdaq_daily_bias"]}
    row = {
        "run_timestamp_utc": run_ts.isoformat(),
        "ny_time": ctx["ny_time"],
        "ny_date": ctx["ny_time"][:10],
        "run_label": run_label,
        "current_session": ctx["current_session"],
        "london_direction": ctx.get("london_session_direction"),
        "asia_overnight_change": ctx.get("asia_overnight_change"),
        "us_premarket_change": ctx.get("us_premarket_change"),
        "minutes_to_us_open": ctx["minutes_to_us_open"],
        "is_half_day": ctx["is_half_day"],
        "is_holiday": ctx["is_holiday"],
        "session_overlap": ctx["session_overlap"],
        "predicted_bias": parsed["nasdaq_daily_bias"],
        "confidence": parsed["confidence"],
        "trade_mode": parsed.get("trade_mode"),
        "main_support": parsed.get("main_support"),
        "main_resistance": parsed.get("main_resistance"),
        "invalid_if": parsed.get("invalid_if"),
        "reason_summary": parsed.get("reason_summary"),
        "raw_payload": parsed.get("raw_payload"),
    }
    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    res = client.table("bias_test_log").insert(row)
    if res.get("error"):
        raise BiasTestError(str(res["error"]))

    # CORTEX episodic memory (fail-open — never breaks bias logging).
    # NASDAQ-only by design: other symbols' runs skip the episodic store.
    _sym = (payload.get("symbol") if isinstance(payload, dict) else None) or NDX
    try:
        from config import settings
        if settings.cortex_enabled and _sym == NDX:
            from services import cortex_memory as cortex
            situation = payload.get("_cortex_situation") if isinstance(payload, dict) else None
            if situation is None:
                situation = await cortex.build_situation(run_ts)
            cortex.record_episode(
                situation, predicted_bias=parsed["nasdaq_daily_bias"],
                confidence=parsed["confidence"], run_label=run_label,
                source="bias_run", now_utc=run_ts)
    except Exception as e:
        logger.debug("[bias-test] CORTEX episode skipped: %s", e)

    return {"ok": True, "run_label": run_label,
            "current_session": ctx["current_session"],
            "ny_date": row["ny_date"],
            "predicted_bias": parsed["nasdaq_daily_bias"]}


def recent_track_record(limit: int = 25, symbol: Optional[str] = None) -> str:
    """ÖZ-KALİBRASYON bloğu: sistemin SON tahminlerinin gerçekleşme karnesi (bias_test_log).
    Debate/CIO promptuna enjekte edilir — model kendi sistematik önyargısını GÖRÜR
    (2026-07-09 otopsisi: %30.8 doğruluk; boğa piyasasında art arda bearish çağrılar —
    model kendi karnesini görmediği için aynı hatayı tekrarlıyordu). Fail-open: DB yoksa ''."""
    try:
        client = _client()
        if client is None:
            return ""
        # NOT: özel REST wrapper'da `.not_` zinciri YOK — eski `.not_.is_(...)`
        # çağrısı sessizce exception'a düşüyor ve blok hep "" dönüyordu (ölü
        # öz-kalibrasyon, 2026-07-18'de fark edildi). Null filtresi Python'da.
        # `sym:raw_payload->>symbol` — transkript içeren koca raw_payload yerine
        # yalnız sembol alanı iner (PostgREST JSON path select).
        raw_rows = (client.table("bias_test_log")
                    .select("predicted_bias,was_correct,ny_date,run_label,"
                            "ret_60m,ret_240m,sym:raw_payload->>symbol")
                    .order("ny_date", desc=True).limit(limit * 6).execute()
                    ).get("data") or []
        rows = [r for r in raw_rows if r.get("was_correct") is not None
                and (symbol is None or symbol_for_row(
                        {"raw_payload": {"symbol": r.get("sym")},
                         "run_label": r.get("run_label")}) == symbol)][:limit]
        if len(rows) < 5:
            return ""
        # 2026-07-18 revizyonu: karne YÖNLÜ ve ÇEKİMSER çağrıları ayırır.
        # Eski hali nötrleri ±0.15 flat bandıyla notluyordu (günlerin ~%80'i
        # banda sığmaz → nötr otomatik yanlış) ve "neutral'e sistematik önyargın
        # var" uyarısıyla CIO'yu haksız yönlü karara itiyordu (DAX kilitlenmesi).
        directional = [r for r in rows
                       if (r.get("predicted_bias") or "").lower() in ("bullish", "bearish")]
        abstain = [r for r in rows if r not in directional]

        by: dict = {}
        for r in directional:
            b = (r.get("predicted_bias") or "?").lower()
            w, n = by.get(b, (0, 0))
            by[b] = (w + (1 if r.get("was_correct") else 0), n + 1)
        tot_w = sum(w for w, _ in by.values())
        tot_n = sum(n for _, n in by.values())
        parts = [f"{b}: {w}/{n}" for b, (w, n) in sorted(by.items(), key=lambda x: -x[1][1])]
        warn = ""
        if by:
            worst = min(by.items(), key=lambda x: (x[1][0] / max(x[1][1], 1), -x[1][1]))
            if worst[1][1] >= 3 and worst[1][0] / worst[1][1] < 0.4:
                warn = (f" ⚠ '{worst[0]}' calls hit only {worst[1][0]}/{worst[1][1]} — before "
                        f"calling '{worst[0]}' again, show that your evidence DIFFERS "
                        f"from those failed calls.")

        # UFUK KARNESİ: asıl ölçü sembolün birincil ufkundaki yönlü gerçekleşme.
        prim = PRIMARY_HORIZON_MIN.get(symbol or "", 60)
        hz = ""
        for m, tag in ((prim, f"PRIMARY +{prim}min"), (60, "+60min"), (240, "+240min")):
            if tag != f"PRIMARY +{prim}min" and m == prim:
                continue
            sgn = [signed_ret(r, m) for r in rows]
            sgn = [x for x in sgn if x is not None]
            if len(sgn) >= 5:
                w = sum(1 for x in sgn if x > 0)
                hz += f" {tag}: {w}/{len(sgn)}"
        if hz:
            hz = (" INTRADAY HORIZON RECORD (directional calls, move in your "
                  "predicted direction):" + hz + " — this horizon record is the "
                  "PRIMARY success metric, not the daily close.")

        # YÖN DENGESİ (2026-07-26): asıl kusur isabet değil, YANLILIK. Ölçüm:
        # 32 yönlü çağrının 25'i bearish (%78) iken piyasa 29 yukarı / 28 aşağı
        # kapandı → binom p=0.002. Model kendi yön dağılımını GÖRMÜYORDU; karne
        # bloğu yalnız yön-başına isabeti gösteriyordu, dağılımı değil. Burada
        # çağrı dağılımını GERÇEKLEŞEN piyasa taban oranıyla yan yana koyuyoruz.
        bal = ""
        n_bear = sum(1 for r in directional
                     if (r.get("predicted_bias") or "").lower() == "bearish")
        n_bull = len(directional) - n_bear
        if len(directional) >= 8:
            moves = [r.get(f"ret_{prim}m") for r in rows]
            moves = [m for m in moves if m is not None]
            share = max(n_bear, n_bull) / len(directional)
            side = "bearish" if n_bear >= n_bull else "bullish"
            bal = (f" DIRECTIONAL BALANCE: of your last {len(directional)} directional "
                   f"calls, {n_bear} were bearish and {n_bull} bullish — "
                   f"{share*100:.0f}% {side}.")
            if moves:
                up = sum(1 for m in moves if m > 0)
                # Yanlılık, piyasanın KENDİ asimetrisine göre ölçülür: gerçekten
                # düşen bir piyasada ayı ağırlıklı çağrı doğru davranıştır.
                # Tilt = çağrı payı − piyasanın aynı yöndeki payı.
                mkt_side = (up if side == "bullish" else len(moves) - up) / len(moves)
                bal += (f" Over the last {len(moves)} graded runs in this period the "
                        f"market actually moved {'up' if side == 'bullish' else 'down'} "
                        f"{mkt_side*100:.0f}% of the time (+{prim}min horizon).")
                if share - mkt_side >= 0.20:
                    bal += (f" ⚠ You call {side} {(share-mkt_side)*100:.0f} points more "
                            f"often than the market actually goes that way — a "
                            f"systematic {side.upper()} TILT in YOUR reasoning, not a "
                            f"market read. Before issuing another {side} call, state "
                            f"explicitly which concrete, level-based evidence makes "
                            f"today different from that run of {side} calls. Apply the "
                            f"SAME evidence bar you would demand for the opposite "
                            f"direction.")

        ab = ""
        if abstain:
            realized = [abs(r.get("ret_240m")) for r in abstain if r.get("ret_240m") is not None]
            avg_mv = f"{sum(realized)/len(realized):.2f}" if realized else "?"
            ab = (f" ABSTAIN RECORD: you abstained (neutral/choppy) {len(abstain)}× "
                  f"(avg realized |4h move| {avg_mv}%). Abstaining on weak evidence is "
                  f"CORRECT and is NOT counted against you — but when the evidence is "
                  f"strong and confluent, COMMIT to a direction cleanly.")

        head = (f"SELF-CALIBRATION (your LAST {tot_n} DIRECTIONAL predictions, day-close "
                f"legacy metric): {tot_w}/{tot_n}; breakdown → " + " | ".join(parts) + "."
                ) if tot_n else "SELF-CALIBRATION: no directional calls graded yet."
        return head + warn + bal + hz + ab
    except Exception as e:
        logger.debug("[bias-test] track record skipped: %s", e)
        return ""


def already_logged(ny_date: str, run_label: str) -> bool:
    """Has a row already been recorded for this (date, label)? (idempotency)."""
    client = _client()
    if client is None:
        return False
    rows = (client.table("bias_test_log").select("id")
            .eq("ny_date", ny_date).eq("run_label", run_label)
            .limit(1).execute()).get("data") or []
    return bool(rows)


# ── Çok-ufuklu notlama (2026-07-18) ──────────────────────────────────────────
# Gerekçe: gün-kapanışı metriği ajan isabetini gizliyor (NDX bearish gün 0/4
# ama +60dk 4/6, +240dk 4/5 — backend/data/agent_debate_analysis_report.md).
# ret_* ham (yönsüz) % değişimdir; isabet okuma tarafında tahmin yönüyle
# işaretlenerek hesaplanır. mfe/mae_60m tahmin yönüne görelidir.
# Karar dayanıklılık merdiveni (2026-07-20): karar anından +10dk → +6 saat.
# Panel ısı haritası bu ufuklarla "karar kaç dakika/saat geçerli kalıyor"u çizer.
HORIZONS_MIN = (10, 30, 60, 90, 120, 180, 240, 300, 360)
_HORIZON_LOOKBACK_BARS = 6   # hedef anda mum yoksa geriye en çok 30dk bak

# Sembol başına BİRİNCİL ufuk (dk) — başarı karnesinin ana metriği bu ufukta
# hesaplanır. Seçim 2026-07-18 çok-ufuklu analizinden (NDX 240dk %75 vs gün
# %33; USOIL/XAU/DAX 60dk). ⚠ n küçük — sembol başına n≥30 yönlü çağrıda
# yeniden türet (backlog kaydı var).
PRIMARY_HORIZON_MIN = {
    NDX: 240,
    "GDAXI.INDX": 60,
    "XAUUSD": 60,
    "USOIL.FOREX": 60,
}

#: Çekimser (nötr/choppy) çağrının "haklı" sayıldığı gün-hareket eşiği (%).
#: ±0.15 flat bandı günlerin ~%80'inde tutmuyor ve çekimserliği otomatik
#: cezalandırıyordu; 0.5 altı gün "sakin gün" kabul edilir.
ABSTAIN_QUIET_PCT = 0.5

#: Bu sayının altındaki örneklem "erken gözlem"dir — yüzde gösterilir ama kanıt
#: olarak işaretlenmez (2026-07-30: 48 yönlü çağrının tamamı ±14pp güven
#: aralığında; sembol×ufuk hücreleri n=6-18). Rapor hücreleri bu eşiğin altında
#: `early_observation: true` taşır; panel soluk gösterir.
EARLY_OBS_MIN_N = 30


def signed_ret(row: dict, minutes: int) -> Optional[float]:
    """Tahmin yönünde işaretli ufuk getirisi (%); yönsüz çağrıda None."""
    b = (row.get("predicted_bias") or "").lower()
    v = row.get(f"ret_{minutes}m")
    if v is None or b not in ("bullish", "bearish"):
        return None
    return v if b == "bullish" else -v


def _decision_price(row: dict) -> Optional[float]:
    raw = row.get("raw_payload") or {}
    if isinstance(raw, dict) and raw.get("price_at_decision"):
        try:
            return float(raw["price_at_decision"])
        except (TypeError, ValueError):
            pass
    return None


def _horizon_stats(client, symbol: str, run_ts: datetime,
                   p0: Optional[float], predicted: str) -> Optional[dict]:
    """5m mumlardan +10/30/60/240dk getirileri + ilk-60dk MFE/MAE hesapla.

    ``p0`` yoksa karar anındaki 5m kapanışı çapa alınır. 240dk penceresi henüz
    kapanmadıysa None döner (kısmi yazım yok — catch-up sonra tamamlar).
    """
    if datetime.now(timezone.utc) < run_ts + timedelta(minutes=HORIZONS_MIN[-1] + 6):
        return None
    start = (run_ts - timedelta(minutes=5 * _HORIZON_LOOKBACK_BARS)).isoformat()
    end = (run_ts + timedelta(minutes=HORIZONS_MIN[-1] + 5)).isoformat()
    try:
        rows = (client.table("candle_cache").select("candle_time,high,low,close")
                .eq("symbol", symbol).eq("timeframe", "5m")
                .gte("candle_time", start).lte("candle_time", end)
                .order("candle_time").limit(120).execute()).get("data") or []
    except Exception as e:
        logger.warning("[bias-test] horizon 5m read error (%s): %s", symbol, e)
        return None
    bars = []
    for r in rows:
        try:
            t = datetime.fromisoformat(str(r["candle_time"]).replace("Z", "+00:00"))
            bars.append((t, float(r["high"]), float(r["low"]), float(r["close"])))
        except (TypeError, ValueError, KeyError):
            continue
    if not bars:
        return None

    def close_at(target: datetime) -> Optional[float]:
        best = None
        for t, _h, _l, c in bars:
            if t <= target and (target - t) <= timedelta(minutes=5 * _HORIZON_LOOKBACK_BARS):
                best = c
        return best

    anchor = p0 or close_at(run_ts)
    if not anchor:
        return None
    out: dict[str, Optional[float]] = {}
    for m in HORIZONS_MIN:
        px = close_at(run_ts + timedelta(minutes=m))
        out[f"ret_{m}m"] = round((px - anchor) / anchor * 100.0, 4) if px else None
    win = [b for b in bars if run_ts < b[0] <= run_ts + timedelta(minutes=60)]
    if win:
        up = (max(h for _t, h, _l, _c in win) - anchor) / anchor * 100.0
        dn = (anchor - min(l for _t, _h, l, _c in win)) / anchor * 100.0
        if (predicted or "").lower() == "bearish":
            out["mfe_60m"], out["mae_60m"] = round(dn, 4), round(up, 4)
        else:   # bullish + nötr/choppy: lehte = yukarı (belgeli kabul)
            out["mfe_60m"], out["mae_60m"] = round(up, 4), round(dn, 4)
    if all(out.get(f"ret_{m}m") is None for m in HORIZONS_MIN):
        return None
    out["horizon_filled_at"] = datetime.now(timezone.utc).isoformat()
    return out


def _synth_session_stats(symbol: str, ny_date: str) -> Optional[dict]:
    """Synthesize the instrument's session-day OHLC from 1h candle_cache rows.

    The MT5 bridge never streams 1d bars (candle_cache has zero 1d rows), which
    left outcome-filling permanently dead. This rebuilds each instrument's own
    session window (DST-correct via zoneinfo) from the 1h bars that DO exist:
    NDX 09:30-16:00 NY · DAX 09:00-17:30 Berlin · XAU day→17:00 NY ·
    USOIL day→14:30 NY settle."""
    from zoneinfo import ZoneInfo
    win = _SESSION_WINDOWS.get(symbol)
    client = _client()
    if win is None or client is None:
        return None
    tz_name, start_min, end_min = win
    client_tz = ZoneInfo(tz_name)
    try:
        rows = (client.table("candle_cache").select("candle_time,open,high,low,close")
                .eq("symbol", symbol).eq("timeframe", "1h")
                .gte("candle_time", f"{ny_date}T00:00:00+00:00")
                .lte("candle_time", f"{ny_date}T23:59:59+00:00")
                .order("candle_time").limit(60).execute()).get("data") or []
    except Exception as e:
        logger.warning("[bias-test] 1h synth read error (%s): %s", symbol, e)
        return None
    keep = []
    for r in rows:
        try:
            t = datetime.fromisoformat(str(r["candle_time"]).replace("Z", "+00:00"))
            local = t.astimezone(client_tz)
            minutes = local.hour * 60 + local.minute
            if (start_min is None or minutes >= start_min) and minutes < end_min:
                keep.append(r)
        except (ValueError, KeyError):
            continue
    if len(keep) < 3:
        return None
    try:
        return {"open": float(keep[0]["open"]), "close": float(keep[-1]["close"]),
                "high": max(float(r["high"]) for r in keep),
                "low": min(float(r["low"]) for r in keep)}
    except (TypeError, ValueError):
        return None


async def _day_stats(symbol: str, ny_date: str) -> Optional[dict]:
    """Session-day OHLC for `symbol` on `ny_date` (1d feed → 1h synthesis)."""
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, "1d", limit=60)
    except Exception:
        candles = []
    for c in candles or []:
        ts = str(c.get("timestamp") or c.get("time") or c.get("date") or "")
        if ts.startswith(ny_date):
            o = c.get("open") or c.get("o")
            cl = c.get("close") or c.get("c")
            if o and cl:
                return {"open": float(o), "close": float(cl),
                        "high": float(c.get("high") or c.get("h") or cl),
                        "low": float(c.get("low") or c.get("l") or cl)}
    # 1d feed dead → synthesize from 1h (the fix that unblocks learning)
    return _synth_session_stats(symbol, ny_date)


async def _ndx_day_stats(ny_date: str) -> Optional[dict]:
    return await _day_stats(NDX, ny_date)


def pending_dates(max_days: int = 10) -> list[str]:
    """NY dates (before today) that still have ungraded rows — catch-up queue."""
    client = _client()
    if client is None:
        return []
    today = datetime.now(sc.NY).date().isoformat()
    try:
        rows = (client.table("bias_test_log")
                .select("ny_date,was_correct,horizon_filled_at")
                .limit(500).execute()).get("data") or []
    except Exception:
        return []
    dates = sorted({str(r["ny_date"]) for r in rows
                    if r.get("ny_date") and str(r["ny_date"]) < today
                    and (r.get("was_correct") is None
                         or r.get("horizon_filled_at") is None)})
    return dates[-max_days:]


async def fill_pending(max_days: int = 10) -> dict:
    """Grade every past day left ungraded (backend down at 16:15 ET, or the 1d
    feed was broken). Idempotent."""
    results = {}
    for d in pending_dates(max_days):
        try:
            r = await fill_outcomes(d)
            results[d] = f"{r['rows_updated']} rows → {r['actual_close_direction']}"
        except BiasTestError as e:
            results[d] = f"skipped: {e}"
    return results


def backfill_horizons(max_rows: int = 500) -> dict:
    """Ufuk merdiveni genişleyince ESKİ satırların yeni kolonlarını doldur.

    horizon_filled_at dolu olsa bile yeniden hesaplar (yeni ret_90m..360m
    kolonları null kaldığı için) — _horizon_stats idempotent, 5m mumlardan
    aynı çapayla üretir. Tek seferlik bakım aracı; panelden çağrılmaz.
    """
    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log")
            .select("id,run_timestamp_utc,raw_payload,predicted_bias,run_label,ny_date")
            .is_("ret_360m", "null")
            .order("ny_time").limit(max_rows).execute()).get("data") or []
    done, skipped = 0, 0
    for r in rows:
        try:
            run_ts = datetime.fromisoformat(
                str(r["run_timestamp_utc"]).replace("Z", "+00:00"))
            sym = symbol_for_row(r)
            h = _horizon_stats(client, sym, run_ts,
                               _decision_price(r), r.get("predicted_bias") or "")
        except Exception as e:
            logger.warning("[bias-test] backfill error id=%s: %s", r.get("id"), e)
            h = None
        if h:
            client.table("bias_test_log").eq("id", r["id"]).update(h)
            done += 1
        else:
            skipped += 1
    return {"candidates": len(rows), "filled": done, "skipped": skipped}


async def fill_outcomes(ny_date: Optional[str] = None) -> dict:
    """Grade every row for `ny_date` against its OWN instrument's session.

    NDX rows keep the legacy metric (session open→close, so the whole
    measurement series stays comparable). Other symbols are graded
    decision-price→session-close — the honest question for a bias issued at
    the decision hour. Rows whose session data isn't available yet are left
    ungraded (picked up later by the catch-up filler)."""
    if not ny_date:
        ny_date = datetime.now(sc.NY).date().isoformat()

    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log").select("*")
            .eq("ny_date", ny_date).execute()).get("data") or []

    stats_cache: dict[str, Optional[dict]] = {}
    updated, skipped, horizons_filled, ndx_change, ndx_dir = 0, 0, 0, None, None
    for r in rows:
        sym = symbol_for_row(r)

        # Çok-ufuklu notlama — gün verisi olmasa da bağımsız doldurulur.
        if r.get("horizon_filled_at") is None:
            try:
                run_ts = datetime.fromisoformat(
                    str(r["run_timestamp_utc"]).replace("Z", "+00:00"))
                h = _horizon_stats(client, sym, run_ts,
                                   _decision_price(r), r.get("predicted_bias") or "")
            except Exception as e:
                logger.warning("[bias-test] horizon fill error id=%s: %s", r.get("id"), e)
                h = None
            if h:
                (client.table("bias_test_log").eq("id", r["id"]).update(h))
                horizons_filled += 1

        if sym not in stats_cache:
            stats_cache[sym] = await _day_stats(sym, ny_date)
        stats = stats_cache[sym]
        if not stats:
            skipped += 1
            continue

        # Grading anchor: NDX = session open (legacy); others = decision price.
        raw = r.get("raw_payload") or {}
        p0 = None
        if sym != NDX and isinstance(raw, dict):
            try:
                p0 = float(raw.get("price_at_decision")) if raw.get("price_at_decision") else None
            except (TypeError, ValueError):
                p0 = None
        anchor = p0 or stats["open"]
        change_pct = round((stats["close"] - anchor) / anchor * 100.0, 3)
        actual_dir = direction_from_pct(change_pct)
        if sym == NDX:
            ndx_change, ndx_dir = change_pct, actual_dir

        predicted = r.get("predicted_bias")
        correct = predicted_matches_actual(predicted, actual_dir)
        triggered = None
        sup, resist = r.get("main_support"), r.get("main_resistance")
        if predicted == "bullish" and sup:
            triggered = stats["low"] < float(sup)
        elif predicted == "bearish" and resist:
            triggered = stats["high"] > float(resist)
        (client.table("bias_test_log").eq("id", r["id"]).update({
            "actual_close_direction": actual_dir,
            "actual_change_pct": change_pct,
            "was_correct": correct,
            "invalid_if_triggered": triggered,
            "outcome_filled_at": datetime.now(timezone.utc).isoformat(),
        }))
        updated += 1

    if updated == 0 and horizons_filled == 0 and rows:
        raise BiasTestError(f"no session/horizon data for {ny_date}")

    # CORTEX — grade the same day's NDX episodes (fail-open, NASDAQ-only).
    cortex_filled = 0
    try:
        from config import settings
        if settings.cortex_enabled and ndx_dir is not None:
            from services import cortex_memory as cortex
            cortex_filled = cortex.fill_outcomes(ny_date, ndx_dir, ndx_change)
    except Exception as e:
        logger.debug("[bias-test] CORTEX fill skipped: %s", e)

    return {"ok": True, "ny_date": ny_date, "actual_change_pct": ndx_change,
            "actual_close_direction": ndx_dir, "rows_updated": updated,
            "rows_skipped_no_data": skipped, "horizons_filled": horizons_filled,
            "cortex_episodes_filled": cortex_filled}


# ── Canlı tüketici okuyucusu (debate_bias_gate, 2026-07-18) ──────────────────
_LATEST_CACHE_TTL = 60.0
_latest_cache: dict[str, tuple[float, Optional[dict]]] = {}


def latest_bias_for_symbol(symbol: str) -> Optional[dict]:
    """Sembolün EN SON tartışma kararı (60s cache'li; fail-open → None).

    Dönen dict: bias, run_ts (datetime, UTC), age_min, run_label, confidence,
    debate_winner, main_support, main_resistance. Nötr/choppy kararlar da
    döner — ufuk/yön politikası çağıranın (signal_gates) sorumluluğudur.
    """
    now = time.monotonic()
    hit = _latest_cache.get(symbol)
    if hit and now - hit[0] < _LATEST_CACHE_TTL:
        return hit[1]
    result: Optional[dict] = None
    try:
        client = _client()
        if client is not None:
            rows = (client.table("bias_test_log").select(
                        "run_timestamp_utc,ny_date,run_label,predicted_bias,"
                        "confidence,main_support,main_resistance,raw_payload")
                    .order("run_timestamp_utc", desc=True).limit(24)
                    .execute()).get("data") or []
            for r in rows:
                if symbol_for_row(r) != symbol:
                    continue
                run_ts = datetime.fromisoformat(
                    str(r["run_timestamp_utc"]).replace("Z", "+00:00"))
                raw = r.get("raw_payload") or {}
                result = {
                    "bias": (r.get("predicted_bias") or "").lower(),
                    "run_ts": run_ts,
                    "age_min": (datetime.now(timezone.utc) - run_ts).total_seconds() / 60.0,
                    "run_label": r.get("run_label"),
                    "confidence": r.get("confidence"),
                    "debate_winner": (raw.get("debate_winner") if isinstance(raw, dict) else None),
                    "main_support": r.get("main_support"),
                    "main_resistance": r.get("main_resistance"),
                }
                break
    except Exception as e:
        logger.debug("[bias-test] latest_bias_for_symbol fail-open (%s): %s", symbol, e)
        result = None
    _latest_cache[symbol] = (now, result)
    return result


def _conf_bucket(c: float) -> str:
    if c < 60:
        return "low(<60)"
    if c < 75:
        return "med(60-75)"
    return "high(>75)"


def _rate(rows: list[dict]) -> dict[str, Any]:
    graded = [r for r in rows if r.get("was_correct") is not None]
    correct = sum(1 for r in graded if r["was_correct"])
    n = len(graded)
    return {"n": n, "correct": correct,
            "accuracy_pct": round(correct / n * 100.0, 1) if n else None}


def accuracy_report() -> dict:
    client = _client()
    if client is None:
        raise BiasTestError("db unavailable")
    rows = (client.table("bias_test_log").select("*")
            .order("ny_time", desc=True).limit(2000).execute()).get("data") or []
    # Çift-yazar kalıntıları (`*_dup`) TÜM istatistiklerden dışlanır (2026-07-30:
    # daha önce yalnız timeline şeridinden dışlanıyorlardı; by_run_label'da sahte
    # kovalar oluşturuyor ve ufuk oranlarını çift sayımla şişiriyorlardı).
    rows = [r for r in rows
            if not str(r.get("run_label") or "").endswith("_dup")]
    graded = [r for r in rows if r.get("was_correct") is not None]

    def group(key_fn):
        out: dict[str, list] = {}
        for r in graded:
            out.setdefault(str(key_fn(r)), []).append(r)
        return {k: _rate(v) for k, v in sorted(out.items())}

    def horizon_rates(rws: list[dict]) -> dict:
        """Yönlü çağrıların ufuk-bazlı isabeti (işaretli getiri > 0).

        Her hücre baseline taşır (2026-07-30): aynı satırlar üzerinde en iyi
        SABİT yönün (hep-boğa / hep-ayı) isabeti. Ham isabet dönem drift'ini de
        sayar — beceri = isabet − baseline; pozitif olmayan beceri = öngörü yok
        (EK A placebo düzeltmesi: USOIL'in '3/3'ü koşulsuz-ayı ile de tutuyordu)."""
        out = {}
        for m in HORIZONS_MIN:
            sgn = []
            raw = []
            for r in rws:
                b, v = (r.get("predicted_bias") or "").lower(), r.get(f"ret_{m}m")
                if v is None or b not in ("bullish", "bearish"):
                    continue
                sgn.append(v if b == "bullish" else -v)
                raw.append(v)
            n, w = len(sgn), sum(1 for x in sgn if x > 0)
            acc = round(w / n * 100.0, 1) if n else None
            base = None
            if n:
                up = sum(1 for x in raw if x > 0)
                base = round(max(up, n - up) / n * 100.0, 1)
            out[f"{m}m"] = {
                "n": n, "correct": w,
                "accuracy_pct": acc,
                "baseline_acc_pct": base,
                "skill_vs_baseline_pp": (round(acc - base, 1)
                                         if acc is not None and base is not None else None),
                "avg_signed_ret_pct": round(sum(sgn) / n, 3) if n else None,
                "early_observation": n < EARLY_OBS_MIN_N,
            }
        return out

    by_sym_rows: dict[str, list] = {}
    for r in rows:
        by_sym_rows.setdefault(symbol_for_row(r), []).append(r)

    def primary_block() -> dict:
        """ANA BAŞARI METRİĞİ (2026-07-18): yönlü çağrılar sembolün birincil
        ufkunda notlanır; çekimserler (nötr/choppy) AYRI izlenir ve doğruluk
        oranına karıştırılmaz (haklı çekimserlik cezalandırılmaz)."""
        out: dict[str, Any] = {"per_symbol": {}}
        tot_n = tot_w = 0
        tot_raw: list[float] = []   # genel baseline havuzu (sembol birincil ufkunda)
        for sym, rws in sorted(by_sym_rows.items()):
            m = PRIMARY_HORIZON_MIN.get(sym, 60)
            sgn = [x for x in (signed_ret(r, m) for r in rws) if x is not None]
            n, w = len(sgn), sum(1 for x in sgn if x > 0)
            acc = round(w / n * 100.0, 1) if n else None
            # Baseline (2026-07-30): aynı yönlü satırlar üzerinde en iyi SABİT
            # yönün isabeti. Beceri = isabet − baseline; ham yüzde tek başına
            # dönem drift'ini de saydığı için beceri sayılmaz.
            raw_prim = []
            for r in rws:
                b, v = (r.get("predicted_bias") or "").lower(), r.get(f"ret_{m}m")
                if v is not None and b in ("bullish", "bearish"):
                    raw_prim.append(v)
            base = None
            if n:
                up = sum(1 for x in raw_prim if x > 0)
                base = round(max(up, n - up) / n * 100.0, 1)
            ab_rows = [r for r in rws
                       if (r.get("predicted_bias") or "").lower() not in ("bullish", "bearish")]
            ab_meas = [r for r in ab_rows if r.get("actual_change_pct") is not None]
            quiet = [r for r in ab_meas if abs(r["actual_change_pct"]) < ABSTAIN_QUIET_PCT]
            # Zaman şeridi (panel ısı-şeridi): kronolojik son 20 karar —
            # yeşil/kırmızı (yönlü isabet/ıska, birincil ufukta) + gri (çekimser).
            # '_dup' etiketli çift-yazar satırlar istatistik dışı (2026-07-18).
            timeline: list[dict] = []
            for r in sorted(rws, key=lambda x: str(x.get("ny_time") or "")):
                if str(r.get("run_label") or "").endswith("_dup"):
                    continue
                bias_val = (r.get("predicted_bias") or "").lower()
                if bias_val in ("bullish", "bearish"):
                    sv = signed_ret(r, m)
                    if sv is None:
                        continue  # yönlü ama henüz notlanmamış — şeride girmez
                    timeline.append({"d": str(r.get("ny_date") or "")[:10],
                                     "ok": sv > 0,
                                     "bias": bias_val,
                                     "label": r.get("run_label")})
                else:
                    timeline.append({"d": str(r.get("ny_date") or "")[:10],
                                     "ok": None, "bias": bias_val or "neutral",
                                     "label": r.get("run_label")})
            out["per_symbol"][sym] = {
                "horizon_min": m, "n": n, "correct": w,
                "accuracy_pct": acc,
                "baseline_acc_pct": base,
                "skill_vs_baseline_pp": (round(acc - base, 1)
                                         if acc is not None and base is not None else None),
                "early_observation": n < EARLY_OBS_MIN_N,
                "avg_signed_ret_pct": round(sum(sgn) / n, 3) if n else None,
                "abstain_n": len(ab_rows),
                "abstain_rate_pct": round(len(ab_rows) / len(rws) * 100.0, 1) if rws else None,
                "abstain_quiet_day_pct": (round(len(quiet) / len(ab_meas) * 100.0, 1)
                                          if ab_meas else None),
                "timeline": timeline[-20:],
            }
            tot_n += n
            tot_w += w
            tot_raw.extend(raw_prim)
        tot_acc = round(tot_w / tot_n * 100.0, 1) if tot_n else None
        tot_base = None
        if tot_raw:
            up = sum(1 for x in tot_raw if x > 0)
            tot_base = round(max(up, len(tot_raw) - up) / len(tot_raw) * 100.0, 1)
        out["overall"] = {"n": tot_n, "correct": tot_w,
                          "accuracy_pct": tot_acc,
                          "baseline_acc_pct": tot_base,
                          "skill_vs_baseline_pp": (round(tot_acc - tot_base, 1)
                                                   if tot_acc is not None and tot_base is not None else None),
                          "early_observation": tot_n < EARLY_OBS_MIN_N}
        return out

    def direction_balance() -> dict:
        """YÖN DAĞILIMI İZLEME (2026-07-30) — SYMMETRY RULE işe yarıyor mu?
        Sembol başına ayı/boğa çağrı sayısı + yöne göre birincil-ufuk isabeti.
        07-26 denetimi: 32 yönlü çağrının 25'i ayıydı (binom p=0.002) ve ayı
        çağrıları −EV üretiyordu; bu blok yanlılığın kırılıp kırılmadığını ölçer."""
        out: dict[str, Any] = {}
        for sym, rws in sorted(by_sym_rows.items()):
            m = PRIMARY_HORIZON_MIN.get(sym, 60)
            entry: dict[str, Any] = {}
            for side in ("bearish", "bullish"):
                sgn = [x for x in (signed_ret(r, m) for r in rws
                                   if (r.get("predicted_bias") or "").lower() == side)
                       if x is not None]
                w = sum(1 for x in sgn if x > 0)
                entry[side] = {
                    "n": len(sgn),
                    "accuracy_pct": round(w / len(sgn) * 100.0, 1) if sgn else None,
                    "avg_signed_ret_pct": round(sum(sgn) / len(sgn), 3) if sgn else None,
                }
            tot = entry["bearish"]["n"] + entry["bullish"]["n"]
            entry["bearish_share_pct"] = (round(entry["bearish"]["n"] / tot * 100.0, 1)
                                          if tot else None)
            out[sym] = entry
        return out

    return {
        "total_graded": len(graded),
        "primary_intraday": primary_block(),
        "direction_balance": direction_balance(),
        "overall": _rate(graded),
        "by_horizon": horizon_rates(rows),
        "by_symbol_horizon": {s: horizon_rates(v) for s, v in sorted(by_sym_rows.items())},
        "by_symbol": group(symbol_for_row),
        "by_run_label": group(lambda r: r.get("run_label")),
        "by_confidence_bucket": group(lambda r: _conf_bucket(float(r.get("confidence") or 0))),
        "by_session_overlap": group(lambda r: r.get("session_overlap")),
        "by_half_day": group(lambda r: r.get("is_half_day")),
        "by_holiday": group(lambda r: r.get("is_holiday")),
        "by_current_session": group(lambda r: r.get("current_session")),
        "go_live_hint": (
            "ANA METRİK: primary_intraday (sembolün birincil ufkunda yönlü isabet; "
            "çekimserler ayrı). Canlıya bağlama eşiği: n≥30 VE skill_vs_baseline_pp "
            "açık pozitif (ham isabet değil — baseline dönem drift'ini ayıklar). "
            "early_observation=true hücreler (n<30) kanıt değildir. "
            "overall/by_* gün-kapanışı LEGACY metriktir. '*_dup' satırlar tüm "
            "istatistiklerden dışlanır."
        ),
    }
