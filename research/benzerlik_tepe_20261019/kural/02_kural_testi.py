"""ME-10 adım 2 — ön-kayıtlı kural testi (PROTOCOL.md; değiştirmeden uygular, BİR KEZ çalıştırılır).

Çalıştır: nice -n 10 python3.13 research/benzerlik_tepe_20261019/kural/02_kural_testi.py | tee results/02_stdout.txt
Çıktılar: results/02_hucreler.csv, results/02_olaylar.csv, results/02_sonuc.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tepe_ozellik import features, load_dax, load_ndx, query_index

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
W = 9
GAP = 10                 # bölüm ayırıcı (sorgu-günü)
RUN_N = 2                # tamamlanma: ≥ 2 gün yandıktan sonra söndü
MIN_CELL = 10
B = 10_000
NPLAC = 2_000
DEV_END = pd.Timestamp("2025-11-30 23:00", tz="UTC")
HO_START = pd.Timestamp("2025-12-01", tz="UTC")
TPL_START = pd.Timestamp("2026-07-06", tz="UTC")
TPL_END = pd.Timestamp("2026-08-20 23:59", tz="UTC")
P_BASIC, P_STRONG = 0.975, 1 - 0.025 / 18
TEMPL_END = {"T1_incel": "2026-07-17", "T1_kullanici": "2026-07-21", "T2": "2026-07-29", "T3": "2026-08-20"}
FROZEN = {
    "K1": {"pos": ("<=", 0.222), "net_s": ("<=", -1.524), "dist60_s": (">=", -4.827), "rv_ratio": (">=", 0.742),
           "swings": (">=", 3), "eff": ("<=", 0.129)},
    "K2": {"pos": ("<=", 0.222), "net_s": ("<=", -3.901), "dist60_s": (">=", -4.827), "rv_ratio": (">=", 1.115),
           "swings": (">=", 6), "eff": ("<=", 0.129), "lh": (">=", 1)},
    "K3": {"pos": ("<=", 0.222), "net_s": ("<=", -1.524), "rv_ratio": (">=", 0.742), "swings": (">=", 3),
           "eff": ("<=", 0.129)},
}
rng = np.random.default_rng(20261019)


# ───────────────────────── yardımcılar ─────────────────────────
def rule(f: pd.DataFrame, spec: dict) -> np.ndarray:
    m = np.ones(len(f), bool)
    for col, (op, thr) in spec.items():
        x = f[col].to_numpy(dtype=float)
        m &= np.isfinite(x) & ((x <= thr) if op == "<=" else (x >= thr))
    return m


def episodes_first(days: np.ndarray) -> np.ndarray:
    """days: artan k indeksleri → her kümenin (aralık ≤ GAP) ilk elemanı."""
    if len(days) == 0:
        return days
    keep = np.r_[True, np.diff(days) > GAP]
    return days[keep]


def events(fire: np.ndarray) -> dict:
    k = np.arange(len(fire))
    form = episodes_first(np.flatnonzero(fire))
    sig = np.zeros(len(fire), bool)
    sig[RUN_N:] = ~fire[RUN_N:]
    for j in range(1, RUN_N + 1):
        sig[RUN_N:] &= fire[RUN_N - j:len(fire) - j]
    comp = episodes_first(k[sig])
    return {"olusum": form, "tamamlanma": comp, "yanan_gun": np.flatnonzero(fire)}


def mboot_pos(diff: np.ndarray, month: np.ndarray) -> float:
    ok = np.isfinite(diff); diff, month = diff[ok], month[ok]
    if len(diff) < 5:
        return np.nan
    u, inv = np.unique(month, return_inverse=True); S = np.bincount(inv, diff); N = np.bincount(inv)
    i = rng.integers(0, len(u), size=(B, len(u)))
    return float(((S[i].sum(1) / N[i].sum(1)) > 0).mean())


def derive_k1(f: pd.DataFrame, kt: dict[str, int], names: tuple[str, ...]) -> dict:
    """Aynı yöntem: adlandırılmış şablonlarda her özelliğin en gevşek değeri, 3 ondalığa dışa yuvarlanmış."""
    v = {c: [float(f[c].iloc[kt[nm]]) for nm in names] for c in ("pos", "net_s", "dist60_s", "rv_ratio", "swings", "eff")}
    up = lambda x: np.ceil(x * 1000) / 1000  # noqa: E731
    dn = lambda x: np.floor(x * 1000) / 1000  # noqa: E731
    return {"pos": ("<=", up(max(v["pos"]))), "net_s": ("<=", up(max(v["net_s"]))),
            "dist60_s": (">=", dn(min(v["dist60_s"]))), "rv_ratio": (">=", dn(min(v["rv_ratio"]))),
            "swings": (">=", min(v["swings"])), "eff": ("<=", up(max(v["eff"])))}


class Market:
    """Bir piyasanın sorgu günleri, özellikleri, ufuk sonuçları ve eşli taban hücreleri."""

    def __init__(self, name: str, d: pd.DataFrame, hour: int, day_based: bool, halves: tuple[str, str]):
        self.name = name; self.d = d; self.Q = query_index(d, hour); self.day_based = day_based
        self.c = np.log(d.close.to_numpy()); self.n = len(d)
        self.f = features(d, self.Q, W)
        self.ts = pd.Series(self.f.ts.to_numpy())
        self.month = self.ts.dt.strftime("%Y-%m").to_numpy()
        self.valid = self.f.rv_ratio.notna().to_numpy() & self.f.sref.notna().to_numpy()
        self.dev = self.valid & (self.ts <= DEV_END).to_numpy()
        self.h1 = (self.ts < pd.Timestamp(halves[1], tz="UTC")).to_numpy()
        self.halves = halves
        self.H = {"1s": ("bar", 1), "1g": ("day", 1) if day_based else ("bar", 24), "5g": ("day", 5) if day_based else ("bar", 120)}
        self.r, self.endts = {}, {}
        for hn, (kind, h) in self.H.items():
            K = len(self.Q); r = np.full(K, np.nan); e = pd.Series(pd.NaT, index=range(K), dtype="datetime64[ns, UTC]")
            if kind == "bar":
                ok = self.Q + h < self.n; ei = self.Q[ok] + h
                r[ok] = self.c[ei] - self.c[self.Q[ok]]; e[ok] = d.ts.iloc[ei].to_numpy()
            else:
                ok = np.arange(K) + h < K; ei = self.Q[np.flatnonzero(ok) + h]
                r[ok] = self.c[ei] - self.c[self.Q[ok]]; e[ok] = d.ts.iloc[ei].to_numpy()
            self.r[hn] = r; self.endts[hn] = e
        fd = self.f[self.dev]
        self.e_net = np.nanpercentile(fd.net, np.linspace(0, 100, 11))
        self.e_rv = np.nanpercentile(fd.rv, np.linspace(0, 100, 11))
        self.bi = np.clip(np.searchsorted(self.e_net, self.f.net.to_numpy(), side="right") - 1, 0, 9)
        self.bj = np.clip(np.searchsorted(self.e_rv, self.f.rv.to_numpy(), side="right") - 1, 0, 9)

    def dev_ok(self, hn: str) -> np.ndarray:
        return self.dev & np.isfinite(self.r[hn]) & (self.endts[hn] <= DEV_END).to_numpy()

    def base(self, hn: str, fire: np.ndarray) -> np.ndarray:
        """Her gün için eşli taban (geliştirme hücre ortalaması, kontrol = t, t−1, t−2'de yanmayan)."""
        quiet = ~fire.copy()
        quiet[1:] &= ~fire[:-1]; quiet[2:] &= ~fire[:-2]
        ctrl = self.dev_ok(hn) & quiet
        S = np.zeros((10, 10)); N = np.zeros((10, 10))
        np.add.at(S, (self.bi[ctrl], self.bj[ctrl]), self.r[hn][ctrl]); np.add.at(N, (self.bi[ctrl], self.bj[ctrl]), 1)
        tab = np.full((10, 10), np.nan)
        for i in range(10):
            for j in range(10):
                for w in range(10):
                    a, b = max(0, i - w), min(9, i + w)
                    if N[a:b + 1, j].sum() >= MIN_CELL:
                        tab[i, j] = S[a:b + 1, j].sum() / N[a:b + 1, j].sum(); break
        return tab[self.bi, self.bj]


def cell_stats(mk: Market, ev: np.ndarray, hn: str, base: np.ndarray, period: str) -> dict:
    r = mk.r[hn]
    if period == "gelistirme":
        okm = mk.dev_ok(hn)
    else:
        e = mk.endts[hn]
        okm = mk.valid & np.isfinite(r) & (mk.ts >= HO_START).to_numpy()
        if mk.name == "NDX":  # şablon çakışması: pencere başı ≤ şablon sonu ve ufuk sonu ≥ şablon başı
            wstart = pd.Series(mk.d.ts.iloc[mk.Q[np.clip(np.arange(len(mk.Q)) - W, 0, None)] + 1].to_numpy())
            okm &= ~((wstart <= TPL_END).to_numpy() & (e >= TPL_START).to_numpy())
    ev = ev[okm[ev]]
    allm = r[okm]
    out = {"n_olay": int(len(ev))}
    if len(ev) == 0:
        return out
    x = r[ev]; dif = x - base[ev]; dall = x - np.nanmean(allm)
    out |= {"ort_bp": 1e4 * np.nanmean(x), "medyan_bp": 1e4 * np.nanmedian(x), "negatif_pay_%": 100 * np.mean(x < 0),
            "tum_gun_ort_bp": 1e4 * np.nanmean(allm),
            "fark_kosulsuz_bp": 1e4 * np.nanmean(dall), "fark_esli_bp": 1e4 * np.nanmean(dif),
            "fark_esli_medyan_bp": 1e4 * np.nanmedian(dif), "fark_esli_negatif_pay_%": 100 * np.mean(dif < 0),
            "fark_esli_enkotu_haric_bp": 1e4 * np.mean(np.sort(dif)[1:]) if len(dif) > 1 else np.nan,
            "fark_esli_eniyi_haric_bp": 1e4 * np.mean(np.sort(dif)[:-1]) if len(dif) > 1 else np.nan,
            "sd_fark_bp": 1e4 * np.nanstd(dif, ddof=1) if len(dif) > 1 else np.nan}
    if period == "gelistirme":
        p_pos = mboot_pos(dif, mk.month[ev]); p_pos_all = mboot_pos(dall, mk.month[ev])
        out |= {"P_fark>0": p_pos, "P_fark<0": 1 - p_pos if np.isfinite(p_pos) else np.nan,
                "P_kosulsuz>0": p_pos_all}
        for nm, hm in (("yari1", mk.h1), ("yari2", ~mk.h1)):
            s = ev[hm[ev]]
            out[f"fark_esli_{nm}_bp"] = 1e4 * np.nanmean(r[s] - base[s]) if len(s) else np.nan
            out[f"n_{nm}"] = int(len(s))
        # plasebo: olay göstergesini geliştirme sorgu dizisinde dairesel kaydır
        pos_idx = np.flatnonzero(okm); D = r[pos_idx] - base[pos_idx]; N = len(pos_idx)
        evpos = np.searchsorted(pos_idx, ev)
        okD = np.isfinite(D)
        shifts = rng.integers(60, N - 60, size=NPLAC)
        pl = np.array([np.nanmean(np.where(okD[(evpos + s) % N], D[(evpos + s) % N], np.nan)) for s in shifts])
        act = np.nanmean(dif)
        out["plasebo_yuzdelik_%"] = 100 * float(np.mean(pl <= act))
        out["plasebo_ort_bp"] = 1e4 * float(np.mean(pl)); out["plasebo_sd_bp"] = 1e4 * float(np.std(pl))
    else:
        out["olay_tarihleri"] = ";".join(str(mk.ts.iloc[i].date()) for i in ev)
        out["olay_r_bp"] = ";".join(f"{1e4 * r[i]:.0f}" for i in ev)
    return out


def verdict(row: dict, dax: dict | None) -> str:
    v = []
    for sgn, nm in ((-1, "H1(<0)"), (+1, "H2(>0)")):
        p = row.get("P_fark<0") if sgn < 0 else row.get("P_fark>0")
        if p is None or not np.isfinite(p):
            continue
        same = lambda x: np.isfinite(x) and np.sign(x) == sgn  # noqa: E731
        ok = (p >= P_BASIC and same(row["fark_esli_yari1_bp"]) and same(row["fark_esli_yari2_bp"])
              and row["n_olay"] >= 20 and same(row["fark_esli_medyan_bp"])
              and ((row["fark_esli_negatif_pay_%"] >= 50) if sgn < 0 else (row["fark_esli_negatif_pay_%"] <= 50))
              and same(row["fark_esli_enkotu_haric_bp"] if sgn < 0 else row["fark_esli_eniyi_haric_bp"]))
        if ok:
            strong = (p >= P_STRONG and ((row["plasebo_yuzdelik_%"] <= 5) if sgn < 0 else (row["plasebo_yuzdelik_%"] >= 95))
                      and dax is not None and same(dax.get("fark_esli_bp", np.nan))
                      and (dax.get("P_fark<0" if sgn < 0 else "P_fark>0", 0) >= 0.95))
            v.append(nm + (" GÜÇLÜ" if strong else " GEÇTİ"))
        elif p >= P_BASIC:
            v.append(nm + " P-yalnız")
    return ",".join(v) if v else "-"


def describe_fire(mk: Market, fire: np.ndarray) -> dict:
    dv = mk.dev
    ev = events(fire)
    yrs = (mk.ts[dv].iloc[-1] - mk.ts[dv].iloc[0]).days / 365.25
    form_dev = ev["olusum"][dv[ev["olusum"]]]; comp_dev = ev["tamamlanma"][dv[ev["tamamlanma"]]]
    return {"yanan_gun_payi_%": round(100 * float(fire[dv].mean()), 2), "gelistirme_yil": round(yrs, 2),
            "olusum_bolum": int(len(form_dev)), "tamamlanma_olay": int(len(comp_dev)),
            "yilda_bolum": round(len(form_dev) / yrs, 2),
            "bolum_basina_yanan_gun_medyan": float(np.median(np.diff(np.r_[np.flatnonzero(np.r_[True, np.diff(ev['yanan_gun']) > GAP]), len(ev['yanan_gun'])]))) if len(ev["yanan_gun"]) else np.nan}


def main() -> None:
    nd = Market("NDX", load_ndx(), 20, False, ("2016-01-01", "2021-01-01"))
    dx = Market("DAX", load_dax(), 19, True, ("2020-01-01", "2023-01-01"))
    qd = pd.Series(nd.ts.dt.date.to_numpy())
    kt = {nm: int(np.flatnonzero((qd == pd.Timestamp(v).date()).to_numpy())[0]) for nm, v in TEMPL_END.items()}
    res: dict = {"W": W, "ndx_son_bar": str(nd.d.ts.iloc[-1]), "dax_son_bar": str(dx.d.ts.iloc[-1])}
    # dondurulmuş K1 = yöntemle türetilen K1 (denetim)
    der = derive_k1(nd.f, kt, ("T1_incel", "T2", "T3"))
    assert all(abs(der[c][1] - FROZEN["K1"][c][1]) < 1e-9 for c in der), (der, FROZEN["K1"])
    rules = dict(FROZEN)
    sens = {"K1lit": derive_k1(nd.f, kt, ("T1_kullanici", "T2", "T3"))}
    res["kurallar"] = {k: {c: list(v) for c, v in s.items()} for k, s in {**rules, **sens}.items()}

    # ── tanımlayıcı: sıklık, şablonlar, 2026 yaz ──
    desc = {}
    for mk in (nd, dx):
        for rn, spec in {**rules, **sens}.items():
            fire = rule(mk.f, spec)
            dsc = describe_fire(mk, fire)
            if mk is nd:
                dsc["sablonlarda"] = {nm: bool(fire[k]) for nm, k in kt.items()}
                m26 = (mk.ts >= pd.Timestamp("2026-06-01", tz="UTC")).to_numpy()
                dsc["2026_06_sonrasi_yanan_gunler"] = [str(mk.ts.iloc[i].date()) for i in np.flatnonzero(fire & m26)]
                ev = events(fire)
                dsc["2026_olusum"] = [str(mk.ts.iloc[i].date()) for i in ev["olusum"] if mk.ts.iloc[i].year == 2026]
                dsc["2026_tamamlanma"] = [str(mk.ts.iloc[i].date()) for i in ev["tamamlanma"] if mk.ts.iloc[i].year == 2026]
            desc[f"{mk.name}_{rn}"] = dsc
    # W = 6 / 12 duyarlılık sıklığı (yöntemle yeniden türetilmiş K1)
    for Wx in (6, 12):
        fx = features(nd.d, nd.Q, Wx); spec = derive_k1(fx, kt, ("T1_incel", "T2", "T3"))
        fire = rule(fx, spec); dv = nd.dev
        evx = events(fire)
        desc[f"NDX_K1_W{Wx}"] = {"kural": {c: list(v) for c, v in spec.items()},
                                 "yanan_gun_payi_%": round(100 * float(fire[dv].mean()), 2),
                                 "olusum_bolum": int(dv[evx["olusum"]].sum()),
                                 "sablonlarda": {nm: bool(fire[k]) for nm, k in kt.items()}}
    res["tanimlayici"] = desc
    print(json.dumps(desc, ensure_ascii=False, indent=1, default=str))

    # ── sonuç hücreleri ──
    rows, evrows = [], []
    for rn, spec in {**rules, **sens}.items():
        for mk in (nd, dx):
            fire = rule(mk.f, spec); ev = events(fire)
            for hn in mk.H:
                base = mk.base(hn, fire)
                for et in ("olusum", "tamamlanma", "yanan_gun"):
                    for per in ("gelistirme", "dogrulama"):
                        st = cell_stats(mk, ev[et], hn, base, per)
                        rows.append({"piyasa": mk.name, "kural": rn, "olay": et, "ufuk": hn, "donem": per,
                                     "aile": rn in rules and et != "yanan_gun" and per == "gelistirme", **st})
                    if et != "yanan_gun":
                        okm = mk.dev_ok(hn) | ((mk.ts >= HO_START).to_numpy() & np.isfinite(mk.r[hn]) & mk.valid)
                        for i in ev[et][okm[ev[et]]]:
                            evrows.append({"piyasa": mk.name, "kural": rn, "olay": et, "ufuk": hn, "tarih": str(mk.ts.iloc[i].date()),
                                           "r_bp": 1e4 * mk.r[hn][i], "taban_bp": 1e4 * base[i],
                                           "fark_bp": 1e4 * (mk.r[hn][i] - base[i]), "net_s": mk.f.net_s.iloc[i],
                                           "pos": mk.f.pos.iloc[i], "dist60_s": mk.f.dist60_s.iloc[i],
                                           "rv_ratio": mk.f.rv_ratio.iloc[i], "gelistirme": bool(mk.dev_ok(hn)[i])})
    cdf = pd.DataFrame(rows)
    # karar (DAX eşini bağla)
    dax_lookup = {(r["kural"], r["olay"], r["ufuk"]): r for r in rows if r["piyasa"] == "DAX" and r["donem"] == "gelistirme"}
    cdf["karar"] = [verdict(r, dax_lookup.get((r["kural"], r["olay"], r["ufuk"])))
                    if (r["piyasa"] == "NDX" and r["donem"] == "gelistirme" and r["olay"] != "yanan_gun" and "P_fark<0" in r) else ""
                    for r in rows]
    cdf.to_csv(OUT / "02_hucreler.csv", index=False)
    pd.DataFrame(evrows).to_csv(OUT / "02_olaylar.csv", index=False)
    fam = cdf[cdf.aile & (cdf.piyasa == "NDX")]
    res["aile_ozeti"] = {"hucre": int(len(fam)), "P_fark<0>=0.975": int((fam["P_fark<0"] >= P_BASIC).sum()),
                         "P_fark>0>=0.975": int((fam["P_fark>0"] >= P_BASIC).sum()),
                         "gecen": fam.loc[fam.karar.str.contains("GEÇTİ|GÜÇLÜ"), ["kural", "olay", "ufuk", "karar"]].to_dict("records")}
    # güç (doğrulama): MDE80 = 2.80 × sd(geliştirme farkları)/√n
    pw = []
    for _, r in cdf[(cdf.donem == "dogrulama") & (cdf.olay != "yanan_gun")].iterrows():
        g = cdf[(cdf.piyasa == r.piyasa) & (cdf.kural == r.kural) & (cdf.olay == r.olay) & (cdf.ufuk == r.ufuk) & (cdf.donem == "gelistirme")]
        sd = float(g.sd_fark_bp.iloc[0]) if len(g) and np.isfinite(g.sd_fark_bp.iloc[0]) else np.nan
        pw.append({"piyasa": r.piyasa, "kural": r.kural, "olay": r.olay, "ufuk": r.ufuk, "n": int(r.n_olay),
                   "MDE80_bp": 2.80 * sd / np.sqrt(r.n_olay) if r.n_olay > 0 else np.inf})
    res["dogrulama_gucu"] = pw

    # ── bölüm içi yol (NDX geliştirme): oluşum → sonraki tamamlanma ──
    path = {}
    for rn, spec in rules.items():
        fire = rule(nd.f, spec); ev = events(fire)
        F, C = ev["olusum"], ev["tamamlanma"]
        pairs = []
        for j, a in enumerate(F):
            nxt = F[j + 1] if j + 1 < len(F) else len(fire)
            cc = C[(C > a) & (C < nxt)]
            if len(cc) and nd.dev[a] and nd.ts.iloc[cc[0]] <= DEV_END:
                pairs.append((int(cc[0] - a), 1e4 * (nd.c[nd.Q[cc[0]]] - nd.c[nd.Q[a]])))
        pa = np.array(pairs) if pairs else np.zeros((0, 2))
        path[rn] = {"eslesen_bolum": int(len(pa)), "sure_gun_medyan": float(np.median(pa[:, 0])) if len(pa) else np.nan,
                    "olusum_to_tamamlanma_bp_ort": float(pa[:, 1].mean()) if len(pa) else np.nan,
                    "olusum_to_tamamlanma_bp_medyan": float(np.median(pa[:, 1])) if len(pa) else np.nan,
                    "negatif_pay_%": float(100 * (pa[:, 1] < 0).mean()) if len(pa) else np.nan}
    res["bolum_ici_yol"] = path

    # ── bugün ──
    today = {}
    for mk, hour in ((nd, 20), (dx, 19)):
        last_bar = mk.n - 1
        Qx = mk.Q if mk.Q[-1] == last_bar else np.r_[mk.Q, last_bar]
        fx = features(mk.d, Qx, W)
        for lab, i in (("son_sorgu_gunu", len(mk.Q) - 1), ("son_bar", len(Qx) - 1)):
            row = fx.iloc[i]
            today[f"{mk.name}_{lab}"] = {"ts": str(row.ts), "kapanis": float(mk.d.close.iloc[Qx[i]]),
                                         **{c: round(float(row[c]), 3) for c in ("pos", "net_s", "dist60_s", "dist60_pct", "rv_ratio", "swings", "eff", "lh")},
                                         **{rn: bool(rule(fx.iloc[[i]], spec)[0]) for rn, spec in {**rules, **sens}.items()}}
        fire = rule(mk.f, rules["K1"]); last_fire = np.flatnonzero(fire)
        today[f"{mk.name}_K1_son_yanan_gun"] = str(mk.ts.iloc[last_fire[-1]].date()) if len(last_fire) else None
    res["bugun"] = today
    (OUT / "02_sonuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))

    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)
    show = ["piyasa", "kural", "olay", "ufuk", "n_olay", "ort_bp", "medyan_bp", "negatif_pay_%", "tum_gun_ort_bp", "fark_kosulsuz_bp",
            "fark_esli_bp", "fark_esli_medyan_bp", "fark_esli_negatif_pay_%", "fark_esli_enkotu_haric_bp", "fark_esli_eniyi_haric_bp",
            "P_fark<0", "P_fark>0", "fark_esli_yari1_bp", "fark_esli_yari2_bp", "n_yari1", "n_yari2", "plasebo_yuzdelik_%", "karar"]
    print("\n=== GELİŞTİRME ===")
    print(cdf[cdf.donem == "gelistirme"][show].round(3).to_string(index=False))
    print("\n=== DOĞRULAMA ===")
    print(cdf[cdf.donem == "dogrulama"][["piyasa", "kural", "olay", "ufuk", "n_olay", "ort_bp", "fark_esli_bp", "olay_tarihleri", "olay_r_bp"]].to_string(index=False))
    print(json.dumps({k: res[k] for k in ("aile_ozeti", "bolum_ici_yol", "bugun")}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
