"""Gölge Modu paneli — sistemde GÖLGE çalışan her şeyin tek karnesi.

Sistemde "gölge" (shadow) demek: **karar üretiliyor ve kaydediliyor ama canlı
akışa müdahale etmiyor**. Üç ayrı aile var ve bugüne kadar hiçbiri tek yerde
görünmüyordu:

1. **Gölge kapılar** (`services/signal_gates.py`, ``*_GATE_BLOCK=0``) — kapı
   "bloklardım" der, sinyal yine de geçer. Verdikt 2026-08-26'dan beri
   ``prediction_logs.factors.shadow_gates`` içine yazılır (bkz.
   ``signal_gates._shadow_verdict``). Bu panel o verdiktleri sinyalin GERÇEK
   sonucuyla eşleştirir → "kapıyı açsam ne kazanırdım?" sorusunun cevabı.
2. **Gölge modeller** (``<model>_inv`` ters sinyaller + ``ml_cross_*`` deneyi)
   — prediction_logs'a normal satır olarak yazılır ama işleme dönüşmez.
3. **Gölge işlemler** (``shadow_pattern_trades``) — formasyon / fakeout
   dedektörü / meta sinyallerinin sızıntısız kâğıt-işlem doğrulaması.

Ölçüm kanonu ``services.signal_metrics``tir: çıplak WR yasak — her satır
beklenti (R), başabaş WR ve epoch kırılımıyla birlikte döner.

**Karar okuması (kritik):** bir gölge kapının "iyi" olması, engelleyeceği
sinyallerin KAYBETMESİ demektir. Bu yüzden ``verdict`` alanı bloklanan kümenin
beklentisine bakar: negatifse kapı değerlidir (``ac`` = aç), pozitifse kapı
kazandıran sinyalleri keserdi (``acma`` = açma).
"""

from __future__ import annotations

import logging
import os
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client, is_db_available
from services.signal_metrics import aggregate_outcomes, summarize_for_panel

logger = logging.getLogger(__name__)

#: PostgREST tek istekte en fazla 1000 satır döndürür.
_PAGE = 1000
#: Kapı/model karnesi için üst tavan (sayfalanarak çekilir).
_MAX_ROWS = 6000

#: Hedef/stop oranı bunun üstündeyse geometri BOZUK sayılır: stop girişe
#: yapışıktır, işlem yapısal olarak kayıptır. Ortalama RR bu kuyruk yüzünden
#: kullanılamaz (2026-08-26 bulgusu: formasyon kayıplarında ort. RR 21,95).
_DEGENERATE_RR = 5.0

#: Bir gölge kapının verdiktini "kanıtlı" saymak için gereken minimum
#: çözülmüş sinyal sayısı. Altındaki her şey "veri birikiyor" olarak döner.
MIN_N_FOR_VERDICT = 30

