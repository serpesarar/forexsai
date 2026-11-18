"""kurallar.py — olay, ana mum, kurulum durum makinesi, S1–S4 sinyalleri ve icra (PROTOCOL §2–3).

Sızıntı ilkesi: her karar yalnız `tend`'i karar anından önce/anında olan mumlarla verilir; giriş karar anından SONRA açılan ilk
yol barının açılışıdır; TP/SL yolu giriş barından başlar (giriş açılışta olduğundan barın uçları girişten sonradır).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date

import numpy as np
import pandas as pd

import veri  # noqa: F401  (sys.path: lib)
import lib
from veri import NY, PathBars

MAX_GAP_S = 4 * 86400          # girişte en çok bu kadar boşluk (hafta sonu + tatil)
CAP_S = 7 * 86400              # açık işlem hesap tavanı (PROTOCOL §2)


@dataclass(frozen=True)
class Cfg:
    thr: float = 0.50          # alt fitil eşiği (% fiyat)
    window: str = "L6"         # L6 | L14 | L3 | F3
    tol: float = 0.0003        # fiyatın %0,03'ü
    s1_hold_min: int = 30
    s1_tp: float = 0.0030
    s2_tp: float = 0.0018
    s2_first_only: bool = False
    s3_lvl: float = 0.48
    s3_tp_mode: str = "lvl"    # lvl: BB+0,25B | dist: giriş−0,25B
    s4_lvl: float = 0.50
    s4_tp_mode: str = "bb"     # bb | wick (ana mumun fitil dibi)
    s4_body: bool = False      # True: max(O,C) < L50
    uw_ratio: float | None = 0.5   # EK-1: üst fitil ≤ uw_ratio × alt fitil (None → sınırsız, v1)
    body_rule: bool = True     # EK-4: alt fitil ≥ gövde ("fitil yeterince uzun görünmeli" — kullanıcı etiketi, örnek 5)
    h4_check: bool = True      # EK-4: fitil dibini içeren MT5 H4 mumu (kullanıcının gördüğü) da uzun alt / kısa üst fitil (örnek 1)
    h4_body: bool = False      # H4'te gövde koşulu — kullanıcının 17 Kas örneğini elediği için ana kuralda YOK (varyant H4G)
    confirm: str = "MT5"       # MT5: broker mumu da kuralı sağlamalı | none | MT5_def: olayı broker mumu tanımlar
    name: str = "ANA"


@dataclass
class Signal:
    strat: str
    t_sig: int                 # karar anı (UTC)
    side: int
    sl: float | None
    tp: float | None           # mutlak seviye; None ise oranla (tp_ratio)
    tp_ratio: float | None
    setup: int
    sig_close: float           # sinyal mumunun kapanışı (iyimser icra)
    extra: dict = field(default_factory=dict)


# ═══════════════════════════ olay ve ana mum ═══════════════════════════

def rule_mask(b: pd.DataFrame, thr: float, uw_ratio: float | None, body_rule: bool) -> np.ndarray:
    """Olay kuralı: alt fitil ≥ thr (%), üst fitil ≤ uw_ratio × alt fitil, (G1) alt fitil ≥ gövde."""
    m = b.lw_pct.values >= thr
    if uw_ratio is not None:
        m &= b.uw_pct.values <= uw_ratio * b.lw_pct.values
    if body_rule:
        m &= b.lw_pct.values >= b.gv_pct.values
    return m


def events(b210: pd.DataFrame, thr: float, exclude_t: set[int] | None = None, uw_ratio: float | None = None,
           body_rule: bool = False, conf: pd.DataFrame | None = None, confirm: str = "none",
           q: pd.DataFrame | None = None, h4: pd.DataFrame | None = None, h4_body: bool = False) -> pd.DataFrame:
    """Olay mumları. conf = broker (MT5) 210m tablosu; confirm='MT5' → iki besleme de kuralı sağlamalı;
    'MT5_def' → olayı broker mumu tanımlar (yol beslemesinin mumu kuralı sağlamasa da)."""
    m = rule_mask(b210, thr, uw_ratio, body_rule)
    if conf is not None and confirm != "none":
        ok = set(conf.t.values[rule_mask(conf, thr, uw_ratio, body_rule)].astype(np.int64))
        in_ok = b210.t.isin(ok).values
        m = (m & in_ok) if confirm == "MT5" else in_ok
    e = b210[m].copy()
    if h4 is not None and q is not None and len(e):
        e = e[h4_view_ok(e, q, h4, thr, uw_ratio, h4_body)]
    if exclude_t:
        e = e[~e.t.isin(exclude_t)]
    return e.sort_values("tend").reset_index(drop=True)


def low_time(e: pd.DataFrame, q: pd.DataFrame) -> np.ndarray:
    """Her olayın 210m dibinin oluştuğu 15m mumun açılışı (UTC)."""
    lo = q.low.values
    out = np.empty(len(e), np.int64)
    for n, (a, b) in enumerate(zip(e.i_first.values, e.i_last.values)):
        out[n] = q.t.values[a + int(np.argmin(lo[a:b + 1]))]
    return out


def h4_view_ok(e: pd.DataFrame, q: pd.DataFrame, h4: pd.DataFrame, thr: float, uw_ratio: float | None,
               body_rule: bool) -> np.ndarray:
    """EK-2: fitil dibinin bulunduğu MT5 H4 mumu (kullanıcının grafiğinde gördüğü) da aynı kuralı sağlıyor mu."""
    import veri
    keys = veri.h4_key(low_time(e, q))
    ok_keys = set(h4.index[rule_mask(h4, thr, uw_ratio, body_rule)])
    return np.array([k in ok_keys for k in keys], bool)


def pick_main(q: pd.DataFrame, ev: pd.Series, window: str) -> tuple[int | None, int, str]:
    """Ana mumun 15m indeksi, kurulumun başladığı 15m indeksi ve durum (ok | ana_yok | eksik_15m).
    Pencere eksiksiz olmalı (EK-1): son-N penceresi nominal bitişe kadar N adet kesintisiz 15m; W14 son mum nominal bitişte."""
    i0, i1 = int(ev.i_first), int(ev.i_last)
    t = q.t.values
    if window == "F3":
        cand = np.arange(i1 + 1, min(i1 + 4, len(q)))
        start = i1 + 4
        ok = len(cand) == 3 and np.all(np.diff(t[cand]) == 900)
    else:
        nom_last = int(ev.t_end_nom) - 900
        allc = np.arange(i0, i1 + 1)
        if window == "L14":
            cand = allc
            ok = t[i1] == nom_last and np.all(np.diff(t[cand]) == 900)
        else:
            n = {"L6": 6, "L3": 3}[window]
            cand = allc[t[allc] > nom_last - n * 900]
            ok = len(cand) == n and t[i1] == nom_last and np.all(np.diff(t[cand]) == 900)
        start = i1 + 1
    if not ok:
        return None, start, "eksik_15m"
    o, c = q.open.values[cand], q.close.values[cand]
    body = np.where(c < o, o - c, -1.0)
    if body.max() <= 0:
        return None, start, "ana_yok"
    return int(cand[int(np.argmax(body))]), start, "ok"


# ═══════════════════════════ kurulum ve sinyaller ═══════════════════════════

def setup_signals(q: pd.DataFrame, ev: pd.DataFrame, cfg: Cfg) -> tuple[list[Signal], pd.DataFrame]:
    """Her olay bir kurulum; kurulum bölge dışı kapanışta veya sonraki olayın kapanışında biter."""
    O, H, L, C, TE = (q[k].values for k in ("open", "high", "low", "close", "tend"))
    sigs: list[Signal] = []
    rows = []
    pre = "start_pre" in ev.columns                                # canlı mum: ana mum + başlangıç önceden hesaplı
    nxt_start = (np.r_[ev.start_pre.values[1:], len(q)] if pre else np.r_[ev.i_last.values[1:] + 1, len(q)])
    for k, e in ev.iterrows():
        if pre:
            j_main = None if pd.isna(e.j_main_pre) else int(e.j_main_pre)
            start, durum = int(e.start_pre), ("ok" if j_main is not None else "ana_yok")
        else:
            j_main, start, durum = pick_main(q, e, cfg.window)
        row = {"setup": k, "t_ev": int(e.t), "tend_ev": int(e.tend), "slot": int(e.slot), "lw_pct": float(e.lw_pct),
               "uw_pct": float(e.uw_pct), "gv_pct": float(e.gv_pct), "j_main": j_main, "n_bar": 0, "bitis": durum}
        if j_main is None:
            rows.append(row)
            continue
        if cfg.window == "F3" and k + 1 < len(ev) and int(ev.i_last.iloc[k + 1]) < start:
            row["bitis"] = "yeni_olay_once"      # ana mum seçilirken yeni olay kapandı
            rows.append(row)
            continue
        BT, BB, LOW = O[j_main], C[j_main], L[j_main]
        B = BT - BB
        L25, L48, L50 = BB + 0.25 * B, BB + cfg.s3_lvl * B, BB + cfg.s4_lvl * B
        lo_z, hi_z = BB * (1 - cfg.tol), BT * (1 + cfg.tol)
        row.update({"BT": BT, "BB": BB, "B": B, "L50": L50, "bitis": "veri_sonu"})
        end = int(nxt_start[k])
        n = 0
        for j in range(start, end):
            c, h, o = C[j], H[j], O[j]
            if not (lo_z <= c <= hi_z):
                row["bitis"] = "bolge_disi"
                break
            n += 1
            ts = int(TE[j])
            if not cfg.s2_first_only or n == 1:
                sigs.append(Signal("S2", ts, +1, BB, None, cfg.s2_tp, k, c))
            if c > L48:
                tp3 = L25 if cfg.s3_tp_mode == "lvl" else None
                sigs.append(Signal("S3", ts, -1, BT, tp3, None, k, c, {"dist": 0.25 * B} if tp3 is None else {}))
            body_ok = (max(o, c) < L50) if cfg.s4_body else (c < L50)
            if h > L50 and body_ok and h > max(o, c):
                sigs.append(Signal("S4", ts, -1, BT, BB if cfg.s4_tp_mode == "bb" else LOW, None, k, c))
        else:
            if end < len(q):
                row["bitis"] = "yeni_olay"
        row["n_bar"] = n
        rows.append(row)
    return sigs, pd.DataFrame(rows)


def s1_signals(ev: pd.DataFrame, cfg: Cfg) -> list[Signal]:
    return [Signal("S1", int(e.tend), +1, None, None, cfg.s1_tp, k, float(e.close)) for k, e in ev.iterrows()]


# ═══════════════════════════ icra ═══════════════════════════

def _first_hit(mask: np.ndarray) -> int:
    k = int(np.argmax(mask))
    return k if mask[k] else -1


def walk(p: PathBars, i0: int, t_end: int, side: int, stop: float | None, tp: float | None) -> tuple[int, float, str, float]:
    """Vektörel yol: uzunda BID low ≤ stop / high ≥ tp; kısada ask high ≥ stop / ask low ≤ tp; aynı bar → stop.
    Zaman çıkışı t_end'de açılan barın açılışı (uzun bid, kısa ask)."""
    j_end = int(np.searchsorted(p.t, t_end))
    a, ref = i0, p.o[i0]
    chunk = 256
    mae = 0.0
    while a < j_end:
        b = min(j_end, a + chunk)
        lo, hi, sp, op = p.l[a:b], p.h[a:b], p.spr[a:b], p.o[a:b]
        if side > 0:
            hs = lo <= stop if stop is not None else np.zeros(b - a, bool)
            ht = hi >= tp if tp is not None else np.zeros(b - a, bool)
        else:
            hs = (hi + sp) >= stop if stop is not None else np.zeros(b - a, bool)
            ht = (lo + sp) <= tp if tp is not None else np.zeros(b - a, bool)
        k = _first_hit(hs | ht)
        seg = slice(0, k + 1) if k >= 0 else slice(0, b - a)
        mae = min(mae, float((lo[seg].min() / ref - 1) if side > 0 else -((hi[seg] + sp[seg]).max() / ref - 1)))
        if k >= 0:
            j = a + k
            if hs[k]:
                px = min(stop, op[k]) if side > 0 else max(stop, op[k] + sp[k])
                return j, px, "stop", mae
            px = max(tp, op[k]) if side > 0 else min(tp, op[k] + sp[k])
            return j, px, "tp", mae
        a = b
        chunk *= 4
    j = min(j_end, len(p.t) - 1)
    if j_end < len(p.t) and p.t[j_end] - t_end <= MAX_GAP_S:
        return j, (p.o[j] if side > 0 else p.o[j] + p.spr[j]), "time", mae
    j = j_end - 1
    return j, (p.c[j] if side > 0 else p.c[j] + p.spr[j]), "time", mae


