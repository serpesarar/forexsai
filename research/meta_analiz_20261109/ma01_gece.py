"""MA-01: C3 kazancının saat dilimi ayrıştırması. Ön kayıt: PROTOCOL.md."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MT5 = ROOT / "c1_turev_20261105/data/mt5"
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)
SPREAD = 1.3      # puan, özgün C3 ile aynı
FIN = 2.0         # bp / gece
RSI_TH = 10.0
N_BOOT = 3000


def bars(sym: str) -> pd.DataFrame:
    x = pd.read_csv(MT5 / f"{sym}_M30.csv.gz")
    x["ts_et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7)
    x["d"] = x.ts_et.dt.normalize()
    x["m"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
    return x[x.ts_et.dt.dayofweek < 5].reset_index(drop=True)


def axis_check(x: pd.DataFrame) -> pd.Series:
    """Ay ay en oynak 30 dk barının dakikası (09:30 ET = 570 beklenir)."""
    r = (x.h - x.l) / x.c
    g = pd.DataFrame({"ym": x.ts_et.dt.to_period("M"), "m": x.m, "r": r}).groupby(["ym", "m"]).r.mean()
    return g.groupby(level=0).idxmax().map(lambda k: k[1]).value_counts()


def rsi2(s: pd.Series) -> pd.Series:
    g = s.diff()
    up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean()
    dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))


def day_table(x: pd.DataFrame) -> pd.DataFrame:
    """Gün başına: S (15:30 öncesi kapanış), 15:30/16:00/09:30/10:00 bar açılışları."""
    prev_c = x.c.shift(1)
    ok = x.t.diff() <= 3 * 1800
    t = pd.DataFrame(index=sorted(x.d.unique()))
    for name, minute in (("o930", 570), ("o1000", 600), ("o1530", 930), ("o1600", 960)):
        b = x[x.m == minute].drop_duplicates("d").set_index("d")
        t[name] = b.o
    sig = pd.Series(prev_c[(x.m == 930) & ok].to_numpy(), index=x.d[(x.m == 930) & ok].to_numpy())
    sig = sig[~sig.index.duplicated()]
    t["S"] = sig
    return t.dropna(subset=["S", "o1530"])


def sr(v: np.ndarray) -> float:
    return float(np.mean(v) / np.std(v, ddof=1)) if len(v) > 2 and np.std(v) > 0 else np.nan


def boot_p(df: pd.DataFrame, a: str, b: str, rng) -> float:
    """Ay-blok bootstrap: P(SR_a > SR_b)."""
    ym = df.index.to_period("M").astype(str)
    groups = [df[ym == u][[a, b]].to_numpy() for u in np.unique(ym)]
    wins = 0
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        z = np.vstack([groups[i] for i in pick])
        wins += sr(z[:, 0]) > sr(z[:, 1])
    return wins / N_BOOT


def boot_mean_p(v: pd.Series, rng) -> float:
    ym = v.index.to_period("M").astype(str)
    groups = [v[ym == u].to_numpy() for u in np.unique(ym)]
    c = 0
    for _ in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        c += np.concatenate([groups[i] for i in pick]).mean() > 0
    return c / N_BOOT


def main() -> None:
    rng = np.random.default_rng(11)
    x = bars("NAS100")
    res: dict = {"eksen_en_oynak_bar_dakikasi": {int(k): int(v) for k, v in axis_check(x).items()}}
    t = day_table(x)
    t["rsi2"] = rsi2(t.S)
    nx = t.shift(-1)
    ent = t.o1530 + SPREAD
    bp = lambda a, b: (a / b - 1) * 1e4
    ev = pd.DataFrame({
        "D1": bp(t.o1600, t.o1530), "D2": bp(nx.o930, t.o1600), "D3": bp(nx.o1530, nx.o930),
        "V0": bp(nx.o1530, ent) - FIN, "V1": bp(nx.o930, ent) - FIN, "V2": bp(nx.o1000, ent) - FIN,
        "V3": bp(nx.o930, t.o1600 + SPREAD) - FIN, "rsi2": t.rsi2,
    }).dropna()
    ev.index = pd.DatetimeIndex(ev.index)
    sig = ev[ev.rsi2 < RSI_TH]
    res["n_gun"], res["n_olay"] = int(len(ev)), int(len(sig))
    res["donem"] = [str(ev.index[0].date()), str(ev.index[-1].date())]
    cols = ["D1", "D2", "D3", "V0", "V1", "V2", "V3"]
    tab = pd.DataFrame({
        "olay_ort": sig[cols].mean(), "olay_ss": sig[cols].std(), "olay_SR": sig[cols].apply(lambda c: sr(c.to_numpy())),
        "olay_isabet": (sig[cols] > 0).mean(), "olay_enkotu": sig[cols].min(),
        "tumgun_ort": ev[cols].mean(), "tumgun_ss": ev[cols].std(),
    }).round(3)
    print(tab.to_string())
    tab.to_csv(OUT / "ma01_dilim.csv")
    h = len(sig) // 2
    crit = {}
    for v in ("V1", "V2", "V3"):
        crit[v] = {
            "ort_orani": round(float(sig[v].mean() / sig.V0.mean()), 3),
            "ss_orani": round(float(sig[v].std() / sig.V0.std()), 3),
            "P_SR_ustun": round(boot_p(sig, v, "V0", rng), 3),
            "yari1_SR": [round(sr(sig[v].iloc[:h].to_numpy()), 3), round(sr(sig.V0.iloc[:h].to_numpy()), 3)],
            "yari2_SR": [round(sr(sig[v].iloc[h:].to_numpy()), 3), round(sr(sig.V0.iloc[h:].to_numpy()), 3)],
        }
    res["olcut"] = crit
    res["yil"] = sig.groupby(sig.index.year)[["D1", "D2", "D3", "V0", "V1"]].mean().round(1).assign(n=sig.groupby(sig.index.year).size()).to_dict("index")
    res["gece_payi"] = round(float(sig.D2.mean() / (sig.D1.mean() + sig.D2.mean() + sig.D3.mean())), 3)

    # Bağımsız dönem: QQQ günlük 1999-03 → 2018-04
    q = pd.read_parquet(ROOT / "fitil_ret_20261106/data_d1_QQQ.parquet")
    q.index = pd.DatetimeIndex(q.index).tz_localize(None).normalize()
    q = q[q.index < "2018-05-01"]
    r = rsi2(q.Close)
    on = bp(q.Open.shift(-1), q.Close)          # gece (temettü günleri hafif aşağı yanlı)
    dy = bp(q.Close.shift(-1), q.Open.shift(-1))  # ertesi gündüz
    qq = pd.DataFrame({"gece": on, "gunduz": dy, "rsi2": r}).dropna()
    qs = qq[qq.rsi2 < RSI_TH]
    res["qqq"] = {
        "n": int(len(qs)), "gece_ort": round(float(qs.gece.mean()), 2), "gunduz_ort": round(float(qs.gunduz.mean()), 2),
        "gece_ss": round(float(qs.gece.std()), 1), "gunduz_ss": round(float(qs.gunduz.std()), 1),
        "gece_payi": round(float(qs.gece.mean() / (qs.gece.mean() + qs.gunduz.mean())), 3),
        "P_gece_poz": round(boot_mean_p(qs.gece, rng), 3), "P_gunduz_poz": round(boot_mean_p(qs.gunduz, rng), 3),
        "tumgun_gece": round(float(qq.gece.mean()), 2), "tumgun_gunduz": round(float(qq.gunduz.mean()), 2),
        "donemler": {f"{a}-{b}": [int(((qs.index >= a) & (qs.index < b)).sum()),
                                  round(float(qs.gece[(qs.index >= a) & (qs.index < b)].mean()), 1),
                                  round(float(qs.gunduz[(qs.index >= a) & (qs.index < b)].mean()), 1)]
                     for a, b in (("1999", "2003"), ("2003", "2009"), ("2009", "2014"), ("2014", "2018-05"))},
    }
    (OUT / "ma01.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: res[k] for k in ("eksen_en_oynak_bar_dakikasi", "n_gun", "n_olay", "donem", "olcut", "gece_payi", "yil", "qqq")}, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
