"""Özel depo: oluştur / indir / sil. Anahtar scripts/remote.py ile aynı kaynaktan, ekrana yazılmaz."""
import sys, importlib.util
from pathlib import Path
R = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("remote", R / "scripts/remote.py"); rm = importlib.util.module_from_spec(s); s.loader.exec_module(rm)
fn = [n for n in dir(rm) if n in ("make_client", "get_client", "client", "_client")]
c = getattr(rm, fn[0])()
B = "research-xfer"; OUT = Path(__file__).parent / "data/mt5"
if sys.argv[1] == "yap":
    try:
        print(c.storage.create_bucket(B, options={"public": False}))
    except Exception as e:
        print("hata/var", str(e)[:120])
elif sys.argv[1] == "indir":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in c.storage.from_(B).list():
        (OUT / f["name"]).write_bytes(c.storage.from_(B).download(f["name"])); print(f["name"], flush=True)
elif sys.argv[1] == "sil":
    names = [f["name"] for f in c.storage.from_(B).list()]
    c.storage.from_(B).remove(names); c.storage.delete_bucket(B); print("silindi", len(names))
