"""IO-17 genişletme: tüm veriyle "geri çekilip TP mi, doğrudan SL mi?" (2026-10-09).

Ön-kayıt eki (PROTOCOL.md'ye ek, sonuçlardan önce):
- İki olay kümesi: GERÇEK (bot kararları, run.event ile aynı D) ve SENTETİK (bot benzeri pozisyonlar: her işlem günü
  06–20 UTC saat başı, iki yön, sembolün gerçek işlemlerinden medyan risk/fiyat ve RR; IO-01'e göre bot girişi ≈ rastgele).
- Özellik aileleri (hepsi D kapanışında bilinen): [bar] run.py'deki 24 özellik · [gösterge] 1m/5m/15m/1h RSI, EMA20/50/200
  uzaklığı, EMA20 eğimi, MACD histogram + değişimi, Bollinger %b + genişlik oranı, Stochastic, ADX + DI farkı; 1m/5m OBV eğimi,
  MFI, CMF; günlük VWAP uzaklığı; gün aralığı konumu · [panel] D'den önceki 30 dk'da pulse1/2/3, emel, smc, ml:main, meta'nın
  son sinyali lehte/aleyhte · [makro] önceki gün VIX · [tick] (28 Ağustos sonrası, MT5) son 15/5/1 dk ve 30 sn tik sayısı ve
  tik-kuralı dengesizliği, 5 dk net akış ve yol, verimlilik, spread oranı, 10 sn en büyük aleyhte/lehte hareket, son 60 sn dipten
  sıçrama ve dibin yaşı.
- Değerlendirme: SENTETİK'te kronolojik %60 eğitim → %40 sınama (ve tersi) lojistik + 200 plasebo; tek özellikte AUC + BH;
  karar kuralı net R eğitimde seç → sınamada ölç. GERÇEK'te aynısı yarı yarıya. Geçme: sınama AUC ≥ 0,60, plaseboyu aşar,
  kural net R iki yönde > 0.
Kullanım: python3 genis.py olaylar   → results/genis_*.parquet (tick hariç)
          python3 genis.py tick      → kutudan tick özellikleri (28 Ağu+) → results/tick_*.parquet
          python3 genis.py analiz    → rapor
"""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from scripts.islem_otopsi import data, settings as S  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars, adx, bollinger, ema, rsi, atr  # noqa: E402
from scripts.islem_otopsi.stats import auc, auc_perm, bh_q  # noqa: E402

OUT = HERE / "results"
SYMS = ["NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"]
BROKER = {"NDX.INDX": 0, "GDAXI.INDX": 1, "XAUUSD": 2, "USOIL.FOREX": 3}     # box SYM listesindeki sıra
THR = 0.5
SYN_HOURS = range(6, 21)
TICK_START = pd.Timestamp("2026-08-28T20:00:00Z")
PANEL_MODELS = ["pulse1", "pulse2", "pulse3", "emel", "smc", "ml:main", "meta"]
PANEL_WIN_MIN = 30
TFS = (1, 5, 15, 60)


def _mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


EV = _mod("dvs_run", HERE / "run.py")          # IO-17 olay + 24 bar özelliği


# ── genişletilmiş göstergeler (sembol başına bir kez, nedensel) ───────────────

def _macd(c: pd.Series) -> pd.Series:
    line = ema(c, 12) - ema(c, 26)
    return line - ema(line, 9)


def _stoch(f: pd.DataFrame, n: int = 14) -> pd.Series:
    lo, hi = f["low"].rolling(n).min(), f["high"].rolling(n).max()
    return (100 * (f["close"] - lo) / (hi - lo).replace(0, np.nan)).rolling(3).mean()


def _mfi(f: pd.DataFrame, n: int = 14) -> pd.Series:
    tp = (f["high"] + f["low"] + f["close"]) / 3
    mf = tp * f["volume"]
    pos = mf.where(tp > tp.shift(1), 0).rolling(n).sum()
    neg = mf.where(tp < tp.shift(1), 0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg.replace(0, np.nan))


def _cmf(f: pd.DataFrame, n: int = 20) -> pd.Series:
    rng = (f["high"] - f["low"]).replace(0, np.nan)
    mfm = ((f["close"] - f["low"]) - (f["high"] - f["close"])) / rng
    return (mfm * f["volume"]).rolling(n).sum() / f["volume"].rolling(n).sum()


