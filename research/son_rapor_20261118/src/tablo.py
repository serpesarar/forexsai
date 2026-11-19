"""tablo.py — 14 kapının tamamı aynı ölçülerle tek tabloda (Duka NDX + MT5 NAS100; Avrupa: Duka DAX/CAC/STOXX). python tablo.py"""
import json, sys
from datetime import datetime
import numpy as np, pandas as pd
import rapor as R, ek_kapilar as E
G, NY = R.G, R.NY
sys.path.insert(0, str(R.ROOT / "research/ndx_korku_avrupa_20261118/src"))
import na  # noqa: E402
cal = R.trading_calendar(); k, a = R.cycle(cal); ev = R.event_days(); vr = E.vix_ratio()

def gates(b, st):
    t = R.k1_table(b, st); t["k"] = k.reindex(t.d).values; t["a"] = a.reindex(t.d).values; t["olay"] = t.d.isin(ev)
    kk = t[t.K1].reset_index(drop=True); n = len(kk); one = np.ones(n)
    veto = np.isin(kk.k.values, [0, 1, 2]); after = np.isin(kk.a.values, range(3, 8))
    ard = (kk.K1_dun | (kk.sess_dun <= -0.01)).values
    olay = kk.olay.values & (kk.d <= R.CAL_END).values
    inv = np.nan_to_num(vr.reindex(kk.d).values >= 1.0, nan=0).astype(bool)
    dp = G.day_prices(b, NY, [570, 900, 930, 960], st)
    r2 = E.rsi2(pd.Series(dp.o960.values, index=pd.to_datetime(dp.index)).dropna())
    c3 = (r2.reindex(kk.d).values < 10)
    es_ok = np.isfinite(kk.es.values); xp_ok = np.isfinite(kk.xp.values)
    rows = {}
    rows["00 Taban: korku gecesi K1"] = R.metrics(kk.d, kk.gece.values, one)
    rows["01 OPEX korku vetosu"] = R.metrics(kk.d, kk.gece.values, np.where(veto, 0, 1.0))
    rows["02 İlk yükselen kapanışta çık (XP)"] = R.metrics(kk.d[xp_ok], kk.xp.values[xp_ok], one[xp_ok])
    rows["03 Önerilen paket: K1 + OPEX vetosu + XP"] = R.metrics(kk.d[xp_ok], kk.xp.values[xp_ok], np.where(veto, 0, 1.0)[xp_ok])
    rows["04 Korku ertesi seansı (gece yok)"] = R.metrics(kk.d[es_ok], kk.es.values[es_ok], one[es_ok])
    rows["05 Art arda korku dozu ×1,5"] = R.metrics(kk.d, kk.gece.values, np.where(ard, 1.5, 1.0))
    rows["06 Olay günü vetosu"] = R.metrics(kk.d, kk.gece.values, np.where(olay, 0, 1.0))
    rows["07 Vade sonrası 3.–7. gün dozu ×1,5"] = R.metrics(kk.d, kk.gece.values, np.where(after, 1.5, 1.0))
    rows["08 Korku ∧ ters VIX eğrisi dozu ×1,5"] = R.metrics(kk.d, kk.gece.values, np.where(inv, 1.5, 1.0))
    rows["09 Korku ∧ C3b aynı gün dozu ×1,5"] = R.metrics(kk.d, kk.gece.values, np.where(c3, 1.5, 1.0))
    t3 = []
    for d in kk.d:  # K3 ayrı kural (K1'den bağımsız tetik)
        pass
    tt = t.copy(); k3 = []
    for d in tt.d:
        r = dp.loc[d.date()] if d.date() in dp.index else None
        k3.append(bool(r is not None and np.isfinite(r.o900) and r.o960 / r.o900 - 1 <= -0.003))
    z = tt[np.array(k3)]
    rows["10 K3 son saat korkusu"] = R.metrics(z.d, z.gece.values, np.ones(len(z)))
    for nm, (sec, w, en, ex) in {"11 Geniş fitilli KSG": (7200, 43200, 930, 960), "12 Referans fitilli KSG": (3600, 21600, 960, 570)}.items():
        ends = E.GC.wick_ends(b, NY, sec, 0.50, st); nts = E.GC.nights(dp, en, ex, 900, E.GC.nyse_ok)
        m = E.GC.tag(nts.t_in.values, ends, w) & (nts.ksg_ret < 0).values; zz = nts[m]
        rows[nm] = R.metrics(pd.to_datetime(zz.d), zz.net_bp.values, np.ones(len(zz)))
    ks = R.ksg_trades(b); ks["k"] = k.reindex(ks.d).values
    rows["13a KSG taban"] = R.metrics(ks.d, ks.net.values, np.ones(len(ks)))
    rows["13 KSG OPEX vetosu"] = R.metrics(ks.d, ks.net.values, np.where(np.isin(ks.k.values, [0, 1, 2]), 0, 1.0))
    return rows

def europe():
    n = na.gn.nts(G.ndx_bars(), 60); rows = []
    for sym in ("DAX", "CAC", "STOXX"):
        tz, cl, src = na.EU[sym]; b, spr = na.kk.load(sym, src); t = b.t.values
        dp = G.day_prices(b, tz, [cl], 60); ed = [z for z in dp.index if z.weekday() < 5 and np.isfinite(dp.loc[z, f"o{cl}"])]
        for d, k1 in zip(n.d, n.K1):
            if not k1: continue
            u = int(pd.Timestamp(datetime(d.year, d.month, d.day, 16, 0), tz=NY).timestamp()); i = int(np.searchsorted(t, u))
            if i >= len(t) or t[i] - u > 18 * 3600: continue
            dl = pd.Timestamp(int(t[i]), unit="s", tz="UTC").tz_convert(tz)
            j = int(np.searchsorted(np.array(ed), dl.date(), side="right" if dl.hour * 60 + dl.minute >= cl else "left"))
            if j >= len(ed): continue
            rows.append({"d": pd.Timestamp(d), "net": (dp.loc[ed[j], f"o{cl}"] / (b.o.values[i] + spr) - 1) * 1e4 - na.kk.FIN * (ed[j] - d).days})
    x = pd.DataFrame(rows)
    return R.metrics(x.d, x.net.values, np.ones(len(x)))

c3 = R.c3b_book(); c3["k"] = k.reindex(c3.d).values
out = {"DUKA": gates(G.ndx_bars(), 60), "MT5": gates(R.KD.mt5_m30("NAS100"), 1800)}
out["DUKA"]["14a C3b taban"] = R.metrics(c3.d, c3.net.values, np.ones(len(c3)))
out["DUKA"]["14 C3b + OPEX vetosu"] = R.metrics(c3.d, c3.net.values, np.where(np.isin(c3.k.values, [0, 1, 2]), 0, 1.0))
out["DUKA"]["15 NDX korkusu → Avrupa (DAX+CAC+STOXX)"] = europe()
d = json.load(open(R.RES / "son_rapor.json")); d["tek_tablo"] = out
json.dump(d, open(R.RES / "son_rapor.json", "w"), ensure_ascii=False, indent=1, default=str)
keys = ["islem", "yilda", "isabet_%", "ort_bp", "en_kotu_bp", "en_kotu_%10_ort_bp", "maks_dusus_bp", "arti_yil"]
for nm in sorted(set(out["DUKA"]) | set(out["MT5"])):
    du, mt = out["DUKA"].get(nm, {}), out["MT5"].get(nm, {})
    print(f"{nm:44s} D {[du.get(x) for x in keys]}  M {[mt.get(x) for x in keys] if mt else '-'}")
