"""Notlar için markdown tabloları üret (out/tables.md)."""
import numpy as np, pandas as pd
O = "/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out"
L = []
def md(df):
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(out)
fr = pd.read_csv(f"{O}/frontier_min_bracket.csv")
for frac in (0.10, 0.20):
    x = fr[fr.cost_frac_R == frac].copy()
    x["cell"] = x.apply(lambda r: f"{r.min_bp:g} bp ({r.min_bp_in_ATR5m:.1f}×ATR5) · τ {r.tau_med_min:.0f} dk · {r.opp_day_med_noTS:.0f}/gün", axis=1)
    p = x.pivot(index="venue", columns="year", values="cell").reset_index()
    L.append(f"### Maliyet ≤ %{int(frac*100)} R için asgari simetrik braket (SL=TP)\n\n" + md(p) + "\n")
    c = x.pivot(index="venue", columns="year", values="cost_bp").reset_index()
    if frac == 0.10:
        L.append("### Gidiş-dönüş maliyet (bp)\n\n" + md(c) + "\n")
td = pd.read_csv(f"{O}/tau_dist.csv")
t = td[td.bp.isin([5, 10, 20, 30, 50, 100])].copy()
t["cell"] = t.apply(lambda r: f"{r.tau_med:.0f} [{r.tau_p25:.0f}–{r.tau_p90:.0f}] · amb %{100*r.amb_rate:.1f}", axis=1)
L.append("### Çözülme süresi (dk; medyan [p25–p90]) ve aynı-bar belirsizliği, simetrik braket, zaman stopu yok\n\n" + md(t.pivot(index="bp", columns="year", values="cell").reset_index()) + "\n")
a = td.groupby("year")[["atr1_bp_med", "atr5_bp_med"]].first().reset_index().round(2)
L.append("### ATR medyanları (bp)\n\n" + md(a) + "\n")
op = pd.read_csv(f"{O}/opp_per_day.csv")
o = op[(op.ts == "noTS") & op.bp.isin([5, 10, 20, 30, 50, 100])]
L.append("### Ardışık örtüşmesiz işlem/gün (medyan; zaman stopu yok)\n\n" + md(o.pivot(index="bp", columns="year", values="trades_day_med").reset_index()) + "\n")
s = pd.read_csv(f"{O}/grid_sym_year.csv"); s = s[s.year == "ALL"]
g = s.groupby(["tp_bp", "H"]).agg(gross_R_L=("gross_R", "first"), gross_R_S=("gross_R", "last"), amb=("amb_rate", "mean"),
    wr=("wr_tp", "mean"), ts=("ts_share", "mean"), PEP=("net_R_PEP_PCT", "mean"), FIX15=("net_R_PEP_FIX15", "mean"),
    TAKER=("net_R_BIN_TAKER", "mean"), MAKER=("net_R_BIN_MAKER", "mean"), MIXTP=("net_R_BIN_MIXTP", "mean")).reset_index()
g = g[g.tp_bp.isin([5, 10, 20, 30, 50, 100]) & g.H.isin([5, 15, 60])].round(3)
L.append("### Rastgele giriş, simetrik braket, tüm yıllar (R)\n\n" + md(g) + "\n")
ar = pd.read_csv(f"{O}/grid_asym_year.csv"); ar = ar[(ar.year == "ALL") & (ar.H == 60)]
h = ar.groupby(["tp_bp", "sl_bp"]).agg(gross_bp=("gross_bp", "mean"), gross_R=("gross_R", "mean"), wr=("wr_tp", "mean"),
    ts=("ts_share", "mean"), PEP=("net_R_PEP_PCT", "mean"), TAKER=("net_R_BIN_TAKER", "mean"), MAKER=("net_R_BIN_MAKER", "mean")).reset_index()