def extend(f: pd.DataFrame, with_volume: bool) -> dict[str, np.ndarray]:
    c = f["close"]
    a = atr(f)
    bb = bollinger(c)
    ax = adx(f)
    out = {"close": c, "atr": a, "rsi": rsi(c), "ema20": ema(c, 20), "ema50": ema(c, 50), "ema200": ema(c, 200),
           "macd_h": _macd(c), "bb_pctb": bb["bb_pctb"], "bb_w": bb["bb_width"] / bb["bb_width"].rolling(100, min_periods=20).median(),
           "stoch": _stoch(f), "adx": ax["adx"], "di": ax["plus_di"] - ax["minus_di"]}
    if with_volume:
        obv = (np.sign(c.diff()).fillna(0) * f["volume"]).cumsum()
        out.update({"obv": obv, "mfi": _mfi(f), "cmf": _cmf(f), "vol": f["volume"]})
    return {k: np.asarray(v, dtype=float) for k, v in out.items()}


def vwap_day(m1: pd.DataFrame) -> np.ndarray:
    tp = (m1["high"] + m1["low"] + m1["close"]) / 3
    day = m1.index.normalize()
    num = (tp * m1["volume"]).groupby(day).cumsum()
    den = m1["volume"].groupby(day).cumsum().replace(0, np.nan)
    return np.asarray(num / den, dtype=float)


class Ext:
    def __init__(self, sb: SymbolBars) -> None:
        self.sb = sb
        self.f = {1: extend(sb.m1, True)}
        for k in (5, 15, 60):
            self.f[k] = extend(sb.tf[k], k == 5)
        self.vwap = vwap_day(sb.m1)


def ind_features(x: Ext, D: int, s: int) -> dict:
    sb = x.sb
    t_close = sb.m1.index[D] + pd.Timedelta(minutes=1)
    out = {}
    for tf in TFS:
        j = D if tf == 1 else sb.last_closed(tf, t_close)
        if j < 3:
            continue
        g = x.f[tf]
        a, c = g["atr"][j], g["close"][j]
        p = f"g{tf}_"
        out.update({
            p + "rsi": g["rsi"][j] if s > 0 else 100 - g["rsi"][j],
            p + "ema20": s * (c - g["ema20"][j]) / a, p + "ema50": s * (c - g["ema50"][j]) / a,
            p + "ema200": s * (c - g["ema200"][j]) / a,
            p + "ema20_egim": s * (g["ema20"][j] - g["ema20"][j - 3]) / a,
            p + "macd_h": s * g["macd_h"][j] / a, p + "macd_h_degisim": s * (g["macd_h"][j] - g["macd_h"][j - 1]) / a,
            p + "bb_pctb": g["bb_pctb"][j] if s > 0 else 1 - g["bb_pctb"][j], p + "bb_genislik": g["bb_w"][j],
            p + "stoch": g["stoch"][j] if s > 0 else 100 - g["stoch"][j],
            p + "adx": g["adx"][j], p + "di": s * g["di"][j],
        })
        if "obv" in g:
            o = g["obv"][j - 9:j + 1]
            vm = g["vol"][j - 9:j + 1].mean()
            out.update({p + "obv_egim": s * np.polyfit(np.arange(10), o, 1)[0] / vm if vm > 0 else np.nan,
                        p + "mfi": g["mfi"][j] if s > 0 else 100 - g["mfi"][j], p + "cmf": s * g["cmf"][j]})
    a1 = x.f[1]["atr"][D]
    out["vwap_atr"] = s * (sb.a["close"][D] - x.vwap[D]) / a1
    dh, dl = sb.a["day_high"][D], sb.a["day_low"][D]
    out["gun_araligi_konum"] = ((sb.a["close"][D] - dl) / (dh - dl) if s > 0 else (dh - sb.a["close"][D]) / (dh - dl)) if dh > dl else 0.5
    return out


# ── olaylar ──────────────────────────────────────────────────────────────────

def _ctx(sb, s, entry, risk, rr, i0, i_exit, spread):
    return SimpleNamespace(sb=sb, s=s, entry=entry, risk=risk, reward=risk * rr, spread=spread,
                           sl0=entry - s * risk, i_pre=i0 - 1, i_in0=i0, i_exit=i_exit,
                           r=lambda p, e=entry, s_=s, rk=risk: s_ * (p - e) / rk)


