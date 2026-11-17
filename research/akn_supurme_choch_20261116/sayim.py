"""Sonuç GÖRMEDEN olay sayımı (EK-0 gerekçesi): katman başına olay ve işlem sayısı, 9 yıl."""
import time
import akn as A
t0 = time.time()
B = A.load(); cx = A.build(B)
print("kuruldu", round(time.time() - t0), "sn", flush=True)
print("K1 (1H iğne süpürmesi):", len(A.k1_events(cx)))
for ch in ("K1K2", "K1K2n", "K1", "K2"):
    st = A.chain_starts(cx, ch)
    n = {lt: len(A.run(cx, ch, lt, "E50")) for lt in ("C53",)}
    print(ch, "başlangıç", len(st), "işlem C53·E50", n, round(time.time() - t0), "sn", flush=True)
