"""Decider XAUUSD işlem veri setini kurar (bir satır = bir OPEN kararı / icra).

Kaynaklar:
  * data/journal_xau_raw.jsonl   — Supabase decider_journal (kutu journal.jsonl aynası), tüm XAU kayıtları
  * data/decider_exec_bot_trades.csv — bot_trades magic 52890989 (decider execute_mt5 emirleri);
    open/close_time BROKER saatinde (UTC+3) → −3s (journal ts ile saniye düzeyinde eşleşmeyle doğrulandı)
  * data/xau_1m_utc.csv.gz       — broker 1m BID barları (03_build_bars.py)

Giriş tanımları (sızıntı yok):
  * GÖLGE (icra edilmemiş) karar: journal ts = karar YAZILDIĞI an (Claude çağrısı bittikten sonra).
    Giriş = ts'den SONRA açılan ilk 1m barın açılışı (+ ölçülen spread, BUY'da ask).
  * İCRA edilmiş: gerçek dolum fiyatı (bot_trades.open_price, ask) ve dolum zamanı; yol dolum
    dakikasından SONRAKİ ilk tam barla başlar (dolum dakikasının dolum-öncesi kısmı kullanılmaz).
  * ATR(M5/M15/H1, 14): giriş anında KAPANMIŞ barlardan (bar_end ≤ giriş).
Yinelenen kayıtlar: aynı yönde ≤10 sn arayla iki OPEN (10-05..10-07 çift süreç) → ilki tutulur."""
import json
import numpy as np
import pandas as pd
import core

HERE = core.HERE
DUP_SEC = 10
MATCH_WINDOW_S = (-5, 90)          # icra zamanı − karar ts (sn)
BROKER_SHIFT = pd.Timedelta(hours=3)
DEFAULT_SPREAD = 0.14              # journal'da spread'i olmayan erken kayıtlar için ölçülen medyan
HORIZONS = (30, 60, 120, 240)


def load_journal_opens() -> pd.DataFrame:
    recs = []
    for ln in open(HERE / "data" / "journal_xau_raw.jsonl"):
        r = json.loads(ln)
        raw = r["raw"]; dec = raw.get("decision") or {}
        if dec.get("action") != "OPEN":
            continue
        tr = raw.get("trade") or {}
        recs.append({
            "id": r["id"], "decision_time_utc": pd.Timestamp(r["ts"]), "direction": dec.get("direction"),
            "size_factor": dec.get("size_factor"), "mode": raw.get("mode") or "evidence",
            "free_ctx": raw.get("free_ctx"), "model": raw.get("model"),
            "j_price": tr.get("entry_price"), "j_atr5": tr.get("atr"), "j_tp": tr.get("tp"), "j_sl": tr.get("sl"),
            "j_rr": tr.get("rr"), "j_spread": tr.get("spread"),
            "j_outcome": raw.get("outcome") if isinstance(raw.get("outcome"), str) else r.get("outcome"),
            "j_pnl_r": raw.get("pnl_r"), "j_pnl_r_net": raw.get("pnl_r_net"),
            "reason": str(dec.get("reason") or "")[:200].replace("\n", " "),
        })
    d = pd.DataFrame(recs).sort_values("decision_time_utc").reset_index(drop=True)
    d["dup"] = False
    for dirn, g in d.groupby("direction"):
        gap = g.decision_time_utc.diff().dt.total_seconds()
        d.loc[g.index[gap < DUP_SEC], "dup"] = True
    return d


def load_exec() -> pd.DataFrame:
    e = pd.read_csv(HERE / "data" / "decider_exec_bot_trades.csv")
    e = e[e.symbol == "XAUUSD"].copy()
    e["exec_open_utc"] = pd.to_datetime(e.open_time, utc=True) - BROKER_SHIFT
    e["exec_close_utc"] = pd.to_datetime(e.close_time, utc=True) - BROKER_SHIFT
    e["exec_outcome"] = e.comment.str.extract(r"^\[(\w+)")[0].map({"tp": "WIN", "sl": "LOSS"}).fillna("OTHER")
    e["exec_pnl_usd"] = e.profit + e.commission.fillna(0) + e.swap.fillna(0)
    return e.reset_index(drop=True)


