"""
run_decider.py — Faz-1 canlı döngü (SHADOW): kanıt-temelli özerk Opus kararı.
=============================================================================
AKIŞ (her cadence ya da --once):
  1. Her sembol için canlı 5m bar + VIX çek.                                [bedava]
  2. Her (yasak-olmayan) yön için canlı feature + GEÇMİŞ KANIT-paketi kur.  [bedava]
  3. Durum "ilginç" mi? (mean-rev aşırılığı/gate). Değilse Opus çağrılMAZ.  [bedava]
  4. İlginçse: Opus durumdan KENDİ görüşünü oluşturur (evidence.py kanıtıyla) → journal.
  5. SHADOW: kararı loglar, henüz MT5'e EMİR GÖNDERMEZ (execution sıradaki adım).

Sert yasaklar (XAU SELL, USOIL BUY) decide._enforce_guardrails'te kodla zorlanır.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decider_config as config  # noqa: E402
from gates import ALLOW, vix_regime  # noqa: E402
from decide import (decide_situation, decide_free, append_journal, append_free_journal,  # noqa: E402
                    JOURNAL_JSONL, DECIDE_MODEL, HARD_BANS)
import evidence as ev  # noqa: E402
import free_context as fx  # noqa: E402
import forensics  # noqa: E402
from data_contract import validate_bars, validate_multi  # noqa: E402  (sıfır-güven)
import outcomes  # noqa: E402

CADENCE_SEC = 1200       # 20dk (maliyet: 15→20dk ~%25 az çağrı; mean-rev bu hızda yeterli)
BARS_N = 120
# Opus'a danışma eşiği. 1.6: rev<1.6 "zayıf" durumlar (kanıt: neredeyse hep WAIT, breakeven
# altı) MEKANİK elenir → maliyet düşer. gate_fired (rev>2.0) her zaman geçer. rev 1.6-2.0
# "sınırda fırsat" Opus'a gider; prompt gevşediği için orada daha CESUR açar (2026-07-02).
CONSULT_REV = 1.6
FREE_SYMBOL = "XAUUSD"   # serbest-zekâ modu (kanıt-tablosu yok; edge yok, çıplak muhakeme)
FREE_TFS = {"1m": None, "5m": None, "30m": None, "1h": None}  # MT5 TF sabitleri runtime'da doldurulur
try:
    import MetaTrader5 as mt5  # noqa: E402
    _HAS_MT5 = True
except Exception:
    mt5 = None
    _HAS_MT5 = False

_SYM_MAP: dict[str, str] = {}     # iç ad → Pepperstone gerçek sembol (startup'ta otomatik tespit)
_VIX_SYM = None
_TABLES = ev.load_tables()


# ── Pepperstone MT5 (tek terminal: NASDAQ/DAX/Altın/Petrol + VIX) ─────────────
def connect_mt5() -> bool:
    if not _HAS_MT5:
        print("⚠️  MetaTrader5 modülü yok (Windows'ta çalışır).")
        return False
    if not mt5.initialize(config.PEPPERSTONE_TERMINAL_PATH):
        print("❌ Pepperstone terminaline bağlanılamadı:", mt5.last_error())
        print("   Terminal AÇIK + demo'ya giriş yapılmış olmalı; PEPPERSTONE_TERMINAL_PATH doğru mu?")
        return False
    info = mt5.account_info()
    print(f"✓ Pepperstone bağlı | hesap={getattr(info,'login','?')} {getattr(info,'company','')}")
    return _resolve_symbols()


def _find_symbol(cands: list[str]):
    for s in cands:
        if mt5.symbol_info(s) is not None:
            mt5.symbol_select(s, True)
            return s
    return None


def _resolve_symbols() -> bool:
    """İç adları Pepperstone gerçek adlarına otomatik eşle + ekrana yaz (ilk koşuda doğrula)."""
    global _VIX_SYM
    print("Sembol tespiti (Pepperstone):")
    for fx_sym, cands in config.SYMBOL_CANDIDATES.items():
        found = _find_symbol(cands)
        if found:
            _SYM_MAP[fx_sym] = found
            print(f"  {fx_sym:14s} → {found}")
        else:
            print(f"  {fx_sym:14s} → ❌ BULUNAMADI (adaylar: {cands}) — decider_config'e doğru adı ekle")
    _VIX_SYM = _find_symbol(config.VIX_CANDIDATES)
    print(f"  {'VIX':14s} → {_VIX_SYM or '❌ yok (NDX VIX bağlamı olmadan çalışır)'}")
    if not _SYM_MAP:
        print("❌ Hiç sembol bulunamadı — Market Watch'a ekli mi, adlar doğru mu?"); return False
    return True


def fetch_bars_mt5(n: int = BARS_N) -> dict[str, list[dict]]:
    out = {}
    for fx_sym, mt5_sym in _SYM_MAP.items():
        rates = mt5.copy_rates_from_pos(mt5_sym, mt5.TIMEFRAME_M5, 0, n)
        if rates is None or len(rates) == 0:
            continue
        bars = [{"high": float(r["high"]), "low": float(r["low"]), "close": float(r["close"]),
                 "volume": float(r["tick_volume"]), "time": int(r["time"])} for r in rates]
        ok, why = validate_bars(bars, "5m")            # SIFIR-GÜVEN: sözleşmesiz bar kullanılmaz
        if ok:
            out[fx_sym] = bars
        else:
            print(f"  🛡 DataContract: {fx_sym} 5m REDDEDİLDİ — {why}")
    return out


def fetch_multi_tf(fx_sym: str, n: int = 150) -> dict:
    """Çok-TF bar (1m/5m/30m/1h/4h) — free mod + FORENSİK snapshot için (tüm semboller)."""
    mt5_sym = _SYM_MAP.get(fx_sym)
    if not mt5_sym:
        return {}
    tf_map = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5,
              "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1, "4h": mt5.TIMEFRAME_H4}
    out = {}
    for tf, const in tf_map.items():
        rates = mt5.copy_rates_from_pos(mt5_sym, const, 0, n)
        if rates is not None and len(rates):
            out[tf] = [{"high": float(r["high"]), "low": float(r["low"]), "close": float(r["close"]),
                        "volume": float(r["tick_volume"]), "time": int(r["time"])} for r in rates]
    return validate_multi(out)                        # SIFIR-GÜVEN: geçersiz TF'ler düşer


def fetch_dxy() -> float | None:
    """Canlı DXY (dolar endeksi — altına ters). Pepperstone'da varsa oradan; yoksa None."""
    for cand in ("USDX", "DXY", "USDOLLAR", "DX", "USDIDX"):
        info = mt5.symbol_info(cand) if _HAS_MT5 else None
        if info is not None:
            mt5.symbol_select(cand, True)
            tick = mt5.symbol_info_tick(cand)
            if tick:
                for v in (getattr(tick, "last", 0), getattr(tick, "bid", 0)):
                    if v and v > 0:
                        return round(float(v), 3)
    return None


