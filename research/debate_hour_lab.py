"""Debate-hour ceiling lab — hangi KARAR SAATİ en çok edge barındırıyor?

Soru (kullanıcı, 2026-07-26): "ajan tartışmasını NY 09:45 yerine Asya/Çin
açılışında ya da 01:00/03:00'te koştursak daha mı iyi olur?"

Bunu canlı LLM koşusuyla test etmek imkânsız: sembol başına günde 1 koşu,
~%60 çekimserlik → tek bir saat dilimi için n=30 yönlü çağrıya ~5 ay gerekir.
5 aday saat × 4 sembol = yıllar + binlerce dolar token.

Bunun yerine TAVANI ölçüyoruz: bir tartışma o saatte en fazla ne yakalayabilir?
    tavan = (o saatten sonraki hareketin büyüklüğü)
          × (yönün, o an MEVCUT sızıntısız bilgiden öngörülebilirliği)
LLM bu tavanın üstüne çıkamaz — o saatte bilgi yoksa hiçbir ajan üretemez.

KRİTİK AYRIM — "beceri" vs "sürüklenme"
    always_long bir saatte %65 tutuyorsa bu TARTIŞMA gerektirmez; sabit yönlü
    bias yeter. Tartışmanın değeri ancak KOŞULLU okumanın sabit yönü GEÇTİĞİ
    kadardır. Bu yüzden skor = koşullu kural WR − en iyi sabit yön WR.
    (Sabit yön de train'de seçilir; ikisi de aynı test setinde raporlanır.)

Veri
    yfinance 1h, ~730 gün. Vekiller: NQ=F→NDX, GC=F→XAUUSD, CL=F→USOIL
    (vadeliler 24 saat işlem görür → Asya/Çin/Londra saatleri ölçülebilir),
    ^GDAXI→DAX (yalnız nakit seans, 07-16 UTC — DAX'ın işlem penceresi zaten bu).
    NOT: candle_cache 1h bu iş için KULLANILAMAZ — kapsama delikli (NDX'te
    US seansı saatleri ~133 bar, diğerleri ~76) ve saatler arası kıyası bozar.

Sızıntı ve aşırı-uyum korumaları
    * Tüm özellikler karar barının kapanışı ve öncesinden.
    * Bar ızgarası tam saatlik reindex edilir → shift(4) gerçekten 4 saat
      öncesidir; boşluklu günlerde gün atlayıp uydurma momentum üretmez.
    * Kural ve sabit-yön seçimi kronolojik train (ilk %60); rapor test (son %40).
    * 24 saat × 4 ufuk × 6 kural taranıyor → PLASEBO: ileri getiriler
      karıştırılıp aynı seçim prosedürü koşulur; gerçek zirve, plasebo
      dağılımının p95'ini geçmezse BULGU YOK sayılır.

Çıktı: backend/data/debate_hour_report.md
"""
from __future__ import annotations

import os
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# vekil → gerçek sembol (vadeliler 24h işlem gördüğü için saat çalışmasına uygun)
#: (sembol, vekil, not, max_gap_h). ``max_gap_h`` = bir özelliğin/hedefin
#: kapsamasına izin verilen en uzun duvar-saati aralığı. 24h vadelilerde 8 saat
#: (hafta sonu boşluğunu eler); DAX nakitte 30 saat — çünkü seans 07-16 UTC ve
#: sabah 08:00'de "son 4 bar" zorunlu olarak geceyi kapsar (bu gerçek bilgidir:
#: dünkü kapanış → bugünkü açılış gap'i).
PROXIES = [
    ("NDX.INDX",    "NQ=F",   "NASDAQ 100 vadeli", 8),
    ("GDAXI.INDX",  "^GDAXI", "DAX nakit (yalnız 07-16 UTC seansı)", 30),
    ("XAUUSD",      "GC=F",   "Altın vadeli", 8),
    ("USOIL.FOREX", "CL=F",   "WTI vadeli", 8),
]

HORIZONS_H = [1, 2, 4, 6]
TRAIN_FRAC = 0.60
MIN_FIRE_TRAIN = 40      # kuralın train'de ateşlediği örnek tabanı
MIN_FIRE_TEST = 30       # kuralın test'te ateşlediği örnek tabanı
MIN_HOUR_BARS = 120      # saat dilimi toplam bar tabanı
PLACEBO_ROUNDS = 150
RNG = np.random.default_rng(20260726)

