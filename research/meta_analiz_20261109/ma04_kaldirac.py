"""MA-04: C3b etkisi kaldıraçlı akış yoğunluğuyla artıyor mu? Ön kayıt: PROTOCOL.md EK-1."""
import json
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
OUT = Path(__file__).resolve().parent / "results"; OUT.mkdir(exist_ok=True)
TICK = ["QQQ", "SOXX", "SMH", "XLP", "XLU"]
def rsi2(s):
    g = s.diff(); up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))
def trades(c: pd.Series) -> pd.DataFrame:
    S = c.to_numpy(); r = rsi2(c).to_numpy(); dv = c.pct_change().rolling(20).std().to_numpy() * 1e4; out = []; i = 25; n = len(S)
    while i < n - 1:
        if r[i] < 10:
            j = next((k for k in range(i + 1, min(i + 6, n)) if S[k] > S[k - 1]), min(i + 5, n - 1))
            bp = (S[j] / S[i] - 1) * 1e4 - 4 - 2 * (j - i); out.append((c.index[i], bp, bp / dv[i])); i = j; continue
        i += 1
    return pd.DataFrame(out, columns=["t", "bp", "R"]).set_index("t")
def mp(v: pd.Series, rng, n=3000) -> float:
    ym = v.index.to_period("M").astype(str); g = [v[ym == u].to_numpy() for u in np.unique(ym)]
    return float(np.mean([np.concatenate([g[k] for k in rng.integers(0, len(g), len(g))]).mean() > 0 for _ in range(n)]))
rng = np.random.default_rng(31); res = {}
px = yf.download(TICK, start="2009-11-01", end="2026-11-08", auto_adjust=True, progress=False)["Close"]
px.index = pd.DatetimeIndex(px.index).tz_localize(None); px.to_parquet(OUT / "ma04_fiyat.parquet")
for tk in TICK:
    tr = trades(px[tk].dropna()); tr = tr[tr.index >= "2010-01-01"]; a = tr[tr.index < "2018-01-01"]; b = tr[tr.index >= "2018-01-01"]
    res[tk] = {"n": len(tr), "bp": round(tr.bp.mean(), 1), "R": round(tr.R.mean(), 3), "isabet": round((tr.bp > 0).mean(), 3), "P_bp>0": round(mp(tr.bp, rng), 3),
               "R_2010_17": round(a.R.mean(), 3), "n1": len(a), "R_2018_26": round(b.R.mean(), 3), "n2": len(b), "bp_2010_17": round(a.bp.mean(), 1), "bp_2018_26": round(b.bp.mean(), 1), "enkotu_bp": round(tr.bp.min(), 0)}
    print(tk, res[tk])
q = res["QQQ"]
res["olcut"] = {"1_yari_iletken>QQQ": bool(res["SOXX"]["R"] > q["R"] and res["SMH"]["R"] > q["R"]), "2_savunmaci<QQQ": bool(res["XLP"]["R"] < q["R"] and res["XLU"]["R"] < q["R"]),
                "3_iki_yarida": bool(all(res[s][k] > q[k] for s in ("SOXX", "SMH") for k in ("R_2010_17", "R_2018_26")) and all(res[s][k] < q[k] for s in ("XLP", "XLU") for k in ("R_2010_17", "R_2018_26"))),
                "4_SOXX_P>=0.95": bool(res["SOXX"]["bp"] > 0 and res["SOXX"]["P_bp>0"] >= 0.95)}
print(res["olcut"]); (OUT / "ma04.json").write_text(json.dumps(res, indent=1))