def execute(p: PathBars, sigs: list[Signal], optimistic: bool = False, single: bool = True,
            tags: dict | None = None, s1_hold_min: int = 30) -> pd.DataFrame:
    """Sinyalleri strateji başına tek pozisyonla icra eder. optimistic: giriş = sinyal mumu kapanışı, spread yok."""
    pp = p.zero_spread() if optimistic else p
    out: list[lib.Trade] = []
    busy: dict[str, int] = {}
    skip = {"mesgul": 0, "bosluk": 0, "gecersiz": 0}
    for s in sorted(sigs, key=lambda x: (x.t_sig, x.strat)):
        if single and busy.get(s.strat, -1) > s.t_sig:
            skip["mesgul"] += 1
            continue
        i = int(np.searchsorted(pp.t, s.t_sig))
        if i >= len(pp.t) or pp.t[i] - s.t_sig > MAX_GAP_S:
            skip["bosluk"] += 1
            continue
        bid = s.sig_close if optimistic else pp.o[i]
        spi = pp.spr[i]
        px_in = bid + spi if s.side > 0 else bid
        if s.strat == "S1":
            tp, sl, t_end = px_in * (1 + s.tp_ratio), None, int(pp.t[i]) + s1_hold_min * 60
        else:
            sl = s.sl
            tp = px_in * (1 + s.tp_ratio) if s.tp_ratio is not None else (s.tp if s.tp is not None else bid - s.extra["dist"])
            t_end = int(pp.t[i]) + CAP_S
            if s.side > 0 and not (bid > sl and tp > px_in):
                skip["gecersiz"] += 1
                continue
            if s.side < 0 and not (bid + spi < sl and tp < bid):
                skip["gecersiz"] += 1
                continue
        j, px_out, why, mae = walk(pp, i, t_end, s.side, sl, tp)
        t_out = int(pp.t[j]) + (pp.step if why != "time" else 0)
        d = pd.Timestamp(int(pp.t[i]), unit="s", tz="UTC").tz_convert(NY).date()
        risk = abs(px_in - sl) if sl is not None else np.nan
        tr = lib.Trade(s.strat, d, int(pp.t[i]), t_out, s.side, px_in, px_out, risk=risk, spr_in=spi,
                       spr_out=pp.spr[j], mae=mae, why=why, tags={"setup": s.setup, "t_sig": s.t_sig, **(tags or {})})
        out.append(tr)
        busy[s.strat] = t_out
    df = lib.to_frame(out)
    df.attrs["skip"] = skip
    return df