#: Gölge kapıların insan-okur künyesi. `flag` = gerçekten bloklamaya geçiren
#: env değişkeni; `enabled_flag` = kapının hiç çalışıp çalışmadığı.
SHADOW_GATES: Dict[str, Dict[str, str]] = {
    "entry_score_gate": {
        "label": "Giriş Skoru",
        "flag": "ENTRY_SCORE_GATE_BLOCK",
        "enabled_flag": "ENTRY_SCORE_GATE_ENABLED",
        "note": "8 koşullu giriş skoru < eşik. Bot tarafında sızıntısız canlı "
                "ölçüm kapının ALEYHİNE çıkmıştı (2026-08-11) — panel tarafı "
                "yeniden ölçülüyor.",
    },
    "fakeout_gate": {
        "label": "Sahte Kırılım",
        "flag": "FAKEOUT_GATE_BLOCK",
        "enabled_flag": "FAKEOUT_GATE_ENABLED",
        "note": "Dedektör kırılımı SAHTE çağırdı. Dedektörün kendi OOS karnesi "
                "yalnız NDX'te %70/%70 doğrulandı.",
    },
    "debate_bias_gate": {
        "label": "Tartışma Biası",
        "flag": "DEBATE_BIAS_GATE_BLOCK",
        "enabled_flag": "DEBATE_BIAS_GATE_ENABLED",
        "note": "Günlük tartışma kararına KARŞIT sinyal freni (NDX+USOIL).",
    },
    "trend_align_gate": {
        "label": "1h Trend Hizası",
        "flag": "TREND_ALIGN_GATE_BLOCK",
        "enabled_flag": "TREND_ALIGN_GATE_ENABLED",
        "note": "NDX pulse sinyali 1h EMA50'ye karşıt. Bot tarafı 30g/332: "
                "hizalı %63,3 vs karşıt %43,4.",
    },
    "wave_position_gate": {
        "label": "Dalga Pozisyonu",
        "flag": "WAVE_POSITION_GATE_BLOCK",
        "enabled_flag": "WAVE_POSITION_GATE_ENABLED",
        "note": "4h dalganın tepesinde BUY / dibinde SELL.",
    },
    "vix_regime_gate": {
        "label": "VIX Rejimi",
        "flag": "VIX_REGIME_GATE_BLOCK",
        "enabled_flag": "VIX_REGIME_GATE_ENABLED",
        "note": "VIX rejimine karşıt yön. 2026-08-01'de BLOĞA alındı — burada "
                "görünüyorsa bayrak gölgeye çekilmiş demektir.",
    },
    "xau_scalp_gate": {
        "label": "XAU Scalp",
        "flag": "XAU_SCALP_GATE_BLOCK",
        "enabled_flag": "XAU_SCALP_GATE_ENABLED",
        "note": "XAUUSD pulse/smc scalp sinyalleri (statik-SL epoch'unda %16-18 WR).",
    },
    "time_quality_gate": {
        "label": "Zaman Kalitesi",
        "flag": "TQ_GATE_BLOCK",
        "enabled_flag": "TQ_GATE_ENABLED",
        "note": "Çukur saat/gün penceresinde düşük güvenli sinyal.",
    },
}

#: Gölge model aileleri — prediction_logs.model_type deseni.
SHADOW_MODEL_FAMILIES: Dict[str, Dict[str, str]] = {
    "inverse": {
        "label": "Ters Sinyal (inversion)",
        "note": "Canlı sinyalin tam tersi gölge satır. Ana modelin anti-kenarı "
                "varsa burada görünür; işleme DÖNÜŞMEZ.",
    },
    "ml_cross": {
        "label": "Çapraz ML Deneyi",
        "note": "ml_cross_xau_nasdaq — SELL %6,9 WR kanıtıyla kapatılması "
                "gereken deney (CROSS_MODEL_EXPERIMENT_ENABLED=0).",
    },
}


#: Panel canlı polling yapar (30 sn) ama bu raporlar 6000 satıra kadar çekiyor
#: (~15 sn). TTL cache olmadan her poll DB'yi döverdi. TTL polling aralığından
#: kısa tutulur ki "anlık" hissi bozulmasın.
_CACHE_TTL_S = 45
_cache: Dict[str, tuple] = {}


def _cached(key: str, ttl: int = _CACHE_TTL_S):
    """Basit TTL cache dekoratör-üreticisi (sync fonksiyonlar için)."""
    def wrap(fn):
        def inner(*args, **kwargs):
            ck = f"{key}:{args}:{sorted(kwargs.items())}"
            hit = _cache.get(ck)
            now = datetime.now(timezone.utc).timestamp()
            if hit and now - hit[0] < ttl:
                return hit[1]
            val = fn(*args, **kwargs)
            _cache[ck] = (now, val)
            return val
        inner.__name__ = fn.__name__
        inner.__doc__ = fn.__doc__
        inner.cache_clear = lambda: _cache.clear()  # type: ignore[attr-defined]
        return inner
    return wrap


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _client():
    if not is_db_available():
        raise RuntimeError("Supabase erişilemiyor")
    return get_supabase_client()


def _flag_on(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).strip().lower() in ("1", "true", "yes", "on")


