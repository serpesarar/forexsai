"""Son run_analysis komutunu (etiket alt dizesiyle) bekler, WTI_DATA bloğunu çözer ve kaydeder."""
import sys, json, time, base64, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.remote import _client
lab, out = sys.argv[1], Path(sys.argv[2]); wait = int(sys.argv[3]) if len(sys.argv) > 3 else 600
c = _client(); t0 = time.time()
while time.time() - t0 < wait:
    r = c.table('evolution_commands').select('id,status,output,analysis_name,created_at').ilike('analysis_name', f'%{lab}%').order('created_at', desc=True).limit(1).execute().data
    if r and r[0]['status'] in ('done', 'failed', 'timeout'):
        o = r[0].get('output') or ''
        if 'WTI_DATA_BEGIN' not in o:
            print(r[0]['status'], o[-1500:]); sys.exit(1)
        x = json.loads(zlib.decompress(base64.b64decode(o.split('WTI_DATA_BEGIN', 1)[1].split('WTI_DATA_END', 1)[0])))
        out.write_text(json.dumps(x, indent=1)); print('ok', r[0]['status']); sys.exit(0)
    time.sleep(5)
print('timeout'); sys.exit(2)
