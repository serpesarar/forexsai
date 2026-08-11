"""CANLIYA ALMA KARTI — yeni bir scope canlıya çıkmadan önce ZORUNLU adım.

Neden (2026-08-11 dersi): USOIL BREAKOUT scope'u "kronolojik TEST %58.8" diyen bir
raporla canlıya alındı ve 19 işlemde −895$ verdi. Fark tek bir varsayımdan geliyordu:
rapor girişi KIRILIM BARININ KAPANIŞINDAN ve SPREAD'SİZ ölçmüştü. Gerçekte bot bir
sonraki tick'te ASK'ten alıyor. Aynı kural gerçek icra koşullarında ölçüldüğünde
%42.7 / −0.147R çıktı — yani scope hiç canlıya çıkmamalıydı.

Bu betik o hatayı yapılandırır: bir scope'un giriş kuralını verirsin, kart çıkarır.
Kart 6 ölçütün HEPSİNİ geçmeden scope canlıya alınmaz.

  1) HACİM        : ≥150 çözülmüş olay (yoksa istatistik konuşamaz)
  2) BEKLENTİ     : ort. R > 0 ve bootstrap P(EV>0) ≥ %90
  3) KARARLILIK   : kronolojik iki yarının İKİSİ de ≥ 0
  4) SÜRTÜNME     : spread 1.5×'e çıkarıldığında hâlâ pozitif
  5) İCRA         : giriş sinyal barının KAPANIŞI değil, SONRAKİ M1 AÇILIŞI + spread
                    (bu varsayım zaten kodda; ölçüt, kapanış-girişi ile arasındaki
                     farkın ort. R'nin yarısından büyük olmaması — kırılgan geometri uyarısı)
  6) SIRA-BAĞIMLI : "aynı anda tek pozisyon" kısıtıyla da pozitif

Verdikt: LIVE (hepsi geçti) · SHADOW (2,3,4,6'dan biri düştü) · RED (hacim yok).

Kullanım (kutuda):
    python backend/research/go_live_gate.py usoil_breakout
    python backend/research/go_live_gate.py --list

Yeni scope eklemek: SCOPES sözlüğüne bir giriş-kuralı fonksiyonu yaz (m5 barlarından
olay listesi üretir, her olay {'t','atr'} taşımalı) ve geometrisini belirt.

NOT: Panel sinyallerine dayanan scope'lar (pulse/emel/smc oylu MOM/SR, VIXREG…)
bar verisinden yeniden üretilemez. Onların karşılığı `entry_gate_live_validation.py`
tarzı CANLI İŞLEM kartıdır: en az 100 gölge/canlı işlem + aynı 6 ölçüt.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from usoil_breakout_lab import DAYS, build_events, fetch, get_spread

CARD_DIR = (Path(__file__).resolve().parents[1] / "data" / "evolution" / "go_live_cards")
RNG = np.random.default_rng(11)
MIN_EVENTS = 150
MIN_P_EV = 0.90
SPREAD_STRESS = 1.5

# ── scope kayıtları: giriş kuralı + geometri ────────────────────────────────
SCOPES: dict[str, dict] = {
    "usoil_breakout": {
        "symbol": "SpotCrude",
        "events": build_events,            # Donchian(48) kırılımı + 5m EMA200
        "tp_atr": 1.0, "sl_atr": 1.0, "be_trail": False,
        "aciklama": "USOIL Donchian48 kırılım-devam (BUY)",
    },
}


def simulate(ev, m1, spread, tp_atr, sl_atr, be_trail=False, entry_at_close=False):
    """Dürüst TP/SL yarışı. entry_at_close=True → RAPORLARIN yaptığı iyimser varsayım."""
    t1, o1, h1, l1 = m1[:, 0], m1[:, 1], m1[:, 2], m1[:, 3]
    out = []
    for e in ev:
        close_t = e["t"] + 300
        k = int(np.searchsorted(t1, close_t))
        if k >= len(t1) - 5 or t1[k] - close_t > 600:
            continue
        entry = e["close"] if entry_at_close else o1[k] + spread
        unit = sl_atr * e["atr"]
        tp, sl = entry + tp_atr * e["atr"], entry - unit
        cur_sl, runner, peak, R = sl, False, entry, None
        hi, lo = h1[k:k + 1440], l1[k:k + 1440]
        for j in range(len(hi)):
            hit_sl = lo[j] <= cur_sl
            hit_tp = (not runner) and hi[j] >= tp
            if hit_sl:
                R = (cur_sl - entry) / unit; break
            if hit_tp:
                if not be_trail:
                    R = (tp - entry) / unit; break
                runner = True
                cur_sl = max(cur_sl, tp - unit)
            if runner:
                peak = max(peak, hi[j])
                cur_sl = max(cur_sl, peak - unit)
        if R is None:
            continue
        out.append({**e, "R": R, "win": 1 if R > 0 else 0, "k": k,
                    "hold": j + 1, "entry": entry})
    return out


def boot_p(rows, n=5000):
    x = np.array([r["R"] for r in rows])
    if len(x) < 20:
        return 0.0, (np.nan, np.nan)
    m = RNG.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return float((m > 0).mean()), (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def as_traded(rows):
    rows = sorted(rows, key=lambda r: r["t"])
    taken, busy = [], -1
    for r in rows:
        if r["k"] < busy:
            continue
        taken.append(r)
        busy = r["k"] + r["hold"]
    return taken


def mean_R(rows):
    return float(np.mean([r["R"] for r in rows])) if rows else 0.0


def card(name: str) -> dict:
    spec = SCOPES[name]
    m5, m1 = fetch("M5", DAYS), fetch("M1", DAYS)
    spread = get_spread()
    ev = spec["events"](m5)
    tp, sl, tr = spec["tp_atr"], spec["sl_atr"], spec["be_trail"]

    base = simulate(ev, m1, spread, tp, sl, tr)
    stress = simulate(ev, m1, spread * SPREAD_STRESS, tp, sl, tr)
    optimistic = simulate(ev, m1, 0.0, tp, sl, tr, entry_at_close=True)
    seq = as_traded(base)
    half = len(base) // 2
    b = sorted(base, key=lambda r: r["t"])
    h1r, h2r = b[:half], b[half:]
    p_ev, ci = boot_p(base)

    checks = {
        "1_hacim": {"deger": len(base), "esik": f"≥{MIN_EVENTS}", "gecti": len(base) >= MIN_EVENTS},
        "2_beklenti": {"deger": f"ortR={mean_R(base):+.3f} P(EV>0)=%{100*p_ev:.1f}",
                       "esik": f"ortR>0 ve P≥%{100*MIN_P_EV:.0f}",
                       "gecti": mean_R(base) > 0 and p_ev >= MIN_P_EV},
        "3_kararlilik": {"deger": f"ilk={mean_R(h1r):+.3f} son={mean_R(h2r):+.3f}",
                         "esik": "ikisi de ≥0",
                         "gecti": mean_R(h1r) >= 0 and mean_R(h2r) >= 0},
        "4_surtunme": {"deger": f"spread×{SPREAD_STRESS}: ortR={mean_R(stress):+.3f}",
                       "esik": ">0", "gecti": mean_R(stress) > 0},
        "5_icra": {"deger": f"kapanış-girişi ortR={mean_R(optimistic):+.3f} vs "
                            f"gerçek {mean_R(base):+.3f}",
                   "esik": "fark, gerçek |ortR|'nin 0.5 katından küçük (kırılgan değil)",
                   "gecti": abs(mean_R(optimistic) - mean_R(base)) <= 0.5 * max(abs(mean_R(base)), 1e-9)},
        "6_sira_bagimli": {"deger": f"n={len(seq)} ortR={mean_R(seq):+.3f}",
                           "esik": ">0", "gecti": mean_R(seq) > 0},
    }
    if not checks["1_hacim"]["gecti"]:
        verdict = "RED"
    elif all(c["gecti"] for c in checks.values()):
        verdict = "LIVE"
    else:
        verdict = "SHADOW"

    return {
        "scope": name, "aciklama": spec["aciklama"], "tarih": datetime.now().isoformat(),
        "sembol": spec["symbol"], "spread": spread,
        "geometri": {"tp_atr": tp, "sl_atr": sl, "be_trail": tr},
        "olay": len(ev), "cozulen": len(base),
        "wr": round(100 * np.mean([r["win"] for r in base]), 1) if base else 0.0,
        "ort_R": round(mean_R(base), 4), "bootstrap_%95": [round(ci[0], 4), round(ci[1], 4)],
        "p_ev_pozitif": round(p_ev, 4), "checks": checks, "verdikt": verdict,
    }


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--list":
        print("kayıtlı scope'lar:", ", ".join(SCOPES))
        return
    name = sys.argv[1]
    if name not in SCOPES:
        raise SystemExit(f"bilinmeyen scope: {name} (--list ile bak)")
    c = card(name)
    w = 74
    print("=" * w)
    print(f"CANLIYA ALMA KARTI — {c['scope']}  ({c['aciklama']})")
    print("=" * w)
    print(f"  sembol={c['sembol']}  spread={c['spread']}  geometri={c['geometri']}")
    print(f"  olay={c['olay']}  çözülen={c['cozulen']}  WR=%{c['wr']}  ort.R={c['ort_R']:+.3f}"
          f"  %95={c['bootstrap_%95']}")
    print("-" * w)
    for k, v in c["checks"].items():
        mark = "GEÇTİ " if v["gecti"] else "KALDI "
        print(f"  [{mark}] {k:<16} {v['deger']:<44} ({v['esik']})")
    print("-" * w)
    print(f"  VERDİKT: {c['verdikt']}"
          + ("  → canlıya alınabilir" if c["verdikt"] == "LIVE"
             else "  → CANLIYA ALINMAZ (gölgede ölçmeye devam)"))
    print("=" * w)
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    out = CARD_DIR / f"{name}.json"
    out.write_text(json.dumps(c, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"kart yazıldı: {out}")


if __name__ == "__main__":
    main()