def _fetch_paged(table: str, columns: str, since_col: str, since: str,
                 extra: Optional[List[str]] = None,
                 max_rows: int = _MAX_ROWS) -> List[dict]:
    """Sayfalı çekim — PostgREST 1000 satır tavanını aşmak için.

    `extra` ham PostgREST filtre ifadeleri listesi (bkz. TableQuery.raw_filter).
    """
    client = _client()
    rows: List[dict] = []
    for start in range(0, max_rows, _PAGE):
        q = (client.table(table).select(columns)
             .gte(since_col, since).order(since_col, desc=True))
        for f in extra or []:
            q = q.raw_filter(f)
        chunk = (q.range(start, start + _PAGE - 1).execute().get("data")) or []
        rows.extend(chunk)
        if len(chunk) < _PAGE:
            break
    return rows


# ── 1) Gölge kapılar ─────────────────────────────────────────────────────────

_SIGNAL_COLUMNS = (
    "id,created_at,symbol,model_type,status,ml_direction,ml_entry_price,"
    "ml_target_price,ml_stop_price,targets,targets_hit,stop_loss_pips,"
    "highest_profit_pips,lowest_drawdown_pips,exit_price,exit_time,"
    "resolution_reason,close_reason,factors"
)


def _gate_verdict(metrics: Dict[str, Any], n: int) -> Dict[str, Any]:
    """Bloklanacak kümenin karnesinden kapı kararı üret.

    Kapı, engelleyeceği sinyaller KAYBEDİYORSA değerlidir. Karar metriği
    beklenti (R) — WR değil: RR<1 geometride %55 WR bile net kayıptır.
    """
    exp = metrics.get("expectancy_r")
    if n < MIN_N_FOR_VERDICT or exp is None:
        return {
            "code": "veri_yok",
            "label": "Veri birikiyor",
            "detail": f"{n}/{MIN_N_FOR_VERDICT} çözülmüş sinyal — karar için yetersiz.",
        }
    if exp <= -0.10:
        return {
            "code": "ac",
            "label": "Kapıyı AÇ",
            "detail": f"Bloklayacağı {n} sinyal ortalama {exp:+.3f}R kaybettirmiş — "
                      "kapı gerçek bir fren.",
        }
    if exp >= 0.10:
        return {
            "code": "acma",
            "label": "AÇMA",
            "detail": f"Bloklayacağı {n} sinyal ortalama {exp:+.3f}R KAZANDIRMIŞ — "
                      "kapı kazandıran sinyalleri keserdi.",
        }
    return {
        "code": "notr",
        "label": "Nötr",
        "detail": f"Bloklayacağı {n} sinyalin beklentisi {exp:+.3f}R — "
                  "sıfıra yakın, kapının ölçülebilir katkısı yok.",
    }


@_cached("gates")
def get_shadow_gate_report(days: int = 30) -> Dict[str, Any]:
    """Gölge kapıların "açsam ne olurdu" karnesi.

    Kaynak: ``prediction_logs.factors.shadow_gates`` (2026-08-26'dan itibaren
    yazılıyor). Her kapı için o kapının bloklayacağı sinyallerin kanonik
    karnesi + kapıyı açma/açmama verdikti döner.
    """
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged(
        "prediction_logs", _SIGNAL_COLUMNS, "created_at", since,
        extra=["factors->shadow_gates=not.is.null"],
    )

    by_gate: Dict[str, List[dict]] = {}
    for r in rows:
        factors = r.get("factors") or {}
        if not isinstance(factors, dict):
            continue
        for gate in factors.get("shadow_gates") or []:
            by_gate.setdefault(str(gate), []).append(r)

    gates: List[Dict[str, Any]] = []
    for gate_id, meta in SHADOW_GATES.items():
        blocked = by_gate.get(gate_id, [])
        metrics = summarize_for_panel(aggregate_outcomes(blocked))
        blocking_live = _flag_on(meta["flag"], "1" if gate_id == "vix_regime_gate"
                                 or gate_id == "time_quality_gate" else "0")
        gates.append({
            "id": gate_id,
            "label": meta["label"],
            "note": meta["note"],
            "flag": meta["flag"],
            "enabled": _flag_on(meta["enabled_flag"], "1"),
            "blocking": blocking_live,
            "mode": "BLOK" if blocking_live else "GÖLGE",
            "would_block_total": len(blocked),
            "metrics": metrics,
            "verdict": _gate_verdict(metrics, metrics.get("n") or 0),
            "recent": [
                {
                    "id": b.get("id"),
                    "at": b.get("created_at"),
                    "symbol": b.get("symbol"),
                    "model": b.get("model_type"),
                    "direction": b.get("ml_direction"),
                    "status": b.get("status"),
                    "reason": ((b.get("factors") or {}).get("shadow_gate_reasons")
                               or {}).get(gate_id),
                }
                for b in blocked[:15]
            ],
        })

    gates.sort(key=lambda g: (-(g["metrics"].get("n") or 0), g["label"]))
    measured = [g for g in gates if (g["metrics"].get("n") or 0) >= MIN_N_FOR_VERDICT]
    return {
        "days": days,
        "signals_with_shadow_verdict": len(rows),
        "gates": gates,
        "measured_gates": len(measured),
        "since_instrumented": "2026-08-26",
        "note": ("Gölge kapı verdiktleri 2026-08-26'da yazılmaya başlandı — "
                 "bu tarihten ÖNCEKİ sinyallerde kayıt yoktur."),
    }


