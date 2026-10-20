"""Sıkışma — yedinci tur: VIXREG VEKİLİ, bot ÖNCESİ (02-18 → 06-12) ve bot dönemi panel → results/rapor7.md

Ön-kayıt eki (2026-10-20, sonuçlara bakmadan):
- VIXREG vekili = panel pulse1/2/3 NDX sinyali, yönü önceki günün VIX rejiminin lehte yönüyle aynı (VIX ≥ 18,4 → BUY,
  altı → SELL), ASYA 22–07 UTC ve Cuma hariç (botun entry_window kapısı), 30 dk'da bir (yön başına). Geometri botun
  VIXREG'i: TP 80 / SL 110 puan sabit, spread 1,5, sonraki 1m açılış.
- Ölçü: Δ = ortR(sıkışık) − ortR(diğer) (atr_14_100 < 1,00), P(Δ<0) gün-blok, saat-içi tabakalı Δ ve P, engel kurt_R +
  P(kurt>0), çeyrekler. Ayrıca botun gerçek VIXREG'i ile aynı dönem (06-15 → 10-09) vekil kıyası (sadakat).
- Geçme (bağımsız kaynak ölçütü 3 için): bot ÖNCESİ vekilde P(Δ<0) ≥ %90 VE saat-içi P ≥ %90.
  Geçse de ileri ölçüt (1) ayrıca gerekir; bu tur yalnız "botun asıl sinyal tipinde bağımsız dönemde tutuyor mu" sorar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
import events as E
import exp6 as X6

OUT = C.HERE / "results"
TP_PTS, SL_PTS, VIX_T = 80.0, 110.0, 18.4
PULSES = ("pulse1", "pulse2", "pulse3")


def sim_pts(sb, ev: pd.DataFrame) -> np.ndarray:
    idx = sb.m1.index
    out = np.full(len(ev), np.nan)
    for k, (t, s) in enumerate(zip(pd.to_datetime(ev.t, utc=True), ev.s)):
        j = idx.searchsorted(t, side="left")
        if j >= idx.size - 30 or (idx[j] - t) > pd.Timedelta(minutes=5):
            continue
        e = float(sb.a["open"][j]) + (C.SPREAD["NDX.INDX"] if s > 0 else 0.0)
        R, kk, _ = C.simulate(sb, int(s), e, j, SL_PTS, TP_PTS, C.SPREAD["NDX.INDX"])
        out[k] = R if kk >= 0 else np.nan
    return out


def proxy(p: pd.DataFrame, vix: pd.Series) -> pd.DataFrame:
    p = p[p.model_type.isin(PULSES)].copy()
    t = pd.to_datetime(p.ts, utc=True)
    day = pd.to_datetime(t.dt.tz_convert("America/New_York").dt.date)
    vi = vix.reindex(vix.index.union(day.unique())).sort_index().ffill().shift(1).reindex(day).to_numpy()
    fav = np.where(vi >= VIX_T, "BUY", "SELL")
    h = t.dt.hour
    ok = (p.ml_direction.to_numpy() == fav) & ~((h >= 22) | (h < 7)).to_numpy() & (t.dt.dayofweek != 4).to_numpy()
    ev = pd.DataFrame({"t": t[ok].to_numpy(), "s": np.where(p.ml_direction[ok] == "BUY", 1, -1), "fam": "vixreg_vekil"})
    ev["t"] = pd.to_datetime(ev.t, utc=True)
    return E.dedup(ev, ["s"])


def summary(d: pd.DataFrame, lab: str) -> dict:
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()].sort_values("t").reset_index(drop=True)
    R, sq = d.R.to_numpy(float), (d.atr_14_100 < 1).to_numpy()
    days = C.day_ids(d.t)
    ud, inv = np.unique(days, return_inverse=True)
    dl = []
    for pk in C.RNG.integers(0, ud.size, (C.N_BOOT, ud.size)):
        idx = np.concatenate([np.flatnonzero(inv == j) for j in pk])
        r, s = R[idx], sq[idx]
        if s.sum() >= 3 and (~s).sum() >= 3:
            dl.append(r[s].mean() - r[~s].mean())
    st = X6.run(d, lab)
    qs = C.quarters(R, sq)
    return {"küme": lab, "n": len(d), "SELL%": float((d.s < 0).mean()), "sıkışık": int(sq.sum()),
            "ortR sıkışık": R[sq].mean(), "ortR diğer": R[~sq].mean(), "Δ": R[sq].mean() - R[~sq].mean(),
            "P(Δ<0)": float(np.mean(np.array(dl) < 0)), "saat-içi Δ": st["saat-içi Δ"],
            "P(saat-içi<0)": st["P(saat-içi Δ<0)"], "kurt_R": -R[sq].sum(),
            "P(kurt>0)": C.boot_saved(R, sq, days), "çeyrekler": "/".join(f"{x:+.1f}" for x in qs)}


def main() -> None:
    vix = C.data.load_vix(pd.Timestamp("2026-01-01", tz="UTC"), C.data.utc_now()).sort_index()
    long = C.bars_ndx_long()
    FL = C.compute_feats(long)
    sbl = C.SymbolBars("NDX.INDX", long)
    snap = C.bars_snapshots("NDX.INDX", "2026-05-20")
    Fs, sbs = C.compute_feats(snap), C.SymbolBars("NDX.INDX", snap)

    old = proxy(pd.read_parquet(OUT / "panel_old.parquet"), vix)
    old["R"] = sim_pts(sbl, old)
    old = E.add(old, FL)
    new = proxy(pd.read_parquet(C.ROOT / "research" / "donus_vs_sl_20261009" / "results" / "panel.parquet")
                .query("symbol == 'NDX.INDX'"), vix)
    new["R"] = sim_pts(sbs, new)
    new = E.add(new, Fs)
    old.to_parquet(OUT / "ev_S10_vixreg_vekil_eski.parquet")
    new.to_parquet(OUT / "ev_S10_vixreg_vekil_yeni.parquet")
    bot = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    bot = bot[(bot.sym == "NDX.INDX") & (bot.fam == "VIXREG")]

    rows = [summary(old, "VEKİL bot öncesi 02-18→06-12"), summary(old[old.t >= pd.Timestamp("2026-03-09", tz="UTC")],
            "VEKİL bot öncesi (03-09→, E4 şüphesiz)"), summary(new, "VEKİL bot dönemi 06-15→10-09"),
            summary(bot, "GERÇEK bot VIXREG")]
    # sadakat: vekil olayların gerçek VIXREG girişine ±30 dk yakınlığı
    bt = pd.to_datetime(bot.t, utc=True).dt.tz_convert(None).to_numpy(dtype="datetime64[ns]")
    nt = pd.to_datetime(new.t, utc=True).dt.tz_convert(None).to_numpy(dtype="datetime64[ns]")
    def _near(a, b):
        if not a.size or not b.size:
            return np.zeros(a.size, bool)
        return np.array([np.abs((b - x) / np.timedelta64(1, "m")).min() <= 30 for x in a])
    near, bn = _near(nt, bt), _near(bt, nt)
    L = ["# Sıkışma — yedinci tur: VIXREG vekili (exp7.py; ön-kayıt eki dosya başında)", C.md(pd.DataFrame(rows)),
         f"\nSadakat: bot dönemi vekil olaylarının %{100 * near.mean():.0f}'i gerçek bir VIXREG girişine ±30 dk yakın; "
         f"gerçek VIXREG girişlerinin %{100 * bn.mean():.0f}'inin ±30 dk'sında vekil olay var."]
    txt = "\n".join(L)
    (OUT / "rapor7.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
