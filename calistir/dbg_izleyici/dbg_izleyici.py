"""DBG 303733 canlı izleyici: gerçek botu SALT-OKUMA izler, hiçbir emir göndermez.

Ayrı terminal: C:\\Program Files\\MetaTrader 5 (investor girişi, kayıtlı oturum). Botun Pepperstone
terminaline dokunmaz. Şifre işlemez: yalnız terminalin kayıtlı oturumuna bağlanır, oturum açma çağrısı yok.

Her yoklamada (0,5 sn) kaydedilenler (log: %LOCALAPPDATA%\\dbg_izleyici\\dbg_izleyici_log.jsonl):
  giris / kapanis / tp_degisti / hacim_degisti : gerçek pozisyon değişimleri, ms zamanlı.
      MT5 geçmişinde olmayan TP değişiklik anı yalnız burada ölçülür.
  bar / bar_uyumsuz : her M3 açılışında GERÇEK durumla kuralın beklentisi (C3-v2) ve sonucu.
  sessizlik_basladi / sessizlik_bitti : ≥3 ardışık barda beklenen eylem yok. Başlangıç anının hesap
      durumu yazılır; nedeni kanıtlamaz ("neden belirsiz eylemsizlik").
  klon_* : aynı DBG fiyatıyla kapalı döngü klon (taban 0,05). Fiyat farkı karışmadan kural kıyası.
  hesap (60 sn), nabiz (5 dk), baglanti_yok / baglanti_geldi, hata.
Tick'ler: ticks\\YYYYMMDD.csv.gz (saatlik, gün sunucu saatine göre).

Bilerek durdurmak: önce bu klasöre DBG_IZLEYICI_DURDUR yazın; yoksa ajan yeniden başlatır.
Hesap 303733/DBG değilse ya da işlem izni açıksa çalışmayı reddeder.
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "dbg_klon"))
from klon_kurallar import BUY, NONE, SELL, KlonAyar, decide_side, in_window_dt  # noqa: E402
from klon_yonetici import KlonYonetici  # noqa: E402

TERMINAL = r"C:\Program Files\MetaTrader 5\terminal64.exe"
SYMBOL = "XAUUSD.GC"
LOGIN = 303733
SERVER_HINT = "DBG"
BOT_MAGIC = 6686
SIDES = (BUY, SELL)
VERI = Path(os.environ.get("LOCALAPPDATA") or HERE) / "dbg_izleyici"
LOG_FILE = VERI / "dbg_izleyici_log.jsonl"
STATE_FILE = VERI / "dbg_izleyici_state.json"
TICK_DIR = VERI / "ticks"
OFF_FILE = HERE / "DBG_IZLEYICI_DURDUR"
POLL_S = 0.5
BAR_WAIT_S = 20.0        # kuralın beklediği eylem için gerçek botu bekleme (C3'te gecikme %99 ≤ 3,1 sn)
QUIET_BARS = 3
HESAP_S = 60
NABIZ_S = 300
TICK_S = 3600
TICK_CHUNK_H = 6
RECONNECT_S = 60
# Kural sürümü: C3-v2 (research/dbg_xau_ilk_ayrisma_20261030). Taban ve TP gerçek botun güncel ayarı.
AYAR = KlonAyar(base_lot=0.05, mult=1.1, tp_usd=5.0, incl_end=True, strict_step=True, step0_no_body=True)
KURAL = "C3-v2-2026-10-30"

log = logging.getLogger("dbg_izleyici")


class GuvenlikHatasi(RuntimeError):
    """Beklenen salt-okuma DBG hesabı değil."""


def hesap_dogrula(acc: object) -> None:
    """Yalnız investor (işlem izni kapalı) DBG 303733 kabul edilir."""
    if acc is None:
        raise GuvenlikHatasi("hesap bilgisi yok")
    if acc.login != LOGIN or SERVER_HINT not in str(acc.server):
        raise GuvenlikHatasi(f"yanlış hesap: {acc.login} @ {acc.server}")
    if acc.trade_allowed:
        raise GuvenlikHatasi("işlem izni açık: bu izleyici yalnız investor girişiyle çalışır")


def jlog(olay: str, **kw: object) -> None:
    rec = {"ts_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "olay": olay, **kw}
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except OSError as exc:      # log yazılamıyor diye izleme durmasın
        log.error("log yazılamadı: %s", exc)


def poz_ozet(p: object) -> dict:
    return {"ticket": p.ticket, "side": BUY if p.type == 0 else SELL, "lot": p.volume, "price": p.price_open,
            "tp": p.tp, "sl": p.sl, "magic": p.magic, "time_msc": p.time_msc, "comment": p.comment}


class Izleyici:
    """Karar mantığı; MT5 modülü dışarıdan verilir (testte sahte, kutuda gerçek)."""

    def __init__(self, mt5: object, simdi=time.time) -> None:
        self.mt5 = mt5
        self.simdi = simdi
        self.poz: dict[int, dict] = {}
        self.son_bar = 0
        self.bekleyen: dict | None = None
        self.sessiz_bar = 0
        self.sessiz_aktif = False
        self.tick_wm = 0
        self.t_hesap = self.t_nabiz = self.t_tick = self.t_baglan = 0.0
        self.bagli = True
        self.sayac = {"giris": 0, "kapanis": 0, "tp_degisti": 0, "bar": 0, "bar_uyumsuz": 0}
        info = mt5.symbol_info(SYMBOL)
        self.klon = KlonYonetici(AYAR, float(info.trade_contract_size) if info else 100.0)
        self.klon_kar = 0.0

    # ------------------------------------------------------------ başlangıç / durum
    def baslat(self) -> None:
        acc = self.mt5.account_info()
        hesap_dogrula(acc)
        self._durum_yukle()
        self.poz = {p.ticket: poz_ozet(p) for p in self._pozisyonlar()}
        bar = self._bar()
        if bar:
            self.son_bar = bar[0]     # yarım barda karar yok: ilk TAM bar açılışını bekle
        tk = self.mt5.symbol_info_tick(SYMBOL)
        if not self.tick_wm and tk:
            self.tick_wm = int(tk.time_msc)
        jlog("baslangic", kural=KURAL, login=acc.login, server=acc.server, trade_allowed=acc.trade_allowed,
             balance=acc.balance, equity=acc.equity, acik=list(self.poz.values()), klon=self.klon.durum())

    def _durum_yukle(self) -> None:
        if STATE_FILE.exists():
            d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            self.klon.yukle(d.get("klon", {}))
            self.tick_wm = int(d.get("tick_wm", 0))
            self.klon_kar = float(d.get("klon_kar", 0.0))

    def _durum_yaz(self) -> None:
        try:
            STATE_FILE.write_text(json.dumps({"klon": self.klon.durum(), "tick_wm": self.tick_wm,
                                              "klon_kar": self.klon_kar}), encoding="utf-8")
        except OSError as exc:
            log.error("durum yazılamadı: %s", exc)

    # ------------------------------------------------------------ MT5 okuma
    def _pozisyonlar(self) -> list:
        return list(self.mt5.positions_get(symbol=SYMBOL) or [])

    def _bar(self) -> tuple[int, float] | None:
        r = self.mt5.copy_rates_from_pos(SYMBOL, self.mt5.TIMEFRAME_M3, 0, 2)
        if r is None or len(r) < 2:
            return None
        return int(r[-1]["time"]), float(r[-2]["close"] - r[-2]["open"])

    def _yan_durum(self, side: str) -> dict:
        L = sorted((p for p in self.poz.values() if p["side"] == side and p["magic"] == BOT_MAGIC),
                   key=lambda p: p["time_msc"])
        lots = sum(p["lot"] for p in L)
        return {"n": len(L), "lots": round(lots, 2), "son_px": L[-1]["price"] if L else None,
                "vwap": round(sum(p["lot"] * p["price"] for p in L) / lots, 3) if L else None}

    # ------------------------------------------------------------ bağlantı
    def baglanti_tamam(self) -> bool:
        """Kopuksa terminale yeniden bağlanır (kapalıysa initialize açar). Şifre girmez."""
        ti = self.mt5.terminal_info()
        if ti is not None and ti.connected:
            if not self.bagli:
                jlog("baglanti_geldi")
                self.bagli = True
            return True
        if self.bagli:
            jlog("baglanti_yok", son_hata=str(self.mt5.last_error()))
            self.bagli = False
        now = self.simdi()
        if now - self.t_baglan >= RECONNECT_S:
            self.t_baglan = now
            self.mt5.initialize(TERMINAL)
            acc = self.mt5.account_info()
            if acc is not None:
                hesap_dogrula(acc)
        return False

    # ------------------------------------------------------------ pozisyon farkı
    def _pozisyon_farki(self, tick_msc: int) -> list[str]:
        yeni = {p.ticket: poz_ozet(p) for p in self._pozisyonlar()}
        girenler = []
        for t, p in yeni.items():
            eski = self.poz.get(t)
            if eski is None:
                n = sum(1 for q in self.poz.values() if q["side"] == p["side"] and q["magic"] == p["magic"])
                jlog("giris", **p, n_acik_once=n, bar_sn=round((p["time_msc"] / 1000) % 180, 3), goruldu_msc=tick_msc)
                self.sayac["giris"] += 1
                girenler.append(p["side"])
                continue
            if eski["tp"] != p["tp"]:
                jlog("tp_degisti", ticket=t, side=p["side"], eski=eski["tp"], yeni=p["tp"], goruldu_msc=tick_msc)
                self.sayac["tp_degisti"] += 1
            if eski["lot"] != p["lot"]:
                jlog("hacim_degisti", ticket=t, side=p["side"], eski=eski["lot"], yeni=p["lot"], goruldu_msc=tick_msc)
        for t, p in self.poz.items():
            if t not in yeni:
                jlog("kapanis", **p, goruldu_msc=tick_msc, **self._kapanis_bilgi(t))
                self.sayac["kapanis"] += 1
        self.poz = yeni
        return girenler

    def _kapanis_bilgi(self, ticket: int) -> dict:
        ds = self.mt5.history_deals_get(position=ticket) or []
        cik = [d for d in ds if d.entry == 1]
        if not cik:
            return {"deal": None}
        d = cik[-1]
        return {"cikis_msc": d.time_msc, "cikis_px": d.price, "reason": d.reason, "profit": d.profit,
                "swap": d.swap, "cikis_comment": d.comment}

    # ------------------------------------------------------------ bar: beklenti ve sessizlik
    def _yeni_bar(self, bar: tuple[int, float], bid: float, ask: float) -> None:
        utc = datetime.fromtimestamp(self.simdi(), tz=timezone.utc)
        win = in_window_dt(utc, AYAR.schedule, AYAR.incl_end)
        taraf = {}
        for s in SIDES:
            st = self._yan_durum(s)
            px = ask if s == BUY else bid
            st["beklenen"] = decide_side(s, bar[1], st["n"], st["son_px"] or 0.0, px, win, AYAR)
            taraf[s] = st
        jlog("bar", t=bar[0], govde=round(bar[1], 3), bid=bid, ask=ask, spread=round(ask - bid, 3), pencere=win, **taraf)
        self.sayac["bar"] += 1
        self.bekleyen = {"t": bar[0], "son": self.simdi() + BAR_WAIT_S, "bek": {s: taraf[s]["beklenen"] for s in SIDES},
                         "giren": []}
        for e in self.klon.on_bar(bar[1], bid, ask, utc):
            jlog("klon_" + e.kind, side=e.side, level=e.level, lot=e.lot, price=e.price, tp=e.tp)
        self._durum_yaz()

    def _bar_kontrol(self) -> None:
        b = self.bekleyen
        if b is None or self.simdi() < b["son"]:
            return
        self.bekleyen = None
        bek = {s: k for s, k in b["bek"].items() if k != NONE}
        uyumsuz = [s for s in SIDES if (b["bek"][s] != NONE) != (s in b["giren"])]
        if uyumsuz:
            self.sayac["bar_uyumsuz"] += 1
            jlog("bar_uyumsuz", t=b["t"], beklenen=b["bek"], giren=b["giren"])
        if b["giren"]:
            if self.sessiz_aktif:
                jlog("sessizlik_bitti", t=b["t"], sessiz_bar=self.sessiz_bar, giren=b["giren"])
                self.sessiz_aktif = False
            self.sessiz_bar = 0
        elif bek:
            self.sessiz_bar += 1
            if self.sessiz_bar >= QUIET_BARS and not self.sessiz_aktif:
                self.sessiz_aktif = True
                a = self.mt5.account_info()
                jlog("sessizlik_basladi", t=b["t"], sessiz_bar=self.sessiz_bar, beklenen=bek,
                     balance=a.balance, equity=a.equity, margin=a.margin, margin_level=a.margin_level,
                     durum={s: self._yan_durum(s) for s in SIDES})

    # ------------------------------------------------------------ tick arşivi
    def _tick_arsivle(self, son_msc: int) -> None:
        """Filigrandan itibaren tick'leri ekler. Saat parametreleri tick epoch'uyla aynı eksende."""
        if not self.tick_wm or son_msc <= self.tick_wm:
            return
        bas = datetime.fromtimestamp(self.tick_wm / 1000, tz=timezone.utc)
        bit = min(bas + timedelta(hours=TICK_CHUNK_H), datetime.fromtimestamp(son_msc / 1000 + 1, tz=timezone.utc))
        tt = self.mt5.copy_ticks_range(SYMBOL, bas, bit, self.mt5.COPY_TICKS_ALL)
        if tt is None:
            jlog("hata", mesaj=f"tick okunamadı: {self.mt5.last_error()}")
            return
        rows = [t for t in tt if int(t["time_msc"]) > self.tick_wm]
        if not rows:
            self.tick_wm = int(bit.timestamp() * 1000) if bit.timestamp() * 1000 < son_msc else self.tick_wm
            return
        by_day: dict[str, list[str]] = {}
        for t in rows:
            g = datetime.fromtimestamp(int(t["time_msc"]) / 1000, tz=timezone.utc).strftime("%Y%m%d")
            by_day.setdefault(g, []).append(f'{int(t["time_msc"])},{t["bid"]},{t["ask"]},{int(t["flags"])}\n')
        TICK_DIR.mkdir(parents=True, exist_ok=True)
        for g, lines in by_day.items():
            with gzip.open(TICK_DIR / f"{g}.csv.gz", "at", encoding="ascii") as f:
                f.writelines(lines)
        self.tick_wm = int(rows[-1]["time_msc"])
        self._durum_yaz()

    # ------------------------------------------------------------ tek adım
    def adim(self) -> None:
        if not self.baglanti_tamam():
            return
        tk = self.mt5.symbol_info_tick(SYMBOL)
        if tk is None:
            return
        now = self.simdi()
        bid, ask, msc = float(tk.bid), float(tk.ask), int(tk.time_msc)
        girenler = self._pozisyon_farki(msc)
        if self.bekleyen is not None:
            self.bekleyen["giren"].extend(s for s in girenler if s not in self.bekleyen["giren"])
        self._bar_kontrol()
        bar = self._bar()
        if bar and bar[0] != self.son_bar:
            self.son_bar = bar[0]
            self._yeni_bar(bar, bid, ask)
        for e in self.klon.on_tick(bid, ask):
            self.klon_kar += e.pnl or 0.0
            jlog("klon_" + e.kind, side=e.side, level=e.level, lot=e.lot, price=e.price, pnl=e.pnl)
            self._durum_yaz()
        if now - self.t_hesap >= HESAP_S:
            self.t_hesap = now
            a = self.mt5.account_info()
            if a is not None:
                hesap_dogrula(a)
                jlog("hesap", balance=a.balance, equity=a.equity, margin=a.margin, margin_level=a.margin_level,
                     acik={s: self._yan_durum(s) for s in SIDES})
        if now - self.t_tick >= TICK_S:
            self.t_tick = now
            self._tick_arsivle(msc)
        if now - self.t_nabiz >= NABIZ_S:
            self.t_nabiz = now
            jlog("nabiz", bid=bid, ask=ask, sayac=self.sayac, sessiz_bar=self.sessiz_bar, klon_kar=round(self.klon_kar, 2),
                 klon_seviye={s: (0 if b is None else b.level) for s, b in self.klon.sepet.items()}, tick_wm=self.tick_wm)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    VERI.mkdir(parents=True, exist_ok=True)
    if OFF_FILE.exists():
        log.info("DBG_IZLEYICI_DURDUR var, başlatılmadı")
        return
    import MetaTrader5 as mt5  # noqa: N813
    if not mt5.initialize(TERMINAL):
        jlog("hata", mesaj=f"initialize başarısız: {mt5.last_error()}")
        raise SystemExit(f"initialize başarısız: {mt5.last_error()}")
    mt5.symbol_select(SYMBOL, True)
    iz = Izleyici(mt5)
    try:
        iz.baslat()
    except GuvenlikHatasi as exc:
        jlog("reddedildi", mesaj=str(exc))
        raise SystemExit(f"REDDEDİLDİ: {exc}") from exc
    log.info("DBG izleyici başladı (%s, salt-okuma)", KURAL)
    while not OFF_FILE.exists():
        try:
            iz.adim()
        except GuvenlikHatasi as exc:
            jlog("reddedildi", mesaj=str(exc))
            raise SystemExit(f"REDDEDİLDİ: {exc}") from exc
        except Exception as exc:  # izleme düşmesin; hata loglanır
            log.exception("döngü hatası")
            jlog("hata", mesaj=repr(exc))
            time.sleep(5)
        time.sleep(POLL_S)
    jlog("durdu", neden="DBG_IZLEYICI_DURDUR")


if __name__ == "__main__":
    main()