def fetch_bars_after_mt5(symbol: str, since_ts: float) -> list[dict]:
    """Outcome resolve için: sembolün son ~800 5m barı (entry_bar_time ile filtrelenir)."""
    mt5_sym = _SYM_MAP.get(symbol, symbol)
    rates = mt5.copy_rates_from_pos(mt5_sym, mt5.TIMEFRAME_M5, 0, 800)
    if rates is None:
        return []
    bars = [{"high": float(r["high"]), "low": float(r["low"]),
             "close": float(r["close"]), "time": int(r["time"])} for r in rates]
    ok, why = validate_bars(bars, "5m", min_bars=10)   # grading de sözleşmeli (yanlış grade > grade yok)
    if not ok:
        print(f"  🛡 DataContract(grade): {symbol} REDDEDİLDİ — {why}")
        return []
    return bars


def open_positions_summary() -> dict:
    # Decider Pepperstone'da işlem AÇMAZ (shadow); varsa pozisyonları bağlam için göster
    if not _HAS_MT5:
        return {"count": 0, "by": {}, "note": ""}
    poss = mt5.positions_get() or []
    rev = {v: k for k, v in _SYM_MAP.items()}
    by = {}
    for p in poss:
        by.setdefault(rev.get(p.symbol, p.symbol), []).append("BUY" if p.type == 0 else "SELL")
    longs = sum(1 for v in by.values() for d in v if d == "BUY")
    shorts = sum(1 for v in by.values() for d in v if d == "SELL")
    note = (f"{longs} long açık — korelasyonlu yığılma" if longs >= 2 else
            f"{shorts} short açık — korelasyonlu yığılma" if shorts >= 2 else "")
    return {"count": len(poss), "by": by, "note": note}


