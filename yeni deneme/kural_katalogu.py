"""kural_katalogu.py — canlı kuralların KATALOĞU, lot seviyeleri ve "hangi sinyal açıldı" duyurusu.

Her canlı kural (C3b, ORB×VIX, FR-15 çekiç, CAPREV) burada tek satırla tanımlıdır: ad, geçmiş isabet oranı, ortalama
getiri, SL/TP, işlem sıklığı, lot, magic. İşlem açıldığında `announce_open()` ekrana (konsol log'u + demo_bot.log) şunu basar:

    ╔══ SİNYAL AÇILDI ═══ C3b — NDX RSI2 geri dönüşü ═══
    ║ GEÇMİŞ BAŞARI: isabet %78,1 (n 155) · ort +65 bp/işlem · sınıf A
    ║ NAS100 BUY 2.0 lot @ ... SL ... TP ...

LOT SEVİYELERİ (kanıt sınıfına göre; kullanıcı kararı 2026-11-08). Her biri `config` içinde `getattr(config, <lot_key>, varsayılan)`
ile ezilebilir (kutuda config.py gitignore'da → varsayılan BURADA):
    C3b 2.0  ·  CAPREV 1.0  ·  ORB×VIX 0.75  ·  FR-15 çekiç 0.5 (her endekste)
Aynı sembolde bu ailelerin toplam açık lotu `RULE_MAX_LOTS_PER_SYMBOL` (varsayılan 4.5) üstüne çıkamaz (yoğunlaşma freni).

Kapatma bayrakları (config): C3B_LIVE, ORB_VIX_LIVE, CEKIC_LIVE, CAPREV_LIVE — hepsi varsayılan True (LIVE_TRADING da True olmalı).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS_JSONL = HERE / "kural_canli_olaylar.jsonl"

MAX_LOTS_PER_SYMBOL_DEFAULT = 4.5          # C3b 2.0 + CAPREV 1.0 + ORB 0.75 + FR-15 0.5 = 4.25 < 4.5

# id → tanım. magic_offset: config.MAGIC_NUMBER + offset (+1…+6 başka kapsamlar kullanıyor).
RULES: dict[str, dict] = {
    "C3B": {
        "ad": "C3b — NDX RSI2 geri dönüşü", "kisa": "C3B", "sinif": "A", "magic_offset": 8,
        "lot_key": "C3B_LIVE_LOT", "lot": 2.0, "live_key": "C3B_LIVE",
        "isabet": "%78,1", "n": 155, "ort": "+65 bp/işlem", "tutus": "≈1,6 gün (en fazla 5 gün)",
        "sl": "yok (acil durum SL %10 — geçmişteki en kötü işlem −%6,8)", "tp": "yok; ilk yükselen 15:30 ET fiyatında çık",
        "siklik": "≈ 1,2 işlem/ay (yılda ≈ 15)",
        "kanit": "go_live_cards/ndx_c3b_rsi2_upexit.json (6/6; kör US500/US30/US2000/GER40 pozitif)",
    },
    "CAPREV": {
        "ad": "CAPREV — kapitülasyon alımı (NDX + DAX)", "kisa": "CAPREV", "sinif": "B+", "magic_offset": 7,
        "lot_key": "CAPREV_LIVE_LOT", "lot": 1.0, "live_key": "CAPREV_LIVE",
        "isabet": "%55,3", "n": 161, "ort": "+0,22 R/işlem", "tutus": "aynı gün (seans kapanışı)",
        "sl": "1× günlük oynaklık", "tp": "yok; seans kapanışında çık",
        "siklik": "≈ 1,3 işlem/ay (yılda ≈ 16)",
        "kanit": "go_live_cards/caprev_portfoy.json (6/6)",
    },
    "ORBVIX": {
        "ad": "ORB × VIX — NDX açılış aralığı kırılımı (VIX≥18,4)", "kisa": "ORBVIX", "sinif": "B", "magic_offset": 9,
        "lot_key": "ORB_VIX_LIVE_LOT", "lot": 0.75, "live_key": "ORB_VIX_LIVE",
        "isabet": "%48,7", "n": 152, "ort": "+0,295 R/işlem", "tutus": "aynı gün (15:55 ET'ye kadar)",
        "sl": "açılış aralığı ortası", "tp": "2R",
        "siklik": "≈ 5 işlem/ay (≈ 1,2/hafta)",
        "kanit": "go_live_cards/ndx_orb_vix.json (6/6; 2026 zayıf +0,10R)",
    },
    "CEKIC": {
        "ad": "FR-15 — teyitli çekiç (1h alt fitil)", "kisa": "CEKIC", "sinif": "B", "magic_offset": 10,
        "lot_key": "CEKIC_LIVE_LOT", "lot": 0.5, "live_key": "CEKIC_LIVE",
        "isabet": "≈%26–30 (FR-10 ölçümü; bu kuralın kendi isabeti kayıtlı değil)", "n": 3969, "ort": "+0,07 R/işlem (swap sonrası)",
        "tutus": "en fazla 24 saat", "sl": "çekiç dibi", "tp": "5R",
        "siklik": "endeks başına ≈ 7–8/ay (iki endeks ≈ 15/ay, ≈ 3–4/hafta)",
        "kanit": "go_live_cards/teyitli_cekic_1h.json (yerel 10/10 set artı; MT5 havuz +0,085R P 0,98)",
    },
}


# ═════════════════════════ saf yardımcılar ═════════════════════════

def magic(config, rule_id: str) -> int:
    return int(getattr(config, "MAGIC_NUMBER", 52890969)) + RULES[rule_id]["magic_offset"]


def lot_of(config, rule_id: str) -> float:
    r = RULES[rule_id]
    return float(getattr(config, r["lot_key"], r["lot"]))


def is_enabled(config, rule_id: str) -> bool:
    r = RULES[rule_id]
    return bool(getattr(config, r["live_key"], True)) and bool(getattr(config, "LIVE_TRADING", False))


def rule_magics(config) -> set[int]:
    return {magic(config, k) for k in RULES}


def banner(rule_id: str, line: str, extra: dict | None = None) -> list[str]:
    """İşlem açılış duyurusu satırları (log + stdout için)."""
    r = RULES[rule_id]
    out = [f"╔══ SİNYAL AÇILDI ═══ {r['ad']}",
           f"║ GEÇMİŞ BAŞARI: isabet {r['isabet']} (n {r['n']}) · ort {r['ort']} · sınıf {r['sinif']}",
           f"║ SL: {r['sl']} · TP: {r['tp']} · tutuş: {r['tutus']} · sıklık: {r['siklik']}",
           f"║ {line}"]
    if extra:
        out.append("║ " + " · ".join(f"{k}={v}" for k, v in extra.items()))
    out.append("╚══ " + r["kanit"])
    return out


def announce_open(log, rule_id: str, line: str, extra: dict | None = None) -> None:
    """Kural adı + geçmiş başarı oranını log'a VE ekrana yaz; olay dosyasına ekle."""
    for ln in banner(rule_id, line, extra):
        log.info("%s", ln)                      # bot log'u konsola (ekran) ve demo_bot.log'a yazar
    append_event({"kind": "announce", "rule": rule_id, "line": line, **(extra or {})})