# ── 2) Gölge modeller ────────────────────────────────────────────────────────

def _model_family(model_type: str) -> Optional[str]:
    m = (model_type or "").lower()
    if m.startswith("ml_cross"):
        return "ml_cross"
    if m.endswith("_inv") or m == "emel_inverse":
        return "inverse"
    return None


@_cached("models")
def get_shadow_model_report(days: int = 30) -> Dict[str, Any]:
    """Gölge model ailelerinin (ters sinyal + çapraz ML) kanonik karnesi."""
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged("prediction_logs", _SIGNAL_COLUMNS, "created_at", since)

    families: Dict[str, Dict[str, List[dict]]] = {}
    for r in rows:
        fam = _model_family(r.get("model_type") or "")
        if not fam:
            continue
        families.setdefault(fam, {}).setdefault(r.get("model_type") or "?", []).append(r)

    out: List[Dict[str, Any]] = []
    for fam_id, meta in SHADOW_MODEL_FAMILIES.items():
        buckets = families.get(fam_id, {})
        all_rows = [r for rs in buckets.values() for r in rs]
        models = [
            {
                "model_type": mt,
                "total": len(rs),
                "metrics": summarize_for_panel(aggregate_outcomes(rs)),
            }
            for mt, rs in sorted(buckets.items(), key=lambda kv: -len(kv[1]))
        ]
        out.append({
            "id": fam_id,
            "label": meta["label"],
            "note": meta["note"],
            "total": len(all_rows),
            "metrics": summarize_for_panel(aggregate_outcomes(all_rows)),
            "models": models,
        })

    # ml_cross kill-switch denetimi: bayrak 0 iken satır GELMEMELİ.
    cross_rows = sum(len(rs) for rs in families.get("ml_cross", {}).values())
    alerts: List[Dict[str, str]] = []
    if cross_rows and not _flag_on("CROSS_MODEL_EXPERIMENT_ENABLED", "0"):
        alerts.append({
            "level": "warn",
            "text": (f"CROSS_MODEL_EXPERIMENT_ENABLED=0 olmasına rağmen son {days} "
                     f"günde {cross_rows} ml_cross satırı yazılmış — bu satırları "
                     "yazan süreç eski kodda ya da bayrağı 1 olan bir ortamda."),
        })

    return {"days": days, "families": out, "alerts": alerts}


# ── 3) Gölge işlemler (shadow_pattern_trades) ────────────────────────────────

_SHADOW_SOURCE_LABELS = {
    "pattern": "Formasyon Dedektörü",
    "fakeout": "Sahte Kırılım Dedektörü",
    "meta": "Meta Sinyal",
}