def fetch_vix() -> tuple[float | None, str]:
    """VIX'i Pepperstone MT5'ten DOĞRUDAN oku — canlı 24h, gerçek-zamanlı (poller/yfinance/dosya YOK)."""
    if not _HAS_MT5 or not _VIX_SYM:
        return None, "none"
    tick = mt5.symbol_info_tick(_VIX_SYM)
    if tick is None:
        return None, "none"
    for v in (getattr(tick, "last", 0.0), getattr(tick, "bid", 0.0), getattr(tick, "ask", 0.0)):
        if v and v > 0:
            return float(v), "pepperstone"
    return None, "none"


# ── Bağlam + durum ───────────────────────────────────────────────────────────
def recent_journal_summary(n: int = 8) -> str:
    """Opus'un her kararda gördüğü yakın-geçmiş. C — FIRSAT MUHASEBESİ dahil: model
    yalnız gerçekleşen kaybı görürse çekingenliği öğrenir (kanıt: 360 kaçırılan kazanana
    karşı 79 yakalanan). Vazgeçilen-R'yi göstermek çekingenliği 'bedava' olmaktan çıkarır."""
    from decide import load_journal
    from datetime import timedelta
    rows = load_journal(clean=True)
    if not rows:
        return "henüz geçmiş yok"
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    day = [r for r in rows if r.get("ts", "") >= cutoff]
    if not day:
        day = rows[-n:]
    opens = [r for r in day if str((r.get("decision") or {}).get("action", "")).upper() == "OPEN"]
    realized = sum(r.get("pnl_r") or 0 for r in day if r.get("outcome") in ("WIN", "LOSS"))
    foregone = sum(r.get("cf_pnl_r") or 0 for r in day
                   if str((r.get("decision") or {}).get("action", "")).upper() == "WAIT"
                   and r.get("cf_outcome") in ("WIN", "LOSS"))
    return (f"son 24s: {len(day)} karar, {len(opens)} OPEN; gerçekleşen {realized:+.2f}R; "
            f"VAZGEÇİLEN {foregone:+.2f}R (beklediklerinin cf toplamı — aşırı temkin de maliyettir, "
            f"pozitifse kazananları kaçırıyorsun demektir)")


NEAR_EVENT = False   # TODO(news): kullanıcının haber panelini bağla → yüksek-etkili olay penceresi


def _context(positions: dict, now: datetime) -> dict:
    return {"now_utc": now.isoformat(timespec="minutes"),
            "session": ev._session(now.hour),
            "open_positions": positions.get("count", 0),
            "positions_by_symbol": positions.get("by", {}),
            "exposure_note": positions.get("note", ""),
            "near_event": NEAR_EVENT,
            "recent": recent_journal_summary()}