def run(p: PathBars, q: pd.DataFrame, b210: pd.DataFrame, cfg: Cfg, exclude_t: set[int] | None = None,
        ev: pd.DataFrame | None = None, optimistic: bool = False, with_s1: bool = True,
        conf: pd.DataFrame | None = None, h4: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tek konfigürasyon: olaylar → kurulumlar → sinyaller → işlemler. Döner (işlemler, kurulumlar)."""
    if ev is None:
        ev = events(b210, cfg.thr, exclude_t, cfg.uw_ratio, cfg.body_rule, conf, cfg.confirm if conf is not None else "none",
                    q, h4 if cfg.h4_check else None, cfg.h4_body)
    sigs, setups = setup_signals(q, ev, cfg)
    if with_s1:
        sigs += s1_signals(ev, cfg)
    tr = execute(p, sigs, optimistic=optimistic, s1_hold_min=cfg.s1_hold_min, tags={"cfg": cfg.name})
    if not tr.empty:
        tr["slot"] = ev.slot.values[tr.setup.values]
    tr.attrs["n_ev"] = len(ev)
    return tr, setups


def variants() -> list[Cfg]:
    base = Cfg()
    return [base,
            replace(base, window="L14", name="W14"), replace(base, window="L3", name="W3"), replace(base, window="F3", name="F3"),
            replace(base, thr=0.40, name="T40"), replace(base, thr=0.75, name="T75"), replace(base, thr=1.00, name="T100"),
            replace(base, s3_tp_mode="dist", name="S3d"), replace(base, s4_tp_mode="wick", name="S4w"),
            replace(base, s4_body=True, name="S4g"), replace(base, s2_first_only=True, name="S2f"),
            replace(base, s1_hold_min=15, name="S1h15"), replace(base, s1_hold_min=60, name="S1h60"),
            replace(base, s1_tp=0.0020, name="S1tp20"), replace(base, s1_tp=0.0050, name="S1tp50"),
            replace(base, tol=0.0, name="NOTOL"),
            replace(base, uw_ratio=1.0, name="U1"), replace(base, uw_ratio=1 / 3, name="U3"),
            replace(base, body_rule=False, h4_check=False, name="E1"),
            replace(base, h4_check=False, name="G1"), replace(base, body_rule=False, name="H4"),
            replace(base, h4_body=True, name="H4G"), replace(base, confirm="none", name="DT"),
            replace(base, confirm="MT5_def", name="MD"),
            replace(base, uw_ratio=None, body_rule=False, h4_check=False, confirm="none", name="v1")]


def entry_date(t: int) -> date:
    return pd.Timestamp(t, unit="s", tz="UTC").tz_convert(NY).date()
