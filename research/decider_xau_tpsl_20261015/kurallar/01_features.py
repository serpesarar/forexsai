"""Adım 1 (ön-kayıttan ÖNCE): karar-anı özellikleri. SONUÇ SÜTUNLARINA BAKILMAZ — yalnız özellik dağılımları
yazdırılır (kural eşiklerinin örneklem büyüklüğü açısından anlamlı olup olmadığını görmek için).
Çıktı: data/features_journal.pkl (tüm journal free/evidence kayıtları), results/01_feature_marginals.txt
Sızıntı denetimi: (a) her bar-özelliği için kullanılan son barın t_end ≤ ts, (b) önek testi — 1m serisini ts'den
sonra kesip özellikleri yeniden hesaplamak aynı değeri vermeli (rastgele 40 kayıt)."""
import numpy as np
import pandas as pd
import rules_lib as L

HERE = L.HERE
b1 = L.core.load_1m()
BF = L.BarFeatures(b1)
J = L.load_journal()
J = L.add_bar_features(J, BF)
A = pd.read_pickle(L.ROOT / "data" / "grid_set.pkl")[["id", "direction", "executed", "day", "size_factor"]]
J["in_analysis_set"] = J.id.isin(A.id)
J.to_pickle(HERE / "data_features_journal.pkl")

out = []
def P(s=""): out.append(str(s)); print(s)

# ---- sızıntı denetimi (a): t_end ≤ ts
viol = 0
for t in J.ts.sample(300, random_state=1):
    T = L.core.to64(t)
    for tf in ("5m", "1h", "1d"):
        i = BF.asof_closed(tf, T)
        if i >= 0 and BF.tf[tf]["te"][i] > T:
            viol += 1
P(f"Sızıntı (a) t_end>ts ihlali: {viol} / 900")
# ---- (b) önek testi
rng = np.random.default_rng(3); bad = 0
for t in J.ts.sample(40, random_state=2):
    cut = b1[b1.t_utc + pd.Timedelta(minutes=1) <= t]
    BFc = L.BarFeatures(cut.reset_index(drop=True))
    f0, f1 = BF.features(L.core.to64(t)), BFc.features(L.core.to64(t))
    for k in ("h1_above_ema50", "dist_hi20_h1_atr", "d1_up", "atr5_ratio", "px_closed_1m"):
        a, b = f0.get(k), f1.get(k)
        if a is None and b is None:
            continue
        if (a is None) != (b is None) or (isinstance(a, float) and not np.isclose(a, b, equal_nan=True)) or (not isinstance(a, float) and a != b):
            bad += 1; P(f"  önek farkı {t} {k}: {a} vs {b}")
P(f"Sızıntı (b) önek testi farkı: {bad} (40 kayıt × 5 özellik)")

S = J[J.in_analysis_set].merge(A[["id", "executed"]], on="id")
for dirn in ("BUY", "SELL"):
    s = S[S.direction == dirn]
    P(f"\n=== {dirn} analiz kümesi n={len(s)} (yalnız özellik dağılımı; sonuç YOK)")
    P(f"  trig_sign (+ = 5m baskın z yukarı/güç, − = aşağı/dip): {s.trig_sign.value_counts(dropna=False).to_dict()}")
    P(f"  extremity çeyrekleri: {s.extremity.quantile([.1,.25,.5,.75,.9]).round(2).to_dict()}")
    P(f"  cz5 çeyrekleri: {s.cz5.quantile([.1,.25,.5,.75,.9]).round(2).to_dict()}")
    P(f"  eq_block_buy (D2): {s.eq_block_buy.value_counts(dropna=False).to_dict()} | eq_block_sell: {s.eq_block_sell.value_counts(dropna=False).to_dict()}")
    P(f"  h1_above_ema50: {s.h1_above_ema50.value_counts(dropna=False).to_dict()}")
    P(f"  d1_up: {s.d1_up.value_counts(dropna=False).to_dict()}")
    P(f"  sess_ldn_ny (07–16 UTC): {s.sess_ldn_ny.value_counts().to_dict()} | saat: {s.hour_utc.value_counts().sort_index().to_dict()}")
    P(f"  atr5_ratio çeyrekleri: {s.atr5_ratio.quantile([.1,.25,.5,.75,.9]).round(2).to_dict()} | ≥1.5: {(s.atr5_ratio>=1.5).sum()}")
    P(f"  dist_hi20_h1_atr çeyrekleri: {s.dist_hi20_h1_atr.quantile([.1,.25,.5,.75,.9]).round(2).to_dict()} | ≤1.0: {(s.dist_hi20_h1_atr<=1.0).sum()}")
    P(f"  dist_lo20_h1_atr ≤1.0: {(s.dist_lo20_h1_atr<=1.0).sum()}")
    P(f"  size_factor: {s.size_factor.value_counts().sort_index().to_dict()}")
    P(f"  spread/ATR5 çeyrekleri: {(s.spread/s.atr5_closed).quantile([.1,.5,.9]).round(3).to_dict()}")
    P(f"  ay: {s.ts.dt.strftime('%m').value_counts().sort_index().to_dict()} | gün sayısı {s.ts.dt.date.nunique()}")
C = J[(J['mode'] == 'free')]
P(f"\nTetik popülasyonu (free, tüm danışmalar): n={len(C)} | extremity≥1.6: {(C.extremity>=1.6).sum()} | OPEN {(C.action=='OPEN').sum()} | sahte WAIT {C.fake_wait.sum()} | gerçek WAIT {((C.action=='WAIT')&~C.fake_wait).sum()}")
(HERE / "results" / "01_feature_marginals.txt").write_text("\n".join(out))
