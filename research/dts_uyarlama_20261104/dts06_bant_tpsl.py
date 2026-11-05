"""DTS-06 — Zaman Makinesi bandı × gerçek TP/SL (bot işlemleri + panel sinyalleri). Ön-kayıt: PROTOCOL.md Ek-2.
Bant ORAN olarak hesaplanır (son kapanışa göre) ve işlemin kendi broker girişine uygulanır (emtia beslemesi tabanı farkına dayanıklı)."""
import json, random, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from services import time_machine_service as tm
from common import load, month_boot

TF = {"NDX": "5m", "XAUUSD": "5m", "USOIL": "5m", "GDAXI": "15m"}
CODE = {"NDX.INDX": "NDX", "GDAXI.INDX": "GDAXI", "XAUUSD": "XAUUSD", "USOIL.FOREX": "USOIL"}
REPLAYS = 600
H_BOT_MIN, H_SIG_MIN = 240, 60


def bars(sym):
    tf = TF[sym]; a = load(sym, tf)
    c = pd.read_csv(f"data/cc_{sym}_{tf}.csv"); c["ts"] = pd.to_datetime(c.candle_time, utc=True, format="ISO8601")
    c = c[c.ts > a.ts.max()][["ts", "open", "high", "low", "close"]]
    d = pd.concat([a, c]).sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    return tm.Bars((d.ts.astype("int64") // 10**9).to_numpy(), d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy())


def evaluate(b, bm, days, slots, by_day, full, pools, t_entry, side, d_tp, d_sl, h):
    q = int(np.searchsorted(b.ts, t_entry - bm * 60, side="right")) - 1     # giriş anından önce KAPANMIŞ son bar
    if q < 1:
        return None
    d = int(days[q])
    if d not in pools:
        prev = [x for x in full if x < d][-tm.POOL_SESSIONS:]
        pools[d] = tm.build_pool(b, [{"day": x, "idx": by_day[x]} for x in prev], bm) if len(prev) >= tm.MIN_SESSIONS else None
    pool = pools[d]
    if pool is None:
        return None
    e, k, long = 1.0, int(slots[q]), side == 1
    st = e - d_sl if long else e + d_sl; tg = e + d_tp if long else e - d_tp
    rng = random.Random(19); ends = []; nt = ns = 0
    for _ in range(REPLAYS):
        oc, p, _path = tm._replay(pool, rng, e, st, tg, k, k + h, tm.WINDOW, long)
        ends.append(p); nt += oc == "target"; ns += oc == "stop"
    q05, q25, q75, q95 = np.quantile(ends, [0.05, 0.25, 0.75, 0.95])
    tp_out = (tg > q95) if long else (tg < q05)
    sl_in = (q25 <= st <= q75)
    return {"p_t": nt / REPLAYS, "p_s": ns / REPLAYS, "tp_out": bool(tp_out), "sl_in": bool(sl_in), "w90": float(q95 - q05)}


def prep(sym):
    bm = int(TF[sym][:-1]); b = bars(sym); days, slots = tm.day_and_slot(b.ts, bm)
    by_day = {}
    for i, (d, s) in enumerate(zip(days.tolist(), slots.tolist())):
        by_day.setdefault(d, {})[s] = i
    typ = float(np.median([len(v) for v in by_day.values()]))
    full = [x for x in sorted(by_day) if len(by_day[x]) >= tm.MIN_DAY_FRACTION * typ]
    return b, bm, days, slots, by_day, full


def run(sym):
    b, bm, days, slots, by_day, full = prep(sym); pools = {}
    bt = pd.read_csv("data/bot_trades.csv"); bt["open_time"] = pd.to_datetime(bt.open_time, utc=True, format="ISO8601")
    bt = bt[bt.normalized_symbol.map(CODE) == sym]
    rows = []
    for _, r in bt.iterrows():
        side = 1 if str(r.direction).upper().startswith("BUY") else -1
        e = r.open_price; dsl, dtp = abs(e - r.sl) / e, abs(r.tp - e) / e if r.tp > 0 else np.nan
        if not (dsl > 2e-4 and dtp > 0):
            continue
        ev = evaluate(b, bm, days, slots, by_day, full, pools, int(r.open_time.timestamp()), side, dtp, dsl, H_BOT_MIN // bm)
        if ev:
            rows.append({"kaynak": "bot", "sym": sym, "t": r.open_time.isoformat(), "ticket": r.ticket, "R_tgt": dtp / dsl, **ev})
    sg = pd.read_csv("data/signals.csv"); sg["created_at"] = pd.to_datetime(sg.created_at, utc=True, format="ISO8601")
    sg = sg[sg.symbol.map(CODE) == sym]
    for _, r in sg.iterrows():
        tg = json.loads(r.targets); e = float(r.entry)
        if not tg.get("TP1") or not tg.get("SL") or not e:
            continue
        side = 1 if r.direction == "BUY" else -1
        dtp, dsl = abs(tg["TP1"] - e) / e, abs(tg["SL"] - e) / e
        if dsl <= 0 or dtp <= 0:
            continue
        ev = evaluate(b, bm, days, slots, by_day, full, pools, int(r.created_at.timestamp()), side, dtp, dsl, H_SIG_MIN // bm)
        if ev:
            rows.append({"kaynak": "sinyal", "sym": sym, "t": r.created_at.isoformat(), "id": r.id, "status": r.status, "R_tgt": dtp / dsl, **ev})
    return rows


def judge(df, name, mask_out, R, months, first):
    el, kp = mask_out, ~mask_out
    res = {"kural": name, "n": int(len(df)), "elenen": int(el.sum()), "elenen_ortR": float(R[el].mean()) if el.any() else None,
           "kalan_ortR": float(R[kp].mean()) if kp.any() else None, "hepsi_ortR": float(R.mean()),
           "P_elenen_neg": month_boot(-R[el], months[el]) if el.sum() >= 10 else None}
    for nm, m in (("y1", first), ("y2", ~first)):
        res[f"{nm}_elenen_ortR"] = float(R[el & m].mean()) if (el & m).any() else None
        res[f"{nm}_kalan_minus_hepsi"] = float(R[kp & m].mean() - R[m].mean()) if (kp & m).any() else None
    res["aday"] = bool(res["elenen"] >= 30 and (res["elenen_ortR"] or 0) < 0 and (res["kalan_ortR"] or -9) > res["hepsi_ortR"]
                       and all((res[f"{y}_elenen_ortR"] or 0) < 0 and (res[f"{y}_kalan_minus_hepsi"] or -1) > 0 for y in ("y1", "y2")))
    return res


def main():
    with Pool(4) as p:
        rows = sum(p.map(run, ["NDX", "GDAXI", "XAUUSD", "USOIL"]), [])
    df = pd.DataFrame(rows); df["t"] = pd.to_datetime(df.t, utc=True, format="ISO8601")
    bt = pd.read_csv("data/bot_trades.csv")
    import dts0405_butce_risk as BR
    rmap = BR.load().set_index("ticket").R
    out = {}
    for src in ("bot", "sinyal"):
        x = df[df.kaynak == src].copy()
        if src == "bot":
            x["R"] = x.ticket.map(rmap); x = x.dropna(subset=["R"]); hit = x.R > 0
        else:
            x["R"] = np.where(x.status == "completed", x.R_tgt, -1.0); hit = x.status == "completed"
        x = x.sort_values("t"); R = x.R.to_numpy(); months = x.t.dt.strftime("%Y-%m").to_numpy()
        first = (x.t < x.t.median()).to_numpy()
        share = (x.p_t / (x.p_t + x.p_s)).fillna(0.5).to_numpy(); be = (1 / (1 + x.R_tgt)).to_numpy()
        ptp = x.p_t.to_numpy(); y = hit.to_numpy().astype(float)
        brier, brier_b = float(np.mean((ptp - y) ** 2)), float(np.mean((y.mean() - y) ** 2))
        out[src] = {"n": int(len(x)), "brier_p_tp": brier, "brier_taban": brier_b,
                    "tp_out_pay": float(x.tp_out.mean()), "sl_in_pay": float(x.sl_in.mean()),
                    "kurallar": [judge(x, "TP %90 bandın dışında → atla", x.tp_out.to_numpy(), R, months, first),
                                 judge(x, "SL %50 bandın içinde → atla", x.sl_in.to_numpy(), R, months, first),
                                 judge(x, "dokunma payı < başabaş → atla", share < be, R, months, first)],
                    "sembol_ortR": x.groupby("sym").R.mean().round(3).to_dict()}
    df.to_csv("dts06_satirlar.csv", index=False)
    json.dump(out, open("dts06_sonuc.json", "w"), indent=1, default=float)
    for src, v in out.items():
        print(f"\n== {src}: n={v['n']} Brier p_tp {v['brier_p_tp']:.4f} vs taban {v['brier_taban']:.4f} | TP dışarıda %{100*v['tp_out_pay']:.1f} | SL iç %{100*v['sl_in_pay']:.1f}")
        for k in v["kurallar"]:
            print("  ", {a: (round(b, 3) if isinstance(b, float) else b) for a, b in k.items()})


if __name__ == "__main__":
    main()