HOUR_LABELS = {
    0: "Asya erken", 1: "Çin/HK açılış", 2: "Asya öğle", 3: "Asya öğleden sonra",
    4: "Asya geç", 5: "Tokyo kapanışa", 6: "Tokyo kapanış", 7: "Frankfurt ön",
    8: "Londra/DAX açılış", 9: "Londra sabah", 10: "Londra sabah",
    11: "Londra öğle", 12: "NY ön-piyasa", 13: "NY açılış (13:30)",
    14: "NY ilk saat", 15: "NY öğle", 16: "NY öğleden sonra",
    17: "Londra kapanış", 18: "NY geç", 19: "NY kapanışa", 20: "NY kapanış",
    21: "kapanış sonrası", 22: "Asya öncesi", 23: "Asya öncesi",
}


# ── veri ─────────────────────────────────────────────────────────────────────
def fetch_1h(ticker: str) -> pd.DataFrame:
    import yfinance as yf
    d = yf.Ticker(ticker).history(period="730d", interval="1h")
    if d.empty:
        return pd.DataFrame()
    d = d.rename(columns=str.lower)[["open", "high", "low", "close"]]
    d.index = d.index.tz_convert("UTC")
    d = d[~d.index.duplicated(keep="first")].sort_index()
    return d[d["close"].notna()]


def build_features(d: pd.DataFrame, max_gap_h: int) -> pd.DataFrame:
    """Sıkıştırılmış (boşluksuz) bar serisi üzerinde özellik üret.

    Rolling göstergeler "son N mevcut bar"ı kullanır — canlıda gösterge zaten
    böyle hesaplanır. Ama shift-tabanlı momentum ve ileri getiriler duvar-saati
    açısından kontrol edilir: geri/ileri bakış ``max_gap_h``ı aşıyorsa (hafta
    sonu, tatil, veri deliği) o satır GEÇERSİZ sayılır — yoksa "4 saatlik
    momentum" sessizce 3 günlük harekete dönüşür.
    """
    c = d["close"]
    f = pd.DataFrame(index=d.index)
    f["close"] = c
    t = pd.Series(d.index, index=d.index)
    span_back = {k: (t - t.shift(k)).dt.total_seconds() / 3600 for k in (1, 4, 8, 24)}
    span_fwd = {h: (t.shift(-h) - t).dt.total_seconds() / 3600 for h in HORIZONS_H}
    for k, col in ((1, "mom_1h"), (4, "mom_4h"), (8, "mom_8h"), (24, "mom_24h")):
        v = c.pct_change(k) * 100
        # k bar geriye bakış k*max_gap_h/4'ü aşarsa boşluk yutmuş demektir
        f[col] = v.where(span_back[k] <= max_gap_h * max(1, k / 4))
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    f["ema_state"] = np.sign(c - ema20)
    f["trend_state"] = np.sign(ema20 - ema50)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - c.shift()).abs(),
                    (d["low"] - c.shift()).abs()], axis=1).max(axis=1)
    f["atr_pct"] = (tr.rolling(14).mean() / c) * 100
    hi, lo = d["high"].rolling(24).max(), d["low"].rolling(24).min()
    f["range_pos"] = (c - lo) / (hi - lo).replace(0, np.nan)
    # İLERİ pencere guard'ı GERİ'den ayrı ve SIKI: hedef, karar anından sonraki
    # h saatlik gerçek hareket olmalı. Gevşek bırakılırsa DAX'ta 14:00 UTC'nin
    # "4 saatlik hareketi" seans kapanışını atlayıp ertesi sabaha uzanır ve geç
    # seans saatleri sahte biçimde en hareketli görünür. Seans içinde h saat
    # kalmamışsa o satır hedefsizdir — bu da başlı başına bilgidir.
    for h in HORIZONS_H:
        v = (c.shift(-h) / c - 1) * 100
        f[f"fwd_{h}h"] = v.where(span_fwd[h] <= h * 1.5 + 1)
    f["hour"] = f.index.hour
    f["date"] = f.index.date

    # seans zinciri — tartışmanın gerçekte okuduğu girdiler.
    # Sızıntı guard'ı: pencere karar saatinden ÖNCE kapanmış olmalı.
    piv = f.pivot_table(index="date", columns="hour", values="close", aggfunc="last")
    for name, (h0, h1) in {"asia": (0, 6), "london": (7, 12)}.items():
        if h0 in piv.columns and h1 in piv.columns:
            leg = (piv[h1] / piv[h0] - 1) * 100
            # .map ile hizala — merge DatetimeIndex'i düşürür
            f[name] = f["date"].map(leg)
            f.loc[f["hour"] <= h1, name] = np.nan     # henüz kapanmadı → görünmez
        else:
            f[name] = np.nan
    return f


