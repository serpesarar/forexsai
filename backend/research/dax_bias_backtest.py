"""DAX günlük-bias dürüst backtest — tartışma motoru için kanıt üretimi.

Soru: 10:00 Berlin'de (XETRA açılış+1h, debate'in karar anı) hangi basit,
karar-anında-bilinir sinyaller günün kalanının yönünü (karar-fiyatı →
17:30 Berlin kapanışı — bias_test_service'in notlama penceresiyle BİREBİR)
öngörür?

Dürüstlük protokolü:
  * Özellikler yalnız karar anına kadar kapanmış barlardan (bakış-ileri yok).
  * Kronolojik %70/30 bölme; eşikler yalnız train'de seçilir, test tek geçiş.
  * Kural seti ÖNCEDEN kayıtlı (aşağıda R1-R6) — test sonrası kural eklenmez.
  * İsabet tanımı harness ile aynı: bullish doğru ⇔ değişim > +0.15%,
    bearish doğru ⇔ değişim < −0.15% (flat bandı yanlış sayılır).
"""
import json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

BERLIN = ZoneInfo("Europe/Berlin")
FLAT = 0.15
ENV = {}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            ENV.setdefault(k.strip(), v.strip().strip('"').strip("'"))
URL = ENV["SUPABASE_URL"].rstrip("/")
KEY = ENV.get("SUPABASE_SERVICE_ROLE_KEY") or ENV["SUPABASE_KEY"]


