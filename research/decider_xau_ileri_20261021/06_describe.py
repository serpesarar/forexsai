"""Q1–Q2: veri seti envanteri, orijinal geometri, sonuçlar, MFE/MAE profili + temiz CSV dışa aktarımı.
Analiz kümesi: usable & ~dup (yinelenen ve piyasa-kapalı/veri-boşluğu girişli kararlar hariç)."""
import numpy as np
import pandas as pd
import core

HERE = core.HERE
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
NOTES = HERE / "results"   # 2026-10-21 kopyası: paylaşılan notlar klasörüne YAZMAZ
d = pd.read_pickle(HERE / "data" / "trades_full.pkl")
d["usable"] = d.usable.astype(bool)
d["epoch"] = np.where(d.j_rr.round(2) == 0.40, "SL2.5ATR_rr0.40(≤07-27)", "SL1.5ATR_rr0.67(07-27+)")
d["outcome"] = np.where(d.executed, d.exec_outcome, d.sim_outcome)
d["pnl_usd_per_0p01lot_sim"] = d.sim_pnl_usd_per_oz          # 0.01 lot = 1 ons → $ = fiyat farkı
d["pnl_usd_actual"] = np.where(d.executed, d.exec_pnl_usd, np.nan)
L = []
def P(s=""): L.append(str(s))

P("## 1. Envanter (ham)")
P(d.groupby(["source", "direction", "mode"]).agg(n=("id", "size"), dup=("dup", "sum"), usable=("usable", "sum"),
     first=("decision_time_utc", "min"), last=("decision_time_utc", "max")).to_string())
P("\nYinelenen (≤10sn, aynı yön) kayıtların günleri: " + str(d[d.dup].decision_time_utc.dt.strftime('%m-%d').value_counts().sort_index().to_dict()))
P("Kullanılamayan (giriş barı karardan >30 dk sonra: hafta sonu/veri boşluğu): " +
  str(d[~d.usable & ~d.dup].decision_time_utc.dt.strftime('%m-%d %a').value_counts().sort_index().to_dict()))
A = d[d.usable & ~d.dup].copy()
A.to_pickle(HERE / "data" / "analysis_set.pkl")
P(f"\nANALİZ KÜMESİ n={len(A)} | veri boşluklu (ilk 240dk'da >5dk boşluk) {int(A.data_gap_240m.sum())}")
P(A.groupby(["source", "direction", "epoch"]).size().to_string())
P("\nAylık: " + A.groupby([A.decision_time_utc.dt.strftime('%Y-%m'), "direction"]).size().unstack(fill_value=0).to_string())
P("\nModel/epok: " + A.groupby(["model", "direction"]).size().to_string())

P("\n## 2. Orijinal geometri (mesafeler girişten, $ ve kapalı-bar ATR birimi)")
g = A.groupby(["direction", "epoch"])
P(g.agg(n=("id", "size"), tp_usd=("orig_tp_usd", "median"), sl_usd=("orig_sl_usd", "median"),
        tp_atr5=("orig_tp_atr5", "median"), sl_atr5=("orig_sl_atr5", "median"),
        atr_m5=("atr_m5", "median"), atr_m15=("atr_m15", "median"), atr_h1=("atr_h1", "median"),
        spread=("spread_used", "median")).round(3).to_string())
A["tp_atr15"] = A.orig_tp_usd / A.atr_m15; A["sl_atr15"] = A.orig_sl_usd / A.atr_m15
A["tp_atrh1"] = A.orig_tp_usd / A.atr_h1; A["sl_atrh1"] = A.orig_sl_usd / A.atr_h1
P("M15/H1 ATR biriminde medyan TP/SL: " + A[["tp_atr15", "sl_atr15", "tp_atrh1", "sl_atrh1"]].median().round(3).to_dict().__str__())