# ── aday kurallar ────────────────────────────────────────────────────────────
CONDITIONAL = {
    "momentum_4h": lambda r: np.sign(r["mom_4h"]),
    "reversal_4h": lambda r: -np.sign(r["mom_4h"]),
    "trend_ema":   lambda r: r["trend_state"].to_numpy(dtype=float),
    "range_fade":  lambda r: np.where(r["range_pos"] > 0.8, -1.0,
                             np.where(r["range_pos"] < 0.2, 1.0, 0.0)),
    "follow_asia":   lambda r: np.sign(r["asia"].to_numpy(dtype=float)),
    "follow_london": lambda r: np.sign(r["london"].to_numpy(dtype=float)),
}
CONSTANT = {
    "always_long":  lambda r: np.ones(len(r)),
    "always_short": lambda r: -np.ones(len(r)),
}


def _wr(sig, fwd) -> tuple[float, int]:
    sig = np.nan_to_num(np.asarray(sig, dtype=float), nan=0.0)
    fwd = np.asarray(fwd, dtype=float)
    m = (sig != 0) & ~np.isnan(fwd)
    if m.sum() == 0:
        return float("nan"), 0
    return float((np.sign(fwd[m]) == sig[m]).mean() * 100), int(m.sum())


def _pick(rules: dict, sub_tr, sub_te, fwd_tr, fwd_te,
          min_tr: int, min_te: int) -> dict | None:
    """Train'de en iyi kuralı seç, TEST sonucunu döndür (seçim testi görmez)."""
    best = None
    for name, fn in rules.items():
        wr_tr, n_tr = _wr(fn(sub_tr), fwd_tr)
        if n_tr < min_tr or np.isnan(wr_tr):
            continue
        if best is None or wr_tr > best["wr_train"]:
            wr_te, n_te = _wr(fn(sub_te), fwd_te)
            if n_te < min_te or np.isnan(wr_te):
                continue
            best = {"rule": name, "wr_train": wr_tr,
                    "wr_test": wr_te, "n_test": n_te}
    return best


def _scan(f: pd.DataFrame, cut, shuffled: bool = False) -> list[dict]:
    """Her saat için: sabit-yön tabanı vs koşullu kural → beceri farkı."""
    rows = []
    for hour in range(24):
        sub = f[f["hour"] == hour].dropna(subset=["mom_4h", "atr_pct", "range_pos"])
        if len(sub) < MIN_HOUR_BARS:
            continue
        tr, te = sub[sub.index <= cut], sub[sub.index > cut]
        if len(te) < MIN_FIRE_TEST:
            continue
        best = None
        for h in HORIZONS_H:
            ftr, fte = tr[f"fwd_{h}h"].to_numpy(float), te[f"fwd_{h}h"].to_numpy(float)
            cond = _pick(CONDITIONAL, tr, te, ftr, fte, MIN_FIRE_TRAIN, MIN_FIRE_TEST)
            base = _pick(CONSTANT, tr, te, ftr, fte, MIN_FIRE_TRAIN, MIN_FIRE_TEST)
            if cond is None or base is None:
                continue
            skill = cond["wr_test"] - base["wr_test"]
            if best is None or skill > best["skill"]:
                best = {"horizon_h": h, "skill": skill,
                        "rule": cond["rule"], "wr_cond": cond["wr_test"],
                        "n_cond": cond["n_test"],
                        "base_rule": base["rule"], "wr_base": base["wr_test"]}
        if best is None:
            continue
        if shuffled:
            rows.append(best)
            continue
        f4 = te["fwd_4h"].to_numpy(float)
        atr = te["atr_pct"].to_numpy(float)
        best.update({
            "hour": hour, "n_hour_test": len(te),
            "move_pct": float(np.nanmedian(np.abs(f4))),
            "move_atr": float(np.nanmedian(np.abs(f4 / np.where(atr == 0, np.nan, atr)))),
            "p_up": float(np.nanmean(f4 > 0) * 100),
        })
        rows.append(best)
    return rows