def build_situation(symbol: str, bars: list[dict], vix, positions: dict, now: datetime,
                    vix_source: str = "yfinance"):
    """Sembol için yasak-olmayan yönlerin canlı feature + kanıtı. İlginç değilse None."""
    if not bars or len(bars) < ev.WIN_N:
        return None
    dirs = [d for d in ("BUY", "SELL") if (symbol, d) not in HARD_BANS]
    directions, interesting = {}, False
    primary_dir, best_ext = None, -1e9
    for d in dirs:
        lf = ev.live_features(bars, d, vix=vix)
        if lf.get("gate_fired") or (lf.get("rev_chan") or -9) > CONSULT_REV or (lf.get("rev_vwap") or -9) > CONSULT_REV:
            interesting = True
        # primary_dir = en güçlü mean-rev aşırılığı olan yön (WAIT'te bile karşı-olgu için)
        ext = max(lf.get("rev_chan") or -9, lf.get("rev_vwap") or -9)
        if lf.get("gate_fired"):
            ext += 100        # gate ateşleyen yön öncelikli
        if ext > best_ext:
            best_ext, primary_dir = ext, d
        directions[d] = {"live": lf, "evidence": ev.evidence_pack(symbol, d, lf, _TABLES)}
    if not interesting:
        return None
    live_24h = (vix_source == "pepperstone")     # Pepperstone MT5 futures 24h canlı → RTH-kapısı yok
    fav, label = vix_regime(vix, now, live_24h=live_24h)
    return {"symbol": symbol,
            "price": float(bars[-1]["close"]),       # entry referansı (outcome tracking)
            "bar_time": bars[-1].get("time"),        # MT5-frame: outcome resolve broker-saat tutarlılığı
            "primary_dir": primary_dir,              # WAIT'te bile karşı-olgu (recall analizi)
            "vix": {"value": vix, "regime": label, "favored_ndx": fav, "source": vix_source,
                    "fresh": label in ("stress", "calm"),   # off-hours/neutral → False, Opus güvenmesin
                    "note": ("US RTH kapalı, ^VIX donuk — yön bağlamına güvenme" if label == "stale_offhours"
                             else "eşik bıçak-sırtı — yön belirsiz" if label == "neutral_band"
                             else "Pepperstone canlı 24h (futures, ~spot)" if vix_source == "pepperstone" else "")},
            "context": _context(positions, now),
            "directions": directions}


# ── Çekirdek pass ────────────────────────────────────────────────────────────
_last_bar_seen: dict = {}    # sym → [son_bar_time, kaç_döngüdür_aynı]
_last_consult: dict = {}     # sym → son Opus danışmasının durum-imzası


def _state_changed(sym: str, sig: tuple) -> bool:
    """A — OLAY-TETİKLİ filtre: saat-tetikli sistem 'yeni bilgi yok'u ifade edemiyordu
    (124 kopya karar bunun kanıtı). Aynı bar + aynı durum imzasıyla (yön, gate, rev-bandı)
    Opus'a İKİNCİ kez sorulmaz — karar yalnız durum DEĞİŞTİĞİNDE üretilir. Yan etkiler:
    frozen-sınıfı hatalar imkânsızlaşır, LLM maliyeti düşer, journal kayıtları gerçekten
    bağımsız bilgi taşır (otokorelasyon şişmesi biter)."""
    if _last_consult.get(sym) == sig:
        print(f"  ⏭ {sym}: durum değişmedi (aynı bar+imza) → Opus'a tekrar sorulmadı")
        return False
    _last_consult[sym] = sig
    return True


def _sit_signature(sit: dict) -> tuple:
    p = sit.get("primary_dir")
    lv = ((sit.get("directions") or {}).get(p) or {}).get("live") or {}
    rev = lv.get("rev_chan")
    return (sit.get("bar_time"), p, bool(lv.get("gate_fired")),
            round(rev * 2) / 2 if isinstance(rev, (int, float)) else None)


def _feed_is_frozen(sym: str, bars: list | None) -> bool:
    """DONUK-FEED / KAPALI-PİYASA koruması (2026-07-09 otopsisi: hafta sonu frozen bar'larla
    263 sahte karar üretildi — 129 kopya GDAXI SELL Pazartesi gap'inde otomatik LOSS, tüm
    istatistikleri zehirledi). Bar zamanı ≥3 döngüdür (≈1 saat) İLERLEMİYORSA sembol donuk →
    karar üretme. Saat-dilimi bağımsız (broker-frame vs UTC kıyası yapmaz, ilerleme bakar)."""
    bt = bars[-1].get("time") if bars else None
    if bt is None:
        return False
    st = _last_bar_seen.get(sym)
    if st and st[0] == bt:
        st[1] += 1
    else:
        _last_bar_seen[sym] = st = [bt, 0]
    if st[1] >= 3:
        if st[1] == 3:
            print(f"  ❄ {sym}: bar zamanı ~1 saattir ilerlemiyor (kapalı/donuk feed) → karar üretilmiyor")
        return True
    return False


