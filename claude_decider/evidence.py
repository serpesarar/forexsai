"""
evidence.py — "Veteran'ın hafızası": koşullu base-rate tabloları + canlı kanıt-paketi.
=============================================================================
Kanıt-temelli özerklik (kullanıcı seçimi 2026-06-27): Opus kendi görüşünü oluşturur AMA
her karar geçmiş verimizle beslenir. Bu modül, 97k/21.5k deduped sinyalden per
(sembol×yön × feature-kovası) koşullu WR tabloları üretir (offline), canlı durumda
ilgili hücreleri çekip Opus'a "bu duruma benzer geçmişte WR neydi" kanıtı sunar.

Folklor değil kanıt: Opus grafiğe değil, BİZİM istatistiğimize dayanır.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from channel_filter import channel_zscore, vwap_zscore  # noqa: E402

# evidence_tables.json çalışma-zamanında (bot makinesi) okunur; HERE-relative → taşınabilir.
TABLES = HERE / "evidence_tables.json"
# features.jsonl YALNIZ build_tables (offline, Mac) için — bot makinesinde gerekmez.
FEATURES = HERE.parent / "sr_rejection_research" / "data" / "features.jsonl"

REV_EDGES = [-99, 0.0, 1.0, 1.5, 2.0, 2.5, 3.0, 99]
ADX_EDGES = [0, 18, 25, 35, 999]
MIN_CELL = 15          # bir hücre raporlanması için min örnek (gürültü engeli)
WIN_N = 50             # canlı linreg/vwap penceresi (gates ile aynı)


def _bucket(v, edges):
    for i in range(len(edges) - 1):
        if edges[i] <= v < edges[i + 1]:
            lo, hi = edges[i], edges[i + 1]
            return f"{lo:g}–{hi:g}" if hi < 90 else f">{lo:g}"
    return None


def _session(hour):  # UTC
    if 13 <= hour < 21:
        return "NY"
    if 7 <= hour < 13:
        return "Londra"
    if 0 <= hour < 7:
        return "Asya"
    return "kapanış"


def _cell(wins):
    n = len(wins)
    return {"wr": round(100 * sum(wins) / n), "n": n} if n >= MIN_CELL else None


# ── OFFLINE: koşullu tabloları kur ───────────────────────────────────────────
def build_tables() -> dict:
    recs = [json.loads(l) for l in open(FEATURES)]
    recs.sort(key=lambda r: r["t"])
    # dedup 60dk/kurulum (model,sembol,yön) — sonra (sembol,yön) altında topla
    last = {}; rows = []
    for r in recs:
        k = (r["model"], r["symbol"], r["dir"]); t = datetime.fromisoformat(r["t"]).timestamp()
        if k in last and t - last[k] <= 3600:
            continue
        last[k] = t
        f5 = r["f"].get("5m")
        if not f5:
            continue
        buy = r["dir"] == "BUY"
        c = (f5.get("chan") or {}).get("50") or (f5.get("chan") or {}).get(50)
        rc = ((-c["pm"] / c["spp"]) if buy else (c["pm"] / c["spp"])) if c and c["spp"] > 1e-9 else None
        rv = None
        if f5.get("vwap"):
            vz = f5["vwap"]["vwap_z"]; rv = (-vz) if buy else vz
        rows.append({"symbol": r["symbol"], "dir": r["dir"], "win": bool(r["win"]),
                     "t": t, "rc": rc, "rv": rv, "adx": f5.get("adx"),
                     "hour": datetime.fromisoformat(r["t"]).astimezone(timezone.utc).hour})

    by = {}
    for r in rows:
        by.setdefault((r["symbol"], r["dir"]), []).append(r)

    tables = {}
    for (sym, d), sel in by.items():
        sel.sort(key=lambda x: x["t"])
        split = sel[int(0.6 * len(sel))]["t"] if len(sel) > 10 else None

        def cell_oos(items):
            c = _cell([x["win"] for x in items])
            if c and split:
                oos = [x["win"] for x in items if x["t"] >= split]
                if len(oos) >= MIN_CELL:
                    c["oos_wr"] = round(100 * sum(oos) / len(oos)); c["oos_n"] = len(oos)
            return c

        gate = [x for x in sel if (x["rc"] is not None and x["rc"] > 2.0) or (x["rv"] is not None and x["rv"] > 1.5)]
        t = {"base": cell_oos(sel), "gate": cell_oos(gate), "rev_chan": {}, "rev_vwap": {}, "adx": {}, "session": {}}
        for key, fld, edges in [("rev_chan", "rc", REV_EDGES), ("rev_vwap", "rv", REV_EDGES), ("adx", "adx", ADX_EDGES)]:
            buckets = {}
            for x in sel:
                if x[fld] is None:
                    continue
                b = _bucket(x[fld], edges)
                if b:
                    buckets.setdefault(b, []).append(x["win"])
            t[key] = {b: _cell(w) for b, w in buckets.items() if _cell(w)}
        sess = {}
        for x in sel:
            sess.setdefault(_session(x["hour"]), []).append(x["win"])
        t["session"] = {s: _cell(w) for s, w in sess.items() if _cell(w)}
        tables[f"{sym}|{d}"] = t

    TABLES.write_text(json.dumps(tables, ensure_ascii=False, indent=1), encoding="utf-8")
    return tables


def load_tables() -> dict:
    return json.loads(TABLES.read_text(encoding="utf-8")) if TABLES.exists() else {}


# ── CANLI: feature vektörü + kanıt-paketi ────────────────────────────────────
def live_features(bars: list[dict], direction: str, vix: float | None = None) -> dict:
    """Canlı 5m bardan yön-hizalı feature vektörü (rev_chan, rev_vwap, adx, session)."""
    buy = direction.upper() == "BUY"
    closes = [b["close"] for b in bars]
    cz = channel_zscore(closes, WIN_N)
    vz = vwap_zscore(bars, WIN_N)
    rc = (-cz if buy else cz) if cz is not None else None
    rv = (-vz if buy else vz) if vz is not None else None
    highs = [b["high"] for b in bars]; lows = [b["low"] for b in bars]
    adx = _adx(highs, lows, closes)
    atr = _atr(highs, lows, closes)
    now = datetime.now(timezone.utc)
    return {"rev_chan": round(float(rc), 2) if rc is not None else None,
            "rev_vwap": round(float(rv), 2) if rv is not None else None,
            "adx": round(float(adx), 1) if adx is not None else None,
            "atr": round(float(atr), 5) if atr is not None else None,
            "session": _session(now.hour),
            "gate_fired": bool((rc is not None and rc > 2.0) or (rv is not None and rv > 1.5))}


def evidence_pack(symbol: str, direction: str, lf: dict, tables: dict | None = None) -> dict:
    """Canlı duruma uyan geçmiş hücreleri çek → Opus'a kanıt. 'Benzer geçmişte WR neydi'."""
    tables = tables or load_tables()
    t = tables.get(f"{symbol}|{direction}")
    if not t:
        return {"note": "bu sembol/yön için geçmiş kanıt yok"}
    pack = {"base": t.get("base"), "gate_setup": t.get("gate")}
    if lf.get("rev_chan") is not None:
        b = _bucket(lf["rev_chan"], REV_EDGES)
        pack["rev_chan_bucket"] = {"bucket": b, "hist": t["rev_chan"].get(b)}
    if lf.get("rev_vwap") is not None:
        b = _bucket(lf["rev_vwap"], REV_EDGES)
        pack["rev_vwap_bucket"] = {"bucket": b, "hist": t["rev_vwap"].get(b)}
    if lf.get("adx") is not None:
        b = _bucket(lf["adx"], ADX_EDGES)
        pack["adx_bucket"] = {"bucket": b, "hist": t["adx"].get(b)}
    if lf.get("session"):
        pack["session"] = {"now": lf["session"], "hist": t["session"].get(lf["session"])}
    return pack