def link_exec(j: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    j = j.copy()
    for c in ("ticket", "exec_open_utc", "exec_close_utc", "lot", "exec_entry", "exec_sl", "exec_tp",
              "exec_close_price", "exec_outcome", "exec_pnl_usd", "exec_lag_s"):
        j[c] = np.nan
    j["ticket"] = j["ticket"].astype(object)
    unmatched = []
    for _, x in e.iterrows():
        cand = j[(j.direction == x.direction) & (~j.dup)].copy()
        lag = (x.exec_open_utc - cand.decision_time_utc).dt.total_seconds()
        ok = cand[(lag >= MATCH_WINDOW_S[0]) & (lag <= MATCH_WINDOW_S[1]) & cand.ticket.isna()]
        if ok.empty:
            unmatched.append(x.ticket); continue
        k = (x.exec_open_utc - ok.decision_time_utc).dt.total_seconds().abs().idxmin()
        j.loc[k, ["ticket", "exec_open_utc", "exec_close_utc", "lot", "exec_entry", "exec_sl", "exec_tp",
                  "exec_close_price", "exec_outcome", "exec_pnl_usd"]] = [
            x.ticket, x.exec_open_utc, x.exec_close_utc, x.volume, x.open_price, x.sl, x.tp,
            x.close_price, x.exec_outcome, x.exec_pnl_usd]
        j.loc[k, "exec_lag_s"] = (x.exec_open_utc - j.loc[k, "decision_time_utc"]).total_seconds()
    print(f"icra eşleşti {int(j.ticket.notna().sum())}/{len(e)} | eşleşmeyen ticket: {unmatched}")
    j["executed"] = j.ticket.notna()
    return j


def session_end(ts: pd.Timestamp) -> pd.Timestamp:
    """Girişten sonraki ilk günlük kapanış (21:00 UTC)."""
    se = ts.normalize() + pd.Timedelta(hours=core.SESSION_BREAK_HOUR_UTC)
    return se if se > ts else se + pd.Timedelta(days=1)


def build(j: pd.DataFrame) -> pd.DataFrame:
    b1 = core.load_1m(); P = core.Paths(b1)
    r5, r15, r60 = (core.resample(b1, r) for r in ("5min", "15min", "60min"))
    out = []
    for _, x in j.iterrows():
        r = x.to_dict()
        buy = x.direction == "BUY"
        spread = x.j_spread if pd.notna(x.j_spread) else DEFAULT_SPREAD
        r["spread_used"] = spread
        if x.executed:
            t_entry = pd.Timestamp(x.exec_open_utc)
            i0 = P.first_idx_at_or_after(t_entry.floor("min") + pd.Timedelta(minutes=1))
            entry = float(x.exec_entry)          # gerçek dolum (BUY=ask)
            entry_basis = "fill"
        else:
            t_entry = None
            i0 = P.first_idx_at_or_after(x.decision_time_utc.floor("min") + pd.Timedelta(minutes=1))
            if i0 < len(P.t):
                t_entry = pd.Timestamp(P.t[i0], tz="UTC")
                entry = P.o[i0] + (spread if buy else 0.0)
            entry_basis = "next_m1_open"
        if t_entry is None or i0 >= len(P.t):
            r["usable"] = False; out.append(r); continue
        first_bar = pd.Timestamp(P.t[i0], tz="UTC")
        r.update({"entry_time_utc": t_entry, "path_start_utc": first_bar, "entry_price": entry,
                  "entry_basis": entry_basis,
                  "entry_delay_min": (first_bar - x.decision_time_utc).total_seconds() / 60})
        # giriş ilk barı karardan > 30 dk sonra ise (veri boşluğu / piyasa kapalı) kullanılamaz
        r["usable"] = r["entry_delay_min"] <= 30
        r["atr_m5"] = core.atr_closed(r5, t_entry)
        r["atr_m15"] = core.atr_closed(r15, t_entry)
        r["atr_h1"] = core.atr_closed(r60, t_entry)
        # orijinal geometri: journal'daki ATR çarpanlarının MESAFELERİ girişe göre (execute_mt5 ile aynı)
        if x.executed:
            tp_d = abs(x.exec_tp - entry); sl_d = abs(entry - x.exec_sl)
        else:
            tp_d = abs(x.j_tp - x.j_price); sl_d = abs(x.j_price - x.j_sl)
        r["orig_tp_usd"], r["orig_sl_usd"] = tp_d, sl_d
        r["original_tp"] = entry + tp_d if buy else entry - tp_d
        r["original_sl"] = entry - sl_d if buy else entry + sl_d
        r["orig_tp_atr5"] = tp_d / r["atr_m5"] if r["atr_m5"] else np.nan
        r["orig_sl_atr5"] = sl_d / r["atr_m5"] if r["atr_m5"] else np.nan
        # yol: 48 saat
        w = P.window(i0, core.MAX_HOLD_MIN)
        h, l, c, tt = P.h[w], P.l[w], P.c[w], P.t[w]
        pnl, code, ex = core.sim_grid(x.direction, entry, spread, h, l, c, np.array([tp_d]), np.array([sl_d]))
        r["sim_outcome"] = {1: "WIN", -1: "LOSS", 0: "TIMEOUT48h"}[int(code[0, 0])]
        r["sim_pnl_usd_per_oz"] = float(pnl[0, 0])
        r["sim_R"] = float(pnl[0, 0]) / sl_d
        r["sim_exit_time_utc"] = pd.Timestamp(tt[int(ex[0, 0])], tz="UTC")
        r["sim_hold_min"] = (r["sim_exit_time_utc"] - first_bar).total_seconds() / 60 + 1
        fav, adv, cl = core.fav_adv(x.direction, entry, spread, h, l, c)
        a5 = r["atr_m5"] or np.nan
        for H in HORIZONS:
            k = int(np.searchsorted(tt, tt[0] + np.timedelta64(H, "m")))
            r[f"mfe_{H}m_usd"] = float(fav[:k].max()); r[f"mae_{H}m_usd"] = float(adv[:k].max())
            r[f"mfe_{H}m_atr"] = r[f"mfe_{H}m_usd"] / a5; r[f"mae_{H}m_atr"] = r[f"mae_{H}m_usd"] / a5
            r[f"ret_{H}m_usd"] = float(cl[k - 1])
        se = session_end(first_bar)
        k = int(np.searchsorted(tt, core.to64(se)))
        k = max(k, 1)
        r["mfe_sess_usd"], r["mae_sess_usd"] = float(fav[:k].max()), float(adv[:k].max())
        r["mfe_sess_atr"], r["mae_sess_atr"] = r["mfe_sess_usd"] / a5, r["mae_sess_usd"] / a5
        # orijinal SL'e kadar: SL vurulmadan önce lehte ne kadar gidildi (SL barının lehte kısmı SAYILMAZ)
        kx = int(ex[0, 0])
        pre = fav[:kx] if r["sim_outcome"] == "LOSS" else fav[:kx + 1]
        r["mfe_before_exit_R"] = float(pre.max()) / sl_d if len(pre) else 0.0
        prea = adv[:kx] if r["sim_outcome"] == "WIN" else adv[:kx + 1]   # TP barının aleyhte kısmı sayılmaz
        r["mae_before_exit_R"] = float(prea.max()) / sl_d if len(prea) else 0.0
        # veri boşluğu bayrağı: ilk 240 dk içinde (günlük ara hariç) >5 dk boşluk
        k240 = int(np.searchsorted(tt, tt[0] + np.timedelta64(240, "m")))
        gaps = np.diff(tt[:k240]).astype("timedelta64[m]").astype(int)
        hrs = pd.DatetimeIndex(tt[:k240][:-1]).hour if k240 > 1 else []
        r["data_gap_240m"] = bool(np.any((gaps > 5) & (np.asarray(hrs) != 20))) if len(gaps) else False
        out.append(r)
    return pd.DataFrame(out)


if __name__ == "__main__":
    j = load_journal_opens()
    print("journal OPEN:", len(j), "| yinelenen:", int(j.dup.sum()))
    e = load_exec()
    j = link_exec(j, e)
    d = build(j)
    d["source"] = np.where(d.executed, "live_demo_exec", "shadow_journal")
    d.to_pickle(HERE / "data" / "trades_full.pkl")
    print(d.groupby(["source", "direction", "dup", "usable"]).size())
    print("veri boşluklu:", int(d.data_gap_240m.fillna(False).sum()))