P("\n## 3. Sonuçlar (orijinal geometri, broker 1m, spread dahil, aynı-bar=LOSS)")
def summ(s):
    n = len(s); w = (s.outcome == "WIN").mean()
    be = (s.orig_sl_usd / (s.orig_sl_usd + s.orig_tp_usd)).mean()
    return pd.Series({"n": n, "WR": w, "başabaş_WR": be, "ort_R": s.sim_R.mean(),
                      "ort_$_0.01lot": s.pnl_usd_per_0p01lot_sim.mean(), "top_$_0.01lot": s.pnl_usd_per_0p01lot_sim.sum(),
                      "timeout": (s.outcome == "TIMEOUT48h").sum(), "medyan_süre_dk": s.sim_hold_min.median()})
P(A.groupby(["source", "direction", "epoch"]).apply(summ).round(3).to_string())
P("\nTüm BUY: " + summ(A[A.direction == "BUY"]).round(3).to_dict().__str__())
P("Tüm SELL: " + summ(A[A.direction == "SELL"]).round(3).to_dict().__str__())
X = A[A.executed]
P(f"\nİCRA (gerçek MT5 demo, magic 52890989): n={len(X)} WR={(X.exec_outcome=='WIN').mean():.3f} "
  f"gerçek P&L toplam={X.exec_pnl_usd.sum():.2f}$ ort={X.exec_pnl_usd.mean():.3f}$ | lot dağılımı {X.lot.value_counts().to_dict()} | "
  f"aynı işlemlerin sim R ort={X.sim_R.mean():+.3f} | dönem {X.decision_time_utc.min():%m-%d}→{X.decision_time_utc.max():%m-%d}")
O = A[(A.decision_time_utc >= "2026-10-05") & (A.direction == "BUY")]
XX = d[d.executed]
iv = list(zip(XX.exec_open_utc.apply(pd.Timestamp), XX.exec_close_utc.apply(pd.Timestamp)))
O = O.assign(inpos=O.decision_time_utc.apply(lambda t: any(a <= t <= b for a, b in iv)))
for k, g in O.groupby("executed"):
    P(f"Ekim (10-05+) BUY executed={k}: n={len(g)} WR={(g.outcome=='WIN').mean():.3f} sim R ort={g.sim_R.mean():+.3f}")
ne = O[~O.executed]
P(f"  icra edilmeyen {len(ne)} kararın {int(ne.inpos.sum())}'i açık decider pozisyonu varken (R {ne[ne.inpos].sim_R.mean():+.3f}); "
  f"kalan {int((~ne.inpos).sum())} (R {ne[~ne.inpos].sim_R.mean():+.3f}) için neden live_orders.jsonl olmadan doğrulanamadı "
  f"(olası: canlıya geçiş öncesi, günlük 10 emir tavanı, spread/ATR>0,15, kill-switch)")
P("Journal kendi notu (5m, spread'siz) × bizim 1m simülasyon (gölge): \n" +
  pd.crosstab(A[~A.executed].j_outcome.fillna('None'), A[~A.executed].sim_outcome).to_string())

P("\n## 4. MFE/MAE profili (ATR5 birimi, medyan [p25,p75]) — giriş barından itibaren, sonuç bağımsız ufuklar")
rows = []
for (dirn, oc), s in A.groupby(["direction", "outcome"]):
    r = {"yön": dirn, "sonuç": oc, "n": len(s)}
    for H in (30, 60, 120, 240):
        r[f"MFE{H}"] = f"{s[f'mfe_{H}m_atr'].median():.2f} [{s[f'mfe_{H}m_atr'].quantile(.25):.2f},{s[f'mfe_{H}m_atr'].quantile(.75):.2f}]"
        r[f"MAE{H}"] = f"{s[f'mae_{H}m_atr'].median():.2f} [{s[f'mae_{H}m_atr'].quantile(.25):.2f},{s[f'mae_{H}m_atr'].quantile(.75):.2f}]"
    r["MFEsess"] = f"{s.mfe_sess_atr.median():.2f}"; r["MAEsess"] = f"{s.mae_sess_atr.median():.2f}"
    rows.append(r)
