"""Tartışma motorunun ÖZ-ÖĞRENME döngüsü — karneden ders damıtma (2026-08-02).

Neden yazıldı
-------------
Denetim (bkz. ``backend/data/evolution/analyst_reports/bias_karne_denetimi_2026-08-02.md``)
şunu gösterdi: ``get_active_lessons("bias_debate")`` **boş dönüyordu**. 13 dersin
10'u arşivli, 3 aktif ders yalnız ``claude_decider`` hedefliydi ve en yenisi
2026-07-23'tendi. Yani tartışma motoru panelin öğrendiği hiçbir şeyi GÖRMÜYORDU;
"Öğret" düğmesi elle basılmadıkça öğrenme diye bir şey yoktu.

Tek canlı geri besleme ``bias_test_service.recent_track_record`` idi — o da
notlama ekseni bozuk olduğu için sistemin kendisine YANLIŞ karne gösteriyordu.

Tasarım ilkeleri
----------------
1. **Yalnız savunulabilir bulgu ders olur.** Her aday için örneklem eşiği (n) ve
   iki-yanlı binom testi (p ≤ :data:`P_MAX`) uygulanır. Eşiği geçemeyen aday
   ders ÜRETMEZ — sistemin gürültüyü kendine "ders" diye öğretmesi, hiç
   öğrenmemesinden daha kötüdür.
2. **Ders geri alınabilir.** Kanıtı düşen otomatik ders arşivlenir
   (``retire_auto_lessons``). Öğrenme tek yönlü biriktirme değildir.
3. **Ders davranışsal olur.** "İsabetin düşük" demek bir şey öğretmez; ders
   somut bir DAVRANIŞ kuralı söyler (hangi yön için hangi kanıt çıtası, kararın
   hangi ufukta tüketileceği).
4. **Metrik doğru olan.** Ham isabet değil baseline-göreli beceri; gün-kapanışı
   değil sembolün birincil ufku.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

#: Bir bulgunun ders olabilmesi için gereken en küçük yönlü çağrı sayısı.
MIN_N = 12
#: İki-yanlı binom testi eşiği. 0.01 bilinçli olarak sıkı: karne hücreleri
#: küçük ve çok sayıda hipotez taranıyor (çoklu-karşılaştırma).
P_MAX = 0.01
#: Yön yanlılığı uyarısı için çağrı payı ile piyasa payı arasındaki en az fark.
TILT_MIN_PP = 0.20
#: Otomatik derslerin anahtar öneki — arşivleme bu önekle süpürür.
KEY_PREFIX = "bias_scorecard::"

_TARGETS = ["bias_debate", "panel"]


def _binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """İki-yanlı binom p-değeri (scipy'siz, tam toplam)."""
    if n <= 0:
        return 1.0
    from math import comb
    def pmf(i: int) -> float:
        return comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * 1.0000001))


def _median(xs: list) -> Optional[float]:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return float(xs[m]) if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def _durability_rows() -> list[dict]:
    """Yönlü satırların dayanıklılık blokları (temiz eksende yeniden notlanmış)."""
    from services.bias_test_service import _client, symbol_for_row
    client = _client()
    if client is None:
        return []
    rows = (client.table("bias_test_log")
            .select("predicted_bias,run_label,durability,p0_stale_pct,"
                    "ret_60m,ret_240m,sym:raw_payload->>symbol")
            .order("ny_date", desc=True).limit(400).execute()).get("data") or []
    out = []
    for r in rows:
        if str(r.get("run_label") or "").endswith("_dup"):
            continue
        if (r.get("predicted_bias") or "").lower() not in ("bullish", "bearish"):
            continue
        r["_symbol"] = symbol_for_row({"raw_payload": {"symbol": r.get("sym")},
                                       "run_label": r.get("run_label")})
        out.append(r)
    return out


