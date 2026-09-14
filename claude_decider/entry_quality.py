"""entry_quality.py — giriş kalitesi kapısı (bıçak yakalama + hacim patlaması).

KANIT (2026-09-14 denetimi, claude_decider journal'ının TAMAMI, sızıntısız):
forensics karar anı snapshot'ından üretilen iki koşul, kronolojik OOS'ta ayakta
kaldı. Elenen küme HER İKİ kronolojik yarıda ve 4 sembolün 4'ünde de negatif:

  DECIDER gerçek işlemleri (n=1515, başabaş WR %59.9 / RR 0.67)
    elenen : n= 434 WR %56.0 EV −0.069R | yarı1 −0.078 yarı2 −0.061 | P(EV>0)=%4.2
    kalan  : n=1081 WR %63.1 EV +0.036R | yarı1 +0.008 yarı2 +0.065 | P(EV>0)=%93.7
  KARŞI-OLGU mekanik primary_dir (n=4350 — bağımsız, decider'ın seçimi yok)
    elenen : n=1010 WR %56.6 EV −0.068R | P(EV>0)=%0.4
    kalan  : n=3340 WR %63.5 EV +0.017R | P(EV>0)=%90.2
  Plasebo (aynı kapsamda rastgele kapı, 2000 tur): p=0.0085

İKİ KOŞUL
  1) BIÇAK YAKALAMA — chz_dir ≥ 2.0
     chz_dir = fiyatın, işlem yönünün TERSİNE, 5m kanalında kaç sigma uzaklaştığı.
     BUY'da kanal dibi, SELL'de kanal tepesi. Derinlik arttıkça WR monoton düşüyor:
     <1.0 %63-67 · 1.0-2.0 %60-63 · 2.0-2.5 %55-58 · ≥2.5 %47-53.
     Decider'ın çekirdek tezi ("ne kadar aşırı o kadar iyi") tam burada çöküyor.
  2) HACİM PATLAMASI — vol_ratio(5m) ≥ 1.5
     Botun kendi giriş kapısındaki eşiğin (entry_gate._VOL_RATIO_MAX) aynısı;
     iki bağımsız veri setinde de tekrarlandı.

NOT: Kapı SALT SUPRESİF — yeni sinyal üretmez, yön çevirmez, yalnız OPEN'ı WAIT'e
çevirir. Karşı-olgu grade'i sürdüğü için kapının maliyeti VAZGEÇİLEN-R'de görünür.
"""
from __future__ import annotations

try:
    import decider_config as config          # kutunun yerel ayarları (gitignore'da)
except Exception:                            # pragma: no cover
    config = None

# Doğrulanmış eşikler — değiştirmek OOS kanıtını geçersiz kılar.
KNIFE_CHZ_MAX = float(getattr(config, "EQ_KNIFE_CHZ_MAX", 2.0))
VOL_SPIKE_MAX = float(getattr(config, "EQ_VOL_SPIKE_MAX", 1.5))
GATE_ENABLED = bool(getattr(config, "ENTRY_QUALITY_GATE", True))    # ölç + logla
GATE_BLOCKS = bool(getattr(config, "ENTRY_QUALITY_BLOCK", False))   # GÖLGE varsayılan

# Sürekli skor için yumuşak rampa sınırları (yalnız gösterge; kapı kararı binary).
_CHZ_SOFT, _VOL_SOFT = 1.5, 1.2
_CHZ_HARD, _VOL_HARD = 3.0, 2.0


def _ramp(value: float, soft: float, hard: float) -> float:
    """soft altında 0, hard üstünde 1, arada doğrusal."""
    if value <= soft:
        return 0.0
    if value >= hard:
        return 1.0
    return (value - soft) / (hard - soft)


def assess(forensics: dict | None, direction: str | None) -> dict:
    """Karar anı forensics + yön → giriş kalitesi.

    Dönen: {"score": 0-100, "blocked": bool, "reasons": [...], "chz_dir":…, "vol": …}
    Veri yoksa fail-open (blocked=False, score=None).
    """
    out = {"score": None, "blocked": False, "reasons": [], "chz_dir": None, "vol": None}
    if not forensics or not direction:
        return out
    b5 = ((forensics.get("tfs") or {}).get("5m")) or {}
    cz, vol = b5.get("channel_z"), b5.get("vol_ratio")
    sign = 1.0 if str(direction).upper() == "BUY" else -1.0

    penalty = 0.0
    if cz is not None:
        chz_dir = -sign * float(cz)      # + = işlem yönünün tersine gidilmiş mesafe
        out["chz_dir"] = round(chz_dir, 3)
        if chz_dir >= KNIFE_CHZ_MAX:
            out["reasons"].append(
                f"bicak_yakalama(chz_dir={chz_dir:.2f}>={KNIFE_CHZ_MAX})")
        penalty += 60.0 * _ramp(chz_dir, _CHZ_SOFT, _CHZ_HARD)
    if vol is not None:
        out["vol"] = round(float(vol), 3)
        if float(vol) >= VOL_SPIKE_MAX:
            out["reasons"].append(f"hacim_patlamasi(vol={float(vol):.2f}>={VOL_SPIKE_MAX})")
        penalty += 40.0 * _ramp(float(vol), _VOL_SOFT, _VOL_HARD)

    if cz is not None or vol is not None:
        out["score"] = max(0, round(100.0 - penalty))
    out["blocked"] = bool(out["reasons"])
    return out


def apply_gate(symbol: str, dec: dict, forensics: dict | None) -> tuple[dict, dict]:
    """OPEN kararına kapıyı uygula. Dönen: (karar, kalite).

    GATE_BLOCKS False iken karar DEĞİŞMEZ — yalnız kalite journal'a yazılır
    (gölge ölçüm). True iken OPEN → WAIT.
    """
    quality = assess(forensics, dec.get("direction"))
    if not GATE_ENABLED or str(dec.get("action", "")).upper() != "OPEN":
        return dec, quality
    if not quality["blocked"]:
        return dec, quality

    why = ", ".join(quality["reasons"])
    if not GATE_BLOCKS:
        print(f"  👁 giriş-kalitesi (GÖLGE): {symbol} {dec.get('direction')} — {why}")
        quality["would_block"] = True
        return dec, quality

    print(f"  🛑 giriş-kalitesi: {symbol} {dec.get('direction')} OPEN → WAIT — {why}")
    dec = dict(dec)
    dec["action"] = "WAIT"
    dec["size_factor"] = 0.0
    dec["entry_quality_blocked"] = True
    dec["reason"] = (f"[GİRİŞ-KALİTESİ: {why}] " + str(dec.get("reason") or ""))[:500]
    return dec, quality
