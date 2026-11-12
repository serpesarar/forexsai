"""yigilma_shadow.py — aileler arası yığılma (IO-29 Y2) GÖLGE etiketi.

⚠️ BU MODÜL HİÇBİR EMİR GÖNDERMEZ, hiçbir girişi engellemez. Yalnız MT5 geçmişini okur ve
`yigilma_shadow.jsonl`'e yazar. Hatalar bot akışını etkilemez (çağıran try/except içinde kullanır).

KANIT: research/dax_gun_otopsi_20261112/RAPOR.md + defter §2.7 IO-29 (sınıf C).
  Y2 (400 g, 1.080 işlem): n 44, −0,157R vs +0,003R, Δ −0,16R, P(Δ<0) 0,87, yarılar −0,16/−0,25,
  aileye göre tabakalı −0,17. Ön kayıttaki P ≥ 0,95 tutmadı → gölge etiketi.

TANIM (dondurulmuş; araştırmanın `yigilma.py` tanımıyla birebir):
  Hesaptaki HER yeni pozisyon P için, P açıldığı anda aynı sembolde, aynı yönde, P'den önce açılmış ve
  henüz kapanmamış pozisyonlar Q:
    Y1 = en az bir Q var
    Y2 = en az bir Q P'nin giriş fiyatında zararda (BUY: Q.giriş > P.giriş · SELL: Q.giriş < P.giriş)
  Kaynak: `history_deals_get` (giriş/çıkış deal'leri, sunucu saatinde time_msc). Böylece iki tarama
  arasında açılıp kapanan pozisyonlar ve ayrı süreçteki claude_decider işlemleri de görülür.
Sonuç (pozisyon tamamen kapanınca): net $ ve R = yönlü (çıkış − giriş) / |giriş − ilk SL|.

Karne:   python yigilma_shadow.py --karne
Kapatma: config.YIGILMA_SHADOW_ENABLED = False
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "yigilma_shadow.jsonl"
STATE_FILE = HERE / "yigilma_state.json"

MAGIC_BASE = 52890969
FAMILY_BY_OFFSET = {0: "MOMSR", 1: "CHREV", 2: "VIXREG", 3: "REFLEX", 4: "DAYCOMBO", 5: "USOIL_BRK",
                    6: "REENTRY", 7: "CAPREV", 8: "C3B", 9: "ORBVIX", 10: "CEKIC", 11: "KSG", 20: "DECIDER"}
POLL_EVERY_S = 30
LOOKBACK_DAYS = 8            # deal penceresi; C3b 5 işlem günü tutar, sunucu saati belirsizliğine karşı geniş
STATE_KEEP_DAYS = 14         # bundan eski etiket/sonuç kimlikleri durumdan silinir
DEAL_BUY, DEAL_SELL = 0, 1
ENTRY_IN = 0                 # DEAL_ENTRY_IN; diğerleri (OUT / INOUT / OUT_BY) çıkış sayılır

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def family_of(magic: int) -> str:
    if magic == 0:
        return "MANUEL"
    return FAMILY_BY_OFFSET.get(int(magic) - MAGIC_BASE, f"MAGIC_{magic}")


def build_positions(deals: list[dict]) -> dict[int, dict]:
    """Deal listesinden pozisyonlar: {pid: {sym, dir, E, t_open, t_close, magic, X, net, vol_in, vol_out}}.
    Giriş deal'i pencere dışında kalan pozisyonlar atılır."""
    pos: dict[int, dict] = {}
    for d in sorted(deals, key=lambda x: x["time_msc"]):
        pid = d["position_id"]
        if d["entry"] == ENTRY_IN:
            if d["type"] not in (DEAL_BUY, DEAL_SELL) or pid in pos:
                continue
            pos[pid] = {"pid": pid, "sym": d["symbol"], "dir": "BUY" if d["type"] == DEAL_BUY else "SELL",
                        "E": d["price"], "t_open": d["time_msc"], "magic": d["magic"], "order": d.get("order"),
                        "vol_in": d["volume"], "vol_out": 0.0, "t_close": None, "X": None,
                        "net": d.get("profit", 0.0) + d.get("swap", 0.0) + d.get("commission", 0.0)}
        elif pid in pos:
            p = pos[pid]
            p["vol_out"] += d["volume"]
            p["net"] += d.get("profit", 0.0) + d.get("swap", 0.0) + d.get("commission", 0.0)
            p["X"] = d["price"]
            if p["vol_out"] >= p["vol_in"] - 1e-9:
                p["t_close"] = d["time_msc"]
    return pos


def crowd_at_open(p: dict, pos: dict[int, dict]) -> dict:
    """P açıldığı anda aynı sembol-yönde açık olan önceki pozisyonlar → Y1/Y2 bayrakları."""
    s = 1 if p["dir"] == "BUY" else -1
    same = [q for q in pos.values() if q["pid"] != p["pid"] and q["sym"] == p["sym"] and q["dir"] == p["dir"]
            and q["t_open"] < p["t_open"] and (q["t_close"] is None or q["t_close"] > p["t_open"])]
    under = [q for q in same if s * (p["E"] - q["E"]) < 0]
    fam = family_of(p["magic"])
    return {"y1": bool(same), "y2": bool(under), "n_same": len(same), "n_under": len(under),
            "n_under_other_fam": sum(1 for q in under if family_of(q["magic"]) != fam),
            "under": [{"pid": q["pid"], "fam": family_of(q["magic"]), "E": q["E"],
                       "behind_pts": round(s * (q["E"] - p["E"]), 2)} for q in under]}


