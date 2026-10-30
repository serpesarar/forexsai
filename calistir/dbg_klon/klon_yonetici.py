"""Klon sepet yöneticisi — olay güdümlü, MT5'ten bağımsız durum makinesi.

Koşucu (`dbg_klon_runner.py`) iki olay besler:
  * on_bar(body_prev, bid, ask, utc)  — yeni M3 barının ilk tick'inde: taze giriş / ekleme
  * on_tick(bid, ask)                 — her tick'te: kesici ve TP kontrolü
Her çağrı uygulanacak eylemlerin listesini döner ve iç durumu VARSAYILAN fiyatla günceller.
Canlı modda gerçek dolum fiyatı `dolum_duzelt` ile bildirilir.

Geri test motoruyla eşdeğerliği `test_klon_paket.py` sınar (aynı olay dizisi).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from klon_kurallar import ADD, BUY, FRESH, SELL, KlonAyar, decide_side, in_window_dt, lot_for_level

TP, KESICI, TOPLAM_KESICI = "tp", "kesici", "toplam_kesici"


@dataclass
class Sepet:
    side: str
    lots: list[float] = field(default_factory=list)
    pxs: list[float] = field(default_factory=list)

    @property
    def level(self) -> int:
        return len(self.lots)

    @property
    def lot_sum(self) -> float:
        return sum(self.lots)

    def tp(self, ayar: KlonAyar) -> float:
        vw = sum(l * p for l, p in zip(self.lots, self.pxs)) / self.lot_sum
        return vw + (ayar.tp_usd if self.side == BUY else -ayar.tp_usd)

    def floating(self, bid: float, ask: float, contract: float) -> float:
        if self.side == BUY:
            return sum(l * (bid - p) for l, p in zip(self.lots, self.pxs)) * contract
        return sum(l * (p - ask) for l, p in zip(self.lots, self.pxs)) * contract


@dataclass
class Eylem:
    kind: str           # fresh | add | tp | kesici | toplam_kesici
    side: str
    level: int
    lot: float
    price: float
    tp: float | None = None
    pnl: float | None = None


class KlonYonetici:
    """İki bağımsız sepet (BUY/SELL) + emniyet kesicileri."""

    def __init__(self, ayar: KlonAyar, contract: float, max_total_loss: float = 0.0) -> None:
        self.ayar = ayar
        self.contract = contract
        self.max_total_loss = max_total_loss
        self.sepet: dict[str, Sepet | None] = {BUY: None, SELL: None}
        self.durduruldu = False

    # ---------------------------------------------------------------- olaylar
    def on_bar(self, body_prev: float, bid: float, ask: float, utc: datetime, taze_izinli: bool = True) -> list[Eylem]:
        """Yeni TF barının ilk tick'i. taze_izinli=False → yalnız ekleme (kill-switch dosyası vb.)."""
        out: list[Eylem] = []
        if self.durduruldu:
            return out
        win = in_window_dt(utc, self.ayar.schedule) and taze_izinli
        for s in (BUY, SELL):
            b = self.sepet[s]
            px = ask if s == BUY else bid
            lvl = 0 if b is None else b.level
            last = 0.0 if b is None else b.pxs[-1]
            act = decide_side(s, body_prev, lvl, last, px, win, self.ayar)
            if act == FRESH:
                lot = lot_for_level(self.ayar, 1)
                b = Sepet(s, [lot], [px])
                self.sepet[s] = b
                out.append(Eylem(FRESH, s, 1, lot, px, b.tp(self.ayar)))
            elif act == ADD:
                lot = lot_for_level(self.ayar, lvl + 1)
                b.lots.append(lot)
                b.pxs.append(px)
                out.append(Eylem(ADD, s, b.level, lot, px, b.tp(self.ayar)))
        return out

    def on_tick(self, bid: float, ask: float) -> list[Eylem]:
        """Kesici önce (muhafazakâr), sonra TP. Toplam kesici tüm sepetleri kapatır ve durdurur."""
        out: list[Eylem] = []
        lim = self.ayar.max_basket_loss
        for s in (BUY, SELL):
            b = self.sepet[s]
            if b is None:
                continue
            fl = b.floating(bid, ask, self.contract)
            if lim and fl <= -lim:
                out.append(self._kapat(s, KESICI, bid, ask))
                continue
            tp = b.tp(self.ayar)
            if (bid >= tp) if s == BUY else (ask <= tp):
                out.append(self._kapat(s, TP, bid, ask, px=tp))
        if self.max_total_loss:
            tot = sum(b.floating(bid, ask, self.contract) for b in self.sepet.values() if b is not None)
            if tot <= -self.max_total_loss:
                for s in (BUY, SELL):
                    if self.sepet[s] is not None:
                        out.append(self._kapat(s, TOPLAM_KESICI, bid, ask))
                self.durduruldu = True
        return out

    # ---------------------------------------------------------------- yardımcılar
    def _kapat(self, s: str, kind: str, bid: float, ask: float, px: float | None = None) -> Eylem:
        b = self.sepet[s]
        if px is None:
            px = bid if s == BUY else ask
        sg = 1.0 if s == BUY else -1.0
        pnl = sg * sum(l * (px - p) for l, p in zip(b.lots, b.pxs)) * self.contract
        self.sepet[s] = None
        return Eylem(kind, s, b.level, b.lot_sum, px, None, pnl)

    def dolum_duzelt(self, side: str, fill_px: float) -> None:
        """Canlı modda son girişin gerçek dolum fiyatını işler (TP yeniden hesaplanır)."""
        b = self.sepet[side]
        if b is not None:
            b.pxs[-1] = fill_px

    def disaridan_kapandi(self, side: str) -> None:
        """Sunucu TP'si veya elle kapanış: sepeti boşalt."""
        self.sepet[side] = None

    def durum(self) -> dict:
        return {s: (None if b is None else {"level": b.level, "lots": b.lots, "pxs": b.pxs})
                for s, b in self.sepet.items()} | {"durduruldu": self.durduruldu}

    def yukle(self, d: dict) -> None:
        for s in (BUY, SELL):
            v = d.get(s)
            self.sepet[s] = None if not v else Sepet(s, list(v["lots"]), list(v["pxs"]))
        self.durduruldu = bool(d.get("durduruldu", False))
