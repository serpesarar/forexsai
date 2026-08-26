"""Kanonik sinyal başarı metrikleri — TEK DOĞRULUK KAYNAĞI.

Bu modül, 2026-08-21 çekirdek (Core) denetiminde bulunan dört sistemik şişirme
kusurunu kalıcı olarak kapatmak için yazıldı. Panellerde/endpoint'lerde bir daha
"çıplak win rate" hesaplanmamalı; hepsi ``aggregate_outcomes`` üzerinden geçmeli.

## Kapatılan dört kusur

1. **Çıplak WR yanıltıcıdır.** RR 0,53 geometrisinde %79 WR, RR 2,0'da %45'ten
   KÖTÜDÜR. Artık her WR yanında ``breakeven_wr`` (geometrinin gerektirdiği
   başabaş oranı) ve ``expectancy_r`` (asıl karar metriği) zorunlu döner.
   ``edge_pp = wr - breakeven_wr`` negatifse WR yüksek olsa da kenar YOKTUR.

2. **Aynı-bar TP+SL iyimser çözülüyordu.** ``signal_lifecycle`` bir mumda hem TP
   hem SL değdiğinde TP'yi önce işaretleyip WIN yazıyordu; ``shadow_trade_tracker``
   aynı olayı konservatif kayıp sayıyor. İki sistem aynı olayı zıt etiketliyordu.
   Burada konservatif taraf kanon: ``ambiguous_loss``.

3. **``tp1_3_hit_then_sl`` tam WIN sayılıyordu.** TP1 (≈0,53R) vurup sonra SL
   yiyen sinyal, TP4'e giden sinyalle aynı ağırlıkta "kazanç" oluyordu. Artık
   ayrı sınıf: ``partial`` — WR'a girer ama R'si gerçek realize üzerinden.

4. **Epoch'lar karıştırılıyordu.** ``factors.target_type`` üç ayrı geometri
   dönemini (``static_pips`` RR≈0,53 / ``meta_engine`` / ``atr_ladder_v1``) aynı
   sayıda topluyordu. XAU BUY: static_pips %81,1 (bitiş 2026-05-19) vs güncel
   atr_ladder_v1 %13,3. ``by_epoch`` her zaman ayrı döner ve ``mixed_epochs``
   bayrağı karışım varsa uyarır.

Kullanım::

    from services.signal_metrics import aggregate_outcomes
    m = aggregate_outcomes(rows, default_symbol="NDX.INDX")
    m.win_rate, m.expectancy_r, m.breakeven_wr, m.edge_pp, m.by_epoch

Not: ``signal_analytics.classify_signal`` geriye dönük uyumluluk için
korunuyor (eski çağrı yerleri kırılmasın) ama YENİ kod bu modülü kullanmalı.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from services.signal_analytics import (
    canonical_stop_loss_pips,
    classify_signal,
    coerce_float,
    normalized_targets_hit,
    parse_json_object,
    realized_pips,
    target_hit_profit_floor,
)

logger = logging.getLogger(__name__)

# ── sonuç sınıfları ─────────────────────────────────────────────────────────
WIN = "win"                       # hedefe ulaştı, tam kazanç
PARTIAL = "partial"               # TP1-3 gördü ama sonra SL — kısmi
LOSS = "loss"                     # SL vuruşu
AMBIGUOUS_LOSS = "ambiguous_loss"  # aynı barda TP+SL, sıra bilinmiyor → konservatif
NEUTRAL = "neutral"               # expired / flip_closed — WR'a girmez
OPEN = "open"                     # henüz çözülmemiş

#: WR paydasına giren sınıflar. NEUTRAL ve OPEN bilinçli olarak dışarıda.
WR_CLASSES = frozenset({WIN, PARTIAL, LOSS, AMBIGUOUS_LOSS})
#: WR payına giren sınıflar.
WIN_CLASSES = frozenset({WIN, PARTIAL})

#: Aynı barda hem TP hem SL değdiğini gösteren çözüm sebepleri.
_SAME_BAR_REASONS = frozenset({"tp1_3_hit_then_sl"})

#: Epoch etiketi bulunmayan satırlar için. Karışım tespitinde sayılır.
UNKNOWN_EPOCH = "unknown"

#: Makul R bandı. Dışına çıkan satır bozuk kabul edilir (exit_price=0, kayıp
#: stop mesafesi, birim karışması…) ve beklenti hesabına ALINMAZ.
#: −1,5: en kötü meşru sonuç (SL + kayma). +25: TP4 × geniş merdiven bile aşamaz.
R_PLAUSIBLE_MIN = -1.5
R_PLAUSIBLE_MAX = 25.0


@dataclass(frozen=True)
class Outcome:
    """Tek bir sinyalin kanonik sonucu."""

    klass: str
    r_multiple: Optional[float]
    epoch: str
    reason: str
    realized: Optional[float] = None
    stop_distance: Optional[float] = None

    @property
    def counts_in_wr(self) -> bool:
        return self.klass in WR_CLASSES

    @property
    def is_win(self) -> bool:
        return self.klass in WIN_CLASSES


@dataclass
class Metrics:
    """Bir sinyal kümesinin dürüst karnesi.

    ``win_rate`` TEK BAŞINA okunmamalıdır — ``edge_pp`` negatifse yüksek WR
    kenar anlamına gelmez (kötü geometriyle satın alınmıştır).
    """

    n: int = 0
    wins: int = 0
    partials: int = 0
    losses: int = 0
    ambiguous: int = 0
    neutral: int = 0
    open_n: int = 0
    win_rate: Optional[float] = None
    expectancy_r: Optional[float] = None
    median_r: Optional[float] = None
    breakeven_wr: Optional[float] = None
    edge_pp: Optional[float] = None
    avg_rr_geometry: Optional[float] = None
    total_r: float = 0.0
    excluded_r: int = 0
    mixed_epochs: bool = False
    by_epoch: Dict[str, "Metrics"] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "wins": self.wins,
            "partials": self.partials,
            "losses": self.losses,
            "ambiguous": self.ambiguous,
            "neutral": self.neutral,
            "open": self.open_n,
            "win_rate": self.win_rate,
            "expectancy_r": self.expectancy_r,
            "median_r": self.median_r,
            "breakeven_wr": self.breakeven_wr,
            "edge_pp": self.edge_pp,
            "avg_rr_geometry": self.avg_rr_geometry,
            "total_r": round(self.total_r, 3),
            "excluded_r": self.excluded_r,
            "mixed_epochs": self.mixed_epochs,
            "warnings": self.warnings,
            "by_epoch": {k: v.to_dict() for k, v in self.by_epoch.items()},
        }


# ── yardımcılar ─────────────────────────────────────────────────────────────

def signal_epoch(sig: dict) -> str:
    """``factors.target_type`` epoch etiketi.

    Geometri dönemleri karşılaştırılamaz: ``static_pips`` sabit TP/SL (RR≈0,53),
    ``atr_ladder_v1`` ATR merdiveni (RR≥1). Aynı havuzda toplanırsa WR anlamsız.
    """
    factors = parse_json_object(sig.get("factors"))
    raw = factors.get("target_type") if isinstance(factors, dict) else None
    text = str(raw).strip() if raw not in (None, "") else ""
    return text or UNKNOWN_EPOCH


def _geometry_rr(sig: dict, default_symbol: Optional[str]) -> Optional[float]:
    """TP1 mesafesi / SL mesafesi — sinyalin İLAN EDİLEN risk-ödül geometrisi.

    ⚠️ Bilinçli olarak SONUÇTAN BAĞIMSIZ: ``target_hit_profit_floor`` kullanılmaz,
    çünkü o *ulaşılan* en uzak hedefi döndürür → yalnız kazananlarda tanımlıdır
    ve TP4'e giden işlemde RR'ı 2,67 gösterir. Öyle örneklenirse başabaş WR
    yapay olarak düşer ve kaybeden bir geometri "kenarlı" görünür (ilk sürümde
    tam bu oldu: başabaş %49,7 çıkıp WR %80 ile çelişti).

    Doğrusu: her satır için, kazansın kaybetsin, TP1 hedefinin giriş fiyatına
    uzaklığı / stop mesafesi.
    """
    stop = canonical_stop_loss_pips(sig, default_symbol=default_symbol)
    if not stop or stop <= 0:
        return None
    entry = coerce_float(sig.get("ml_entry_price"))
    if entry is None or entry <= 0:
        return None

    targets = parse_json_object(sig.get("targets"))
    tp1 = None
    if isinstance(targets, dict):
        for key in ("TP1", "tp1", "Tp1"):
            if key in targets:
                tp1 = coerce_float(targets.get(key))
                break
    if tp1 is None:
        tp1 = coerce_float(sig.get("ml_target_price"))
    if tp1 is None or tp1 <= 0:
        return None

    symbol = sig.get("symbol") or default_symbol
    try:
        from services.signal_analytics import pips_from_price_change
        tp_pips = abs(pips_from_price_change(abs(tp1 - entry), symbol))
    except Exception:
        return None
    if not tp_pips or tp_pips <= 0:
        return None
    return tp_pips / stop


def _same_bar_ambiguous(sig: dict, reason: str) -> bool:
    """Aynı barda hem TP hem SL değmiş mi?

    Lifecycle ``tp1_3_hit_then_sl`` yazdığında TP ve SL'in AYNI mumda değmiş
    olması mümkündür (mum içi sıra bilinmez). Kanon: konservatif kayıp.
    Şimdilik yalnız çözüm sebebine bakılır; lifecycle ileride açık bir
    ``ambiguous`` bayrağı yazarsa o öncelik kazanır.
    """
    factors = parse_json_object(sig.get("factors"))
    if isinstance(factors, dict) and factors.get("same_bar_tp_sl") is True:
        return True
    return reason in _SAME_BAR_REASONS and bool(factors.get("same_bar_tp_sl", False))


def _outcome_class(status_class: str, sig: dict, reason: str) -> str:
    """Sonuç sınıfını belirler — R hesabından BAĞIMSIZ.

    Ayrı tutulmasının sebebi: bozuk bir R değeri satırın sınıfını
    değiştirmemeli (satır WR'da kalır, yalnız beklentiye katılmaz).
    """
    if status_class == "stopped":
        return LOSS
    if _same_bar_ambiguous(sig, reason):
        # KUSUR #2: mum içi sıra bilinmiyor → konservatif kayıp
        # (shadow_trade_tracker ile aynı yönde etiketleme).
        return AMBIGUOUS_LOSS
    if reason.endswith("tp1_3_hit_then_sl"):
        # KUSUR #3: kısmi — TP1 (≈0,5R) görüp SL yiyen işlem, TP4'e giden
        # işlemle aynı ağırlıkta "kazanç" sayılamaz.
        return PARTIAL
    return WIN


def signal_outcome(sig: dict, *, default_symbol: Optional[str] = None) -> Outcome:
    """Bir sinyalin kanonik sonucu — dürüst sınıf + R katsayısı.

    ``classify_signal`` mevcut düzeltme katmanlarını (replay correction,
    flip_closed nötrlemesi, MCI) koruduğu için ONUN ÜSTÜNE inşa edilir;
    burada yalnız şişirme yapan noktalarda karar değiştirilir.
    """
    epoch = signal_epoch(sig)
    reason = (sig.get("resolution_reason") or "").lower().strip()
    stop = canonical_stop_loss_pips(sig, default_symbol=default_symbol)
    realized = realized_pips(sig, default_symbol=default_symbol)

    try:
        status_class, _is_win, pips = classify_signal(sig, default_symbol=default_symbol)
    except Exception as exc:  # fail-soft: tek bozuk satır raporu düşürmesin
        logger.warning("[signal_metrics] classify_signal hata: %s", exc)
        return Outcome(OPEN, None, epoch, "classify_error", realized, stop)

    if status_class in (None, "active"):
        return Outcome(OPEN, None, epoch, reason or "active", realized, stop)

    # Nötrler: expired ve flip_closed WR'a GİRMEZ (mevcut davranış korunur).
    if status_class in ("expired", "flip_closed", "market_closed_invalid"):
        return Outcome(NEUTRAL, None, epoch, reason or str(status_class), realized, stop)

    klass = _outcome_class(str(status_class), sig, reason)

    # R katsayısı: realize edilen pip / stop mesafesi.
    #
    # ⚠️ BOZUK SATIR KORUMASI (KUSUR #5): ``exit_price=0`` gibi kayıtlar
    # R=−303 üretip tek başına yüzlerce satırlık ortalamayı deviriyordu
    # (2026-08-21 denetiminde bir XAU satırı beklentiyi +0,5R'den −0,34R'ye
    # çekti). Makul bandın dışındaki R beklentiye KATILMAZ; satır sınıfını
    # ve WR'daki yerini korur, yalnız ``excluded_r`` olarak sayılır.
    effective_pips = realized if realized is not None else pips
    r_multiple: Optional[float] = None
    if stop and stop > 0 and effective_pips is not None:
        candidate = round(float(effective_pips) / float(stop), 4)
        exit_price = coerce_float(sig.get("exit_price"))
        if (exit_price is None or exit_price > 0) and (
            R_PLAUSIBLE_MIN <= candidate <= R_PLAUSIBLE_MAX
        ):
            r_multiple = candidate
        else:
            return Outcome(klass, None, epoch,
                           f"implausible_r:{candidate}", realized, stop)

    if klass == LOSS:
        # Kayıpta R −1'in altına inemez; daha kötüsü kayma/veri hatasıdır.
        r_multiple = -1.0 if r_multiple is None else max(r_multiple, -1.5)
    elif klass == AMBIGUOUS_LOSS:
        r_multiple = -1.0

    return Outcome(klass, r_multiple, epoch, reason or str(status_class), realized, stop)


# ── toplama ─────────────────────────────────────────────────────────────────

def _finalize(m: Metrics, rr_samples: List[float], r_samples: List[float]) -> Metrics:
    denom = m.wins + m.partials + m.losses + m.ambiguous
    m.n = denom
    if denom > 0:
        m.win_rate = round(100.0 * (m.wins + m.partials) / denom, 1)
    if r_samples:
        m.total_r = round(sum(r_samples), 3)
        m.expectancy_r = round(sum(r_samples) / len(r_samples), 4)
        # Medyan, tek bir uç değerin ortalamayı devirmesine karşı çapraz kontrol.
        m.median_r = round(statistics.median(r_samples), 4)
    if rr_samples:
        avg_rr = sum(rr_samples) / len(rr_samples)
        m.avg_rr_geometry = round(avg_rr, 3)
        if avg_rr > 0:
            m.breakeven_wr = round(100.0 / (1.0 + avg_rr), 1)
            if m.win_rate is not None:
                m.edge_pp = round(m.win_rate - m.breakeven_wr, 1)

    # Uyarılar — panelin yanlış okunmasını engelleyen kısa notlar.
    if m.mixed_epochs:
        m.warnings.append(
            "Birden fazla TP/SL geometri epoch'u karışık — by_epoch kırılımına bak, "
            "havuzlanmış WR karşılaştırılabilir DEĞİL."
        )
    if m.edge_pp is not None and m.win_rate is not None and m.edge_pp < 0:
        m.warnings.append(
            f"WR %{m.win_rate} başabaş %{m.breakeven_wr}'ın ALTINDA "
            f"({m.edge_pp} pp) — geometri kaybettiriyor, kenar yok."
        )
    if m.expectancy_r is not None and m.expectancy_r < 0 and (m.win_rate or 0) >= 55:
        m.warnings.append(
            f"Yüksek WR (%{m.win_rate}) ama beklenti NEGATİF ({m.expectancy_r}R) — "
            "kazançlar kötü geometriyle satın alınmış."
        )
    if 0 < denom < 30:
        m.warnings.append(f"Örneklem küçük (n={denom}) — sonuç istikrarsız.")
    if m.ambiguous:
        m.warnings.append(
            f"{m.ambiguous} işlem aynı barda TP+SL gördü, konservatif kayıp sayıldı."
        )
    if m.excluded_r:
        m.warnings.append(
            f"{m.excluded_r} satırın R'si makul bandın dışında (bozuk exit/stop) — "
            "beklentiye katılmadı, WR'da sayıldı."
        )
    if (
        m.expectancy_r is not None
        and m.median_r is not None
        and abs(m.expectancy_r - m.median_r) > 0.5
    ):
        m.warnings.append(
            f"Ortalama ({m.expectancy_r}R) ile medyan ({m.median_r}R) ayrışıyor — "
            "birkaç uç işlem sonucu domine ediyor, ortalamaya tek başına güvenme."
        )
    return m


def aggregate_outcomes(
    rows: Iterable[dict],
    *,
    default_symbol: Optional[str] = None,
    split_epochs: bool = True,
) -> Metrics:
    """Sinyal satırlarından dürüst karne üretir.

    WR, beklenti (R), başabaş WR ve epoch kırılımı BİRLİKTE döner — çıplak WR
    raporlanamasın diye bilinçli olarak tek pakette.
    """
    total = Metrics()
    rr_samples: List[float] = []
    r_samples: List[float] = []
    per_epoch: Dict[str, Tuple[Metrics, List[float], List[float]]] = {}
    seen_epochs: set = set()

    for sig in rows or []:
        out = signal_outcome(sig, default_symbol=default_symbol)
        seen_epochs.add(out.epoch)

        bucket, e_rr, e_r = per_epoch.setdefault(
            out.epoch, (Metrics(), [], [])
        )

        for target, rr_list, r_list in ((total, rr_samples, r_samples), (bucket, e_rr, e_r)):
            if out.klass == OPEN:
                target.open_n += 1
                continue
            if out.klass == NEUTRAL:
                target.neutral += 1
                continue
            if out.klass == WIN:
                target.wins += 1
            elif out.klass == PARTIAL:
                target.partials += 1
            elif out.klass == LOSS:
                target.losses += 1
            elif out.klass == AMBIGUOUS_LOSS:
                target.ambiguous += 1
            if out.r_multiple is not None:
                r_list.append(out.r_multiple)
            elif out.reason.startswith("implausible_r"):
                target.excluded_r += 1

        rr = _geometry_rr(sig, default_symbol)
        if rr is not None and rr > 0:
            rr_samples.append(rr)
            per_epoch[out.epoch][1].append(rr)

    resolved_epochs = {e for e in seen_epochs if e != UNKNOWN_EPOCH}
    total.mixed_epochs = len(resolved_epochs) > 1

    if split_epochs:
        for epoch, (bucket, e_rr, e_r) in per_epoch.items():
            finalized = _finalize(bucket, e_rr, e_r)
            if finalized.n or finalized.open_n or finalized.neutral:
                total.by_epoch[epoch] = finalized

    return _finalize(total, rr_samples, r_samples)


def summarize_for_panel(metrics: Metrics) -> Dict[str, Any]:
    """Panel/endpoint yanıtı için düz sözlük — çıplak WR asla yalnız gitmez."""
    data = metrics.to_dict()
    data["headline"] = _headline(metrics)
    return data


def _headline(m: Metrics) -> str:
    if not m.n:
        return "Çözülmüş sinyal yok."
    parts = [f"n={m.n}", f"WR %{m.win_rate}"]
    if m.breakeven_wr is not None:
        parts.append(f"başabaş %{m.breakeven_wr}")
    if m.expectancy_r is not None:
        parts.append(f"beklenti {m.expectancy_r:+.3f}R")
    return " · ".join(parts)