def run_pass(bars_by_symbol: dict, vix, positions: dict, shadow: bool = True,
             model: str = DECIDE_MODEL, vix_source: str = "yfinance", dxy=None):
    now = datetime.now(timezone.utc)
    # Kanıt-temelli semboller (XAU HARİÇ — o serbest-zekâ moduna gider) + donuk-feed filtresi
    sits = [s for s in (build_situation(sym, bars_by_symbol.get(sym), vix, positions, now, vix_source)
                        for sym in ALLOW
                        if sym != FREE_SYMBOL and not _feed_is_frozen(sym, bars_by_symbol.get(sym))) if s]
    sits = [s for s in sits if _state_changed(s["symbol"], _sit_signature(s))]   # olay-tetikli
    out = []
    tag = "SHADOW" if shadow else "CANLI"
    if sits:
        print(f"[{now:%H:%M}] {len(sits)} ilginç sembol → Opus (kanıt-temelli, {model})...")
        for sit in sits:
            # FORENSİK snapshot (hacim/VIX/DXY/kanal/multi-TF S/R+güç) — model GÖRÜR + journal'a yazılır
            if _HAS_MT5:
                try:
                    sit["forensics"] = forensics.build_forensics(
                        fetch_multi_tf(sit["symbol"]), vix=vix, dxy=dxy)
                except Exception as e:
                    print("  forensics hatası (devam):", e)
                # FAKEOUT radarı: taze seviye-kırılımı sahte mi? (NDX 5m tabanı: %66 sahte;
                # klimaks-imzalılar OOS %78-88 — "kırdı, kesin gidecek" varsayımını kırar)
                try:
                    from fakeout_bridge import fakeout_context
                    fk = fakeout_context(_SYM_MAP, sit["symbol"])
                    if fk:
                        sit["fakeout"] = fk
                        print(f"  ⚡ {sit['symbol']}: taze kırılım — sahte olasılığı "
                              f"%{fk.get('fake_probability')} ({fk.get('verdict')})")
                except Exception as e:
                    print("  fakeout hatası (devam):", e)
            dec = decide_situation(sit, model=model)
            append_journal(sit, dec)["shadow"] = shadow
            act, d, sf = dec.get("action"), dec.get("direction"), dec.get("size_factor")
            print(f"  [{tag}] {sit['symbol']}: {act} {d or ''} size={sf} | {str(dec.get('reason'))[:90]}")
            if not shadow and act == "OPEN" and (sf or 0) > 0:
                execute(sit, dec)
            out.append({"sit": sit, "dec": dec})

    # XAU SERBEST-ZEKÂ (kanıt-tablosu yok; çok-TF ham bağlam → Opus çıplak muhakeme)
    if _HAS_MT5 and FREE_SYMBOL in _SYM_MAP:
        mtf = fetch_multi_tf(FREE_SYMBOL)
        if _feed_is_frozen(FREE_SYMBOL, mtf.get("5m")):
            mtf = {}                      # donuk feed → free karar da üretme
        ctx = fx.build_free_context(mtf, vix=vix, dxy=dxy)
        if ctx:
            cz = ((ctx.get("multi_tf") or {}).get("5m") or {}).get("channel_z")
            free_sig = (ctx.get("bar_time_5m"),
                        round(cz * 2) / 2 if isinstance(cz, (int, float)) else None)
            if not _state_changed(FREE_SYMBOL, free_sig):     # olay-tetikli (free)
                ctx = None
        if ctx:
            try:
                ctx["forensics"] = forensics.build_forensics(mtf, vix=vix, dxy=dxy)
            except Exception as e:
                print("  forensics hatası (devam):", e)
            print(f"[{now:%H:%M}] {FREE_SYMBOL} → Opus (SERBEST-ZEKÂ, çok-TF)...")
            dec = decide_free(ctx, model=model)
            append_free_journal(ctx, dec)["shadow"] = shadow
            act, d, sf = dec.get("action"), dec.get("direction"), dec.get("size_factor")
            print(f"  [{tag}·free] {FREE_SYMBOL}: {act} {d or ''} size={sf} | {str(dec.get('reason'))[:90]}")
            if not shadow and act == "OPEN" and (sf or 0) > 0:
                execute({"symbol": FREE_SYMBOL, "price": ctx.get("price")}, dec)
            out.append({"sit": ctx, "dec": dec})

    if not out:
        print(f"[{now:%H:%M}] ilginç durum yok — Opus çağrılmadı.")
    return out


