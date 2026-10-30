"""DBG 303733 botunun (dönem C3) kural klonu — saf, bağımlılıksız karar çekirdeği.

Bu dosya hem geri test motorunda (`../klon_motor.py`) hem canlı/gölge
koşucuda (`dbg_klon_runner.py`) AYNEN kullanılır: test edilen kod = çalışan kod.

Kurallar (tersine mühendislikle ölçüldü, bkz. ../RAPOR.md §3 ve §13):
  * Her TF (M3) bar açılışında, her yön (BUY/SELL) için bağımsız karar.
  * Taze giriş: o yönün sepeti boş + az önce kapanan barın gövdesi (bid) o yönde
    + saat UTC işlem penceresinde.
  * Ekleme: önceki bar sepete KARŞI kapanmış + fiyat son girişten en az
    adım(seviye) kadar kötüleşmiş (>0). Ekleme pencereden bağımsız.
  * Lot: round(taban × çarpan^(n−1)) lot adımına; TP: lot-ağırlıklı ortalama ± tp_usd.
  * Orijinal botta stop yok. Bu klona iki emniyet kesicisi eklendi (varsayılan kapalı
    geri testte, AÇIK canlı pakette): seviye tavanı ve sepet başına zarar tavanı.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

BUY, SELL = "BUY", "SELL"
FRESH, ADD, NONE = "fresh", "add", "none"

# Seviye -> son girişe göre gereken minimum ters hareket ($).
STEP_TABLE: tuple[tuple[int, float], ...] = ((5, 0.50), (10, 0.00), (20, 1.00), (30, 0.50), (10_000, 1.00))

# UTC saat pencereleri, gün: 0=Pzt ... 4=Cum. [a, b) yarı açık.
SCHEDULE_C3: dict[int, tuple[tuple[int, int], ...]] = {
    0: ((0, 6), (8, 12), (14, 15), (16, 17)),
    1: ((0, 6), (8, 12), (14, 15), (16, 17)),
    2: ((2, 6), (8, 12), (14, 15), (16, 17)),
    3: ((0, 6), (8, 12), (14, 15), (16, 17)),
    4: ((0, 2),),
}
EPS = 1e-9


@dataclass(frozen=True)
class KlonAyar:
    """Klonun tüm ayarları. Varsayılanlar DBG dönem C3 değerleri."""

    tf_min: int = 3
    base_lot: float = 0.05
    mult: float = 1.1
    tp_usd: float = 5.0
    lot_step: float = 0.01
    min_lot: float = 0.01
    step_table: tuple[tuple[int, float], ...] = STEP_TABLE
    schedule: dict[int, tuple[tuple[int, int], ...]] = field(default_factory=lambda: dict(SCHEDULE_C3))
    max_levels: int = 0            # 0 = sınırsız; tavanda yeni ekleme yapılmaz (sepet TP'yi bekler)
    max_basket_loss: float = 0.0   # hesap para birimi; 0 = kapalı; yüzen zarar bunu aşınca sepet kapatılır

    def __hash__(self) -> int:  # dict alanı yüzünden elle
        return hash((self.tf_min, self.base_lot, self.mult, self.tp_usd, self.lot_step, self.min_lot,
                     self.step_table, tuple(sorted(self.schedule.items())), self.max_levels,
                     self.max_basket_loss))


def step_for_level(level: int, table: tuple[tuple[int, float], ...] = STEP_TABLE) -> float:
    """Yeni seviye `level` (2, 3, ...) açılabilmesi için gereken minimum ters hareket ($)."""
    for upto, step in table:
        if level <= upto:
            return step
    return table[-1][1]


def lot_for_level(ayar: KlonAyar, level: int) -> float:
    """Seviye lotu: taban × çarpan^(n−1), lot adımına yuvarlanmış, en az min_lot."""
    raw = ayar.base_lot * ayar.mult ** (level - 1)
    n = round(raw / ayar.lot_step + EPS)
    return max(ayar.min_lot, round(n * ayar.lot_step, 8))


def in_window_utc(dow: int, hour: int, schedule: dict[int, tuple[tuple[int, int], ...]]) -> bool:
    """UTC gün/saat taze giriş penceresinde mi?"""
    for a, b in schedule.get(dow, ()):
        if a <= hour < b:
            return True
    return False


def in_window_dt(utc: datetime, schedule: dict[int, tuple[tuple[int, int], ...]]) -> bool:
    return in_window_utc(utc.weekday(), utc.hour, schedule)


def decide_side(side: str, body_prev: float, level: int, last_px: float, px_now: float,
                in_win: bool, ayar: KlonAyar) -> str:
    """Bir yön için TF bar açılışındaki eylem.

    Args:
        side: "BUY" | "SELL".
        body_prev: az önce kapanan TF barının bid gövdesi (kapanış − açılış).
        level: sepetteki mevcut seviye sayısı (0 = boş).
        last_px: sepetin son giriş fiyatı (BUY ask, SELL bid; boşsa yok sayılır).
        px_now: şimdiki giriş fiyatı (BUY ask, SELL bid).
        in_win: şimdiki UTC saat taze giriş penceresinde mi.
    Returns:
        "fresh" | "add" | "none".
    """
    if body_prev != body_prev or body_prev == 0:  # NaN veya doji
        return NONE
    sg = 1.0 if side == BUY else -1.0
    with_bar = body_prev * sg > 0
    if level == 0:
        return FRESH if (with_bar and in_win) else NONE
    if with_bar:
        return NONE
    if ayar.max_levels and level >= ayar.max_levels:
        return NONE
    adverse = (last_px - px_now) * sg
    need = step_for_level(level + 1, ayar.step_table)
    if adverse > 0 and adverse > need - EPS:
        return ADD
    return NONE


def basket_tp(side: str, lots: list[float], pxs: list[float], ayar: KlonAyar) -> float:
    """Sepetin ortak TP fiyatı: lot-ağırlıklı ortalama ± tp_usd."""
    tot = sum(lots)
    vwap = sum(l * p for l, p in zip(lots, pxs)) / tot
    return vwap + (ayar.tp_usd if side == BUY else -ayar.tp_usd)


def basket_floating(side: str, lots: list[float], pxs: list[float], px_close: float, contract: float) -> float:
    """Sepetin yüzen kâr/zararı (hesap para birimi). px_close: BUY bid, SELL ask."""
    sg = 1.0 if side == BUY else -1.0
    return sg * sum(l * (px_close - p) for l, p in zip(lots, pxs)) * contract