#: Şu anki canlı tartışma pencereleri (UTC saat) — bkz. BIAS_RUN_WINDOWS_ET /
#: BIAS_SYMBOL_RUNS_UTC. NDX ET pencereleri yaz saatinde 12:00 ve 13:45 UTC.
CURRENT_SCHEDULE = {
    "NDX.INDX": [12, 13], "GDAXI.INDX": [8], "XAUUSD": [8], "USOIL.FOREX": [13],
}


def movement_profile(f: pd.DataFrame) -> list[dict]:
    """Saat başına ileri hareket büyüklüğü — plasebo gerektirmeyen betimsel
    istatistik. "Karar verilecek saatte önümüzde ne kadar yol var?" sorusu.

    Yön öngörülebilirliği gürültü çıksa bile bu gerçek: 4 saatlik yönlü bir
    karar, önünde 4 saatlik oynaklık kalmayan bir saatte verilirse tanım gereği
    işe yaramaz.
    """
    rows = []
    for hour in range(24):
        sub = f[f["hour"] == hour].dropna(subset=["fwd_4h", "atr_pct"])
        if len(sub) < MIN_HOUR_BARS:
            continue
        f4 = sub["fwd_4h"].to_numpy(float)
        atr = sub["atr_pct"].to_numpy(float)
        rows.append({
            "hour": hour, "n": len(sub),
            "move_atr": float(np.nanmedian(np.abs(f4 / np.where(atr == 0, np.nan, atr)))),
            "move_pct": float(np.nanmedian(np.abs(f4))),
            "p_up": float(np.nanmean(f4 > 0) * 100),
        })
    return rows


def analyse(symbol: str, ticker: str, note: str, max_gap_h: int) -> dict:
    d = fetch_1h(ticker)
    if d.empty or len(d) < 1500:
        return {"symbol": symbol, "error": f"{ticker}: yetersiz veri"}
    f = build_features(d, max_gap_h)
    valid = f.dropna(subset=["mom_4h"])
    cut = valid.index[int(len(valid) * TRAIN_FRAC)]

    real = _scan(f, cut)
    if not real:
        return {"symbol": symbol, "error": "hiçbir saat taban örneklemi tutturamadı"}
    peak = max(r["skill"] for r in real)

    placebo = []
    for _ in range(PLACEBO_ROUNDS):
        g = f.copy()
        for h in HORIZONS_H:                     # gün-bağını kır, yapıyı koru
            v = g[f"fwd_{h}h"].to_numpy(float).copy()
            RNG.shuffle(v)
            g[f"fwd_{h}h"] = v
        rr = _scan(g, cut, shuffled=True)
        placebo.append(max((r["skill"] for r in rr), default=0.0))
    p95 = float(np.percentile(placebo, 95))

    return {"symbol": symbol, "ticker": ticker, "note": note,
            "span": f"{f.index[0].date()} → {f.index[-1].date()}",
            "n_bars": int(f["close"].notna().sum()), "cut": str(cut.date()),
            "hours": sorted(real, key=lambda r: -r["skill"]),
            "movement": movement_profile(f),
            "peak_skill": peak, "placebo_p95": p95,
            "beats_placebo": bool(peak > p95)}


