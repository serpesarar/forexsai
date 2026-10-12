"""IO-18'in tersi: botun "düşüşü kovalayan" NDX SELL anlarında BUY açılsaydı? (2026-10-10)

Ön-kayıt (sonuçtan önce):
- Koşullar IO-18'den SABİT: C1 = 1h fiyat EMA50'nin ≥2 ATR altında (SELL-işaretli g60_ema50 ≥ 2); C2 = 1h RSI ≤ 35.
- Üç kaynak: (1) botun gerçek NDX SELL kararları · (2) panel pulse1/pulse2 NDX SELL sinyalleri (VIXREG'in oy kaynağı),
  60 dk içinde tekrarlar tek sayılır, + VIX<18,4 (önceki gün) alt kümesi · (3) sinyalsiz genel piyasa 2025-01 → 2026-06 saat
  başı (06–20 UTC), koşul sağlanıyorsa.
- Ters işlem = BUY, giriş sinyalden SONRAKİ 1m açılış + spread (E7). Çıkışlar (hepsi raporlanır, seçim yok):
  braket SL ∈ {1,0, 1,5, 2,0}×ATR1h × TP ∈ {1,0, 1,5, 2,0, 3,0}×ATR1h (aynı barda iki bariyer → SL);
  zaman: 60/120/240 dk, aynı gün 16:00 ET, ertesi gün 16:00 ET (felaket stopu 2×ATR1h).
  R birimi = SL mesafesi (zaman çıkışında 2×ATR1h). Bootstrap %95, kronolojik iki yarı.
- Geçme: kaynak (2)'de bir çıkışın ort R > 0, %95 alt sınır > 0 ve iki yarıda + ; VE kaynak (3) aynı çıkışta belirgin daha
  düşükse "sinyale özgü"; değilse "aşırı-düşüş genel etkisi". 17 çıkış × 2 koşul × 3 kaynak denendi (çoklu test notu).
python3 research/ters_kovalama_20261010/run.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402

SPREAD = 1.5
SLS, TPS = (1.0, 1.5, 2.0), (1.0, 1.5, 2.0, 3.0)
TIMES = ("60dk", "120dk", "240dk", "gün16ET", "ertesi16ET")
CAT_SL = 2.0
VIX_T = 18.4
NY = "America/New_York"


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G = _mod("genis_tk", ROOT / "research" / "donus_vs_sl_20261009" / "genis.py")


def cond_feats(ext, sb: SymbolBars, t: pd.Timestamp) -> tuple[float, float, float]:
    """(SELL-işaretli 1h EMA50 uzaklığı, SELL-işaretli 1h RSI, ATR1h) — t'den önce kapanmış 1h bar."""
    j = sb.last_closed(60, t)
    g = ext.f[60]
    i1 = sb.last_closed(1, t)
    return (float((g["ema50"][j] - sb.a["close"][i1]) / g["atr"][j]), float(100 - g["rsi"][j]), float(g["atr"][j]))


def exits(sb: SymbolBars, t: pd.Timestamp, atr1h: float) -> dict | None:
    a, idx = sb.a, sb.m1.index
    j = sb.pos_at(t) + 1                       # sinyalden sonraki dakika açılışı
    if j >= idx.size - 5:
        return None
    e = float(a["open"][j]) + SPREAD
    hi, lo, cl = a["high"][j:], a["low"][j:], a["close"][j:]
    out = {}
    for slm in SLS:
        for tpm in TPS:
            sl, tp = e - slm * atr1h, e + tpm * atr1h
            ks, kt = np.flatnonzero(lo <= sl), np.flatnonzero(hi >= tp)
            k_s = ks[0] if ks.size else np.inf
            k_t = kt[0] if kt.size else np.inf
            if np.isinf(k_s) and np.isinf(k_t):
                out[f"SL{slm:g}/TP{tpm:g}"] = np.nan
            else:
                out[f"SL{slm:g}/TP{tpm:g}"] = -1.0 if k_s <= k_t else tpm / slm
    ny = t.tz_convert(NY)
    ends = {"60dk": t + pd.Timedelta(minutes=60), "120dk": t + pd.Timedelta(minutes=120),
            "240dk": t + pd.Timedelta(minutes=240),
            "gün16ET": (ny.normalize() + pd.Timedelta(hours=16)).tz_convert("UTC"),
            "ertesi16ET": (ny.normalize() + pd.Timedelta(days=1, hours=16)).tz_convert("UTC")}
    cat = e - CAT_SL * atr1h
    for k, end in ends.items():
        if end <= t:
            end = end + pd.Timedelta(days=1)
        j1 = sb.pos_at(end)
        n = j1 - j
        if n <= 0 or j1 >= idx.size:
            out[k] = np.nan
            continue
        hit = np.flatnonzero(lo[:n] <= cat)
        out[k] = -1.0 if hit.size else float((cl[n - 1] - e) / (CAT_SL * atr1h))
    return out


def events_bot(sb, ext) -> pd.DataFrame:
    b = pd.read_parquet(ROOT / "research" / "sl_ortak_20261009" / "results" / "bot.parquet")
    b = b[(b.sym == "NDX") & (b.yon == "SELL")]
    return pd.DataFrame({"t": b.t0.values, "kaynak": "bot SELL", "aile": b.aile.values})


