"""c_new.py — PROTOCOL §4: H1–H6 (ön kayıtlı). Çıktı results/c_new.json + c_book_daily.parquet."""
from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

import lib
import rules

LOTS = {"C3B": 2.0, "CAPREV": 1.0, "ORBVIX": 0.75, "CEKIC": 0.5, "KSG": 0.5, "AYSONU_SON": 1.0, "AYSONU_E2": 0.75}
EMERG = {"C3B": -0.10, "KSG": -0.07, "AYSONU_SON": -0.04, "AYSONU_E2": -0.08}


def boot_diff(a: np.ndarray, b: np.ndarray, n: int = 4000, seed: int = 3) -> float:
    """P(ort(a) > ort(b)), iki örneklem bootstrap."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan
    rng = np.random.default_rng(seed)
    ma = a[rng.integers(0, len(a), (n, len(a)))].mean(1)
    mb = b[rng.integers(0, len(b), (n, len(b)))].mean(1)
    return float((ma > mb).mean())


def cell(x: pd.Series) -> dict:
    return {"n": int(x.notna().sum()), "mean": float(x.mean()) if len(x) else np.nan}


# ─────────────────────────── H1 ORB OR-genişliği dozu ───────────────────────────

def h1(orb: pd.DataFrame, D: pd.DataFrame) -> dict:
    full = D[D.full].copy()
    full["rng"] = full.high930 - full.low930
    prev20 = full.set_index("d").rng.shift(1).rolling(20).mean()
    o = orb.copy()
    o["g"] = o.or_w / o.d.map(prev20)
    o = o[o.g.notna()]
    o["T"] = pd.qcut(o.g, 3, labels=["dar", "orta", "genis"])     # tertil eşikleri tüm örneklemden (yalnız gruplama)
    out = {"esik": [float(x) for x in o.g.quantile([1 / 3, 2 / 3])]}
    for e in ("ESKI", "YENI", "TUM"):
        g = o if e == "TUM" else o[o.era == e]
        out[e] = {t: cell(g[g["T"] == t].R) for t in ("dar", "orta", "genis")}
        out[e]["P_genis_gt_dar"] = boot_diff(g[g["T"] == "genis"].R, g[g["T"] == "dar"].R)
    s = [np.sign(out[e]["genis"]["mean"] - out[e]["dar"]["mean"]) for e in ("ESKI", "YENI")]
    out["gecti"] = bool(s[0] == s[1] == 1 and out["TUM"]["P_genis_gt_dar"] >= 0.95)
    return out


# ─────────────────────────── kitap: günlük P&L (1m işaretleme) ───────────────────────────

def book_daily(m1: lib.M1, trades: pd.DataFrame, scale: pd.Series | None = None) -> pd.DataFrame:
    """Her işlemi NY gün sonu (o günün son 1m barı) kapanışıyla işaretle → gün başına $ P&L (lot × puan; 1 lot = 1 $/puan).
    scale: işlem indeksine göre lot çarpanı (H2)."""
    day_end_ix = {}
    dd = m1.d
    ends = np.r_[np.where(dd[1:] != dd[:-1])[0], len(dd) - 1]
    for k in ends:
        day_end_ix[pd.Timestamp(dd[k]).date()] = k
    rows = []
    for idx, x in trades.iterrows():
        lot = LOTS.get(x.rule, 0.5) * (1.0 if scale is None else float(scale.get(idx, 1.0)))
        i_in = int(np.searchsorted(m1.t, x.t_in))
        i_out = int(np.searchsorted(m1.t, x.t_out))
        d_in = pd.Timestamp(m1.d[min(i_in, len(m1.d) - 1)]).date()
        d_out = pd.Timestamp(m1.d[min(i_out, len(m1.d) - 1)]).date()
        prev = x.px_in
        fin_day = lib.FIN_BP_PER_DAY / 1e4 * x.px_in if x.side > 0 else 0.0
        d = d_in
        while d < d_out:
            k = day_end_ix.get(d)
            if k is not None and k < i_out:
                mark = m1.c[k] if x.side > 0 else m1.c[k] + m1.spr[k]
                rows.append((d, x.rule, lot * x.side * (mark - prev)))
                prev = mark
            d += timedelta(days=1)
        nights = max(0, (d_out - d_in).days)
        rows.append((d_out, x.rule, lot * (x.side * (x.px_out - prev) - fin_day * nights)))
    df = pd.DataFrame(rows, columns=["d", "rule", "pnl"])
    return df


def sharpe_m(daily: pd.DataFrame) -> pd.Series:
    m = daily.groupby(pd.to_datetime(daily.d).dt.to_period("M")).pnl.sum()
    return m.reindex(pd.period_range("2018-01", "2026-11", freq="M"), fill_value=0.0)


def sh(x: pd.Series) -> float:
    return float(x.mean() / x.std() * np.sqrt(12)) if x.std() > 0 else np.nan


def boot_sharpe_diff(a: pd.Series, b: pd.Series, n: int = 4000, seed: int = 5) -> float:
    rng = np.random.default_rng(seed)
    A, B = a.values, b.values
    idx = rng.integers(0, len(A), (n, len(A)))
    sa = A[idx].mean(1) / A[idx].std(1)
    sb = B[idx].mean(1) / B[idx].std(1)
    return float((sa > sb).mean())


def book_stats(daily: pd.DataFrame) -> dict:
    s = daily.groupby("d").pnl.sum().sort_index()
    eq = s.cumsum()
    dd = eq - eq.cummax()
    mo = sharpe_m(daily)
    yr = s.groupby(pd.to_datetime(s.index).year).sum()
    return {"toplam": float(s.sum()), "en_kotu_gun": float(s.min()), "en_kotu_gun_tarih": str(s.idxmin()),
            "max_dusus": float(dd.min()), "max_dusus_tarih": str(dd.idxmin()), "aylik_sharpe": sh(mo),
            "yil": {int(k): float(v) for k, v in yr.items()},
            "en_kotu_5_gun": {str(k): float(v) for k, v in s.nsmallest(5).items()}}


# ─────────────────────────── H2 oynaklık-yönetimli kitap ───────────────────────────

def rv20_map(m1: lib.M1) -> pd.Series:
    """Gün başına gerçekleşen oynaklık (NY günü, tüm saatler, 1m log getiri) → önceki 20 günün ortalaması (karar günü hariç)."""
    lr = np.r_[0.0, np.diff(np.log(m1.c))]
    lr[np.r_[True, m1.d[1:] != m1.d[:-1]]] = 0.0                # gün sınırı boşluğunu dışla
    dv = pd.Series(lr ** 2).groupby(m1.d).sum() ** 0.5
    dv.index = pd.to_datetime(dv.index).date
    return dv.shift(1).rolling(20).mean()


def h2(m1, book: pd.DataFrame) -> dict:
    rv = rv20_map(m1)
    v = book.d.map(rv)
    tgt = float(np.nanmedian(v))
    inv = (tgt / v).clip(0.5, 2.0).fillna(1.0)
    up = (v / tgt).clip(0.5, 2.0).fillna(1.0)
    inv, up = inv / inv.mean(), up / up.mean()
    base = sharpe_m(book_daily(m1, book))
    mi = sharpe_m(book_daily(m1, book, inv))
    mu = sharpe_m(book_daily(m1, book, up))
    out = {"hedef_rv": tgt}
    for e, sel in (("ESKI", base.index.to_timestamp().date <= lib.ESKI_END),
                   ("YENI", base.index.to_timestamp().date > lib.ESKI_END), ("TUM", slice(None))):
        out[e] = {"sabit": sh(base[sel]), "ters_oynaklik": sh(mi[sel]), "oynaklikla_buyut": sh(mu[sel]),
                  "P_ters_gt_sabit": boot_sharpe_diff(mi[sel], base[sel]),
                  "P_buyut_gt_sabit": boot_sharpe_diff(mu[sel], base[sel])}
    for k in ("ters", "buyut"):
        key = f"P_{k}_gt_sabit"
        a, b = out["ESKI"][key], out["YENI"][key]
        out[f"gecti_{k}"] = bool((a >= 0.90 and b >= 0.90))
    return out


# ─────────────────────────── H3 panik freni ───────────────────────────

def h3(m1, book: pd.DataFrame, vixp: dict, th: float = 35.0) -> dict:
    v = book.d.map(vixp)
    skip = (v >= th) & (book.side > 0)
    kept = book[~skip]
    sk = book[skip]
    b0, b1 = book_stats(book_daily(m1, book)), book_stats(book_daily(m1, kept))
    sk_usd = (sk.net_bp / 1e4 * sk.px_in * sk.rule.map(LOTS)).sum()
    return {"atlanan_n": int(skip.sum()), "atlanan_kural": sk.rule.value_counts().to_dict(),
            "atlanan_ort_bp": float(sk.net_bp.mean()) if len(sk) else np.nan, "atlanan_toplam_usd": float(sk_usd),
            "kitap_tam": {k: b0[k] for k in ("toplam", "max_dusus", "en_kotu_gun", "aylik_sharpe")},
            "kitap_frenli": {k: b1[k] for k in ("toplam", "max_dusus", "en_kotu_gun", "aylik_sharpe")},
            "gecti": bool(len(sk) and sk.net_bp.mean() < 0 and b1["max_dusus"] > b0["max_dusus"]
                          and (b0["toplam"] - b1["toplam"]) < (b1["max_dusus"] - b0["max_dusus"]))}


# ─────────────────────────── H4 KSG yoğunluk dozu ───────────────────────────

def h4(ks: pd.DataFrame, D: pd.DataFrame) -> dict:
    full = D[D.full].copy()
    o16 = full.O16.where(full.O16.notna(), full.c1600)
    full["r"] = o16 / full.O15 - 1
    sd = full.set_index("d").r.shift(1).rolling(20).std()
    k = ks.copy()
    k["z"] = (k.ret_bp / 1e4) / k.d.map(sd)
    k = k[k.z.notna()]
    k["T"] = pd.qcut(k.z, 3, labels=["derin", "orta", "sig"])
    out = {"esik": [float(x) for x in k.z.quantile([1 / 3, 2 / 3])]}
    mono = []
    for e in ("ESKI", "YENI", "TUM"):
        g = k if e == "TUM" else k[k.era == e]
        out[e] = {t: cell(g[g["T"] == t].net_bp) for t in ("derin", "orta", "sig")}
        out[e]["P_derin_gt_sig"] = boot_diff(g[g["T"] == "derin"].net_bp, g[g["T"] == "sig"].net_bp)
        m = [out[e][t]["mean"] for t in ("derin", "orta", "sig")]
        if e != "TUM":
            mono.append(m[0] > m[1] > m[2])
    out["gecti"] = bool(all(mono) and out["TUM"]["P_derin_gt_sig"] >= 0.95)
    return out


# ─────────────────────────── H5 C+ etiketleri ESKİ dilimde ───────────────────────────

def opex_week(d: date) -> bool:
    first = date(d.year, d.month, 1)
    fri3 = first + timedelta(days=(4 - first.weekday()) % 7 + 14)
    return fri3 - timedelta(days=4) <= d <= fri3


def h5(m1, D, vixp, A: pd.DataFrame) -> dict:
    cl = D[D.full].set_index("d").close
    prev_down = (cl.shift(1) < cl.shift(2))          # karar günü d için: d−1 kapanışı < d−2 kapanışı
    full = D[D.full].set_index("d")
    o16 = full.O16.where(full.O16.notna(), full.c1600)
    last_hr_down = (o16 / full.O15 - 1 < 0).shift(1)  # dünkü son saat aşağı
    res = {}

    def split(df, mask, col, name, pred_sign):
        out = {}
        for e in ("ESKI", "YENI"):
            g = df[df.era == e]
            mk = mask.reindex(g.index).fillna(False).astype(bool)
            a, b = g[mk][col], g[~mk][col]
            out[e] = {"acik": cell(a), "kapali": cell(b), "P_acik_gt_kapali": boot_diff(a, b)}
        dE = out["ESKI"]["acik"]["mean"] - out["ESKI"]["kapali"]["mean"]
        out["eski_ayni_isaret"] = bool(np.sign(dE) == pred_sign)
        res[name] = out

    orb = A[A.rule == "ORBVIX"]
    split(orb, orb.d.map(prev_down), "R", "NK-04 ORB × dün düşüş", +1)
    cap = A[A.rule == "CAPREV"]
    split(cap, cap.d.map(last_hr_down) & cap.pre_open.astype(bool), "R", "CK2-03 CAPREV × dün son saat aşağı ∧ 09:30 öncesi", +1)
    ks = A[A.rule == "KSG"]
    split(ks, ks.d.map(lambda d: vixp.get(d, 0) >= 25), "net_bp", "DB-02 KSG × dünkü VIX ≥ 25", +1)
    c3 = A[A.rule == "C3B"]
    split(c3, c3.d.map(opex_week), "net_bp", "TS-01 O4 C3b × vade haftası", -1)
    add = lib.to_frame(rules.c3b(m1, D, add_units=2))
    ex = add[add.unit >= 1]
    res["KT-01 A4 C3b ek birim"] = {e: cell(ex[ex.era == e].net_bp) for e in ("ESKI", "YENI")}
    res["KT-01 A4 C3b ek birim"]["eski_ayni_isaret"] = bool(res["KT-01 A4 C3b ek birim"]["ESKI"]["mean"] > 0)
    return res


def main() -> None:
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    A = pd.read_parquet(lib.RESULTS / "a_trades.parquet")
    book = A[A.rule.isin(LOTS)].reset_index(drop=True)
    out = {"H1": h1(A[A.rule == "ORBVIX"], D)}
    out["H2"] = h2(m1, book)
    out["H3"] = h3(m1, book, vixp)
    out["H4"] = h4(A[A.rule == "KSG"], D)
    out["H5"] = h5(m1, D, vixp, A)
    daily = book_daily(m1, book)
    daily.to_parquet(lib.RESULTS / "c_book_daily.parquet")
    st = book_stats(daily)
    for e, lo, hi in (("ESKI", date(2018, 1, 1), lib.ESKI_END), ("YENI", date(2021, 11, 1), date(2026, 12, 31))):
        sub = daily[(daily.d >= lo) & (daily.d <= hi)]
        st[e] = {k: v for k, v in book_stats(sub).items() if k != "yil"}
    st["acil_stop_degerdi"] = {r: int((A[A.rule == r].mae <= th).sum()) for r, th in EMERG.items()}
    st["acil_stop_en_yakin"] = {r: float(A[A.rule == r].mae.min()) for r in EMERG}
    # 4,5 lot tavanı: aynı anda açık NAS100 lotu (giriş/çıkış olay taraması)
    ev = sorted([(x.t_in, LOTS[x.rule]) for x in book.itertuples()] + [(x.t_out, -LOTS[x.rule]) for x in book.itertuples()])
    cur, mx, over = 0.0, 0.0, 0
    for _, dl in ev:
        cur += dl
        mx = max(mx, cur)
        over += cur > 4.5 + 1e-9
    st["en_yuksek_acik_lot"] = mx
    st["tavan_asim_olayi"] = int(over)
    out["H6"] = st
    (lib.RESULTS / "c_new.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
