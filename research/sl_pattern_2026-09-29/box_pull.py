"""Kutudan SpotCrude M5 geçmişini SALT-OKUMA python -c ile parça parça çek (kutuya yazma yok)."""
import subprocess, sys, base64, zlib, numpy as np, re
REMOTE = "/Users/melihcanodacioglu/Desktop/panel/scripts/remote.py"
CH = 55000
PY = ("import MetaTrader5 as m,numpy as n,zlib,base64;m.initialize();"
      "r=m.copy_rates_from_pos('SpotCrude',m.TIMEFRAME_M5,1,99500);r=r[r['time']<=1790730000][-99000:];"
      "t=r['time'].astype('i8');p=n.round(n.column_stack([r['open'],r['high'],r['low'],r['close']])*1000).astype('i8');"
      "a=n.concatenate([[t[0]],n.diff(t),[p[0,3]],n.diff(p[:,3]),p[:,0]-p[:,3],p[:,1]-p[:,3],p[:,2]-p[:,3],r['spread'].astype('i8')]).astype('i4');"
      "b=base64.b64encode(zlib.compress(a.tobytes(),9)).decode();print('LEN',len(b),len(r),int(t[-1]));print('B64['+b[{i}:{j}]+']')")
def call(i, j):
    cmd = 'python -c "' + PY.format(i=i, j=j) + '"'
    out = subprocess.run(["python3", REMOTE, "sh", cmd, "--timeout", "300"], capture_output=True, text=True).stdout
    L = re.search(r"LEN (\d+) (\d+) (\d+)", out); b = re.search(r"B64\[([A-Za-z0-9+/=]*)\]", out)
    if not L or not b: sys.exit("hata:\n" + out[-800:])
    return int(L.group(1)), int(L.group(2)), int(L.group(3)), b.group(1)
total, n, tlast, first = call(0, CH); parts = [first]; print("toplam", total, "bar", n, flush=True)
i = CH
while i < total:
    t2, n2, tl2, part = call(i, i + CH)
    if (t2, n2, tl2) != (total, n, tlast): sys.exit("veri kaydı değişti — yeniden başlat")
    parts.append(part); i += CH; print(f"{min(i,total)}/{total}", flush=True)
a = np.frombuffer(zlib.decompress(base64.b64decode("".join(parts))), dtype="i4").astype("i8")
t = np.cumsum(a[:n]); c = np.cumsum(a[n:2*n]); o = a[2*n:3*n] + c; h = a[3*n:4*n] + c; l = a[4*n:5*n] + c; sp = a[5*n:6*n]
np.savez("spotcrude_m5.npz", t=t, o=o / 1000, h=h / 1000, l=l / 1000, c=c / 1000, spread=sp)
print("kaydedildi", n, t[0], t[-1])