def events_panel(sb, ext, vix: pd.Series) -> pd.DataFrame:
    p = pd.read_parquet(ROOT / "research" / "donus_vs_sl_20261009" / "results" / "panel.parquet")
    p = p[(p.symbol == "NDX.INDX") & p.model_type.isin(["pulse1", "pulse2"]) & (p.ml_direction == "SELL")].sort_values("ts")
    keep, last = [], None
    for ts in p.ts:
        if last is None or ts - last >= pd.Timedelta(minutes=60):
            keep.append(ts)
            last = ts
    d = pd.DataFrame({"t": keep, "kaynak": "panel pulse SELL"})
    d["vix"] = [_vix(vix, t) for t in d.t]
    return d


def _vix(vix: pd.Series, t: pd.Timestamp) -> float:
    day = pd.Timestamp(t.tz_convert(NY).date())
    prior = vix[vix.index < day]
    return float(prior.iloc[-1]) if len(prior) else np.nan


def events_generic() -> tuple[pd.DataFrame, SymbolBars, object]:
    raw = pd.read_parquet(ROOT / "research" / "ndx_gate_forge" / "data" / "bars_1m_all.parquet")
    raw = raw[raw.ts < pd.Timestamp("2026-06-15", tz="UTC")].set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float)
    sb = SymbolBars("NDX.INDX", raw)
    ext = G.Ext(sb)
    idx = sb.m1.index
    st = idx[(idx.minute == 0) & (idx.hour >= 6) & (idx.hour <= 20) & (idx.dayofweek < 5)]
    return pd.DataFrame({"t": st[st > idx[3000]], "kaynak": "genel piyasa 2025-26"}), sb, ext


def evaluate(ev: pd.DataFrame, sb, ext) -> pd.DataFrame:
    rows = []
    for _, r in ev.iterrows():
        t = pd.Timestamp(r.t)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        if sb.last_closed(60, t) < 60:
            continue
        ema_d, rsi_s, atr1h = cond_feats(ext, sb, t)
        if not (ema_d >= 2.0 or rsi_s >= 65.0):
            continue
        ex = exits(sb, t, atr1h)
        if ex is None:
            continue
        rows.append({**r.to_dict(), "C1": ema_d >= 2.0, "C2": rsi_s >= 65.0, **ex})
    return pd.DataFrame(rows)


def summarize(d: pd.DataFrame, label: str) -> list[str]:
    lines = [f"\n### {label}: n={len(d)} (C1 {int(d.C1.sum())}, C2 {int(d.C2.sum())})"]
    cols = [f"SL{s:g}/TP{t:g}" for s in SLS for t in TPS] + list(TIMES)
    for cn in ("C1", "C2"):
        g = d[d[cn]].sort_values("t").reset_index(drop=True)
        if len(g) < 8:
            lines.append(f"  {cn}: n={len(g)} yetersiz")
            continue
        half = np.arange(len(g)) < len(g) // 2
        lines.append(f"  {cn} (n={len(g)}):  çıkış            ort R   WR   %95             yarılar")
        for c in cols:
            x = g[c].to_numpy(float)
            ok = np.isfinite(x)
            if ok.sum() < 8:
                continue
            lo, hi, p = boot_mean_ci(x[ok])
            h1, h2 = np.nanmean(x[ok & half]), np.nanmean(x[ok & ~half])
            mark = " ✓" if lo > 0 and h1 > 0 and h2 > 0 else ""
            lines.append(f"     {c:14s} {np.nanmean(x):+.3f}  %{100 * (x[ok] > 0).mean():3.0f}  [{lo:+.2f}…{hi:+.2f}]  {h1:+.2f}/{h2:+.2f}{mark}")
    return lines


def main() -> None:
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    now = data.utc_now()
    raw = data.load_bars_raw("NDX.INDX", pd.Timestamp("2026-06-01", tz="UTC"), now)
    sb = SymbolBars("NDX.INDX", data.normalize_snapshot_clock(raw))
    ext = G.Ext(sb)
    vix = data.load_vix(pd.Timestamp("2026-06-01", tz="UTC"), now)
    lines = []
    bot = evaluate(events_bot(sb, ext), sb, ext)
    lines += summarize(bot, "1) Botun gerçek NDX SELL'lerinin TERSİ (BUY)")
    lines.append("     aileler: " + str(bot.aile.value_counts().to_dict()))
    pan = evaluate(events_panel(sb, ext, vix), sb, ext)
    lines += summarize(pan, "2a) Panel pulse1/2 NDX SELL sinyallerinin TERSİ (tüm VIX)")
    lines += summarize(pan[pan.vix < VIX_T], "2b) Aynısı, VIX<18,4 (VIXREG'in SELL rejimi)")
    gev, gsb, gext = events_generic()
    gen = evaluate(gev, gsb, gext)
    lines += summarize(gen, "3) Sinyalsiz genel piyasa 2025-26: aşırı düşmüşken saat başı BUY")
    for nm, d in (("bot", bot), ("panel", pan), ("genel", gen)):
        d.to_csv(out / f"{nm}.csv", index=False)
    txt = "\n".join(lines)
    (out / "rapor.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
