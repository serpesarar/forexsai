"""Toplu çalıştırıcı: indirilen tüm scriptleri 4 sembolün 1h verisinin son N barında çalıştır → tepki durumları.

Çıktı: data/runs/<pencere>/part_<k>.pkl.gz — her kayıt {sid, name, author, boosts, version, per_sym: {SYM: {status,
error, flags, seconds, overlay, states: {ad: packbits bytes}}}}. Devam ettirilebilir (yazılmış sid'ler atlanır).
Kullanım: python batch.py [pencere=recent] [limit] [workers]  |  python batch.py retry [pencere] [workers] [stale|failed|sid_dosyası]
"""
from __future__ import annotations

import gzip
import os
import pickle
import sys
import signal
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
GCM = HERE.parent / "gosterge_cakisma_20261025"
sys.path.insert(0, str(GCM))
sys.path.insert(0, str(HERE))

SYMS = ("NDX", "DAX", "XAU", "USOIL")
TF = "1h"
N_BARS = 12000
TIMEOUT_S = 60
HARD_TIMEOUT_MULT = 3                 # SIGALRM tavanı (bar içi sonsuz döngüler için)
PART_SIZE = 200
WINDOWS = {"recent": None, "past": "past"}        # recent: son N bar; past: ondan önceki N bar (EK-7 §tekrar)

_DF: dict = {}
ENGINE_FILES = ("pine_parser.py", "pine_transpile.py", "pine_runtime.py", "pine_ta.py", "pine_builtins.py",
                "pine_run.py", "pine_broker.py", "signals.py", "data/lib_index_v2.json")


def engine_hash() -> str:
    """Motor sürümü: motor kaynakları + kütüphane indeksi özeti (her kayda yazılır; düzeltme turunda kanıt)."""
    import hashlib
    h = hashlib.sha1()
    for f in ENGINE_FILES:
        p = HERE / f
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


ENGINE = engine_hash()


def _init(window: str):
    import data
    for s in SYMS:
        d = data.load(s, TF)
        if window == "recent":
            d = d.iloc[-N_BARS:]
        else:
            d = d.iloc[max(0, len(d) - 2 * N_BARS):len(d) - N_BARS]
        _DF[s] = d.reset_index(drop=True)


class HardTimeout(BaseException):          # Exception değil: motorun except blokları yutmasın
    pass


def _hard_timeout(signum, frame):
    raise HardTimeout


def _run_one(rec: dict) -> dict:
    import pine_run
    import signals
    out = {k: rec.get(k) for k in ("sid", "name", "author", "boosts", "version", "type")}
    out["engine"] = ENGINE
    out["per_sym"] = {}
    for s in SYMS:
        df = _DF[s]
        try:
            signal.signal(signal.SIGALRM, _hard_timeout)
            signal.setitimer(signal.ITIMER_REAL, TIMEOUT_S * HARD_TIMEOUT_MULT)
            try:
                res = pine_run.run_script(rec["source"], df, TF, s, timeout_s=TIMEOUT_S)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
        except HardTimeout:                      # bar içi sonsuz döngü: motorun bar-başı süre denetimi göremez
            res = {"status": "timeout", "error": "hard", "outputs": {}, "flags": [], "seconds": 0.0, "overlay": False}
        except Exception as e:                   # beklenmedik çökme: kaydet, devam et
            res = {"status": "crash", "error": f"{type(e).__name__}: {e}"[:200], "outputs": {}, "flags": [],
                   "seconds": 0.0, "overlay": False}
        st = {}
        if res["status"] == "ok":
            try:
                st = {k: np.packbits(v).tobytes() for k, v in
                      signals.script_states(res["outputs"], df.close.values.astype(float)).items()}
            except Exception as e:
                res["status"], res["error"] = "signal_error", f"{type(e).__name__}: {e}"[:200]
        out["per_sym"][s] = {"status": res["status"], "error": res.get("error"), "flags": res.get("flags", []),
                             "seconds": res.get("seconds", 0.0), "overlay": res.get("overlay", False), "states": st}
        if res["status"] in ("parse_error", "transpile_error", "timeout"):
            for s2 in SYMS:                          # aynı script diğer sembollerde de aynı sonucu verir
                out["per_sym"].setdefault(s2, out["per_sym"][s])
            break
    return out


def k0_start(run_dir: Path) -> int:
    return len(list(run_dir.glob("part_*.pkl.gz")))


def done_sids(run_dir: Path) -> set:
    sids = set()
    for p in run_dir.glob("part_*.pkl.gz"):
        try:
            with gzip.open(p, "rb") as f:
                sids.update(r["sid"] for r in pickle.load(f))
        except (EOFError, OSError, pickle.UnpicklingError):
            p.unlink()                              # yarım yazılmış parça → yeniden üret
    return sids


