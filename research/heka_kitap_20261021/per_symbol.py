"""Sembol bazında hücre tablosu (SONRADAN; ön kayıtta karar havuzdaydı). Holm tüm sembol×hücre ailesine uygulanır."""
import pandas as pd

from common import OUT, holm, summarize

rows = []
t1 = pd.read_parquet(OUT / "hk1_trades.parquet")
for (s, tf, dr, x), g in t1.groupby(["sym", "tf", "dir", "exit"]):
    rows.append(dict(hyp="HK-1", sym=s, **summarize(g, f"{tf} {'BUY' if dr > 0 else 'SELL'} {x}")))
t2 = pd.read_parquet(OUT / "hk2_trades.parquet")
for (s, dr), g in t2.groupby(["sym", "dir"]):
    rows.append(dict(hyp="HK-2", sym=s, **summarize(g, f"30m {'BUY' if dr > 0 else 'SELL'} VA")))
t3 = pd.read_parquet(OUT / "hk3_trades.parquet")
for (s, tf, b), g in t3.groupby(["sym", "tf", "bucket"]):
    rows.append(dict(hyp="HK-3", sym=s, **summarize(g, f"{tf} dokunuş {b}")))
t4 = pd.read_parquet(OUT / "hk4_trades.parquet")
for (s, tf, dr, v, x), g in t4[t4.kind == "div"].groupby(["sym", "tf", "dir", "var", "exit"]):
    rows.append(dict(hyp="HK-4", sym=s, **summarize(g, f"{tf} {'BOĞA' if dr > 0 else 'AYI'} {v} {x}")))
df = pd.DataFrame(rows)
df["p"] = 1 - df.P
df["holm"] = holm(df.p.fillna(1.0))
df["iyi"] = (df.fark_dev > 0) & (df.fark_test > 0) & (df.ortR_x15 > 0) & (df.ortR_ex5 > 0) & (df.P >= 0.95)
df.to_csv(OUT / "ozet_sembol.csv", index=False)
pd.set_option("display.width", 250)
cols = ["hyp", "sym", "cell", "n", "ortR", "fark", "P", "fark_dev", "fark_test", "ortR_x15", "ortR_ex5", "holm"]
print("toplam hücre", len(df), "| Holm geçen", int(df.holm.sum()), "| P>=0.95 (düzeltmesiz)", int((df.P >= 0.95).sum()),
      "| beklenen tesadüf ~", round(0.05 * len(df), 1))
print("\nP>=0.95 + iki dönem + x1.5 + en iyi 5 gün hariç pozitif:")
print(df[df.iyi][cols].round(3).sort_values("P", ascending=False).to_string(index=False))
print("\nSembol başına hipotez özeti (hücre sayısı / P>=0.95 / ort fark):")
print(df.groupby(["hyp", "sym"]).agg(hucre=("cell", "size"), p95=("P", lambda x: int((x >= 0.95).sum())),
                                     ort_fark=("fark", "mean")).round(3).unstack("sym").to_string())