def geometry() -> dict:
    lk = _mod("lk_run2", ROOT / "research" / "limit_kilit_20261007" / "run.py")
    items = lk.load()
    g = {}
    for sym in SYMS:
        xs = [x["c"] for x in items if x["r"]["symbol"] == sym]
        g[sym] = {"risk_frac": float(np.median([c.risk / c.entry for c in xs])),
                  "rr": float(np.median([c.reward / c.risk for c in xs]))}
    return g, items


def synth(sb: SymbolBars, sym: str, geo: dict) -> list[dict]:
    idx, a = sb.m1.index, sb.a
    starts = idx[(idx.minute == 0) & idx.hour.isin(list(SYN_HOURS)) & (idx.dayofweek < 5)]
    spread = S.TYPICAL_SPREAD.get(sym, 0.0)
    rows = []
    for ts in starts:
        j = sb.pos_at(ts)
        if j < 300 or j + 30 >= idx.size:
            continue
        for s in (1, -1):
            entry = float(a["open"][j]) + (spread if s > 0 else 0.0)
            risk = entry * geo["risk_frac"]
            rr = geo["rr"]
            j1 = min(j + S.REPLAY_MAX_HOLD_MIN, idx.size)
            hi, lo = a["high"][j:j1], a["low"][j:j1]
            adj = 0.0 if s > 0 else spread
            fav = s * ((hi if s > 0 else lo) + adj - entry) / risk
            adv = s * ((lo if s > 0 else hi) + adj - entry) / risk
            end = np.flatnonzero((adv <= -1.0) | (fav >= rr))
            if not end.size:
                continue
            k_end = end[0]
            hit = np.flatnonzero(adv[:k_end] <= -THR)
            if not hit.size:
                continue
            D = j + int(hit[0])
            lab = "SL" if adv[k_end] <= -1.0 else "TP"
            c = _ctx(sb, s, entry, risk, rr, j, j + k_end, spread)
            rows.append({"c": c, "D": D, "sonuc": lab, "side": f"{sym.split('.')[0]} {'BUY' if s > 0 else 'SELL'}",
                         "sym": sym, "R_sonuc": -1.0 if lab == "SL" else rr})
    return rows


def bar_feats(c, D: int) -> dict:
    """run.event'in D'deki 24 özelliği — D zaten belli; run.event'i bu D'yi bulacak şekilde kısa çağır."""
    r = {"pid": 0, "side": "", "family": "", "outcome": "", "r_exit": np.nan}
    c2 = SimpleNamespace(**vars(c))
    c2.r = c.r                                # dataclass metodu vars()'ta yok
    c2.i_exit = D + 1                        # run.event çıkış barından önce arar → D bulunur
    f, why = EV.event(c2, r, THR)
    if f is None:
        return {}
    return {k: v for k, v in f.items() if k not in ("pid", "side", "family", "half", "sonuc", "R_sonuc")}


def panel_table() -> pd.DataFrame:
    p = OUT / "panel.parquet"
    if p.exists():
        return pd.read_parquet(p)
    rows = data.fetch_table(data.get_client(), "prediction_logs", "created_at,symbol,model_type,ml_direction",
                            [("created_at", "gte", "2026-06-15"), ("model_type", "in_", PANEL_MODELS),
                             ("symbol", "in_", SYMS)], "created_at")
    d = pd.DataFrame(rows)
    d["ts"] = pd.to_datetime(d["created_at"], utc=True)
    d = d[d.ml_direction.isin(["BUY", "SELL"])][["ts", "symbol", "model_type", "ml_direction"]]
    d.to_parquet(p, index=False)
    return d


def panel_feats(pt: dict, sym: str, t_close: pd.Timestamp, s: int) -> dict:
    w, a = 0, 0
    for mdl in PANEL_MODELS:
        g = pt.get((sym, mdl))
        if g is None:
            continue
        k = np.searchsorted(g[0], t_close.to_datetime64(), side="right") - 1
        if k < 0 or (t_close.to_datetime64() - g[0][k]) > np.timedelta64(PANEL_WIN_MIN, "m"):
            continue
        same = (g[1][k] == "BUY") == (s > 0)
        w += same
        a += not same
    return {"panel_lehte": float(w), "panel_aleyhte": float(a), "panel_net": float(w - a)}


