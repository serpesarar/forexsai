"""QS-05 EK-1 F1: ay son günü 15:30→16:00 R1 yönünde; kör US500/US30/US2000 + Dukascopy NDX."""
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import side
from qs05 import cycle_frame
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402


def f1(sym, M):
    mk = Mkt(sym); sR1 = side(M.dm.to_numpy()); sig, nos = [], []
    for k, r in M.iterrows():
        if r.d_s < pd.Timestamp("2018-06-01"):
            continue
        i, j = mk.at(r.d_D + pd.Timedelta(minutes=930)), mk.at(r.d_D + pd.Timedelta(minutes=960))
        if i < 0 or j < 0:
            continue
        g = (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4; c = mk.cost(i) / mk.o[i] * 1e4
        if sR1[k] != 0:
            sig.append(sR1[k] * g - c)
        else:
            nos.append(g)
    return st(np.array(sig)), st(np.array(nos))


def duka(M):
    p = pd.read_parquet(H.parent / "geri_cekilme_limit_20261109/data/path.parquet")
    et = pd.to_datetime(p.t, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    s = pd.Series(p.open.values, index=et); sp = pd.Series(p.spr.values, index=et)
    sR1 = side(M.dm.to_numpy()); out = []
    for k, r in M.iterrows():
        if sR1[k] == 0:
            continue
        t0, t1 = r.d_D + pd.Timedelta(minutes=930), r.d_D + pd.Timedelta(minutes=960)
        if t0 in s.index and t1 in s.index:
            out.append(sR1[k] * (s[t1] - s[t0]) / s[t0] * 1e4 - sp[t0] / s[t0] * 1e4)
    return st(np.array(out))


M, cal = cycle_frame()
res = {}
for sym in ("NAS100", "US500", "US30", "US2000"):
    a, b = f1(sym, M); res[sym] = {"F1": a, "sinyalsiz_ay_sonu_uzun": b}
res["Dukascopy_NDX"] = duka(M)
kor = [res[s]["F1"] for s in ("US500", "US30", "US2000")]
pos = sum(x.get("ort", -1) > 0 for x in kor)
# havuz P: kör üç sembolün tarih başına ortalaması yerine işlem havuzu (koşullar aynı aylar → muhafazakâr değil; ayrıca en küçük P raporlanır)
res["ozet"] = {"kor_arti": f"{pos}/3", "kor_ort": [x.get("ort") for x in kor], "kor_P": [x.get("P") for x in kor]}
allk = np.concatenate([np.array([0])])  # yer tutucu
res["sinif"] = "B-" if pos == 3 and min(x.get("P", 0) for x in kor) >= 0.9 else ("C+" if pos >= 2 else "X")
(H / "results/qs05_f1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
