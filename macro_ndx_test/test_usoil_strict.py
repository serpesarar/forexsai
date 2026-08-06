"""
USOIL için VIX-rejim kuralının SIKI testi.

NDX'teki kural (VIX>=esik -> BUY lehte, altinda SELL lehte) USOIL'e ham
uygulandiginda dusuk-VIX rejiminde dev bir fark (%76.8 vs %18.0) veriyordu,
ama bu USOIL'in zaten bilinen yapisal SELL>BUY yanliligiyla karisabilir.
Bu script 3 şeyi ayri ayri test eder:

  1) KRONOLOJIK OOS: esik TRAIN'den, favored/against WR TEST'te olculur
     (in-sample sizinti yok).
  2) PLACEBO: TRAIN'de yon etiketleri karistirilip favored-against farki
     rastgele ne kadar cikiyor olculur (gercek fark bunu gecmeli).
  3) BASELINE KARSILASTIRMASI: "hep SELL ac" naive stratejisiyle
     "VIX-kurali" stratejisi TEST'te karsilastirilir -- VIX gercekten
     yapisal yanliliğin USTUNE bilgi katiyor mu, yoksa sadece o yanliligi
     mi yansitiyor?
"""
import json, bisect, random, statistics as st
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
M = ROOT / "macro_ndx_test"
SYM = "USOIL.FOREX"


def ep(t):
    return datetime.fromisoformat(t).timestamp()


macro = {}
for nm in ["VIX", "TNX", "DXY"]:
    rows = json.loads((M / f"{nm}.json").read_text())
    rows.sort(key=lambda r: r["t"])
    macro[nm] = ([r["t"] for r in rows], [r["close"] for r in rows])


def val_at(nm, epoch):
    ts, cs = macro[nm]
    i = bisect.bisect_right(ts, epoch) - 1
    return cs[i] if i >= 0 else None


sig = [s for s in json.loads((ROOT / "sr_rejection_research" / "data" / "signals.json").read_text())
       if s["symbol"] == SYM and s["ml_direction"] in ("BUY", "SELL")]
sig.sort(key=lambda s: s["created_at"])

last = {}
dedup = []
for s in sig:
    k = s["ml_direction"]
    t = ep(s["created_at"])
    if k not in last or t - last[k] > 3600:
        dedup.append(s)
        last[k] = t

rows = []
for s in dedup:
    t = ep(s["created_at"])
    v = val_at("VIX", t)
    if v is None:
        continue
    rows.append({"t": t, "win": s["status"] == "completed", "dir": s["ml_direction"], "vix": v})

rows.sort(key=lambda r: r["t"])
print(f"USOIL dedup+VIX-hizali: {len(rows)} sinyal "
      f"({datetime.utcfromtimestamp(rows[0]['t'])} -> {datetime.utcfromtimestamp(rows[-1]['t'])})\n")


def wr(rs):
    return sum(1 for r in rs if r["win"]) / len(rs) * 100 if rs else 0


def favored_against_gap(rows_, threshold):
    """NDX kurali: vix>=threshold -> BUY lehte, altinda SELL lehte."""
    favored = []
    against = []
    for r in rows_:
        fav_dir = "BUY" if r["vix"] >= threshold else "SELL"
        if r["dir"] == fav_dir:
            favored.append(r)
        else:
            against.append(r)
    return favored, against


# ─── 1) KRONOLOJIK OOS ────────────────────────────────────────────────────
split = int(len(rows) * 0.65)
train, test = rows[:split], rows[split:]
threshold = st.median(r["vix"] for r in train)
print(f"=== 1) KRONOLOJIK OOS (train=%{100*len(train)/len(rows):.0f} ilk, "
      f"test=son %{100*len(test)/len(rows):.0f}) ===")
print(f"esik (TRAIN medyan VIX) = {threshold:.3f}")
print(f"train donem: {datetime.utcfromtimestamp(train[0]['t']).date()} -> "
      f"{datetime.utcfromtimestamp(train[-1]['t']).date()}")
print(f"test  donem: {datetime.utcfromtimestamp(test[0]['t']).date()} -> "
      f"{datetime.utcfromtimestamp(test[-1]['t']).date()}\n")