def _tilt_for(rows: list[dict]) -> Optional[dict]:
    """Çağrı dağılımı vs piyasanın KENDİ yön dağılımı (aynı pencerelerde).

    Kritik incelik: yanlılık, %50'ye değil piyasanın gerçekleşen asimetrisine
    göre ölçülür. Gerçekten düşen bir piyasada ayı ağırlıklı çağrı doğru
    davranıştır ve ceza almamalıdır.
    """
    from services.bias_test_service import PRIMARY_HORIZON_MIN
    n_bear = sum(1 for r in rows if (r.get("predicted_bias") or "").lower() == "bearish")
    n = len(rows)
    if n < MIN_N:
        return None
    moves = []
    for r in rows:
        m = PRIMARY_HORIZON_MIN.get(r.get("_symbol") or "", 60)
        v = r.get(f"ret_{m}m")
        if v is not None:
            moves.append(v)
    if len(moves) < MIN_N:
        return None
    side, k = ("bearish", n_bear) if n_bear * 2 >= n else ("bullish", n - n_bear)
    down = sum(1 for v in moves if v <= 0)
    mkt_side = (down if side == "bearish" else len(moves) - down) / len(moves)
    share = k / n
    if share - mkt_side < TILT_MIN_PP:
        return None
    p = _binom_two_sided(k, n, mkt_side)
    if p > P_MAX:
        return None
    return {"n": n, "k": k, "side": side, "share": share,
            "mkt_side": mkt_side, "p": p}


def _lesson_direction_tilt(rows: list[dict]) -> list[tuple[str, dict]]:
    """Yön yanlılığı — önce tüm portföy, sonra sembol bazında."""
    out = []
    groups: list[tuple[str, Optional[str], list]] = [("ALL", None, rows)]
    by_sym: dict[str, list] = {}
    for r in rows:
        by_sym.setdefault(r.get("_symbol") or "?", []).append(r)
    groups += [(s, s, v) for s, v in sorted(by_sym.items())]

    for gkey, sym, grows in groups:
        t = _tilt_for(grows)
        if not t:
            continue
        side, n, k, share, mkt_side, p = (t["side"], t["n"], t["k"], t["share"],
                                          t["mkt_side"], t["p"])
        scope = "Tüm semboller" if sym is None else sym
        out.append((f"{KEY_PREFIX}tilt::{gkey}", {
            "title": f"{scope} — sistematik {side.upper()} yanlılığı ölçüldü",
            "symbol": sym,
            "summary": (
                f"Son {n} yönlü çağrının {k}'i {side} (%{share*100:.0f}); aynı "
                f"pencerelerde piyasa o yöne yalnız %{mkt_side*100:.0f} gitti "
                f"(binom p={p:.4f}). Bu bir piyasa okuması değil, akıl "
                f"yürütmedeki bir eğilim. DAVRANIŞ: {side} bir çağrı yapmadan "
                f"önce, bugünü o başarısız {side} serisinden AYIRAN somut ve "
                f"seviye-tabanlı kanıtı açıkça yaz. Ters yön için isteyeceğin "
                f"kanıt çıtasının aynısını bu yöne de uygula. Çekimser kalmak "
                f"cezalandırılmaz."),
            "evidence": {"n": n, "side": side, "share_pct": round(share * 100, 1),
                         "market_share_pct": round(mkt_side * 100, 1),
                         "p": round(p, 5), "scope": gkey},
        }))
    return out


def _lesson_symbol_skill(report: dict) -> list[tuple[str, dict]]:
    """Sembol bazında beceri baseline'ın anlamlı ölçüde ALTINDA mı?"""
    out = []
    for sym, v in (report.get("primary_intraday", {}).get("per_symbol") or {}).items():
        n, k, acc = v.get("n") or 0, v.get("correct") or 0, v.get("accuracy_pct")
        if n < MIN_N or acc is None:
            continue
        p = _binom_two_sided(k, n, 0.5)
        if acc >= 50.0 or p > P_MAX:
            continue
        out.append((f"{KEY_PREFIX}antiskill::{sym}", {
            "title": f"{sym} — yönlü çağrılar yazı-turadan kötü",
            "symbol": sym,
            "summary": (
                f"{sym} üzerinde son {n} yönlü çağrının {k}'i tuttu (%{acc}; "
                f"baseline %{v.get('baseline_acc_pct')}, beceri "
                f"{v.get('skill_vs_baseline_pp')}pp, binom p={p:.4f}). "
                f"DAVRANIŞ: bu sembolde yön çağırmak için OLAĞANIN ÜSTÜNDE kanıt "
                f"iste — çok-kaynak teyidi (yapı + kırılım dedektörü + seans "
                f"bağlamı aynı yönü göstermeli). Teyit yoksa çekimser kal; "
                f"çekimserlik doğruluk oranına yazılmaz."),
            "evidence": {"n": n, "correct": k, "accuracy_pct": acc,
                         "skill_pp": v.get("skill_vs_baseline_pp"), "p": round(p, 5)},
        }))
    return out


