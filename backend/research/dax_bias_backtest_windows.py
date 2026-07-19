"""DAX bias — karar-saati taraması (dürüst uzantı).

Soru: 10:00 Berlin'de edge yoksa, günün ilerleyen saatlerinde (12/14/16
Berlin) karar-fiyatı→17:30 kapanışı için basit-kural edge'i doğuyor mu?
Özellikle 16:00 Berlin: ABD açılışının (15:30) ilk yarım saati görülür.

Protokol dax_bias_backtest.py ile aynı: bakış-ileri yok (yalnız kapanmış
1h barlar), kronolojik %70/30, eşikler train'de, kural seti önceden kayıtlı,
tüm sonuçlar (geçen+kalan) raporlanır. Sağlamlık çıtası: train VE test
≥%55 isabet + n_test≥20 + OOS ort. işaretli getiri > 0.
"""
import json, os, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dax_bias_backtest import load_1h, grade, FLAT   # aynı yükleyici/notlayıcı

BERLIN = ZoneInfo("Europe/Berlin")

dax = load_1h("GDAXI.INDX")
ndx = load_1h("NDX.INDX")

days = defaultdict(dict)
for t, bar in dax.items():
    loc = t.astimezone(BERLIN)
    days[loc.date()][loc.hour] = (t, bar)
ndays = defaultdict(dict)
for t, bar in ndx.items():
    loc = t.astimezone(BERLIN)
    ndays[loc.date()][loc.hour] = (t, bar)

dates = sorted(days)
samples = []
for i, d in enumerate(dates):
    h = days[d]
    if 9 not in h or 17 not in h:
        continue
    if not all(x in h for x in (11, 13, 15)):
        continue
    open_px = h[9][1][0]
    p_close = h[17][1][3]
    prev = None
    for j in range(i - 1, max(i - 5, -1), -1):
        if 17 in days[dates[j]]:
            prev = days[dates[j]][17][1][3]
            break
    if prev is None:
        continue
    nh = ndays.get(d, {})
    row = {"date": d.isoformat()}
    # Karar anı H: son kapanmış bar (H-1). day_move = o kapanış vs 09 açılışı.
    for H in (12, 14, 16):
        pdec = h[H - 1][1][3] if (H - 1) in h else None
        if pdec is None:
            row[f"h{H}"] = None
            continue
        day_move = (pdec - open_px) / open_px * 100.0
        last2 = ((pdec - h[H - 3][1][3]) / h[H - 3][1][3] * 100.0) if (H - 3) in h else None
        target = (p_close - pdec) / pdec * 100.0
        # NDX bugünkü değişim (karar anına kadar) — 22:00 UTC dünkü kapanışa göre
        n_now = nh.get(H - 1, (None, None))[1]
        n_now = n_now[3] if n_now else None
        us_open_drive = None
        if H == 16:
            b15 = nh.get(15, (None, None))[1]   # 15-16 Berlin barı: ABD açılış yarım saati dahil
            if b15:
                us_open_drive = (b15[3] - b15[0]) / b15[0] * 100.0
        row[f"h{H}"] = {"day_move": day_move, "last2": last2,
                        "us_open_drive": us_open_drive, "target": target}
    samples.append(row)

print(f"days: {len(samples)} ({samples[0]['date']} → {samples[-1]['date']})", file=sys.stderr)
split = int(len(samples) * 0.7)

def run(H):
    rows = [r[f"h{H}"] for r in samples if r.get(f"h{H}")]
    tr, te = rows[:int(len(rows) * 0.7)], rows[int(len(rows) * 0.7):]
    dm = sorted(abs(x["day_move"]) for x in tr)
    q50 = dm[len(dm) // 2]
    rules = {
        "gün-yönünü takip": lambda x: 1 if x["day_move"] > 0 else (-1 if x["day_move"] < 0 else 0),
        f"gün-yönü |>{q50:.2f}|": lambda x: (1 if x["day_move"] > 0 else -1) if abs(x["day_move"]) > q50 else 0,
        "son-2h yönü": lambda x: 0 if x["last2"] is None else (1 if x["last2"] > 0.05 else (-1 if x["last2"] < -0.05 else 0)),
        "gün-yönüne TERS": lambda x: -1 if x["day_move"] > 0 else (1 if x["day_move"] < 0 else 0),
    }
    if H == 16:
        rules["ABD açılış sürüşü (NDX 15-16h)"] = lambda x: 0 if x["us_open_drive"] is None else (
            1 if x["us_open_drive"] > 0.05 else (-1 if x["us_open_drive"] < -0.05 else 0))
        rules["gün+ABD aynı yön"] = lambda x: (
            (1 if x["day_move"] > 0 else -1)
            if (x["us_open_drive"] is not None and (x["day_move"] > 0) == (x["us_open_drive"] > 0)
                and abs(x["day_move"]) > 0) else 0)
    print(f"\n===== Karar {H}:00 Berlin → 17:30 kapanış =====")
    for tag, rows_ in (("TRAIN", tr), ("TEST", te)):
        up = sum(1 for x in rows_ if x["target"] > FLAT)
        dn = sum(1 for x in rows_ if x["target"] < -FLAT)
        print(f"[{tag} n={len(rows_)}] taban up %{up/len(rows_)*100:.0f} / down %{dn/len(rows_)*100:.0f} / flat %{(len(rows_)-up-dn)/len(rows_)*100:.0f}")
        for nm, fn in rules.items():
            hits = n = 0
            sgn = []
            for x in rows_:
                dd = fn(x)
                if not dd:
                    continue
                n += 1
                hits += 1 if grade(dd, x["target"]) else 0
                sgn.append(dd * x["target"])
            if n:
                print(f"  {nm:<28} n={n:>3} isabet=%{hits/n*100:4.1f} ort.işaretli={sum(sgn)/n:+.3f}%")

for H in (12, 14, 16):
    run(H)