def main(window="recent", limit=None, workers=7):
    import pine_src
    run_dir = HERE / "data/runs" / window
    run_dir.mkdir(parents=True, exist_ok=True)
    skip = done_sids(run_dir)
    recs = [r for r in pine_src.iter_sources(True) if r["sid"] not in skip and r.get("type") != "library"]
    if limit:
        recs = recs[:int(limit)]
    k0 = len(list(run_dir.glob("part_*.pkl.gz")))
    print(f"çalıştırılacak {len(recs)} (atlanan {len(skip)}), {workers} süreç, motor {ENGINE}", flush=True)
    with open(run_dir / "engine_log.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\tmotor {ENGINE}\tilk parça part_{k0_start(run_dir):04d}\n")
    t0, buf, k, n = time.time(), [], k0, 0
    with Pool(int(workers), initializer=_init, initargs=(window,), maxtasksperchild=200) as pool:
        for res in pool.imap_unordered(_run_one, recs, chunksize=2):
            buf.append(res)
            n += 1
            if len(buf) >= PART_SIZE:
                _flush(run_dir, k, buf)
                k, buf = k + 1, []
                print(f"{n}/{len(recs)}  {time.time() - t0:.0f}s", flush=True)
    if buf:
        _flush(run_dir, k, buf)
    print(f"bitti {n} script {time.time() - t0:.0f}s", flush=True)


FAIL = ("parse_error", "transpile_error", "unsupported", "runtime_error", "crash", "signal_error")


def retry(window="recent", workers=7, mode="failed"):
    """Düzeltme turu (EK-P1 §4, EK-P2): seçilen kayıtları güncel motorla yeniden koştur, parçalarda yerinde değiştir.

    mode: "stale"  → motor özeti güncel motordan farklı (ya da hiç yazılmamış) TÜM kayıtlar,
          "failed" → başarısız (zaman aşımı hariç) kayıtlar,
          dosya yolu → o dosyadaki sid'ler.
    Önceki/sonraki durumlar data/runs/<pencere>/retry_log_<mod>.json'a yazılır.
    """
    import json
    import pine_src
    run_dir = HERE / "data/runs" / window
    parts = sorted(run_dir.glob("part_*.pkl.gz"))
    listed = set(Path(mode).read_text().split()) if mode not in ("stale", "failed") else set()
    before = {}
    for p in parts:
        with gzip.open(p, "rb") as f:
            for r in pickle.load(f):
                pick = (r.get("engine") != ENGINE if mode == "stale" else
                        any(v["status"] in FAIL for v in r["per_sym"].values()) if mode == "failed" else
                        r["sid"] in listed)
                if pick:
                    before[r["sid"]] = {s: v["status"] for s, v in r["per_sym"].items()}
    recs = [r for r in pine_src.iter_sources(True) if r["sid"] in before]
    print(f"düzeltme turu ({mode}): {len(recs)} script yeniden koşuyor, motor {ENGINE}", flush=True)
    new, t0 = {}, time.time()
    with Pool(int(workers), initializer=_init, initargs=(window,), maxtasksperchild=200) as pool:
        for res in pool.imap_unordered(_run_one, recs, chunksize=2):
            new[res["sid"]] = res
            if len(new) % 500 == 0:
                print(f"{len(new)}/{len(recs)}  {time.time() - t0:.0f}s", flush=True)
    for p in parts:
        with gzip.open(p, "rb") as f:
            recs_p = pickle.load(f)
        if any(r["sid"] in new for r in recs_p):
            _flush(run_dir, int(p.name[5:9]), [new.get(r["sid"], r) for r in recs_p])
    log = {sid: {"once": before[sid], "sonra": {s: v["status"] for s, v in new[sid]["per_sym"].items()}} for sid in new}
    tag = mode if mode in ("stale", "failed") else Path(mode).stem
    json.dump(log, open(run_dir / f"retry_log_{tag}.json", "w"), indent=0)
    fixed = sum(1 for v in log.values() if any(x == "ok" for x in v["sonra"].values())
                and not any(x == "ok" for x in v["once"].values()))
    print(f"bitti: {len(new)} yeniden koştu, {fixed} script ilk kez çalıştı ({time.time() - t0:.0f}s)", flush=True)


def _flush(run_dir: Path, k: int, buf: list):
    tmp = run_dir / f"part_{k:04d}.pkl.gz.tmp"
    with gzip.open(tmp, "wb") as f:
        pickle.dump(buf, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, run_dir / f"part_{k:04d}.pkl.gz")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "retry":
        retry(a[1] if len(a) > 1 else "recent", a[2] if len(a) > 2 else 7, a[3] if len(a) > 3 else "failed")
    else:
        main(a[0] if a else "recent", a[1] if len(a) > 1 and a[1] != "0" else None, a[2] if len(a) > 2 else 7)