def append_event(rec: dict) -> None:
    try:
        with EVENTS_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def concentration_ok(mt5, config, symbol: str, new_lot: float) -> tuple[bool, float, float]:
    """(izin, açık lot, tavan): bu ailelerin AYNI sembolde toplam açık lotu tavanı aşmasın."""
    cap = float(getattr(config, "RULE_MAX_LOTS_PER_SYMBOL", MAX_LOTS_PER_SYMBOL_DEFAULT))
    mg = rule_magics(config)
    open_lot = sum(float(p.volume) for p in (mt5.positions_get(symbol=symbol) or []) if p.magic in mg)
    return open_lot + new_lot <= cap + 1e-9, open_lot, cap


def open_positions(mt5, config, rule_id: str, symbol: str | None = None) -> list:
    mg = magic(config, rule_id)
    pos = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    return [p for p in (pos or []) if p.magic == mg]


# ═════════════════════════ MT5 icra (ortak) ═════════════════════════

def buy(mt5, config, log, send_order, mk_comment, rule_id: str, sym: str, lot: float, ask: float,
        sl: float, tp: float, tag: str):
    """Market BUY. (ok, ticket, retcode). SL/TP 0.0 = yok."""
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot, "type": mt5.ORDER_TYPE_BUY,
           "price": ask, "sl": sl, "tp": tp, "deviation": config.DEVIATION_POINTS, "magic": magic(config, rule_id),
           "comment": mk_comment("fxs ", tag), "type_time": mt5.ORDER_TIME_GTC}
    res = send_order(req, sym)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    return ok, int(getattr(res, "order", 0)) if ok else 0, getattr(res, "retcode", None)


def close(mt5, config, log, send_order, rule_id: str, pos, why: str) -> bool:
    """Açık BUY pozisyonu market kapat."""
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return False
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "position": pos.ticket, "volume": float(pos.volume),
           "type": mt5.ORDER_TYPE_SELL, "price": tick.bid, "deviation": config.DEVIATION_POINTS,
           "magic": magic(config, rule_id), "comment": f"fxs {RULES[rule_id]['kisa']} exit"[:28]}
    res = send_order(req, pos.symbol)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    append_event({"kind": "exit", "rule": rule_id, "ticket": pos.ticket, "symbol": pos.symbol, "why": why,
                  "bid": tick.bid, "ok": ok, "retcode": getattr(res, "retcode", None),
                  "entry_price": pos.price_open, "volume": pos.volume})
    (log.info if ok else log.error)("%s %s kapanış ticket=%s @%.2f (%s) retcode=%s", RULES[rule_id]["kisa"],
                                    "✅" if ok else "❌", pos.ticket, tick.bid, why, getattr(res, "retcode", None))
    return ok
