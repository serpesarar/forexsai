"""data.binance.vision S3 listesi (sayfalı). Kullanım: python -I 00_list_s3.py <out_json> <prefix> [<prefix>...]

Her prefix için (key, size, last_modified) listesi JSON'a yazılır. Yalnız XML okunur.
"""
from __future__ import annotations
import json, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def list_prefix(prefix: str) -> list[dict]:
    out, marker = [], ""
    while True:
        q = urllib.parse.urlencode({"prefix": prefix, "marker": marker})
        for i in range(4):
            try:
                with urllib.request.urlopen(f"{S3}?{q}", timeout=60) as r:
                    root = ET.fromstring(r.read())
                break
            except Exception as e:  # noqa: BLE001
                if i == 3:
                    raise
                time.sleep(2 * (i + 1))
        cs = root.findall(f"{NS}Contents")
        for c in cs:
            out.append({"key": c.find(f"{NS}Key").text, "size": int(c.find(f"{NS}Size").text),
                        "lm": c.find(f"{NS}LastModified").text})
        if root.find(f"{NS}IsTruncated").text != "true" or not cs:
            return out
        marker = cs[-1].find(f"{NS}Key").text


def main() -> None:
    res = {}
    for p in sys.argv[2:]:
        items = list_prefix(p)
        z = [x for x in items if x["key"].endswith(".zip")]
        res[p] = z
        tot = sum(x["size"] for x in z)
        print(f"{p}: {len(z)} zip, {tot/1e9:.2f} GB, first={z[0]['key'].rsplit('/',1)[-1] if z else None} last={z[-1]['key'].rsplit('/',1)[-1] if z else None}", flush=True)
    json.dump(res, open(sys.argv[1], "w"), indent=0)


if __name__ == "__main__":
    main()
