"""DBG ızgara klonunun çok sembollü GÖLGE deneyi: NAS100, GER40, SpotCrude (+ referans XAUUSD).

Tamamen SANAL: emir göndermez, oturum açmaz; Pepperstone terminalinden yalnız tick okur.
Kenar iddiası yoktur: altında kart RED, kâr kuyruk riskinin karşılığı
(research/dbg_xau_tersine_20261029/RAPOR.md §17, research/dbg_duzeltme_20261104/RAPOR.md).
Soru: aynı mekanik başka sembolde kâr mı, zarar mı üretiyor, ne kadar derine iniyor.

Ölçekleme (2026-11-04'te sonuçlara bakmadan donduruldu):
  k = sembolün M3 gerçek aralık medyanı / XAUUSD'nin (kutu verisi, ~07-06 → 11-04).
  TP ve adım tablosu = altın değerleri × k, tick'e yuvarlı; adımı 0 olan seviyeler 0 kalır.
  Taban lot: 1. seviyede TP ≈ 5 $ olacak lot (altının 0,01 lotuyla aynı para), lot adımına yuvarlı.
Giriş kuralı ve UTC pencereleri altınla aynı: girişte kenar bulunmadı (RH-04), sembole göre
ayar seçmek geçmişe uydurma olurdu. Takip edilen iki varyant:
  A: kesicisiz (DBG botunun kendisi)   B: 30 seviye tavanı + sepet başına 1.000 $ kesici.
Her sembol her tick'te işlenir; karar, M3 barının ilk tick'inde o tick'in fiyatıyla verilir.
Yeniden başlatmada kaçan tick'ler filigrandan geri okunur, sanal hesapta boşluk kalmaz.

Veri: %LOCALAPPDATA%\\klon_coklu\\ (log, durum, ozet.json). Özet: python klon_coklu_ozet.py
Bilerek durdurmak: önce bu klasöre KLON_COKLU_DURDUR yazın; yoksa ajan yeniden başlatır.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "dbg_klon"))
from klon_kurallar import BUY, SELL, STEP_TABLE, KlonAyar  # noqa: E402
from klon_yonetici import KlonYonetici  # noqa: E402

TERMINAL = r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
SERVER_HINT = "Pepperstone"
VERI = Path(os.environ.get("LOCALAPPDATA") or HERE) / "klon_coklu"
LOG_FILE = VERI / "klon_coklu_log.jsonl"
STATE_FILE = VERI / "klon_coklu_state.json"
OZET_FILE = VERI / "ozet.json"
OFF_FILE = HERE / "KLON_COKLU_DURDUR"
KURAL = "C3-v2-olcekli-2026-11-04"
ALTIN_TP = 5.0
ALTIN_TR = 3.06          # XAUUSD M3 gerçek aralık medyanı (kutu, 40.000 bar)
TF_MS = 180_000
GUN_MS = 86_400_000
POLL_S = 1.0
NABIZ_S = 300
DURUM_S = 60
ILERI_S = 86_400
TICK_PARCA_S = 6 * 3600
KESICI_USD = 1000.0
SEVIYE_TAVANI = 30
SWAP_POINTS, SWAP_INTEREST = 1, 5   # SYMBOL_SWAP_MODE: puan / güncel fiyat üzerinden yıllık %


@dataclass(frozen=True)
class Sembol:
    ad: str
    tr: float          # M3 gerçek aralık medyanı
    tick: float
    digits: int
    taban: float       # 1. seviye TP ≈ 5 $
    lot_step: float
    min_lot: float

    @property
    def k(self) -> float:
        return self.tr / ALTIN_TR

    def ayar(self, kesicili: bool) -> KlonAyar:
        adimlar = tuple((upto, round(round(st * self.k / self.tick) * self.tick, self.digits)) for upto, st in STEP_TABLE)
        tp = round(round(ALTIN_TP * self.k / self.tick) * self.tick, self.digits)
        return KlonAyar(base_lot=self.taban, mult=1.1, tp_usd=tp, lot_step=self.lot_step, min_lot=self.min_lot,
                        step_table=adimlar, incl_end=True, strict_step=True, step0_no_body=True, px_digits=self.digits,
                        max_levels=SEVIYE_TAVANI if kesicili else 0, max_basket_loss=KESICI_USD if kesicili else 0.0)


SEMBOLLER = (
    Sembol("NAS100", 17.0, 0.1, 1, 0.2, 0.1, 0.1),
    Sembol("GER40", 12.0, 0.1, 1, 0.2, 0.1, 0.1),
    Sembol("SpotCrude", 0.137, 0.001, 3, 0.22, 0.01, 0.01),
    Sembol("XAUUSD", ALTIN_TR, 0.01, 2, 0.01, 0.01, 0.01),    # referans: aynı besleme, aynı koşucu
)
log = logging.getLogger("klon_coklu")


def jlog(olay: str, **kw: object) -> None:
    rec = {"ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "olay": olay, **kw}
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except OSError as exc:      # log yazılamıyor diye deney durmasın
        log.error("log yazılamadı: %s", exc)


def _ilk_pazar(y: int, ay: int, sira: int) -> date:
    d = date(y, ay, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7 + 7 * (sira - 1))


def sunucu_farki(gun: date) -> int:
    """Sunucu saati − UTC: ABD yaz saatinde +3, kışın +2 (DBG ve Pepperstone'da ölçüldü)."""
    return 3 if _ilk_pazar(gun.year, 3, 2) <= gun < _ilk_pazar(gun.year, 11, 1) else 2


def sunucu_utc(msc: int) -> datetime:
    srv = datetime.fromtimestamp(msc / 1000, tz=timezone.utc)
    return srv - timedelta(hours=sunucu_farki(srv.date()))


def yeni_istatistik() -> dict:
    return {"gerceklesen": 0.0, "swap": 0.0, "tp": 0, "kesici": 0, "taze": 0, "ekleme": 0, "max_seviye": 0,
            "en_kotu_yuzen": 0.0, "en_kotu_net": 0.0}


class SembolKlon:
    """Bir sembolün iki sanal varyantı. Saf: tick besle, olay al."""

    def __init__(self, s: Sembol, deger: float = 1.0, swap: dict | None = None) -> None:
        self.s = s
        self.deger = deger      # 1 lot × 1 fiyat birimi = kaç USD
        self.swap = swap or {}
        self.v = {"A": KlonYonetici(s.ayar(False), deger), "B": KlonYonetici(s.ayar(True), deger)}
        self.ist = {k: yeni_istatistik() for k in self.v}
        self.bar = self.ilk = self.son = self.gun = None
        self.wm = 0

    def deger_guncelle(self, deger: float, swap: dict) -> None:
        if deger > 0:
            self.deger = deger
            for y in self.v.values():
                y.contract = deger
        self.swap = swap or self.swap

    def _gece_swap(self, gun_ms: int, fiyat: float) -> None:
        """Gün devrinde açık lotlara tahmini swap. Üç katlı gün sembol bilgisinden."""
        sw = self.swap
        if not sw:
            return
        hafta = datetime.fromtimestamp(gun_ms * GUN_MS / 1000, tz=timezone.utc).weekday()
        kat = 3 if hafta == sw.get("uc_kat") else 1
        for ad, y in self.v.items():
            for side, b in y.sepet.items():
                if b is None:
                    continue
                oran = sw.get("long" if side == BUY else "short", 0.0)
                if sw.get("mod") == SWAP_POINTS:
                    birim = oran * sw.get("point", 0.0) * self.deger
                elif sw.get("mod") == SWAP_INTEREST:
                    birim = fiyat * oran / 100.0 / 360.0 * self.deger
                else:
                    birim = 0.0
                self.ist[ad]["swap"] += b.lot_sum * birim * kat

    def tick(self, msc: int, bid: float, ask: float) -> list[dict]:
        olaylar: list[dict] = []
        gun = msc // GUN_MS
        if self.gun is not None and gun != self.gun:
            self._gece_swap(self.gun, bid)
        self.gun = gun
        kova = msc // TF_MS
        if kova != self.bar:
            govde = float("nan") if self.bar is None else self.son - self.ilk
            self.bar, self.ilk = kova, bid
            utc = sunucu_utc(msc)
            for ad, y in self.v.items():
                for e in y.on_bar(govde, bid, ask, utc):
                    st = self.ist[ad]
                    st["taze" if e.kind == "fresh" else "ekleme"] += 1
                    st["max_seviye"] = max(st["max_seviye"], e.level)
                    olaylar.append({"sym": self.s.ad, "v": ad, "tur": e.kind, "side": e.side, "level": e.level,
                                    "lot": e.lot, "price": e.price, "tp": e.tp, "msc": msc})
        self.son = bid
        for ad, y in self.v.items():
            st = self.ist[ad]
            for e in y.on_tick(bid, ask):
                st["gerceklesen"] += e.pnl or 0.0
                st["tp" if e.kind == "tp" else "kesici"] += 1
                olaylar.append({"sym": self.s.ad, "v": ad, "tur": e.kind, "side": e.side, "level": e.level,
                                "lot": e.lot, "price": e.price, "pnl": e.pnl, "msc": msc})
            yz = sum(b.floating(bid, ask, y.contract) for b in y.sepet.values() if b is not None)
            st["en_kotu_yuzen"] = min(st["en_kotu_yuzen"], yz)
            st["en_kotu_net"] = min(st["en_kotu_net"], st["gerceklesen"] + st["swap"] + yz)
            st["_yuzen"] = yz
        self.wm = msc
        return olaylar

    def ozet(self) -> dict:
        out = {}
        for ad, y in self.v.items():
            st = self.ist[ad]
            yz = st.get("_yuzen", 0.0)
            out[ad] = {"net": round(st["gerceklesen"] + st["swap"] + yz, 2), "gerceklesen": round(st["gerceklesen"], 2),
                       "swap": round(st["swap"], 2), "yuzen": round(yz, 2), "tp": st["tp"], "kesici": st["kesici"],
                       "taze": st["taze"], "ekleme": st["ekleme"], "max_seviye": st["max_seviye"],
                       "en_kotu_yuzen": round(st["en_kotu_yuzen"], 2), "en_kotu_net": round(st["en_kotu_net"], 2),
                       "seviye": {s: (0 if b is None else b.level) for s, b in y.sepet.items()},
                       "lot": {s: (0 if b is None else round(b.lot_sum, 2)) for s, b in y.sepet.items()}}
        return out

    def durum(self) -> dict:
        return {"v": {k: y.durum() for k, y in self.v.items()}, "ist": self.ist, "bar": self.bar, "ilk": self.ilk,
                "son": self.son, "gun": self.gun, "wm": self.wm}

    def yukle(self, d: dict) -> None:
        for k, y in self.v.items():
            y.yukle(d["v"][k])
        self.ist = {k: {**yeni_istatistik(), **d["ist"].get(k, {})} for k in self.v}
        self.bar, self.ilk, self.son, self.gun, self.wm = d["bar"], d["ilk"], d["son"], d["gun"], d["wm"]


class Kosucu:
    """MT5'ten tick okur, SembolKlon'lara besler. Yalnız okuma çağrıları kullanır."""

    def __init__(self, mt5: object, simdi=time.time) -> None:
        self.mt5 = mt5
        self.simdi = simdi
        self.k = {s.ad: SembolKlon(s) for s in SEMBOLLER}
        self.sorgu: dict[str, int] = {}
        self.t_durum = self.t_nabiz = self.t_deger = 0.0
        self.portfoy_dip = {"A": 0.0, "B": 0.0}

    def baslat(self) -> None:
        acc = self.mt5.account_info()
        if acc is None or SERVER_HINT not in str(acc.server):
            raise RuntimeError(f"yanlış terminal: {getattr(acc, 'server', None)}")
        if STATE_FILE.exists():
            d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            self.portfoy_dip = d.get("portfoy_dip", self.portfoy_dip)
            for ad, sk in self.k.items():
                if ad in d.get("semboller", {}):
                    sk.yukle(d["semboller"][ad])
        self._deger_oku()
        for ad, sk in self.k.items():
            self.mt5.symbol_select(ad, True)
            tk = self.mt5.symbol_info_tick(ad)
            if not sk.wm and tk is not None:
                sk.wm = int(tk.time_msc)
            self.sorgu[ad] = sk.wm
        jlog("baslangic", kural=KURAL, server=acc.server, login=acc.login,
             olcek={s.ad: {"k": round(s.k, 4), "tp": s.ayar(False).tp_usd, "taban": s.taban,
                           "adim": s.ayar(False).step_table} for s in SEMBOLLER}, deger={a: sk.deger for a, sk in self.k.items()})

    def _deger_oku(self) -> None:
        for ad, sk in self.k.items():
            i = self.mt5.symbol_info(ad)
            if i is None or not i.trade_tick_size:
                continue
            sk.deger_guncelle(i.trade_tick_value / i.trade_tick_size,
                              {"mod": i.swap_mode, "long": i.swap_long, "short": i.swap_short, "point": i.point,
                               "uc_kat": i.swap_rollover3days})

    def _oku(self, ad: str, sk: SembolKlon) -> None:
        bas = self.sorgu[ad] / 1000
        simdi_srv = self.simdi() + ILERI_S
        bit = min(bas + TICK_PARCA_S, simdi_srv)
        tt = self.mt5.copy_ticks_range(ad, datetime.fromtimestamp(bas, tz=timezone.utc),
                                       datetime.fromtimestamp(bit, tz=timezone.utc), self.mt5.COPY_TICKS_ALL)
        if tt is None:
            return
        yeni = 0
        for t in tt:
            msc = int(t["time_msc"])
            if msc <= sk.wm or t["bid"] <= 0 or t["ask"] <= 0:
                continue
            yeni += 1
            for o in sk.tick(msc, float(t["bid"]), float(t["ask"])):
                jlog(o.pop("tur"), **o)
        if yeni:
            self.sorgu[ad] = sk.wm
        elif bit < simdi_srv - ILERI_S:      # uzun boşluk (hafta sonu, kapalı piyasa): sorguyu ilerlet
            self.sorgu[ad] = int(bit * 1000)

    def adim(self) -> None:
        for ad, sk in self.k.items():
            self._oku(ad, sk)
        now = self.simdi()
        if now - self.t_deger >= 3600:
            self.t_deger = now
            self._deger_oku()
        if now - self.t_durum >= DURUM_S:
            self.t_durum = now
            self._yaz()
        if now - self.t_nabiz >= NABIZ_S:
            self.t_nabiz = now
            jlog("nabiz", ozet={a: {v: {"net": o["net"], "yuzen": o["yuzen"], "seviye": o["seviye"]} for v, o in sk.ozet().items()}
                                for a, sk in self.k.items()}, portfoy_dip=self.portfoy_dip)

    def _yaz(self) -> None:
        oz = {a: sk.ozet() for a, sk in self.k.items()}
        for v in self.portfoy_dip:
            tp = sum(oz[a][v]["net"] for a in oz if a != "XAUUSD")
            self.portfoy_dip[v] = min(self.portfoy_dip[v], tp)
        try:
            VERI.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps({"semboller": {a: sk.durum() for a, sk in self.k.items()},
                                              "portfoy_dip": self.portfoy_dip}), encoding="utf-8")
            OZET_FILE.write_text(json.dumps({"ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kural": KURAL,
                                             "semboller": oz, "portfoy_dip": self.portfoy_dip}), encoding="utf-8")
        except OSError as exc:
            log.error("durum yazılamadı: %s", exc)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    VERI.mkdir(parents=True, exist_ok=True)
    if OFF_FILE.exists():
        log.info("KLON_COKLU_DURDUR var, başlatılmadı")
        return
    import MetaTrader5 as mt5  # noqa: N813
    if not mt5.initialize(TERMINAL):
        jlog("hata", mesaj=f"initialize başarısız: {mt5.last_error()}")
        raise SystemExit(f"initialize başarısız: {mt5.last_error()}")
    k = Kosucu(mt5)
    k.baslat()
    log.info("Çok sembol GÖLGE başladı (%s)", KURAL)
    while not OFF_FILE.exists():
        try:
            k.adim()
        except Exception as exc:  # deney düşmesin; hata loglanır
            log.exception("döngü hatası")
            jlog("hata", mesaj=repr(exc))
            time.sleep(5)
        time.sleep(POLL_S)
    k._yaz()
    jlog("durdu", neden="KLON_COKLU_DURDUR")


if __name__ == "__main__":
    main()
