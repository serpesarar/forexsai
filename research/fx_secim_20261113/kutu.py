"""Kutuda python kodu çalıştır (salt-okuma), WTI_DATA bloğunu çöz. Kimlik bilgisi yazdırmaz."""
import sys, json, time, base64, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.remote import _client, submit

def run(code: str, label: str, timeout: int = 900, raw: bool = False):
    enc = base64.b64encode(code.encode()).decode()
    cmd = 'python -c "import base64;exec(base64.b64decode(\'' + enc + '\'))"'
    c = _client(); cid = submit(c, 'mt5_box', 'run_analysis', {'command': cmd, 'timeout': timeout}, 'FX araştırma (salt-okuma): ' + label)
    print('kuyrukta', label, cid, flush=True); t0 = time.time()
    while time.time() - t0 < timeout + 240:
        r = c.table('evolution_commands').select('status,output').eq('id', cid).limit(1).execute().data
        if r and r[0]['status'] in ('done', 'failed', 'timeout'):
            o = r[0].get('output') or ''
            if raw: return r[0]['status'], o
            if 'WTI_DATA_BEGIN' not in o: raise RuntimeError(r[0]['status'] + ' ' + o[-2000:])
            return json.loads(zlib.decompress(base64.b64decode(o.split('WTI_DATA_BEGIN', 1)[1].split('WTI_DATA_END', 1)[0])))
        time.sleep(5)
    raise TimeoutError(label)