@_cached("trades")
def get_shadow_trade_report(days: int = 30) -> Dict[str, Any]:
    """``shadow_pattern_trades`` — sızıntısız kâğıt-işlem karnesi.

    Bu tablo TP/SL'i açıkça kaydettiği için WR doğrudan R'ye çevrilebilir
    (geometri bilindiğinden başabaş WR = 1/(1+RR)).
    """
    since = (_now() - timedelta(days=days)).isoformat()
    rows = _fetch_paged(
        "shadow_pattern_trades",
        "id,created_at,exit_time,source,symbol,timeframe,direction,pattern_type,"
        "pattern_name,confidence,entry_price,tp_price,sl_price,status,exit_price,"
        "r_multiple,ambiguous",
        "created_at", since,
    )

    def _bucket() -> Dict[str, Any]:
        return {"n": 0, "wins": 0, "losses": 0, "expired": 0, "open": 0,
                "ambiguous": 0, "rr": [], "r_sum": 0.0, "r_n": 0, "degenerate": 0}

    def _close(b: Dict[str, Any], label: str, key: str) -> Dict[str, Any]:
        resolved = b["wins"] + b["losses"]
        # RR ORTALAMASI KULLANILMAZ: bozuk geometrili (stop'u sıfıra yakın)
        # işlemler ortalamayı 15-22'ye çekip başabaş çıtasını %6'ya düşürüyor
        # ve "kenar var" yanılsaması üretiyordu. Medyan bu kuyruğa dayanıklı.
        rr_vals = sorted(b["rr"])
        rr = round(statistics.median(rr_vals), 2) if rr_vals else None
        wr = round(100 * b["wins"] / resolved, 1) if resolved else None
        be = round(100 / (1 + rr), 1) if rr else None
        # Beklenti tabloda KAYITLI r_multiple'dan gelir (geometriden türetmek
        # yerine) — kısmi çıkış/aynı-bar belirsizliği orada zaten işlenmiş.
        # Kararın ASIL metriği budur; WR yalnızca yanında okunur.
        exp = round(b["r_sum"] / b["r_n"], 3) if b["r_n"] else None
        warnings: List[str] = []
        if b["degenerate"]:
            share = round(100 * b["degenerate"] / b["n"], 1)
            warnings.append(
                f"{b['degenerate']} işlemin ({share}%) stop mesafesi hedefin "
                f"{int(_DEGENERATE_RR)}'de birinden küçük — bu geometri yapısal "
                "kayıptır, dedektörün seviye hesabı gözden geçirilmeli.")
        if wr is not None and be is not None and exp is not None:
            if wr > be and exp < 0:
                warnings.append(
                    "WR başabaşın üstünde ama beklenti NEGATİF — kazançlar "
                    "kayıpları karşılamıyor, çıplak WR'a güvenme.")
        return {
            "key": key, "label": label,
            "total": b["n"], "resolved": resolved,
            "wins": b["wins"], "losses": b["losses"],
            "expired": b["expired"], "open": b["open"],
            "ambiguous": b["ambiguous"], "degenerate": b["degenerate"],
            "win_rate": wr, "median_rr": rr, "breakeven_wr": be,
            "expectancy_r": exp, "total_r": round(b["r_sum"], 2),
            "edge_pp": round(wr - be, 1) if (wr is not None and be is not None) else None,
            "warnings": warnings,
        }

    by_source: Dict[str, Dict[str, Any]] = {}
    by_source_symbol: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_source_direction: Dict[str, Dict[str, Dict[str, Any]]] = {}
    recent: List[dict] = []

    for r in rows:
        src = r.get("source") or "?"
        status = (r.get("status") or "").lower()
        entry, tp, sl = r.get("entry_price"), r.get("tp_price"), r.get("sl_price")
        rr = None
        try:
            if entry and tp and sl and abs(entry - sl) > 0:
                rr = abs(tp - entry) / abs(entry - sl)
        except (TypeError, ValueError):
            rr = None

        targets = [
            by_source.setdefault(src, _bucket()),
            by_source_symbol.setdefault(src, {}).setdefault(r.get("symbol") or "?", _bucket()),
            by_source_direction.setdefault(src, {}).setdefault(
                (r.get("direction") or "?").upper(), _bucket()),
        ]
        for b in targets:
            b["n"] += 1
            if status == "win":
                b["wins"] += 1
            elif status == "loss":
                b["losses"] += 1
            elif status == "open":
                b["open"] += 1
            else:
                b["expired"] += 1
            if rr:
                b["rr"].append(rr)
                if rr > _DEGENERATE_RR:
                    b["degenerate"] += 1
            if r.get("ambiguous"):
                b["ambiguous"] += 1
            rm = r.get("r_multiple")
            if rm is not None and status in ("win", "loss"):
                try:
                    b["r_sum"] += float(rm)
                    b["r_n"] += 1
                except (TypeError, ValueError):
                    pass

        if len(recent) < 40:
            recent.append({
                "at": r.get("created_at"), "resolved_at": r.get("exit_time"),
                "source": src, "symbol": r.get("symbol"),
                "direction": (r.get("direction") or "").upper(),
                "pattern": r.get("pattern_name") or r.get("pattern_type"),
                "timeframe": r.get("timeframe"),
                "confidence": r.get("confidence"), "status": status,
                "entry": entry, "tp": tp, "sl": sl, "exit": r.get("exit_price"),
                "r": r.get("r_multiple"), "ambiguous": bool(r.get("ambiguous")),
                "rr": round(rr, 2) if rr else None,
            })

    sources = []
    for src, b in sorted(by_source.items(), key=lambda kv: -kv[1]["n"]):
        item = _close(b, _SHADOW_SOURCE_LABELS.get(src, src), src)
        item["by_symbol"] = [
            _close(v, k, k) for k, v in
            sorted(by_source_symbol.get(src, {}).items(), key=lambda kv: -kv[1]["n"])
        ]
        item["by_direction"] = [
            _close(v, k, k) for k, v in
            sorted(by_source_direction.get(src, {}).items(), key=lambda kv: -kv[1]["n"])
        ]
        sources.append(item)

    return {
        "days": days,
        "total": len(rows),
        "enabled": _flag_on("SHADOW_TRACKER_ENABLED", "1"),
        "sources": sources,
        "recent": recent,
        "last_at": rows[0].get("created_at") if rows else None,
    }