P(pd.DataFrame(rows).to_string(index=False))
P("\n$ cinsinden medyan MFE/MAE (yön×sonuç): ")
P(A.groupby(["direction", "outcome"])[[f"mfe_{H}m_usd" for H in (30, 60, 120, 240)] + [f"mae_{H}m_usd" for H in (30, 60, 120, 240)]].median().round(2).to_string())
P("\nYön bazında tüm işlemler (sonuçtan bağımsız) medyan/ortalama ATR5:")
for dirn, s in A.groupby("direction"):
    P(f"  {dirn}: " + ", ".join(f"H{H}: MFE med {s[f'mfe_{H}m_atr'].median():.2f}/ort {s[f'mfe_{H}m_atr'].mean():.2f}, MAE med {s[f'mae_{H}m_atr'].median():.2f}/ort {s[f'mae_{H}m_atr'].mean():.2f}, getiri ort {(s[f'ret_{H}m_usd']/s.atr_m5).mean():+.3f}" for H in (30, 60, 120, 240)))

P("\n## 5. SL vuran işlemler SL'den önce ne kadar lehte gitti (R = orijinal SL mesafesi; SL barının lehte kısmı sayılmaz)")
for dirn, s in A[A.outcome == "LOSS"].groupby("direction"):
    m = s.mfe_before_exit_R
    P(f"  {dirn} LOSS n={len(s)}: ≥+0.25R {np.mean(m>=0.25):.1%} | ≥+0.5R {np.mean(m>=0.5):.1%} | ≥+0.67R(orijinal TP'nin 1.0 ATR'si≈) {np.mean(m>=0.667):.1%} | ≥+1R {np.mean(m>=1.0):.1%} | medyan {m.median():.2f}R")
    for ep, s2 in s.groupby("epoch"):
        m = s2.mfe_before_exit_R
        P(f"     {ep}: n={len(s2)} ≥+0.25R {np.mean(m>=0.25):.1%} ≥+0.5R {np.mean(m>=0.5):.1%} ≥+1R {np.mean(m>=1.0):.1%}")
for dirn, s in A[A.outcome == "WIN"].groupby("direction"):
    m = s.mae_before_exit_R
    P(f"  {dirn} WIN n={len(s)}: TP'den önce aleyhte (R) medyan {m.median():.2f} | ≥0.5R {np.mean(m>=0.5):.1%} | ≥0.75R {np.mean(m>=0.75):.1%} | ≥0.9R {np.mean(m>=0.9):.1%} (SL'i 0.5R/0.75R'e daraltmak bu kazananları öldürürdü)")

(OUT / "describe.txt").write_text("\n".join(L))
print("\n".join(L))

# ── temiz CSV ──
cols = ["id", "source", "executed", "dup", "usable", "direction", "mode", "free_ctx", "model", "epoch", "size_factor",
        "decision_time_utc", "entry_time_utc", "entry_basis", "entry_delay_min", "entry_price", "spread_used",
        "j_price", "original_sl", "original_tp", "orig_sl_usd", "orig_tp_usd", "orig_sl_atr5", "orig_tp_atr5",
        "lot", "ticket", "exec_entry", "exec_sl", "exec_tp", "exec_close_utc", "exec_close_price",
        "outcome", "j_outcome", "sim_outcome", "exec_outcome", "pnl_usd_actual", "pnl_usd_per_0p01lot_sim", "sim_R",
        "sim_exit_time_utc", "sim_hold_min", "atr_m5", "atr_m15", "atr_h1", "j_atr5"] + \
       [f"{k}_{H}m_{u}" for H in (30, 60, 120, 240) for k in ("mfe", "mae") for u in ("usd", "atr")] + \
       [f"ret_{H}m_usd" for H in (30, 60, 120, 240)] + \
       ["mfe_sess_usd", "mae_sess_usd", "mfe_sess_atr", "mae_sess_atr", "mfe_before_exit_R", "mae_before_exit_R", "data_gap_240m", "reason"]
d[[c for c in cols if c in d.columns]].sort_values("decision_time_utc").to_csv(NOTES / "decider_xau_trades.csv", index=False)
print("CSV yazıldı:", NOTES / "decider_xau_trades.csv", len(d))
