"""Ön-kayıtlı geçme ölçütleri + Holm (PROTOCOL.md) → results/ozet.csv + konsol tablosu."""
from __future__ import annotations

import pandas as pd

from common import OUT, boot_diff, holm, summarize

MIN_N = 150


def cells() -> list[dict]:
    rows = []
    t1 = pd.read_parquet(OUT / "hk1_trades.parquet")
    for (tf, dr, x), g in t1.groupby(["tf", "dir", "exit"]):
        rows.append(dict(hyp="HK-1", **summarize(g, f"{tf} {'BUY' if dr > 0 else 'SELL'} {x}")))
    t2 = pd.read_parquet(OUT / "hk2_trades.parquet")
    for dr, g in t2.groupby("dir"):
        s = summarize(g, f"30m {'BUY' if dr > 0 else 'SELL'} VA")
        rows.append(dict(hyp="HK-2", tp_orani=(g.hit == "tp").mean(), **s))
    t3 = pd.read_parquet(OUT / "hk3_trades.parquet")
    for (tf, b), g in t3.groupby(["tf", "bucket"]):
        s = summarize(g, f"{tf} dokunuş {b}")
        base = t3[(t3.tf == tf) & (t3.bucket == "2")]
        s["vs_kova2"] = g.r.mean() - base.r.mean()
        s["P_vs_kova2"] = boot_diff(g, base) if b != "2" else float("nan")
        rows.append(dict(hyp="HK-3", **s))
    t4 = pd.read_parquet(OUT / "hk4_trades.parquet")
    div = t4[t4.kind == "div"]
    for (tf, dr, v, x), g in div.groupby(["tf", "dir", "var", "exit"]):
        s = summarize(g, f"{tf} {'BOĞA' if dr > 0 else 'AYI'} {v} {x}")
        ctl = t4[(t4.kind == "nodiv") & (t4.tf == tf) & (t4.dir == dr) & (t4["var"] == v) & (t4.exit == x)]
        s["vs_yapisal"] = g.r.mean() - ctl.r.mean()
        s["P_vs_yapisal"] = boot_diff(g, ctl)
        s["n_yapisal"] = len(ctl)
        rows.append(dict(hyp="HK-4", **s))
    return rows


def main() -> None:
    df = pd.DataFrame(cells())
    df["p"] = 1 - df.P
    df["holm"] = holm(df.p.fillna(1.0))
    extra = pd.Series(True, index=df.index)
    extra &= df.get("P_vs_kova2").fillna(1.0).where(df.hyp == "HK-3", 1.0) >= 0.95 if "P_vs_kova2" in df else True
    extra &= df.get("P_vs_yapisal").fillna(1.0).where(df.hyp == "HK-4", 1.0) >= 0.95
    sym_ok = df.sym_pos.str.split("/").apply(lambda x: int(x[0]) >= 3)
    df["GECTI"] = (df.holm & extra & (df.fark_dev > 0) & (df.fark_test > 0) & sym_ok & (df.ortR_x15 > 0)
                   & (df.n >= MIN_N) & (df.ortR_ex5 > 0))
    df.to_csv(OUT / "ozet.csv", index=False)
    cols = ["hyp", "cell", "n", "ortR", "plcR", "fark", "P", "holm", "fark_dev", "fark_test", "sym_pos", "ortR_x15",
            "ortR_ex5", "GECTI"]
    pd.set_option("display.width", 250)
    print(df[cols].round(3).to_string(index=False))
    for c in ["tp_orani", "vs_kova2", "P_vs_kova2", "vs_yapisal", "P_vs_yapisal", "n_yapisal"]:
        if c in df:
            print(c, df[[c, "cell"]].dropna().round(3).values.tolist())
    print("GEÇEN:", df[df.GECTI].cell.tolist())


if __name__ == "__main__":
    main()