def r_multiple(p: dict, sl0: float | None) -> float | None:
    if not sl0 or p["X"] is None or abs(p["E"] - sl0) < 1e-9:
        return None
    s = 1 if p["dir"] == "BUY" else -1
    return round(s * (p["X"] - p["E"]) / abs(p["E"] - sl0), 3)


def step(st: dict, pos: dict[int, dict], sl_of, log, now_ms: int) -> bool:
    """Yeni pozisyonları etiketle, kapananların sonucunu yaz. `sl_of(p)` → ilk SL veya None. Değişiklik → True."""
    changed = False
    for pid, p in sorted(pos.items(), key=lambda kv: kv[1]["t_open"]):
        key = str(pid)
        if key not in st["tagged"]:
            c = crowd_at_open(p, pos)
            sl0 = sl_of(p)
            rec = {"kind": "entry", "pid": pid, "sym": p["sym"], "dir": p["dir"], "fam": family_of(p["magic"]),
                   "t_open_srv_ms": p["t_open"], "E": p["E"], "sl0": sl0, "seen_late": p["t_close"] is not None,
                   "retro": p["t_open"] < st["since_ms"], **c}
            _append(rec)
            st["tagged"][key] = {"t": p["t_open"], "sl0": sl0, "y1": c["y1"], "y2": c["y2"]}
            changed = True
            if c["y2"]:
                log.warning("YIĞILMA-GÖLGE Y2: %s %s %s #%s, %d aynı yön pozisyon zararda iken giriş (%s) — EMİR YOK",
                            rec["fam"], p["sym"], p["dir"], pid, c["n_under"],
                            ", ".join(f"{u['fam']} −{u['behind_pts']}p" for u in c["under"]))
        if p["t_close"] is not None and key not in st["resolved"]:
            t = st["tagged"][key]
            _append({"kind": "result", "pid": pid, "sym": p["sym"], "fam": family_of(p["magic"]), "y1": t["y1"],
                     "y2": t["y2"], "net": round(p["net"], 2), "r": r_multiple(p, t.get("sl0")),
                     "dur_min": round((p["t_close"] - p["t_open"]) / 60000, 1)})
            st["resolved"][key] = p["t_close"]
            changed = True
    cut = now_ms - STATE_KEEP_DAYS * 86400 * 1000
    for k in [k for k, v in st["tagged"].items() if v["t"] < cut]:
        st["tagged"].pop(k, None); st["resolved"].pop(k, None)
    return changed


def summarize(records: list[dict]) -> dict:
    res = [r for r in records if r.get("kind") == "result" and not r.get("retro")]
    out = {}
    for name, flt in [("Y2", lambda r: r["y2"]), ("Y1_degil_Y2", lambda r: r["y1"] and not r["y2"]),
                      ("yalniz", lambda r: not r["y1"])]:
        g = [r for r in res if flt(r)]
        rr = [r["r"] for r in g if r.get("r") is not None]
        out[name] = {"n": len(g), "ort_r": round(sum(rr) / len(rr), 3) if rr else None, "n_r": len(rr),
                     "net_usd": round(sum(r["net"] for r in g), 1)}
    return out


# ═════════════════════════ durum ═════════════════════════

def _load_state(now_ms: int) -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("since_ms", now_ms)       # ilk çalışma; öncesi 'retro' etiketlenir
    st.setdefault("tagged", {})
    st.setdefault("resolved", {})
    return st


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _deals(mt5) -> list[dict]:
    now = datetime.now(timezone.utc)
    D = mt5.history_deals_get(now - timedelta(days=LOOKBACK_DAYS), now + timedelta(days=1)) or []
    keys = ("ticket", "order", "time_msc", "type", "entry", "magic", "position_id", "volume", "price",
            "profit", "swap", "commission", "symbol")
    return [{k: getattr(d, k, 0) for k in keys} for d in D]


def _sl_lookup(mt5):
    """İlk SL: açan emrin sl'i; 0 ise (SL sonradan konduysa) açık pozisyonun güncel sl'i."""
    def sl_of(p: dict) -> float | None:
        try:
            o = mt5.history_orders_get(ticket=p["order"]) if p.get("order") else None
            if o and o[0].sl:
                return float(o[0].sl)
            q = mt5.positions_get(ticket=p["pid"])
            if q and q[0].sl:
                return float(q[0].sl)
        except Exception:
            pass
        return None
    return sl_of


def poll(mt5, log, now: float | None = None, force: bool = False) -> None:
    """Bot ana döngüsünden her tarama çağrılır. EMİR YOK. Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if not force and now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    deals = _deals(mt5)
    if not deals:
        return
    now_ms = max(d["time_msc"] for d in deals)      # sunucu ekseninde 'şimdi' ≈ son deal; durum kesimi için yeterli
    st = _load_state(now_ms)
    if step(st, build_positions(deals), _sl_lookup(mt5), log, now_ms):
        _save_state(st)


def _karne() -> None:
    try:
        lines = EVENTS_JSONL.read_text(encoding="utf-8").splitlines()
    except OSError:
        print("henüz kayıt yok")
        return
    recs = [json.loads(x) for x in lines if x.strip()]
    retro = {r["pid"] for r in recs if r.get("kind") == "entry" and r.get("retro")}
    for r in recs:
        if r.get("kind") == "result":
            r["retro"] = r["pid"] in retro
    print(json.dumps(summarize(recs), ensure_ascii=False, indent=1))
    print("Araştırma (400 g): Y2 −0,157R (n 44) vs diğerleri +0,003R. Y2 n ≥ 100 olmadan hüküm verme.")


if __name__ == "__main__":
    if "--karne" in sys.argv:
        _karne()