def execute(sit: dict, dec: dict) -> None:
    """Onaylı kararı MT5'e gönder — SIRADAKI ADIM (botun open_trade/open_trade_sr'ına bağlanacak).
    Şu an kasıtlı boş: shadow doğrulanmadan canlı emir gönderilmez."""
    print(f"  ⚠️  execute() henüz bağlı değil — {sit['symbol']} {dec.get('direction')} "
          f"size={dec.get('size_factor')} icra edilmedi.")


def preflight() -> list[str]:
    """Başlangıç hazırlık kontrolü — eksikleri net raporla (deployment doğrulaması)."""
    import shutil
    problems = []
    from decide import _claude_bin
    _cb = _claude_bin()
    if _cb == "claude" and shutil.which("claude") is None:
        problems.append("claude CLI bulunamadı — PATH'te yok ve CLAUDE_BIN tanımlı değil "
                        "(Claude Code kurulu + Pro-login olmalı; CLAUDE_BIN=C:\\...\\claude.cmd)")
    if not Path(config.PEPPERSTONE_TERMINAL_PATH).exists():
        problems.append(f"Pepperstone terminali yok: {config.PEPPERSTONE_TERMINAL_PATH} — decider_config'te yolu düzelt")
    if not _TABLES:
        problems.append("evidence_tables.json boş/yok — Mac'te `python3 evidence.py` çalıştırıp kopyala")
    for f in ("PLAYBOOK.md", "LESSONS.md", "REGIME.md"):
        if not (HERE / "memory" / f).exists():
            problems.append(f"memory/{f} yok — kopyalanmadı")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--live", action="store_true", help="shadow KAPALI (execute çağrılır; henüz stub)")
    ap.add_argument("--model", default=DECIDE_MODEL)
    args = ap.parse_args()
    shadow = not args.live

    problems = preflight()
    if problems:
        print("⚠️  HAZIRLIK SORUNLARI:")
        for p in problems:
            print("   -", p)
        print()
    if not connect_mt5():
        print("MT5 yok — canlı bar alınamadı."); return
    print(f"Decider başladı | model={args.model} | {'SHADOW' if shadow else 'CANLI'} | "
          f"cadence={CADENCE_SEC}s | semboller={list(ALLOW)} | tablo={len(_TABLES)} hücre")
    try:
        while True:
            # 1) açık kararları grade et (MT5 5m ile TP/SL tarama)
            try:
                ch, rows = outcomes.resolve_journal(fetch_bars_after_mt5)
                if ch:
                    print(f"  [outcome] {ch} güncellendi | {outcomes.summary(rows)}")
            except Exception as e:
                print("  outcome çözüm hatası:", e)
            # 2) yeni durumları tara → Opus (geçici hata döngüyü ÖLDÜRMESİN)
            try:
                vix_val, vix_src = fetch_vix()
                run_pass(fetch_bars_mt5(), vix_val, open_positions_summary(),
                         shadow=shadow, model=args.model, vix_source=vix_src, dxy=fetch_dxy())
            except Exception as e:
                print("  run_pass hatası (döngü devam):", e)
            if args.once:
                break
            time.sleep(CADENCE_SEC)
    except KeyboardInterrupt:
        print("\nDecider durduruldu.")
    finally:
        if _HAS_MT5:
            mt5.shutdown()


if __name__ == "__main__":
    main()