def build_rows(events: list[dict], exts: dict, pt: dict, vix: pd.Series, kind: str) -> pd.DataFrame:
    rows = []
    for e in events:
        c, D, sym = e["c"], e["D"], e["sym"]
        f = bar_feats(c, D)
        if not f:
            continue
        f.update(ind_features(exts[sym], D, c.s))
        t_close = c.sb.m1.index[D] + pd.Timedelta(minutes=1)
        f.update(panel_feats(pt, sym, t_close, c.s))
        day = pd.Timestamp(t_close.tz_convert("America/New_York").date())
        prior = vix[vix.index < day]
        f["vix_onceki"] = float(prior.iloc[-1]) if len(prior) else np.nan
        f.update({"tur": kind, "sym": sym, "side": e["side"], "sonuc": e["sonuc"], "R_sonuc": e["R_sonuc"],
                  "B": int(e["sonuc"] == "SL"), "t_close": t_close, "dir": c.s, "entry": c.entry, "risk": c.risk,
                  "pid": e.get("pid", 0)})
        f.pop("ts", None)
        rows.append(f)
    return pd.DataFrame(rows)


def cmd_olaylar() -> None:
    OUT.mkdir(exist_ok=True)
    geo, items = geometry()
    print("geometri:", {k: (round(v["risk_frac"] * 100, 3), round(v["rr"], 2)) for k, v in geo.items()})
    sbs = {it["c"].sb.symbol: it["c"].sb for it in items}
    exts = {k: Ext(v) for k, v in sbs.items()}
    pan = panel_table()
    pt = {(sym, mdl): (g.ts.values.astype("datetime64[ns]"), g.ml_direction.values)
          for (sym, mdl), g in pan.sort_values("ts").groupby(["symbol", "model_type"])}
    vix = data.load_vix(pd.Timestamp("2026-06-01", tz="UTC"), data.utc_now())
    real = []
    for x in items:
        if x["r"]["outcome"] not in ("TP", "SL"):
            continue
        f, _ = EV.event(x["c"], x["r"], THR)
        if f is None:
            continue
        real.append({"c": x["c"], "D": x["c"].sb.pos_at(f["ts"]), "sonuc": x["r"]["outcome"], "side": x["r"]["side"],
                     "sym": x["r"]["symbol"], "R_sonuc": x["r"]["r_exit"], "pid": x["r"]["pid"]})
    dr = build_rows(real, exts, pt, vix, "gercek")
    dr.to_parquet(OUT / "genis_gercek.parquet", index=False)
    print("gerçek olay:", len(dr), dr.B.value_counts().to_dict())
    syn = [e for sym in SYMS if sym in sbs for e in synth(sbs[sym], sym, geo[sym])]
    ds = build_rows(syn, exts, pt, vix, "sentetik")
    ds.to_parquet(OUT / "genis_sentetik.parquet", index=False)
    print("sentetik olay:", len(ds), ds.B.value_counts().to_dict(), ds.groupby("sym").size().to_dict())


# ── tick (kutuda hesaplanır) ─────────────────────────────────────────────────

