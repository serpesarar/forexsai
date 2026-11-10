"""İşlem açıldıktan sonra ortalama en kötü (MAE) ve en iyi (MFE) seyir. Betimsel; hüküm yok."""
import numpy as np, pandas as pd
from pathlib import Path
from broker import MT5, gun_tablosu
ROOT = Path(__file__).resolve().parents[1]; OUT = Path(__file__).resolve().parent / "results"
x = pd.read_csv(MT5 / "NAS100_M30.csv.gz"); x["et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x = x[x.et.dt.dayofweek < 5].reset_index(drop=True); x["d"] = x.et.dt.normalize(); x["m"] = x.et.dt.hour * 60 + x.et.dt.minute
def seyir(entry_et, exit_et, entry_px):
    """[giriş barı açılışı, çıkış barı açılışı) arası bar high/low; MAE/MFE bp (girişe göre)."""
    seg = x[(x.et >= entry_et) & (x.et < exit_et)]
    if seg.empty: return None
    return (seg.l.min() / entry_px - 1) * 1e4, (seg.h.max() / entry_px - 1) * 1e4, (seg.c.iloc[-1] / entry_px - 1) * 1e4
def ozet(df, ad, px=27800.0):
    a, f, n = df.mae, df.mfe, df.net
    q = lambda s, p: float(np.quantile(s, p))
    return {"kural": ad, "n": len(df), "MAE_ort_bp": a.mean(), "MAE_med": a.median(), "MAE_p90": q(a, .10), "MAE_p95": q(a, .05), "MAE_en_kotu": a.min(),
            "MFE_ort_bp": f.mean(), "MFE_med": f.median(), "MFE_p90": q(f, .90), "MFE_en_iyi": f.max(),
            "MAE_ort_puan": a.mean() * px / 1e4, "MFE_ort_puan": f.mean() * px / 1e4,
            "kazanan_MAE_ort": a[net_pos(df)].mean(), "kaybeden_MFE_ort": f[~net_pos(df)].mean(), "kaybeden_MAE_ort": a[~net_pos(df)].mean(), "kazanan_MFE_ort": f[net_pos(df)].mean(),
            "MAE<=-100bp_%": float((a <= -100).mean() * 100), "MAE<=-200bp_%": float((a <= -200).mean() * 100)}
net_pos = lambda df: (df.net > 0).to_numpy()
rows = []
t = gun_tablosu("NAS100").dropna(subset=["son_saat", "y_net"]); K = t[t.son_saat < 0]; days = list(t.index); rec = []
for d in K.index:
    i = days.index(d); 
    if i + 1 >= len(days): continue
    nd = days[i + 1]; e = x[(x.d == d) & (x.m == 960)]; ex = x[(x.d == nd) & (x.m == 570)]
    if e.empty or ex.empty: continue
    px = e.o.iloc[0] + e.sp.iloc[0]; r = seyir(e.et.iloc[0], ex.et.iloc[0], px)
    if r: rec.append((d, r[0], r[1], r[2], K.loc[d, "y_net"]))
ks = pd.DataFrame(rec, columns=["d", "mae", "mfe", "son", "net"]).set_index("d"); rows.append(ozet(ks, "KSG (16:00→ertesi 09:30)")); ks.to_csv(OUT / "mae_mfe_ksg.csv")
# C3 / C3b (15:30 girişi)
S = x[x.m == 930].drop_duplicates("d").set_index("d"); prev = x.c.shift(1)[x.m == 930]; prev.index = x[x.m == 930].d.to_numpy(); prev = prev[~prev.index.duplicated()]
dd = pd.DataFrame({"S": prev, "E": S.o, "sp": S.sp}).dropna(); g = dd.S.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean(); dd["rsi"] = 100 - 100 / (1 + up / (dn + 1e-12))
idx = list(dd.index); c3 = []; c3b = []; i = 20
while i < len(dd) - 1:
    if dd.rsi.iloc[i] < 10:
        e = S.loc[idx[i]]; px = e.o + e.sp
        j0 = i + 1; r0 = seyir(e.et, S.loc[idx[j0]].et, px)
        if r0: c3.append((idx[i], *r0[:3], (S.loc[idx[j0]].o / px - 1) * 1e4 - 2))
        j = next((k for k in range(i + 1, min(i + 6, len(dd))) if dd.S.iloc[k] > dd.S.iloc[k - 1]), min(i + 5, len(dd) - 1))
        r1 = seyir(e.et, S.loc[idx[j]].et, px)
        if r1: c3b.append((idx[i], *r1[:3], (S.loc[idx[j]].o / px - 1) * 1e4 - 2 * (j - i))); i = j; continue
    i += 1
C3 = pd.DataFrame(c3, columns=["d", "mae", "mfe", "son", "net"]).set_index("d"); C3B = pd.DataFrame(c3b, columns=["d", "mae", "mfe", "son", "net"]).set_index("d")
rows += [ozet(C3, "C3 (15:30→ertesi 15:30)"), ozet(C3B, "C3b (ilk yükselen 15:30, ≤5 gün)")]; C3.to_csv(OUT / "mae_mfe_c3.csv"); C3B.to_csv(OUT / "mae_mfe_c3b.csv")
# bot aileleri (gerçek icra, 1m broker barları)
tr = pd.read_parquet(ROOT / "tp_sonrasi_ters_20261109/data/ndx_trades.parquet"); b1 = pd.read_parquet(ROOT / "tp_sonrasi_ters_20261109/data/ndx_1m.parquet"); tr = tr[tr.sl0 > 0]
d = tr.groupby(["family", "direction", "decision"]).agg(en=("entry_utc", "first"), ex=("exit_utc", "last"), px=("open_price", "first"), sl=("sl0", "first"), tp=("tp0", "first"), net=("net", "sum"), lot=("volume", "sum")).reset_index(); bot = []
for r in d.itertuples():
    s = b1[(b1.index >= r.en.floor("min")) & (b1.index <= r.ex)]
    if s.empty: continue
    sg = 1 if r.direction == "BUY" else -1; lo, hi = s.low.min(), s.high.max()
    mae = (lo - r.px) if sg == 1 else (r.px - hi); mfe = (hi - r.px) if sg == 1 else (r.px - lo)
    bot.append((r.family, r.direction, mae / r.px * 1e4, mfe / r.px * 1e4, mae, mfe, abs(r.px - r.sl), abs(r.tp - r.px) if r.tp else np.nan, r.net, (r.ex - r.en).total_seconds() / 60))
B = pd.DataFrame(bot, columns=["aile", "yon", "mae", "mfe", "mae_p", "mfe_p", "sl_p", "tp_p", "net", "dk"]); B.to_csv(OUT / "mae_mfe_bot.csv", index=False)
for (a, y), x_ in B.groupby(["aile", "yon"]):
    if len(x_) >= 10:
        o = ozet(x_, f"BOT {a} {y}", px=27800.0); o["MAE_ort_puan"] = x_.mae_p.mean(); o["MFE_ort_puan"] = x_.mfe_p.mean(); o["SL_mesafe_puan"] = x_.sl_p.mean(); o["TP_mesafe_puan"] = x_.tp_p.mean(); o["sure_dk_med"] = x_.dk.median(); rows.append(o)
R = pd.DataFrame(rows); R.to_csv(OUT / "mae_mfe_ozet.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(R[["kural", "n", "MAE_ort_bp", "MAE_med", "MAE_p90", "MAE_en_kotu", "MFE_ort_bp", "MFE_med", "MFE_p90", "MFE_en_iyi", "MAE_ort_puan", "MFE_ort_puan"]].round(1).to_string())
print(R[["kural", "kazanan_MAE_ort", "kazanan_MFE_ort", "kaybeden_MAE_ort", "kaybeden_MFE_ort", "MAE<=-100bp_%", "MAE<=-200bp_%"]].round(1).to_string())
print(R[R.kural.str.startswith("BOT")][["kural", "SL_mesafe_puan", "TP_mesafe_puan", "sure_dk_med"]].round(1).to_string())
