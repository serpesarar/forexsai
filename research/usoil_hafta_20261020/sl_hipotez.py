"""USOIL 2 SL'den türetilen H1–H6 — bkz. PROTOCOL_SL.md. Botun kendi entry_gate.compute_entry_score'u birebir.

python3 research/usoil_hafta_20261020/sl_hipotez.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import run as U

sys.path.insert(0, str(U.ROOT / "yeni deneme"))
import entry_gate as EG  # noqa: E402

C = U.C
SOURCE_SL = {405554591, 406667349}
N_C1M, N_C5M, N_C30M = 240, 60, 60
DAY_MOVE_MIN = 0.02


def bar_lists(df: pd.DataFrame):
    g5 = df.resample("5min", label="left", closed="left")
    b5 = pd.DataFrame({"high": g5.high.max(), "low": g5.low.min(), "close": g5.close.last()}).dropna()
    g30 = df.resample("30min", label="left", closed="left")
    b30 = pd.DataFrame({"high": g30.high.max(), "low": g30.low.min(), "close": g30.close.last()}).dropna()
    return b5, b30


def flags(df: pd.DataFrame, b5: pd.DataFrame, b30: pd.DataFrame, t: pd.Timestamp) -> dict | None:
    i1 = df.index.searchsorted(t - pd.Timedelta(minutes=1), side="right")   # 1m barı sonu ≤ t
    if i1 < N_C1M or (t - df.index[i1 - 1]) > pd.Timedelta(minutes=10):
        return None
    c1 = df.iloc[i1 - N_C1M:i1]
    c1m = [{"high": h, "low": l, "close": c, "volume": v} for h, l, c, v in
           zip(c1.high.to_numpy(), c1.low.to_numpy(), c1.close.to_numpy(), c1.volume.to_numpy())]
    j5 = b5.index.searchsorted(t - pd.Timedelta(minutes=5), side="right")
    j30 = b30.index.searchsorted(t - pd.Timedelta(minutes=30), side="right")
    c5m = [{"close": c} for c in b5.close.to_numpy()[max(0, j5 - N_C5M):j5]]
    c30m = [{"close": c} for c in b30.close.to_numpy()[max(0, j30 - N_C30M):j30]]
    score, fails = EG.compute_entry_score("USOIL.FOREX", "BUY", c1m, c5m, c30m, t.hour)
    day0 = df.index.searchsorted(t.normalize())
    dmove = float(c1.close.iloc[-1] / df.open.iloc[day0] - 1) if day0 < i1 else np.nan
    wd, hr = t.dayofweek, t.hour
    return {"H1 bıçak": "bicak_yakalama" in fails, "H2 ema200 ters": "ema200_tarafi" in fails,
            "H3 bıçak∧ema200": ("bicak_yakalama" in fails) and ("ema200_tarafi" in fails),
            "H4 haftalık açılış 2s": bool(wd == 6 and hr >= 22), "H5 skor≤5": score <= 5,
            "H6 gün ≥+%2": bool(dmove >= DAY_MOVE_MIN), "skor": score}


def add_flags(df, b5, b30, ev: pd.DataFrame) -> pd.DataFrame:
    rows = [flags(df, b5, b30, pd.Timestamp(t)) for t in pd.to_datetime(ev.t, utc=True)]
    keep = [i for i, r in enumerate(rows) if r is not None]
    out = ev.iloc[keep].reset_index(drop=True)
    return pd.concat([out, pd.DataFrame([rows[i] for i in keep])], axis=1)


def evaluate(d: pd.DataFrame, h: str, lab: str) -> dict:
    d = d[np.isfinite(d.R)].sort_values("t").reset_index(drop=True)
    R, m = d.R.to_numpy(float), d[h].to_numpy(bool)
    row = {"popülasyon": lab, "hipotez": h, "n": len(d), "işaretli": int(m.sum())}
    if m.sum() < 3 or (~m).sum() < 3:
        return row
    days = C.day_ids(d.t)
    ud, inv = np.unique(days, return_inverse=True)
    dl = []
    for p in U.RNG.integers(0, ud.size, (2000, ud.size)):
        idx = np.concatenate([np.flatnonzero(inv == j) for j in p])
        r, s = R[idx], m[idx]
        if s.sum() >= 2 and (~s).sum() >= 2:
            dl.append(r[s].mean() - r[~s].mean())
    half = np.arange(len(d)) < len(d) // 2
    hd = [R[m & half].mean() - R[~m & half].mean() if (m & half).sum() >= 2 else np.nan,
          R[m & ~half].mean() - R[~m & ~half].mean() if (m & ~half).sum() >= 2 else np.nan]
    rnd = np.array([-R[U.RNG.choice(R.size, int(m.sum()), replace=False)].sum() for _ in range(3000)])
    row.update({"ortR işaretli": R[m].mean(), "ortR diğer": R[~m].mean(), "Δ": R[m].mean() - R[~m].mean(),
                "P(Δ<0)": float(np.mean(np.array(dl) < 0)), "kurt_R": -R[m].sum(),
                "P(kurt>0)": C.boot_saved(R, m, days), "rastgele %": float((rnd < -R[m].sum()).mean()),
                "yarılar Δ": f"{hd[0]:+.2f}/{hd[1]:+.2f}"})
    return row


def main() -> None:
    df = U.bars()
    b5, b30 = bar_lists(df)
    tr = pd.read_csv(U.TRADES)
    tr = tr[(tr.family == "MOMSR") & (tr.direction == "BUY") & tr.outcome.isin(["TP", "SL", "BE", "DIGER_+", "DIGER_-"])]
    src = tr[tr.pid.isin(SOURCE_SL)]
    tr = tr[~tr.pid.isin(SOURCE_SL)]
    p1 = add_flags(df, b5, b30, pd.DataFrame({"t": pd.to_datetime(tr.entry_utc, utc=True), "R": tr.r_exit.astype(float).to_numpy(),
                                              "giris": tr.fp_entry_type.astype(str).to_numpy()}))
    s1 = add_flags(df, b5, b30, pd.DataFrame({"t": pd.to_datetime(src.entry_utc, utc=True), "R": src.r_exit.astype(float).to_numpy()}))
    p2 = add_flags(df, b5, b30, pd.read_parquet(U.OUT / "k3.parquet")[["t", "R"]])
    p3 = add_flags(df, b5, b30, pd.read_parquet(U.OUT / "k2.parquet")[["t", "R"]])
    for nm, x in (("p1", p1), ("p2", p2), ("p3", p3)):
        x.to_parquet(U.OUT / f"sl_{nm}.parquet")
    hyps = ["H1 bıçak", "H2 ema200 ters", "H3 bıçak∧ema200", "H4 haftalık açılış 2s", "H5 skor≤5", "H6 gün ≥+%2"]
    L = ["# USOIL 2 SL → hipotez sınaması (ön-kayıt PROTOCOL_SL.md)",
         "\n## Kaynak SL'lerin bayrakları (yeniden hesap, botun fonksiyonuyla)",
         C.md(s1[["t", "R"] + hyps + ["skor"]].astype({h: str for h in hyps}))]
    rows = []
    for lab, d in (("P1 bot MOMSR BUY (2 SL hariç)", p1), ("P2 panel BUY 02→10", p2),
                   ("P2 panel BUY 06→10", p2[p2.t >= pd.Timestamp("2026-06-01", tz="UTC")]), ("P3 engellenen BUY", p3)):
        rows += [evaluate(d, h, lab) for h in hyps]
    t = pd.DataFrame(rows)
    t.to_csv(U.OUT / "sl_hipotez.csv", index=False)
    for h in hyps:
        L.append(f"\n## {h}")
        L.append(C.md(t[t.hipotez == h].drop(columns=["hipotez"])))
    if "giris" in p1:
        g = p1.groupby("giris").R.agg(["size", "mean"]).reset_index()
        L.append("\n## Ek: botun giriş yolu (parmak izi) — ortR")
        L.append(C.md(g))
    txt = "\n".join(L)
    (U.OUT / "sl_hipotez.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
