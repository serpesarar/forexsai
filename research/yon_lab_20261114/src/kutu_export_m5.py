# Kutuda çalışır (salt okuma, EMİR YOK): US500/US30/US2000/GER40/NAS100 M1+M5 barları → research-xfer deposu (yonlab_*).
# Kalıp: research/c1_turev_20261105/kutu_export.py. MT5 max bars 100.000 (E126): M5 ≈ 1,3 yıl, M1 ≈ 70 gün.
import sys, io, gzip, json, datetime as d
sys.path.insert(0, "remote_agent")
import agent_config as c, MetaTrader5 as m, requests
assert m.initialize(getattr(c, "MT5_TERMINAL_PATH", None))
acc = m.account_info()
assert acc is not None and str(acc.login) == str(getattr(c, "MT5_LOGIN", acc.login)), "yanlış hesap"
url = c.SUPABASE_URL.rstrip("/"); key = c.SUPABASE_SERVICE_KEY
meta = {"login": acc.login, "server": acc.server}
for s in ("US500", "US30", "US2000", "GER40", "NAS100"):
    m.symbol_select(s, True); si = m.symbol_info(s)
    meta[s] = {"point": si.point, "digits": si.digits}
    for tf in ("M5", "M1"):
        pos, parts = 1, []
        while True:
            r = m.copy_rates_from_pos(s, getattr(m, "TIMEFRAME_" + tf), pos, 99000)
            if r is None or len(r) == 0: break
            parts.append(r); pos += len(r)
            if len(r) < 99000: break
        rows = sorted({int(x["time"]): x for p in parts for x in p}.items())
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as g:
            g.write(b"t,o,h,l,c,v,sp\n")
            for t, x in rows:
                g.write(f"{t},{x['open']},{x['high']},{x['low']},{x['close']},{x['tick_volume']},{x['spread']}\n".encode())
        name = f"yonlab_{s}_{tf}.csv.gz"
        h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/gzip"}
        rr = requests.post(f"{url}/storage/v1/object/research-xfer/{name}", headers=h, data=buf.getvalue(), timeout=300)
        print(name, len(rows), str(d.datetime.utcfromtimestamp(rows[0][0])) if rows else None, rr.status_code, flush=True)
tick = m.symbol_info_tick("NAS100")
meta["srv_minus_utc_s"] = int(round((tick.time - d.datetime.now(d.timezone.utc).timestamp()) / 900) * 900)
requests.post(f"{url}/storage/v1/object/research-xfer/yonlab_meta.json", headers={"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/json"}, data=json.dumps(meta), timeout=60)
print(meta)