def rest(path, params, page=1000):
    out, off = [], 0
    while True:
        q = urllib.parse.urlencode({**params, "limit": page, "offset": off})
        req = urllib.request.Request(f"{URL}/rest/v1/{path}?{q}",
            headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
        with urllib.request.urlopen(req) as r:
            b = json.loads(r.read())
        out.extend(b)
        if len(b) < page:
            return out
        off += page


def load_1h(symbol):
    rows = rest("candle_cache", {"select": "candle_time,open,high,low,close",
                                 "symbol": f"eq.{symbol}", "timeframe": "eq.1h",
                                 "order": "candle_time"})
    out = {}
    for r in rows:
        t = datetime.fromisoformat(str(r["candle_time"]).replace("Z", "+00:00"))
        out[t] = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
    return out

dax = load_1h("GDAXI.INDX")
ndx = load_1h("NDX.INDX")
print(f"DAX 1h bars: {len(dax)}  NDX 1h bars: {len(ndx)}", file=sys.stderr)

# Berlin-lokal gün haritası: her işlem günü için saat→bar
days = defaultdict(dict)
for t, bar in dax.items():
    loc = t.astimezone(BERLIN)
    days[loc.date()][loc.hour] = (t, bar)

ndx_by_utc = dict(ndx)

def ndx_close_at(target_utc):
    """NDX 1h kapanışı: hedef saatte veya en çok 3 saat geriye."""
    base = target_utc.replace(minute=0, second=0, microsecond=0)
    for i in range(4):
        b = ndx_by_utc.get(base - timedelta(hours=i))
        if b:
            return b[3]
    return None

samples = []
dates = sorted(days)
for i, d in enumerate(dates):
    hours = days[d]
    # XETRA: 09 açılış barı, 10 karar anı, 17 son tam bar (17:30 kapanış ~ 17h bar kapanışı)
    if 9 not in hours or 10 not in hours or 17 not in hours:
        continue
    open_bar = hours[9][1]
    dec_utc, dec_bar = hours[10]          # 10:00 Berlin barı → kapanışı 11:00'de biter!
    # DİKKAT (bakış-ileri): karar 10:00 Berlin'deyse yalnız 09:00-10:00 barı kapanmıştır.
    # Karar fiyatı = 09h barının kapanışı (=10:00 anındaki fiyat).
    p_decision = open_bar[3]
    drive = (p_decision - open_bar[0]) / open_bar[0] * 100.0     # açılış sürüşü 09→10
    close_bar = hours[17][1]
    p_close = close_bar[3]
    target = (p_close - p_decision) / p_decision * 100.0

    # Önceki gün kapanışı (Berlin 17h barı)
    prev = None
    for j in range(i - 1, max(i - 5, -1), -1):
        if 17 in days[dates[j]]:
            prev = days[dates[j]]
            break
    if prev is None:
        continue
    prev_close = prev[17][1][3]
    gap = (open_bar[0] - prev_close) / prev_close * 100.0
    prev_day_dir = None
    if 9 in prev:
        po = prev[9][1][0]
        prev_day_dir = 1 if prev[17][1][3] > po else -1

    # NDX gece proxy'si: NDX şimdi (10:00 Berlin = dec anı) vs dün 22:00 UTC
    dec_moment_utc = hours[9][0] + timedelta(hours=1)   # 10:00 Berlin'in UTC karşılığı
    n_now = ndx_close_at(dec_moment_utc)
    n_prev = ndx_close_at(dec_moment_utc.replace(hour=21, minute=0) - timedelta(
        days=1) + timedelta(hours=0))
    ndx_overnight = ((n_now - n_prev) / n_prev * 100.0) if (n_now and n_prev) else None

    samples.append({"date": d.isoformat(), "drive": drive, "gap": gap,
                    "prev_day_dir": prev_day_dir, "ndx_on": ndx_overnight,
                    "target": target})

print(f"samples: {len(samples)}  ({samples[0]['date']} → {samples[-1]['date']})",
      file=sys.stderr)

split = int(len(samples) * 0.7)
train, test = samples[:split], samples[split:]

def grade(direction, target):
    """Harness-uyumlu: bullish doğru ⇔ >+0.15; bearish doğru ⇔ <−0.15."""
    if direction == 0:
        return None
    return target > FLAT if direction > 0 else target < -FLAT

def evaluate(rows, rule, name):
    hits, n, sgn = 0, 0, []
    for r in rows:
        d = rule(r)
        if d == 0 or d is None:
            continue
        g = grade(d, r["target"])
        n += 1
        hits += 1 if g else 0
        sgn.append(d * r["target"])
    cov = n / len(rows) * 100 if rows else 0
    avg = sum(sgn) / n if n else 0
    return f"{name:<34} n={n:>3} kaps=%{cov:4.0f} isabet={hits}/{n} (%{hits/n*100:4.1f}) ort.işaretli={avg:+.3f}%" if n else f"{name:<34} n=0"

# Train'de eşik seçimi (yalnız train!)
drives = sorted(abs(r["drive"]) for r in train)
q50 = drives[len(drives) // 2]
q70 = drives[int(len(drives) * 0.7)]
print(f"\ntrain |drive| medyan={q50:.3f}%  q70={q70:.3f}%", file=sys.stderr)

RULES = {
    "R1 sürüşü takip et (her gün)": lambda r: 1 if r["drive"] > 0 else (-1 if r["drive"] < 0 else 0),
    f"R2 sürüş, |drive|>medyan({q50:.2f})": lambda r: (1 if r["drive"] > 0 else -1) if abs(r["drive"]) > q50 else 0,
    f"R3 sürüş, |drive|>q70({q70:.2f})": lambda r: (1 if r["drive"] > 0 else -1) if abs(r["drive"]) > q70 else 0,
    "R4 gap yönünü takip et": lambda r: 1 if r["gap"] > 0.1 else (-1 if r["gap"] < -0.1 else 0),
    "R5 NDX gece yönü": lambda r: 0 if r["ndx_on"] is None else (1 if r["ndx_on"] > 0.1 else (-1 if r["ndx_on"] < -0.1 else 0)),
    "R6 sürüş+NDX aynı yönde": lambda r: (1 if r["drive"] > 0 else -1) if (r["ndx_on"] is not None and abs(r["drive"]) > 0 and ((r["drive"] > 0) == (r["ndx_on"] > 0))) else 0,
    "R7 sürüşe TERS (fade)": lambda r: -1 if r["drive"] > 0 else (1 if r["drive"] < 0 else 0),
    "R8 önceki gün yönü devam": lambda r: r["prev_day_dir"] or 0,
}

for name_set, rows in (("TRAIN", train), ("TEST (OOS — tek geçiş)", test)):
    print(f"\n== {name_set} ({rows[0]['date']} → {rows[-1]['date']}, n={len(rows)}) ==")
    # Taban oranlar
    up = sum(1 for r in rows if r["target"] > FLAT)
    dn = sum(1 for r in rows if r["target"] < -FLAT)
    fl = len(rows) - up - dn
    print(f"taban: up %{up/len(rows)*100:.0f} | down %{dn/len(rows)*100:.0f} | flat(±{FLAT}) %{fl/len(rows)*100:.0f}")
    for nm, fn in RULES.items():
        print(evaluate(rows, fn, nm))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                   "dax_bias_backtest_samples.json")
with open(out, "w") as f:
    json.dump(samples, f)
print(f"\nsamples -> {out}", file=sys.stderr)