for name, ds in [("TRAIN (in-sample)", train), ("TEST (OOS)", test)]:
    fav, aga = favored_against_gap(ds, threshold)
    fav_low = [r for r in fav if r["vix"] < threshold]
    fav_high = [r for r in fav if r["vix"] >= threshold]
    aga_low = [r for r in aga if r["vix"] < threshold]
    aga_high = [r for r in aga if r["vix"] >= threshold]
    print(f"--- {name} ---")
    print(f"  lehte  toplam WR={wr(fav):.1f}% (n={len(fav)}) | "
          f"karsit toplam WR={wr(aga):.1f}% (n={len(aga)}) | fark={wr(fav)-wr(aga):+.1f}pp")
    print(f"  dusuk VIX  -> lehte(SELL)={wr(aga_high) if False else wr([r for r in ds if r['vix']<threshold and r['dir']=='SELL']):.1f}% "
          f"karsit(BUY)={wr([r for r in ds if r['vix']<threshold and r['dir']=='BUY']):.1f}%")
    print(f"  yuksek VIX -> lehte(BUY)={wr([r for r in ds if r['vix']>=threshold and r['dir']=='BUY']):.1f}% "
          f"karsit(SELL)={wr([r for r in ds if r['vix']>=threshold and r['dir']=='SELL']):.1f}%")
print()

# ─── 2) PLACEBO (TRAIN icinde yon etiketi karistir) ───────────────────────
print("=== 2) PLACEBO (TRAIN, yon etiketleri 2000x karistirilir) ===")
real_fav, real_aga = favored_against_gap(train, threshold)
real_gap = wr(real_fav) - wr(real_aga)
print(f"gercek (TRAIN) lehte-karsit farki = {real_gap:+.1f}pp")

dirs = [r["dir"] for r in train]
gaps = []
for _ in range(2000):
    random.shuffle(dirs)
    fav_w, fav_n, aga_w, aga_n = 0, 0, 0, 0
    for r, d in zip(train, dirs):
        fav_dir = "BUY" if r["vix"] >= threshold else "SELL"
        if d == fav_dir:
            fav_n += 1
            fav_w += r["win"]
        else:
            aga_n += 1
            aga_w += r["win"]
    g = (fav_w / fav_n * 100 if fav_n else 0) - (aga_w / aga_n * 100 if aga_n else 0)
    gaps.append(abs(g))
gaps.sort()
p95 = gaps[int(0.95 * len(gaps))]
p_val = sum(1 for g in gaps if g >= abs(real_gap)) / len(gaps)
print(f"placebo p95 |fark| = {p95:.1f}pp | ampirik p-degeri = {p_val:.3f} "
      f"({'GECTI' if abs(real_gap) > p95 else 'GECEMEDI'})\n")

# ─── 3) BASELINE KARSILASTIRMASI (TEST/OOS uzerinde) ──────────────────────
print("=== 3) BASELINE: 'hep SELL ac' vs 'VIX-kurali' (TEST/OOS) ===")
test_sell_only = [r for r in test if r["dir"] == "SELL"]
test_buy_only = [r for r in test if r["dir"] == "BUY"]
print(f"TEST'te 'hep SELL' evreni: WR={wr(test_sell_only):.1f}% (n={len(test_sell_only)})")
print(f"TEST'te 'hep BUY'  evreni: WR={wr(test_buy_only):.1f}% (n={len(test_buy_only)})")

vix_rule_signals = [r for r in test
                     if (r["dir"] == "BUY" and r["vix"] >= threshold)
                     or (r["dir"] == "SELL" and r["vix"] < threshold)]
print(f"'VIX-kurali' (yuksekte BUY, dusukte SELL) evreni: "
      f"WR={wr(vix_rule_signals):.1f}% (n={len(vix_rule_signals)})")

# VIX-kuralinin SELL-only baseline'a gore GERCEK katkisi: yuksek-VIX'te BUY
# SELL'den DAHA MI iyi, yoksa SELL'i o rejimde de acsak daha mi iyi olurdu?
high_vix_test = [r for r in test if r["vix"] >= threshold]
hv_buy = [r for r in high_vix_test if r["dir"] == "BUY"]
hv_sell = [r for r in high_vix_test if r["dir"] == "SELL"]
print(f"\nYuksek-VIX alt-kumesinde (TEST, n={len(high_vix_test)}): "
      f"BUY WR={wr(hv_buy):.1f}% (n={len(hv_buy)}) vs SELL WR={wr(hv_sell):.1f}% (n={len(hv_sell)})")
print("-> Eger SELL burada da BUY'dan iyiyse, 'yuksek VIX'te BUY'a gec' onerisi"
      " SELL-only baseline'i YENEMIYOR demektir.")