def _lesson_durability(rows: list[dict]) -> list[tuple[str, dict]]:
    """Karar ne kadar süre lehte kalıyor? Ufuk beyanını gerçeğe bağla."""
    alive = [(r.get("durability") or {}).get("alive_until_min") for r in rows]
    alive = [a for a in alive if a is not None]
    if len(alive) < MIN_N:
        return []
    med = _median(alive)
    dead_fast = sum(1 for a in alive if a <= 10)
    share = dead_fast / len(alive)
    if share < 0.5:
        return []
    return [(f"{KEY_PREFIX}durability::all", {
        "title": "Kararların ömrü ölçüldü — gün-boyu bias değil, dakikalık pencere",
        "symbol": None,
        "summary": (
            f"Son {len(alive)} yönlü kararın {dead_fast}'i (%{share*100:.0f}) "
            f"ilk 10 dakika içinde yönünü kaybetti; medyan yaşam süresi "
            f"{med:.0f} dakika. DAVRANIŞ: kararını 'gün boyu geçerli bias' "
            f"diye çerçeveleme. Ya (a) ilk 30 dakikada gerçekleşmesi beklenen, "
            f"seviyeye bağlı somut bir hareket tarif et, ya da (b) tetikleyici "
            f"koşulu yaz ('X seviyesi kırılırsa') ve o gelene kadar çekimser "
            f"kal. Uzun ufuk iddiası, o ufukta ölçülmüş dayanağın varsa "
            f"meşrudur — yoksa değil."),
        "evidence": {"n": len(alive), "median_alive_min": med,
                     "dead_within_10min_pct": round(share * 100, 1)},
    })]


def _lesson_stale_levels(rows: list[dict]) -> list[tuple[str, dict]]:
    """S/R seviyeleri karar anında zaten aşılmış mıydı? (bayat fiyat izi)"""
    flags = [(r.get("durability") or {}).get("invalid_prebreached") for r in rows]
    flags = [f for f in flags if f is not None]
    if len(flags) < MIN_N:
        return []
    bad = sum(1 for f in flags if f)
    share = bad / len(flags)
    if share < 0.15:
        return []
    return [(f"{KEY_PREFIX}levels::prebreached", {
        "title": "Geçersizleşme seviyeleri karar anında zaten aşılmıştı",
        "symbol": None,
        "summary": (
            f"Son {len(flags)} yönlü kararın {bad}'inde (%{share*100:.0f}) "
            f"verdiğin geçersizleşme seviyesi daha karar anında fiyatın yanlış "
            f"tarafındaydı — yani seviye canlı fiyattan değil, hatırlanan ya da "
            f"bayat bir fiyattan türetilmişti. DAVRANIŞ: destek/direnç yazmadan "
            f"önce bağlamdaki canlı fiyata göre KONUMUNU söyle ('direnç, "
            f"fiyatın %X üstünde'). Seviye fiyatın yanlış tarafında kalıyorsa o "
            f"seviye geçersizdir, yeniden seç."),
        "evidence": {"n": len(flags), "prebreached": bad,
                     "share_pct": round(share * 100, 1)},
    })]


def distill_scorecard_lessons(dry_run: bool = False) -> dict:
    """Karneyi oku → eşiği geçen bulguları ders yap → düşenleri arşivle.

    ``bias_auto_runner`` notlamadan hemen sonra günde bir çağırır. LLM
    kullanmaz (token harcamaz) — tamamen ölçümden türer.
    """
    from services import bias_test_service as bts
    try:
        report = bts.accuracy_report()
    except Exception as e:
        logger.warning("[self-learn] karne okunamadı: %s", e)
        return {"ok": False, "error": str(e)}

    rows = _durability_rows()
    candidates: list[tuple[str, dict]] = []
    candidates += _lesson_direction_tilt(rows)
    candidates += _lesson_symbol_skill(report)
    candidates += _lesson_durability(rows)
    candidates += _lesson_stale_levels(rows)

    if dry_run:
        return {"ok": True, "dry_run": True,
                "would_write": [{"key": k, **v} for k, v in candidates]}

    from services import evolution_service as ev
    written = []
    for key, spec in candidates:
        try:
            ev.upsert_auto_lesson(
                key=key, title=spec["title"], summary=spec["summary"],
                targets=_TARGETS, symbol=spec.get("symbol"),
                evidence=spec.get("evidence"))
            written.append(key)
        except Exception as e:
            logger.warning("[self-learn] ders yazılamadı (%s): %s", key, e)
    retired = ev.retire_auto_lessons(KEY_PREFIX, set(written))
    logger.info("[self-learn] %d ders yazıldı/güncellendi, %d arşivlendi",
                len(written), retired)
    return {"ok": True, "written": written, "retired": retired,
            "evaluated": len(candidates)}