BOX_CODE = r'''
import MetaTrader5 as m,json,zlib,base64,statistics,time
import numpy as np
from datetime import datetime,timezone
assert m.initialize()
o=[]
for s in ["NAS100","GER40","XAUUSD","SpotCrude"]:
 t=m.symbol_info_tick(s)
 if t:o.append(round((t.time-time.time())/900)*900)
off=int(statistics.median(o))
SYM=["NAS100","GER40","XAUUSD","SpotCrude"]
EV=json.loads(zlib.decompress(base64.b64decode("__EV__")))
def F(t,x,sp,de,rk):
 dx=np.diff(x);tt=t[1:];R=[]
 for sec in(900,300,60,30):
  w=tt>=de-sec;u=int((dx[w]>0).sum());d=int((dx[w]<0).sum());R+=[int(w.sum()),(u-d)/max(u+d,1)]
 w=tt>=de-300;R+=[float(dx[w].sum()/rk),float(np.abs(dx[w]).sum()/rk)]
 R+=[float(sp[t>=de-60].mean()/max(sp.mean(),1e-9)),float(sp[t>=de-300].max()/rk)]
 i=np.searchsorted(t,t-10);ch=x-x[i];m5=t>=de-300
 R+=[float(ch[m5].min()/rk),float(ch[m5].max()/rk)]
 w1=t>=de-60;xs=x[w1];ts=t[w1];k=int(np.argmin(xs))
 R+=[float(de-ts[k]),float((xs[-1]-xs[k])/rk)]
 return R
out=[]
for i,si,de,d,rk in EV:
 a=datetime.fromtimestamp(de-900+off,timezone.utc);b=datetime.fromtimestamp(de+off,timezone.utc)
 tk=m.copy_ticks_range(SYM[si],a,b,m.COPY_TICKS_ALL)
 if tk is None or len(tk)<30:out.append([i]);continue
 t=tk["time_msc"]/1000.0-off;bid=tk["bid"].astype(float);ask=tk["ask"].astype(float)
 out.append([i]+F(t,d*bid,ask-bid,de,rk))
print("TICK_DATA_BEGIN"+base64.b64encode(zlib.compress(json.dumps({"off":off,"r":out}).encode())).decode()+"TICK_DATA_END")
m.shutdown()
'''
TICK_NAMES = ["tik_n15", "tik_denge15", "tik_n5", "tik_denge5", "tik_n1", "tik_denge1", "tik_n30s", "tik_denge30s",
              "tik_akis5_R", "tik_yol5_R", "tik_spread_orani1", "tik_spread_max5_R", "tik_10sn_aleyhte_R",
              "tik_10sn_lehte_R", "tik_dip_yasi_sn", "tik_dipten_sicrama_R"]
BATCH = 140


def cmd_tick() -> None:
    import box
    for kind in ("gercek", "sentetik"):
        d = pd.read_parquet(OUT / f"genis_{kind}.parquet")
        d = d[d.t_close >= TICK_START].reset_index(drop=True)
        path = OUT / f"tick_{kind}.parquet"
        done = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=["i"])
        todo = [i for i in d.index if i not in set(done["i"])]
        print(kind, "tick olayı:", len(d), "kalan:", len(todo))
        res = [done]
        for b0 in range(0, len(todo), BATCH):
            ids = todo[b0:b0 + BATCH]
            ev = [[int(i), BROKER[d.at[i, "sym"]], int(d.at[i, "t_close"].timestamp()), int(d.at[i, "dir"]),
                   round(float(d.at[i, "risk"]), 4)] for i in ids]
            blob = base64.b64encode(zlib.compress(json.dumps(ev, separators=(",", ":")).encode(), 9)).decode()
            code = BOX_CODE.replace("__EV__", blob)
            out = box.decode(box.run_code(code, f"{kind} {b0}/{len(todo)}", 600))
            rows = [dict(zip(["i"] + TICK_NAMES, r)) for r in out["r"] if len(r) > 1]
            res.append(pd.DataFrame(rows))
            pd.concat(res, ignore_index=True).to_parquet(path, index=False)
            print(f"  {kind} {b0 + len(ids)}/{len(todo)} · tick bulunan {len(rows)}/{len(ids)} · offset {out['off']}", flush=True)


# ── analiz ───────────────────────────────────────────────────────────────────

SKIP = {"tur", "sym", "side", "sonuc", "R_sonuc", "B", "t_close", "dir", "entry", "risk", "pid", "R_D", "rr", "i"}


def cols(d: pd.DataFrame) -> list[str]:
    return [c for c in d.columns if c not in SKIP and pd.api.types.is_numeric_dtype(d[c]) and d[c].notna().mean() > 0.7
            and d[c].nunique() > 1]


def univariate(d: pd.DataFrame, split: pd.Series) -> pd.DataFrame:
    rows = []
    for c in cols(d):
        A, B = d.loc[d.B == 0, c].to_numpy(float), d.loc[d.B == 1, c].to_numpy(float)
        a, p = auc_perm(B, A, n_perm=500)
        tr, te = d[split], d[~split]
        rows.append({"özellik": c, "A_TP_medyan": np.nanmedian(A), "B_SL_medyan": np.nanmedian(B), "AUC": a, "p": p,
                     "AUC_ilk": auc(tr.loc[tr.B == 1, c].to_numpy(float), tr.loc[tr.B == 0, c].to_numpy(float)),
                     "AUC_son": auc(te.loc[te.B == 1, c].to_numpy(float), te.loc[te.B == 0, c].to_numpy(float))})
    out = pd.DataFrame(rows)
    out["q"] = bh_q(out.p.to_numpy())
    out["tutarlı"] = np.where(np.sign(out.AUC_ilk - 0.5) == np.sign(out.AUC_son - 0.5), "evet", "hayır")
    return out.reindex((out.AUC - 0.5).abs().sort_values(ascending=False).index)