# ── 4) Bayrak künyesi ────────────────────────────────────────────────────────

def get_shadow_flags() -> Dict[str, Any]:
    """Gölge/blok bayraklarının canlı durumu — "ne gölgede, ne canlıda"."""
    items = []
    for gate_id, meta in SHADOW_GATES.items():
        block_default = "1" if gate_id in ("vix_regime_gate", "time_quality_gate") else "0"
        enabled = _flag_on(meta["enabled_flag"], "1")
        blocking = _flag_on(meta["flag"], block_default)
        items.append({
            "id": gate_id, "label": meta["label"],
            "enabled_flag": meta["enabled_flag"], "block_flag": meta["flag"],
            "enabled": enabled, "blocking": blocking,
            "mode": "KAPALI" if not enabled else ("BLOK" if blocking else "GÖLGE"),
        })
    extras = [
        ("PULSE_SHADOW_INVERSION_ENABLED", "Ters sinyal gölge loglaması", "1"),
        ("SHADOW_TRACKER_ENABLED", "Gölge işlem izleyici", "1"),
        ("CROSS_MODEL_EXPERIMENT_ENABLED", "Çapraz ML deneyi", "0"),
        ("PATTERN_BONUS_GATE_ENABLED", "Formasyon bonus kapısı", "1"),
    ]
    return {
        "gates": sorted(items, key=lambda x: (x["mode"] != "GÖLGE", x["label"])),
        "experiments": [
            {"flag": f, "label": lbl, "on": _flag_on(f, d)} for f, lbl, d in extras
        ],
    }


# ── Toplu görünüm ────────────────────────────────────────────────────────────

def get_shadow_overview(days: int = 30) -> Dict[str, Any]:
    """Gölge Modu panelinin tek çağrılık verisi (her blok fail-soft)."""
    out: Dict[str, Any] = {"days": days, "generated_at": _now().isoformat(), "errors": []}

    for key, fn in (
        ("gates", lambda: get_shadow_gate_report(days)),
        ("models", lambda: get_shadow_model_report(days)),
        ("trades", lambda: get_shadow_trade_report(days)),
        ("flags", get_shadow_flags),
    ):
        try:
            out[key] = fn()
        except Exception as exc:  # fail-soft: bir blok patlasa panel açılsın
            logger.warning("shadow_overview.%s başarısız: %s", key, exc)
            out[key] = None
            out["errors"].append({"block": key, "error": str(exc)[:200]})

    return out
