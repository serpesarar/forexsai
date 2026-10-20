"""Supabase decider_journal'dan TÜM XAUUSD kayıtlarını (OPEN + WAIT) ham JSONL olarak indirir.
Çıktı: data/journal_xau_raw.jsonl (bir satır = bir kayıt, raw jsonb dahil)."""
import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parents[1] / "backend" / ".env")
url = os.environ["SUPABASE_URL"]
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
sb = create_client(url, key)
PAGE = 200
out = HERE / "data" / "journal_xau_raw.jsonl"
n = 0
with open(out, "w") as f:
    start = 0
    while True:
        r = (sb.table("decider_journal").select("id,host,ts,symbol,decision,confidence,outcome,raw")
             .eq("symbol", "XAUUSD").order("ts").range(start, start + PAGE - 1).execute())
        rows = r.data or []
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
        if len(rows) < PAGE:
            break
        start += PAGE
print("yazıldı", n, out)