def multi(d: pd.DataFrame, split: pd.Series, feats: list[str], rng) -> list[str]:
    lines = []
    for lab, tr, te in (("ilk→son", d[split], d[~split]), ("son→ilk", d[~split], d[split])):
        Xtr, Xte = EV._standardize(tr, te, feats)
        w = EV.logit_fit(Xtr, tr.B.to_numpy(float), lam=5.0)
        pr = EV.logit_pred(w, Xte)
        yt = te.B.to_numpy()
        a = auc(pr[yt == 1], pr[yt == 0])
        null = []
        for _ in range(100):
            ws = EV.logit_fit(Xtr, rng.permutation(tr.B.to_numpy(float)), lam=5.0, it=400)
            ps = EV.logit_pred(ws, Xte)
            null.append(auc(ps[yt == 1], ps[yt == 0]))
        thr = EV._best_thr(EV.logit_pred(w, Xtr), tr)
        flag = pr >= thr
        net = float((te.R_D - te.R_sonuc)[flag].sum())
        lines.append(f"    {lab}: sınama AUC {a:.3f} (plasebo %95 üst {np.quantile(null, 0.95):.3f}) · "
                     f"kural {int(flag.sum())}/{len(te)} işlemde D'de çık → net {net:+.1f}R")
    return lines


def report(d: pd.DataFrame, title: str, rng) -> None:
    d = d.sort_values("t_close").reset_index(drop=True)
    split = pd.Series(np.arange(len(d)) < int(len(d) * 0.6), index=d.index)
    print(f"\n######## {title}: n={len(d)} · A (döndü→TP) {int((d.B == 0).sum())} · B (SL) {int(d.B.sum())} · "
          f"'hep D'de çık' {(d.R_D - d.R_sonuc).sum():+.1f}R")
    u = univariate(d, split)
    print(u.head(20).round(3).to_string(index=False))
    fam = {"bar": [c for c in cols(d) if not c.startswith(("g", "tik_", "panel_", "vix", "vwap", "gun_"))],
           "gösterge": [c for c in cols(d) if c.startswith(("g1_", "g5_", "g15_", "g60_", "vwap", "gun_"))],
           "panel+makro": [c for c in cols(d) if c.startswith(("panel_", "vix"))],
           "tick": [c for c in cols(d) if c.startswith("tik_")]}
    fam["HEPSİ"] = cols(d)
    for k, fs in fam.items():
        if fs:
            print(f"  [{k}] {len(fs)} özellik")
            print("\n".join(multi(d, split, fs, rng)))


def cmd_analiz() -> None:
    rng = np.random.default_rng(11)
    pd.set_option("display.width", 230)
    for kind in ("gercek", "sentetik"):
        d = pd.read_parquet(OUT / f"genis_{kind}.parquet")
        report(d, f"{kind.upper()} — bar+gösterge+panel (tüm dönem)", rng)
        tp = OUT / f"tick_{kind}.parquet"
        if tp.exists():
            t = pd.read_parquet(tp)
            dt = d[d.t_close >= TICK_START].reset_index(drop=True).join(t.set_index("i"), how="inner")
            for a_, b_, nm in (("tik_n1", "tik_n15", "tik_hiz_1dk_orani"), ("tik_n30s", "tik_n15", "tik_hiz_30sn_orani")):
                dt[nm] = dt[a_] / (dt[b_] / (15 if nm.endswith("1dk_orani") else 30))
            dt["tik_verim5"] = dt["tik_akis5_R"].abs() / dt["tik_yol5_R"].replace(0, np.nan)
            report(dt, f"{kind.upper()} — TICK dönemi (28 Ağu+) tüm özellikler", rng)


if __name__ == "__main__":
    {"olaylar": cmd_olaylar, "tick": cmd_tick, "analiz": cmd_analiz}[sys.argv[1]]()
