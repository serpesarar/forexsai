"""Canlı işlem kartı (CLAUDE.md 2. Kural, E22) — panel sinyaline dayanan scope'lar için.

ÖN KAYIT (2026-10-09, sonuçlara bakmadan):
  Kaynak   : Supabase ``bot_trades`` (gerçek MT5 kapanışları), broker 1m ``indicator_snapshots``;
             saat ekseni ``islem_otopsi.align`` ile fiyat eşleştirmesinden.
  Birim    : KARAR (aynı sembol+yön, 2 dk içinde açılan bacaklar tek karar, E9).
             R = karar net $ / karar ilk risk $ (|giriş − ilk SL| × lot × puan değeri).
  Ölçütler : 1) ≥100 karar  2) ortR>0 ve gün-bloklu bootstrap P(EV>0) ≥ %90
             3) kronolojik iki yarı ≥0  4) ek 0,5×tipik spread maliyetiyle hâlâ >0
             5) kâğıt giriş (karar anından önceki kapanmış 1m bar kapanışı) ile gerçek dolum
                arasındaki ortR farkı < 0,5×|gerçek ortR|
             6) aile içinde aynı anda tek pozisyon (sonraki karar önceki kapanmadan açıldıysa atla) >0
  Verdikt  : 1 düşerse RED, diğerlerinden biri düşerse SHADOW, hepsi geçerse LIVE.
Kullanım: python3 research/canli_kart_20261009/live_card.py VIXREG [MOMSR …]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import align, data  # noqa: E402
from scripts.islem_otopsi import settings as S  # noqa: E402

CARD_DIR = ROOT / "backend/data/evolution/go_live_cards"
SINCE = pd.Timestamp("2026-06-01", tz="UTC")
MIN_DECISIONS, MIN_P_EV, EXTRA_SPREAD = 100, 0.90, 0.5
RNG = np.random.default_rng(11)


def point_values(t: pd.DataFrame) -> dict:
    """Sembol başına $/puan/lot — kapanmış işlemlerin brüt kâr / (fiyat farkı × lot) medyanı."""
    out = {}
    for sym, g in t.groupby("symbol"):
        mv = (g.close_price - g.open_price) * np.where(g.direction.str.upper() == "BUY", 1, -1) * g.volume
        ok = mv.abs() > 1e-9
        pv = (g.loc[ok, "net"] - g.loc[ok, "swap"]) / mv[ok]
        out[sym] = float(pv[(pv > 0) & np.isfinite(pv)].median())
    return out


def paper_close(bars: pd.DataFrame, ts: pd.Timestamp) -> float:
    """Karar anından ÖNCE kapanmış son 1m barın kapanışı (bar başlangıç etiketli)."""
    i = bars.index.searchsorted(ts.floor("min") - pd.Timedelta(minutes=1), side="right") - 1
    return float(bars.close.iat[i]) if i >= 0 else np.nan


def per_trade(t: pd.DataFrame, bars: dict, pv: dict) -> pd.DataFrame:
    t = t.copy()
    s = np.where(t.direction.str.upper() == "BUY", 1, -1)
    t["s"] = s
    t["risk_pts"] = (t.open_price - t.sl0).abs()
    t["pv"] = t.symbol.map(pv)
    t["risk_usd"] = t.risk_pts * t.volume * t.pv
    t["paper"] = [paper_close(bars[r.symbol], r.entry_utc) for r in t.itertuples()]
    t["slip_usd"] = s * (t.open_price - t.paper) * t.volume * t.pv        # >0 → gerçek dolum kötü
    t["spread_usd"] = t.symbol.map(S.TYPICAL_SPREAD) * t.volume * t.pv
    return t[(t.risk_pts > 0) & t.risk_usd.notna()]


def decisions(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    t["dec"] = align.assign_decisions(t)
    g = t.groupby("dec")
    d = pd.DataFrame({"entry": g.entry_utc.min(), "exit": g.exit_utc.max(), "symbol": g.symbol.first(),
                      "side": g.direction.first(), "net": g.net.sum(), "risk": g.risk_usd.sum(),
                      "slip": g.slip_usd.sum(), "spread": g.spread_usd.sum(), "legs": g.size()})
    d["R"] = d.net / d.risk
    d["R_paper"] = (d.net + d.slip) / d.risk
    d["R_stress"] = (d.net - EXTRA_SPREAD * d.spread) / d.risk
    return d.sort_values("entry").reset_index(drop=True)


def boot_p(R: np.ndarray, days: np.ndarray, n: int = 4000) -> tuple[float, list]:
    u, inv = np.unique(days, return_inverse=True)
    s, c = np.bincount(inv, weights=R), np.bincount(inv)
    pick = RNG.integers(0, len(u), size=(n, len(u)))
    m = s[pick].sum(1) / c[pick].sum(1)
    return float((m > 0).mean()), [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def single_position(d: pd.DataFrame) -> pd.DataFrame:
    keep, busy_until = [], pd.Timestamp.min.tz_localize("UTC")
    for r in d.itertuples():
        if r.entry >= busy_until:
            keep.append(r.Index)
            busy_until = r.exit
    return d.loc[keep]


def card(d: pd.DataFrame, family: str) -> dict:
    R = d.R.to_numpy()
    p, ci = boot_p(R, d.entry.dt.strftime("%Y-%m-%d").to_numpy())
    h = len(R) // 2
    m, m_paper, m_st = float(R.mean()), float(d.R_paper.mean()), float(d.R_stress.mean())
    sp = single_position(d)
    chk = {
        "1_hacim": {"deger": len(R), "esik": f"≥{MIN_DECISIONS} karar", "gecti": len(R) >= MIN_DECISIONS},
        "2_beklenti": {"deger": f"ortR={m:+.3f} P(EV>0)=%{100 * p:.1f}", "esik": "ortR>0 ve P≥%90",
                       "gecti": m > 0 and p >= MIN_P_EV},
        "3_kararlilik": {"deger": f"ilk={R[:h].mean():+.3f} son={R[h:].mean():+.3f}", "esik": "ikisi de ≥0",
                         "gecti": bool(R[:h].mean() >= 0 and R[h:].mean() >= 0)},
        "4_surtunme": {"deger": f"+0,5×spread: ortR={m_st:+.3f}", "esik": ">0", "gecti": m_st > 0},
        "5_icra": {"deger": f"kâğıt giriş ortR={m_paper:+.3f} vs gerçek {m:+.3f}",
                   "esik": "fark < 0,5×|gerçek ortR|", "gecti": abs(m_paper - m) < 0.5 * abs(m)},
        "6_sira_bagimli": {"deger": f"tek pozisyonla n={len(sp)} ortR={sp.R.mean():+.3f}", "esik": ">0",
                           "gecti": bool(sp.R.mean() > 0)},
    }
    verdict = "RED" if not chk["1_hacim"]["gecti"] else ("LIVE" if all(c["gecti"] for c in chk.values()) else "SHADOW")
    by_side = {f"{sym} {side}": {"n": int(len(g)), "ortR": round(float(g.R.mean()), 3), "net$": round(float(g.net.sum()), 0)}
               for (sym, side), g in d.groupby(["symbol", "side"])}
    months = {k: round(float(v), 3) for k, v in d.groupby(d.entry.dt.strftime("%Y-%m")).R.mean().items()}
    return {"scope": family.lower(), "tur": "canlı işlem kartı (E22)", "tarih": datetime.now().isoformat(timespec="seconds"),
            "aralik": [str(d.entry.min().date()), str(d.entry.max().date())], "karar": len(R),
            "bacak": int(d.legs.sum()), "wr": round(100 * float((R > 0).mean()), 1), "ort_R": round(m, 3),
            "toplam_R": round(float(R.sum()), 2), "net_usd": round(float(d.net.sum()), 0),
            "bootstrap_%95": ci, "p_ev_pozitif": round(p, 3), "sembol_yon": by_side, "aylik_ortR": months,
            "checks": chk, "verdikt": verdict,
            "not": "research/canli_kart_20261009/live_card.py; bot_trades + indicator_snapshots, karar bazında."}


def main(families: list[str]) -> None:
    client = data.get_client()
    tr = data.load_trades(client, SINCE)
    tr = tr[tr.family.isin(families)].reset_index(drop=True)
    pad = pd.Timedelta(hours=6)
    need = {s: (g.open_raw.min() - pad, g.close_raw.max() + pad) for s, g in tr.groupby("symbol")}
    bars = data.load_bars(sorted(need), need)
    al = align.align_trades(tr, bars)
    print(f"hizalama: {al.status} kesin={al.aligned_frac:.2f} dışlanan={len(al.excluded)}")
    t = per_trade(al.trades, bars, point_values(al.trades))
    for fam in families:
        d = decisions(t[t.family == fam])
        if d.empty:
            print(fam, "işlem yok")
            continue
        c = card(d, fam)
        (CARD_DIR / f"{fam.lower()}_canli.json").write_text(json.dumps(c, ensure_ascii=False, indent=1))
        print(f"\n== {fam}: {c['karar']} karar ({c['bacak']} bacak) {c['aralik']} WR %{c['wr']} ortR {c['ort_R']:+.3f} "
              f"toplam {c['toplam_R']:+.1f}R net {c['net_usd']:+.0f}$ CI {c['bootstrap_%95']} → {c['verdikt']}")
        for k, x in c["checks"].items():
            print(f"   {k:16} {'✓' if x['gecti'] else '✗'}  {x['deger']}")
        print("   sembol·yön:", c["sembol_yon"])
        print("   aylık:", c["aylik_ortR"])


if __name__ == "__main__":
    main([a.upper() for a in sys.argv[1:]] or ["VIXREG"])
