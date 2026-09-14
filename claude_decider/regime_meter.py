"""regime_meter.py — piyasa rejiminin SÜREKLİ ÖLÇÜMÜ (kapı DEĞİL, enstrüman).

NEDEN KAPI DEĞİL (2026-09-14 denetimi, 5.297 karar):
Rejim-tabanlı giriş zamanlaması kurulmak istendi ve kurulamadı — ama sebebi
"rejim önemsiz" değil, **örneklemde rejim çeşitliliği olmaması**:

    Tüm journal boyunca VIX 15.1 – 19.6 (medyan 17.1); VIX ≥ 20 olan kayıt: 0.
    Panelin kanıtlı VIX≥18.4 rejimi kayıtların yalnız %7.3'ünde.
    DXY 98.6 – 101.6. Yani 2,5 ay TEK bir düşük-oynaklık rejimi.

Tek rejimden rejim etkisi öğrenilemez. Denenen ve ELENEN rejim adayları:
  · geçmiş performansın kalıcılığı  → r=0.006-0.053 (öngörü yok)
  · ADX(1h/4h) üst-TF trend gücü    → train/test tutarsız
  · ATR%(4h) oynaklık                → KONFOUND: ≥1.2 kovasının 223/223'ü USOIL,
                                        sembol-içi yüzdelikte test dönemi dejenere
  · VIX                              → aralık zaten yok (yukarı bak)

BU YÜZDEN bu modül HİÇBİR ŞEYİ BLOKLAMAZ. İki işi var:
  1. Rejim durumunu her karara damgalar → rejim DEĞİŞTİĞİNDE elde veri olur ve
     kapı o zaman kanıtla kurulur (şimdi kurulursa tek rejime aşırı-uyum olur).
  2. ZARF UYARISI: mevcut koşul, kapıların doğrulandığı zarfın dışına çıktıysa
     bunu işaretler — `entry_quality` eşikleri (chz_dir≥2.0, vol≥1.5) bu düşük-VIX
     rejiminde ölçüldü; VIX 25'te aynı eşiklerin geçerli olduğu KANITLANMADI.
"""
from __future__ import annotations

# Denetimin gözlediği zarf — kapı kanıtlarının geçerli olduğu koşullar.
OBSERVED = {
    "vix": (15.1, 19.6),
    "dxy": (98.6, 101.6),
    # sembol → 4h ATR/fiyat % (p10, p90); dışına çıkması "görülmemiş oynaklık" demek
    "atrp_4h": {
        "GDAXI.INDX": (0.30, 0.60),
        "NDX.INDX": (0.48, 0.97),
        "USOIL.FOREX": (1.26, 2.22),
        "XAUUSD": (0.69, 0.92),
    },
}
VIX_HIGH = 18.4      # panelin kanıtlı eşiği (bu veride yalnız %7.3 — ölçülemedi)


def _band(vix: float | None) -> str | None:
    if vix is None:
        return None
    if vix < 15:
        return "cok_sakin"
    if vix < 17:
        return "sakin"
    if vix < VIX_HIGH:
        return "normal"
    if vix < 25:
        return "gergin"
    return "kriz"


def _atrp(tf_block: dict | None) -> float | None:
    """ATR'yi fiyat seviyesine oranla (%) — sembolden bağımsız oynaklık ölçüsü."""
    b = tf_block or {}
    atr, sr = b.get("atr"), (b.get("sr") or {})
    lvl = (sr.get("res") or {}).get("level") or (sr.get("sup") or {}).get("level")
    if not atr or not lvl:
        return None
    return round(100.0 * float(atr) / float(lvl), 3)


def measure(forensics: dict | None, symbol: str | None = None) -> dict | None:
    """Karar anındaki rejim durumu + zarf uyarıları. Veri yoksa None."""
    if not forensics:
        return None
    tfs = forensics.get("tfs") or {}
    macro = forensics.get("macro") or {}
    b4, b1 = tfs.get("4h") or {}, tfs.get("1h") or {}
    vix, dxy = macro.get("vix"), macro.get("dxy")
    atrp = _atrp(b4)

    trs = [(tfs.get(x) or {}).get("trend") for x in ("5m", "30m", "1h", "4h")]
    yonlu = [x for x in trs if x in ("yukari", "asagi")]

    out = {
        "vix": vix, "vix_band": _band(vix), "dxy": dxy,
        "atrp_4h": atrp, "adx_4h": b4.get("adx"), "adx_1h": b1.get("adx"),
        "vol_4h": b4.get("vol_ratio"),
        "tf_yatay": sum(1 for x in trs if x == "yatay"),
        "tf_uyum": (round(max(yonlu.count("yukari"), yonlu.count("asagi")) / len(yonlu), 2)
                    if yonlu else None),
        "disarida": [],
    }

    lo, hi = OBSERVED["vix"]
    if vix is not None and not (lo <= vix <= hi):
        out["disarida"].append(f"vix={vix} gözlenen zarf dışında ({lo}-{hi})")
    lo, hi = OBSERVED["dxy"]
    if dxy is not None and not (lo <= dxy <= hi):
        out["disarida"].append(f"dxy={dxy} gözlenen zarf dışında ({lo}-{hi})")
    env = OBSERVED["atrp_4h"].get(symbol or "")
    if env and atrp is not None and not (env[0] <= atrp <= env[1]):
        out["disarida"].append(f"atrp_4h={atrp} {symbol} zarfı dışında ({env[0]}-{env[1]})")

    if out["disarida"]:
        out["uyari"] = ("Kapı eşikleri (entry_quality) bu koşulda DOĞRULANMADI — "
                        "gözlenen rejim zarfının dışındasınız.")
    return out