h["be_wr_PEP"] = (h.sl_bp + 1.85) / (h.tp_bp + h.sl_bp); h["be_wr_TAKER"] = (h.sl_bp + 10) / (h.tp_bp + h.sl_bp)
h = h[h.tp_bp.isin([5, 10, 20, 50, 100]) & h.sl_bp.isin([5, 10, 20, 50, 100])].round(3)
L.append("### Asimetrik braket, H=60 dk, tüm yıllar, L/S ortalaması\n\n" + md(h) + "\n")
gr = pd.read_csv(f"{O}/gamblers_ruin.csv")
gr["ov"] = (gr.p_tp_first * (gr.tp + gr.sl) - gr.sl) / (1 - 2 * gr.p_tp_first)
q = gr[gr.tp.isin([100, 50, 20, 10]) & (gr.sl.isin([5, 10])) & (gr.tp > gr.sl)].groupby(["tp", "sl", "year"]).agg(
    p=("p_tp_first", "mean"), theo=("p_theory", "mean"), ov=("ov", "mean")).reset_index()
q["cell"] = q.apply(lambda r: f"%{100*r.p:.2f} vs %{100*r.theo:.2f} (ov {r.ov:.2f})", axis=1)
L.append("### Uzak hedefe önce varma olasılığı: gerçek vs sürekli martingal (L/S ort.), örtük aşım bp\n\n" + md(q.pivot(index=["tp", "sl"], columns="year", values="cell").reset_index()) + "\n")
bc = pd.read_csv(f"{O}/broker_compare.csv").round(3)
L.append("### Broker vs Binance (16 gün, H=60)\n\n" + md(bc[["bp", "side", "agree_class", "binance_tp", "broker_tp", "amb_binance", "amb_broker", "evR_binance_pess", "evR_binance_heur", "evR_binance_opt", "evR_broker_pess", "evR_broker_opt", "net_R_binance_plus_S", "net_R_broker_real"]]) + "\n")
by = pd.read_csv(f"{O}/by_group.csv")
x = by[(by.bracket == "1xATR5m") & (by.group.isin(["hour", "weekend", "rv"])) & (by.side == "L") & (by.level != "nan")].copy()
x["lv"] = x.level.astype(str)
x = x[["group", "lv", "atr5_bp_med", "tau_nots_med", "res_in60"]].round(2)
x["PEP_costR_med"] = (1.85 / x.atr5_bp_med).round(3); x["TAKER_costR_med"] = (10 / x.atr5_bp_med).round(3); x["MAKER_costR_med"] = (4 / x.atr5_bp_med).round(3)
L.append("### Saat / hafta sonu / RV rejimi: 1×ATR5m braketi (L)\n\n" + md(x) + "\n")
y = by[(by.bracket == "20bp") & (by.group.isin(["hour", "weekend", "rv"])) & (by.side == "L") & (by.level != "nan")][["group", "level", "tau_nots_med", "res_in60", "amb_rate"]].round(3)
L.append("### 20 bp braket: saat/hafta sonu/RV\n\n" + md(y) + "\n")
mc = pd.read_csv(f"{O}/mc_risk.csv")
m = mc[(mc.geom == "1:1") & mc.risk_pct.isin([0.25, 0.5, 1, 2, 5])][["edge_R", "wr", "trades_day", "risk_pct", "kelly_pct", "final_med", "final_p05", "P_loss", "maxdd_med", "maxdd_p95", "P_dd20", "P_dd50"]]
m = m.copy(); m["final_med"] = m.final_med.map(lambda v: f"{v:.3g}"); m["final_p05"] = m.final_p05.map(lambda v: f"{v:.3g}")
L.append("### Monte Carlo 1:1, 365 gün\n\n" + md(m.round(3)) + "\n")
m2 = mc[(mc.geom == "1.5:1") & mc.risk_pct.isin([0.25, 0.5, 1, 2]) & (mc.trades_day == 20)][["edge_R", "wr", "risk_pct", "kelly_pct", "P_loss", "maxdd_med", "maxdd_p95", "P_dd20", "P_dd50"]]
L.append("### Monte Carlo 1,5:1, 20 işlem/gün, 365 gün\n\n" + md(m2.round(3)) + "\n")
open(f"{O}/tables.md", "w").write("\n".join(L))
print("ok")