def main() -> None:
    out = [f"# Tartışma Saati — Tavan Analizi ({datetime.now(timezone.utc):%Y-%m-%d})",
           "",
           "**Soru:** ajan tartışması hangi saatte koşulursa en çok edge yakalayabilir?",
           "",
           "**Skor = beceri:** koşullu kuralın test isabeti − en iyi SABİT yönün test",
           "isabeti. Sabit yön zaten tutuyorsa tartışmaya gerek yok; tartışmanın",
           "değeri sabit yönü geçtiği kadardır. Kural + sabit yön kronolojik train",
           f"(ilk %{int(TRAIN_FRAC*100)}) üzerinde seçilir, ikisi de test (son "
           f"%{int((1-TRAIN_FRAC)*100)}) üzerinde raporlanır.",
           "",
           f"**Plasebo:** {PLACEBO_ROUNDS} tur karıştırılmış ileri getiri, aynı seçim "
           "prosedürü. Gerçek zirve p95'i geçmezse saat seçimi gürültüdür.",
           ""]
    for symbol, ticker, note, max_gap_h in PROXIES:
        print(f"\n=== {symbol} ({ticker}) ===", flush=True)
        res = analyse(symbol, ticker, note, max_gap_h)
        if res.get("error"):
            print("  ", res["error"])
            out += [f"## {symbol}", f"- ⚠ {res['error']}", ""]
            continue
        verdict = ("✅ plaseboyu GEÇTİ" if res["beats_placebo"]
                   else "❌ plaseboyu GEÇEMEDİ — saat seçimi gürültü")
        print(f"  {res['span']} · {res['n_bars']} bar · zirve beceri "
              f"{res['peak_skill']:+.1f}pp vs plasebo p95 {res['placebo_p95']:+.1f}pp → {verdict}")
        out += [f"## {symbol} — vekil {ticker} ({note})",
                f"- Veri: {res['span']} · {res['n_bars']} adet 1h bar · train/test kesimi {res['cut']}",
                f"- **Zirve beceri {res['peak_skill']:+.1f}pp · plasebo p95 "
                f"{res['placebo_p95']:+.1f}pp → {verdict}**", "",
                "| UTC | Etiket | 4h hareket (ATR) | 4h hareket % | P(yukarı) | sabit taban | koşullu kural | ufuk | n | koşullu WR | **beceri** |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in res["hours"][:8]:
            out.append(
                f"| {r['hour']:02d}:00 | {HOUR_LABELS.get(r['hour'],'')} | {r['move_atr']:.2f} | "
                f"{r['move_pct']:.2f} | {r['p_up']:.0f}% | {r['base_rule']} {r['wr_base']:.0f}% | "
                f"{r['rule']} | +{r['horizon_h']}h | {r['n_cond']} | {r['wr_cond']:.1f}% | "
                f"**{r['skill']:+.1f}pp** |")
            print(f"   {r['hour']:02d}:00 UTC {HOUR_LABELS.get(r['hour'],''):<20} "
                  f"hareket {r['move_atr']:.2f}ATR ({r['move_pct']:.2f}%)  "
                  f"taban {r['base_rule']} {r['wr_base']:.0f}%  →  {r['rule']} +{r['horizon_h']}h "
                  f"n={r['n_cond']} {r['wr_cond']:.1f}%  beceri {r['skill']:+.1f}pp")

        # ── hareket profili: yön gürültü çıksa da bu betimsel gerçek ────────
        mv = sorted(res["movement"], key=lambda r: -r["move_atr"])
        cur = CURRENT_SCHEDULE.get(symbol, [])
        rank = {r["hour"]: i + 1 for i, r in enumerate(mv)}
        out += ["", "**Hareket profili** — karar saatinden sonraki 4 saatte medyan "
                "mutlak hareket (ATR birimi). Yön öngörülemese bile bu betimsel: "
                "önünde yol olmayan saatte 4 saatlik yönlü karar vermenin anlamı yok.",
                "", "| sıra | UTC | Etiket | 4h hareket (ATR) | 4h hareket % | mevcut koşu |",
                "|---|---|---|---|---|---|"]
        for i, r in enumerate(mv[:6]):
            out.append(f"| {i+1} | {r['hour']:02d}:00 | {HOUR_LABELS.get(r['hour'],'')} | "
                       f"{r['move_atr']:.2f} | {r['move_pct']:.2f} | "
                       f"{'← ŞU AN BURADA' if r['hour'] in cur else ''} |")
        for h in cur:
            hit = next((r for r in mv if r["hour"] == h), None)
            if hit and rank[h] > 6:
                out.append(f"| {rank[h]} | {h:02d}:00 | {HOUR_LABELS.get(h,'')} | "
                           f"{hit['move_atr']:.2f} | {hit['move_pct']:.2f} | ← ŞU AN BURADA |")
        cur_txt = ", ".join(
            f"{h:02d}:00 UTC (hareket sırası {rank.get(h,'?')}/{len(mv)})" for h in cur)
        out += ["", f"- Mevcut koşu saati: **{cur_txt}** · en hareketli saat: "
                f"**{mv[0]['hour']:02d}:00 UTC ({mv[0]['move_atr']:.2f} ATR)**", ""]
        print(f"   → mevcut koşu {cur_txt} | en hareketli {mv[0]['hour']:02d}:00 "
              f"({mv[0]['move_atr']:.2f} ATR)")
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "data",
                        "debate_hour_report.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"\n→ {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
