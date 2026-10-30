"""DBG klon ızgarası — MT5 koşucusu. VARSAYILAN GÖLGE: hiçbir emir göndermez, yalnız log yazar.

Kullanım (Windows kutusu, MT5 terminali açık):
    python dbg_klon_runner.py                         # GÖLGE (varsayılan): sanal dolum + log
    python dbg_klon_runner.py --terminal "C:\\...\\terminal64.exe"
    python dbg_klon_runner.py --canli --demo-onayi EVET   # yalnız DEMO hesapta gerçek emir

Emniyet (hepsi bayrakla değiştirilir; varsayılanlar 10k $ demo için):
    --taban 0.01 --carpan 1.1 --tp 5.0          klon ayarı (DBG C3)
    --max-seviye 30                              tavanda ekleme durur
    --max-sepet-zarar 1000                       USD; aşılırsa sepet piyasadan kapatılır
    --max-toplam-zarar 2500                      USD; iki sepet toplamı aşılırsa HEPSİ kapanır, koşucu durur
    --min-marjin-seviyesi 300                    %; altına inerse yeni giriş yok (ekleme dahil)
    DBG_KLON_OFF dosyası bu klasörde varsa yeni TAZE giriş yapılmaz.

Ayrı magic (52896686) ve kısa yorum ("DBGK B3", ≤28 karakter) kullanır; botun ve
decider'ın pozisyonlarına dokunmaz. Canlı mod gerçek hesapta (trade_mode != DEMO)
açılmayı REDDEDER.

Log: dbg_klon_log.jsonl (her olay bir satır), durum: dbg_klon_state.json (yeniden başlatmaya dayanıklı).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from klon_kurallar import BUY, SELL, KlonAyar  # noqa: E402
from klon_yonetici import ADD, FRESH, Eylem, KlonYonetici  # noqa: E402

MAGIC = 52896686            # bot 52890969(+n), decider 52890989 — çakışmaz
COMMENT_PREFIX = "DBGK"
LOG_FILE = HERE / "dbg_klon_log.jsonl"
STATE_FILE = HERE / "dbg_klon_state.json"
OFF_FILE = HERE / "DBG_KLON_OFF"
POLL_S = 0.5
HEARTBEAT_S = 300
DEVIATION_PTS = 30

log = logging.getLogger("dbg_klon")


def jlog(kind: str, **kw: object) -> None:
    rec = {"ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "olay": kind, **kw}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def save_state(yon: KlonYonetici, last_bar: int, sanal: dict) -> None:
    STATE_FILE.write_text(json.dumps({"yonetici": yon.durum(), "last_bar": last_bar, "sanal": sanal}, indent=1))


def load_state(yon: KlonYonetici) -> tuple[int, dict]:
    if not STATE_FILE.exists():
        return 0, {"gerceklesen": 0.0, "sepet": 0}
    d = json.loads(STATE_FILE.read_text())
    yon.yukle(d.get("yonetici", {}))
    return int(d.get("last_bar", 0)), d.get("sanal", {"gerceklesen": 0.0, "sepet": 0})


class MT5Adapter:
    """MetaTrader5 paketine ince sarmalayıcı (yalnız kutuda çalışır)."""

    def __init__(self, terminal: str | None, symbol: str) -> None:
        import MetaTrader5 as mt5  # noqa: N813
        self.mt5 = mt5
        ok = mt5.initialize(terminal) if terminal else mt5.initialize()
        if not ok:
            raise RuntimeError(f"mt5.initialize başarısız: {mt5.last_error()}")
        self.symbol = self._resolve(symbol)
        mt5.symbol_select(self.symbol, True)
        self.info = mt5.symbol_info(self.symbol)
        self.contract = float(self.info.trade_contract_size)   # 1 lot = contract oz → 1 $ = contract USD

    def _resolve(self, base: str) -> str:
        if self.mt5.symbol_info(base) is not None:
            return base
        for s in self.mt5.symbols_get() or []:
            if s.name.upper().startswith(base.upper()):
                return s.name
        raise RuntimeError(f"sembol bulunamadı: {base}")

    def is_demo(self) -> bool:
        acc = self.mt5.account_info()
        return acc is not None and acc.trade_mode == self.mt5.ACCOUNT_TRADE_MODE_DEMO

    def is_hedging(self) -> bool:
        """İki yönlü sepet için hedge hesabı şart (netting hesapta BUY ve SELL birbirini kapatır)."""
        acc = self.mt5.account_info()
        return acc is not None and acc.margin_mode == self.mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING

    def account(self) -> dict:
        a = self.mt5.account_info()
        return {"equity": a.equity, "margin": a.margin, "margin_level": a.margin_level or 0.0, "login": a.login}

    def last_closed_bar(self, tf_min: int) -> tuple[int, float] | None:
        """(yeni barın açılış zamanı, önceki KAPANMIŞ barın bid gövdesi)."""
        tf = getattr(self.mt5, f"TIMEFRAME_M{tf_min}")
        r = self.mt5.copy_rates_from_pos(self.symbol, tf, 0, 2)
        if r is None or len(r) < 2:
            return None
        return int(r[-1]["time"]), float(r[-2]["close"] - r[-2]["open"])

    def tick(self) -> tuple[float, float] | None:
        t = self.mt5.symbol_info_tick(self.symbol)
        return None if t is None else (float(t.bid), float(t.ask))

    def positions(self, side: str) -> list:
        ps = self.mt5.positions_get(symbol=self.symbol) or []
        typ = self.mt5.POSITION_TYPE_BUY if side == BUY else self.mt5.POSITION_TYPE_SELL
        return [p for p in ps if p.magic == MAGIC and p.type == typ]

    def market(self, side: str, lot: float, comment: str, close_ticket: int | None = None) -> float | None:
        m = self.mt5
        t = m.symbol_info_tick(self.symbol)
        buy = (side == BUY) if close_ticket is None else (side == SELL)
        req = {"action": m.TRADE_ACTION_DEAL, "symbol": self.symbol, "volume": lot,
               "type": m.ORDER_TYPE_BUY if buy else m.ORDER_TYPE_SELL,
               "price": t.ask if buy else t.bid, "deviation": DEVIATION_PTS, "magic": MAGIC,
               "comment": comment[:28], "type_time": m.ORDER_TIME_GTC, "type_filling": m.ORDER_FILLING_IOC}
        if close_ticket is not None:
            req["position"] = close_ticket
        r = m.order_send(req)
        if r is None or r.retcode != m.TRADE_RETCODE_DONE:
            jlog("emir_hatasi", side=side, lot=lot, retcode=getattr(r, "retcode", None), yorum=getattr(r, "comment", None))
            return None
        return float(r.price)

    def set_tp(self, side: str, tp: float) -> None:
        m = self.mt5
        tp = round(tp, self.info.digits)
        for p in self.positions(side):
            if abs(p.tp - tp) < self.info.point:
                continue
            r = m.order_send({"action": m.TRADE_ACTION_SLTP, "symbol": self.symbol, "position": p.ticket,
                              "sl": 0.0, "tp": tp, "magic": MAGIC})
            if r is None or r.retcode != m.TRADE_RETCODE_DONE:
                jlog("tp_hatasi", ticket=p.ticket, retcode=getattr(r, "retcode", None))

    def close_side(self, side: str) -> None:
        for p in self.positions(side):
            self.market(side, p.volume, f"{COMMENT_PREFIX} X", close_ticket=p.ticket)


def parse() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--terminal", default=None)
    ap.add_argument("--sembol", default="XAUUSD")
    ap.add_argument("--canli", action="store_true", help="gerçek emir (yalnız DEMO hesapta)")
    ap.add_argument("--demo-onayi", default="", help="--canli için 'EVET' yazılmalı")
    ap.add_argument("--taban", type=float, default=0.01)
    ap.add_argument("--carpan", type=float, default=1.1)
    ap.add_argument("--tp", type=float, default=5.0)
    ap.add_argument("--max-seviye", type=int, default=30)
    ap.add_argument("--max-sepet-zarar", type=float, default=1000.0)
    ap.add_argument("--max-toplam-zarar", type=float, default=2500.0)
    ap.add_argument("--min-marjin-seviyesi", type=float, default=300.0)
    return ap.parse_args()


def apply_live(mt: MT5Adapter, yon: KlonYonetici, e: Eylem) -> None:
    """Canlı modda bir eylemi uygular; dolum fiyatını yöneticiye işler."""
    if e.kind in (FRESH, ADD):
        fill = mt.market(e.side, e.lot, f"{COMMENT_PREFIX} {e.side[0]}{e.level}")
        if fill is None:
            # emir gitmediyse yöneticideki varsayılan seviyeyi geri al
            b = yon.sepet[e.side]
            if b is not None:
                b.lots.pop()
                b.pxs.pop()
                if not b.lots:
                    yon.disaridan_kapandi(e.side)
            return
        yon.dolum_duzelt(e.side, fill)
        b = yon.sepet[e.side]
        mt.set_tp(e.side, b.tp(yon.ayar))
    else:
        mt.close_side(e.side)


def main() -> None:
    args = parse()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ayar = KlonAyar(base_lot=args.taban, mult=args.carpan, tp_usd=args.tp, max_levels=args.max_seviye,
                    max_basket_loss=args.max_sepet_zarar)
    mt = MT5Adapter(args.terminal, args.sembol)
    canli = bool(args.canli)
    if canli and (args.demo_onayi != "EVET" or not mt.is_demo()):
        raise SystemExit("CANLI mod reddedildi: hesap DEMO değil veya --demo-onayi EVET verilmedi.")
    if canli and not mt.is_hedging():
        raise SystemExit("CANLI mod reddedildi: hesap hedge değil (netting'de iki yönlü sepet çalışmaz).")
    yon = KlonYonetici(ayar, mt.contract, max_total_loss=args.max_toplam_zarar)
    last_bar, sanal = load_state(yon)
    if canli:
        for s in (BUY, SELL):   # gerçek pozisyonlarla uzlaştır
            ps = sorted(mt.positions(s), key=lambda p: p.time_msc)
            yon.yukle({**yon.durum(), s: ({"lots": [p.volume for p in ps], "pxs": [p.price_open for p in ps]}
                                         if ps else None)})
    jlog("baslangic", mod="CANLI" if canli else "GOLGE", sembol=mt.symbol, contract=mt.contract,
         ayar={k: v for k, v in asdict(ayar).items() if k != "schedule"}, hesap=mt.account(), durum=yon.durum())
    log.info("DBG klon %s başladı (%s, magic %d)", "CANLI" if canli else "GÖLGE", mt.symbol, MAGIC)
    hb = 0.0
    ilk = mt.last_closed_bar(ayar.tf_min)
    if ilk is not None and ilk[0] != last_bar:
        last_bar = ilk[0]   # yarım barda başlatıldıysa o barda karar verme; ilk TAM bar açılışını bekle
    while True:
        try:
            tk = mt.tick()
            bar = mt.last_closed_bar(ayar.tf_min)
            if tk is None or bar is None:
                time.sleep(POLL_S)
                continue
            bid, ask = tk
            if canli:
                for s in (BUY, SELL):
                    if yon.sepet[s] is not None and not mt.positions(s):
                        jlog("disaridan_kapandi", side=s, level=yon.sepet[s].level)
                        yon.disaridan_kapandi(s)
            if bar[0] != last_bar:
                last_bar = bar[0]
                acc = mt.account()
                marj_ok = acc["margin"] == 0 or acc["margin_level"] >= args.min_marjin_seviyesi
                if marj_ok:
                    for e in yon.on_bar(bar[1], bid, ask, datetime.now(timezone.utc), taze_izinli=not OFF_FILE.exists()):
                        jlog(e.kind, **asdict(e), mod="CANLI" if canli else "GOLGE")
                        if canli:
                            apply_live(mt, yon, e)
                else:
                    jlog("marjin_freni", margin_level=acc["margin_level"])
                save_state(yon, last_bar, sanal)
            for e in yon.on_tick(bid, ask):
                jlog(e.kind, **asdict(e), mod="CANLI" if canli else "GOLGE")
                sanal["gerceklesen"] = sanal.get("gerceklesen", 0.0) + (e.pnl or 0.0)
                sanal["sepet"] = sanal.get("sepet", 0) + 1
                if canli:
                    apply_live(mt, yon, e)
                save_state(yon, last_bar, sanal)
            if yon.durduruldu:
                jlog("durdu", neden="toplam_kesici", durum=yon.durum())
                log.error("toplam zarar kesicisi tetiklendi — koşucu durdu")
                return
            if time.time() - hb > HEARTBEAT_S:
                hb = time.time()
                fl = {s: (None if b is None else round(b.floating(bid, ask, mt.contract), 2)) for s, b in yon.sepet.items()}
                jlog("nabiz", bid=bid, ask=ask, yuzen=fl, sanal=sanal,
                     seviye={s: (0 if b is None else b.level) for s, b in yon.sepet.items()})
        except Exception as exc:  # koşucu düşmesin; hata loglanır
            log.exception("döngü hatası")
            jlog("hata", mesaj=str(exc))
            time.sleep(5)
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