def _adx(highs, lows, closes, n=14):
    if len(closes) < n + 1:
        return None
    trs, pdm, ndm = [], [], []
    for i in range(1, len(closes)):
        up, dn = highs[i] - highs[i - 1], lows[i - 1] - lows[i]
        pdm.append(up if (up > dn and up > 0) else 0.0)
        ndm.append(dn if (dn > up and dn > 0) else 0.0)
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    if len(trs) < n:
        return None

    def _rma(x):
        r = sum(x[:n]) / n
        for v in x[n:]:
            r = (r * (n - 1) + v) / n
        return r
    atr = _rma(trs)
    if atr <= 0:
        return None
    pdi = 100 * _rma(pdm) / atr; ndi = 100 * _rma(ndm) / atr
    s = pdi + ndi
    return (100 * abs(pdi - ndi) / s) if s > 0 else None


def _atr(highs, lows, closes, n=14):
    """Wilder ATR14 — TP/SL seviyeleri için (outcome tracking)."""
    if len(closes) < n + 1:
        return None
    trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
           for i in range(1, len(closes))]
    if len(trs) < n:
        return None
    r = sum(trs[:n]) / n
    for v in trs[n:]:
        r = (r * (n - 1) + v) / n
    return r


if __name__ == "__main__":
    print("Koşullu base-rate tabloları kuruluyor (features.jsonl)...")
    tb = build_tables()
    print(f"Tablo: {len(tb)} sembol×yön → {TABLES.name}\n")
    for key in ["NDX.INDX|BUY", "USOIL.FOREX|SELL", "XAUUSD|BUY"]:
        t = tb.get(key, {})
        print(f"{key}: base={t.get('base')}  gate={t.get('gate')}")
        print(f"   rev_chan: {t.get('rev_chan')}")
        print(f"   session:  {t.get('session')}\n")
