"""genis.py — aynı düzenek: kör endeksler + canlı KSG kitabı + C3b uzun geçmiş. python genis.py"""
import json, numpy as np, pandas as pd
import rapor as R
cal = R.trading_calendar(); k, a = R.cycle(cal); ev = R.event_days()
out = json.load(open(R.RES / "son_rapor.json"))
for nm, (sym, since) in {"MT5_US500": ("US500", "2018-06-01"), "MT5_US30": ("US30", None), "MT5_US2000": ("US2000", None)}.items():
    out[nm] = R.run_feed(nm, R.KD.mt5_m30(sym, since), 1800, k, a, ev)
    t = R.k1_table(R.KD.mt5_m30(sym, since), 1800); t["k"] = k.reindex(t.d).values; kk = t[t.K1].reset_index(drop=True)
    w = np.where(np.isin(kk.k.values, [0, 1, 2]), 0.0, 1.0); ok = np.isfinite(kk.xp.values)
    out[nm]["PAKET_K1_veto_XP"] = R.metrics(kk.d[ok], kk.xp.values[ok], w[ok])
    print(nm, "tamam", flush=True)
# canlı KSG kitabı (rules.ksg, Duka)
t = pd.read_parquet(R.ROOT / "research/ndx_10y_1m_20261116/results/a_trades.parquet"); t = t[t.rule == "KSG"].copy(); t["d"] = pd.to_datetime(t.d)
t["k"] = k.reindex(t.d).values; v = np.isin(t.k.values, [0, 1, 2])
out["KSG_canli_kitap_DUKA"] = {"taban": R.metrics(t.d, t.net_bp.values, np.ones(len(t))), "veto": R.metrics(t.d, t.net_bp.values, np.where(v, 0.0, 1.0)),
                               "vetolanan_ort": round(float(t.net_bp[v].mean()), 1), "P": round(R.gate_p(t.net_bp.values, v, 5), 4)}
# C3b uzun geçmiş günlük
for nm, x in (("C3b_QQQ_1999_2026", R.V.ohlc("QQQ")), ("C3b_NDX_1985_1999", R.V.ndx_frame()[lambda z: (z.index >= "1985-10-01") & (z.index <= "1999-02-28")])):
    c = R.vm.c3b(x); c["k"] = k.reindex(c.d).values; c["a"] = a.reindex(c.d).values
    v = np.isin(c.k.values, [0, 1, 2]); da = np.isin(c.a.values, range(3, 8))
    out[nm] = {"taban": R.metrics(c.d, c.net.values, np.ones(len(c))), "veto": R.metrics(c.d, c.net.values, np.where(v, 0.0, 1.0)),
               "vetolanan_ort": round(float(c.net[v].mean()), 1), "P": round(R.gate_p(c.net.values, v, 6), 4),
               "veto_doz": R.metrics(c.d, c.net.values, np.where(v, 0.0, np.where(da, 1.5, 1.0))), "doz_icinde_ort": round(float(c.net[da].mean()), 1)}
json.dump(out, open(R.RES / "son_rapor.json", "w"), ensure_ascii=False, indent=1, default=str)
keys = ["islem", "yilda", "isabet_%", "ort_bp", "en_kotu_bp", "en_kotu_%10_ort_bp", "maks_dusus_bp", "arti_yil", "islem_basi_kalite"]
for f in ("MT5_US500", "MT5_US30", "MT5_US2000", "KSG_canli_kitap_DUKA", "C3b_QQQ_1999_2026", "C3b_NDX_1985_1999"):
    print("==", f)
    for kk_, vv in out[f].items(): print(f"  {kk_:24s}", [vv.get(x) for x in keys] if isinstance(vv, dict) else vv)
