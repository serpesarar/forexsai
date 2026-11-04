"""Generate an offline, searchable research catalogue from static evidence."""
from __future__ import annotations

from collections import Counter
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> None:
    code = json.loads((ROOT / "IMPLEMENTATIONS.json").read_text())
    discovery = json.loads((ROOT / "TRADINGVIEW_DISCOVERY.json").read_text())
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text())
    families = []
    for index, line in enumerate((ROOT / "families.tsv").read_text().splitlines()):
        name, category, data, explanation, aliases, caveat = line.split("|")
        keys = {norm(x) for x in aliases.split(",")}
        matches = [r for r in code if norm(r["name"]) in keys or norm(Path(r["local_path"]).stem) in keys]
        families.append({"id": f"FAM-{index+1:03}", "name": name, "family": category, "inputs": data,
                         "explanation": explanation, "caveat": caveat,
                         "implementations": [r["id"] for r in matches],
                         "source_matches_are_discovery_not_equivalence_proof": True})
    (ROOT / "FAMILIES.json").write_text(json.dumps(families, ensure_ascii=False, indent=2))
    lines = ["# Indicator and analysis families\n\n", "120 research cards. Names and aliases preserve English, Japanese and Chinese terminology. Linked source matches are navigation aids: matching a name does not establish mathematical equivalence or runtime correctness. A card with no local match has no exact local implementation claimed; use the linked publication directory and report for external sources. All four target markets require independent execution and profitability validation.\n\n"]
    for family in families:
        lines.extend([f"## {family['id']} — {family['name']}\n\n",
                      f"**Group:** {family['family']}  \n**Required data:** {family['inputs']}\n\n",
                      f"{family['explanation']}\n\n**Implementation detail:** {family['caveat']}\n\n"])
        matches = [r for r in code if r['id'] in family['implementations']]
        if matches:
            lines.append("**Source implementations:**\n\n")
            for row in matches:
                lines.append(f"- {row['id']} — {row['repository']} / {row['name']}: [local source]({row['local_path']}) · [pinned upstream]({row['source_url']}); {row['status']}.\n")
        else:
            lines.append("**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.\n")
        lines.append("\n")
    (ROOT / "FAMILIES.md").write_text(''.join(lines))

    tv = sorted(discovery['records'], key=lambda r: r.get('title', '').lower())
    lines = ["# TradingView public publications\n\n",
             f"{len(tv)} distinct script IDs from the first page of 24 topics plus selected publications. This is a bounded discovery inventory, not all TradingView scripts and not an endorsement. Only selected detail pages had code-access badges checked; source code was not downloaded for these publication records. Pine snapshots are separately provided in vendor/everget__tradingview-pinescript-indicators. Listing descriptions are short excerpts supplied by their authors; claims have not been independently validated.\n\n",
             "| Publication | Discovery topics | Code access evidence | Author description excerpt |\n|---|---|---|---|\n"]
    for row in tv:
        desc = re.sub(r'\s+', ' ', row.get('description_excerpt', '')).replace('|', '/')
        lines.append(f"| [{row.get('title') or row['script_id']}]({row['url']}) | {', '.join(row.get('topics', []))} | {row.get('code_access', 'not_checked_listing_only')} | {desc} |\n")
    (ROOT / "TRADINGVIEW_PUBLICATIONS.md").write_text(''.join(lines))

    lines = ["# Source provenance and licences\n\n", "Sources were collected at pinned commits. File hashes prove snapshot integrity, not algorithm correctness. Vendor code has not been imported, installed, compiled or executed. Source snapshots contain selected computational directories and licence notices, not necessarily complete buildable repositories. Download the full pinned repository for dependencies and build files.\n\n",
             "| Repository | Commit | Indexed records | Files copied | Licence evidence |\n|---|---|---:|---:|---|\n"]
    counts = Counter(r['repository'] for r in code)
    for repo in manifest:
        name = repo['repository']
        if 'error' in repo:
            lines.append(f"| {name} | — | — | — | {repo['error']} |\n")
            continue
        license_evidence = repo['license_api']
        if name == 'mpquant/MyTT':
            license_evidence = 'README badge says GPL; no root licence text/version. Code excluded from distributable archive; upstream links retained.'
        elif name == 'waditu/czsc':
            license_evidence = 'Root LICENSE contains Apache-2.0 notice; API NOASSERTION. Rust subcrate terms need separate confirmation; code excluded from distributable archive.'
        lines.append(f"| [{name}](https://github.com/{name}) | [{repo['commit'][:12]}]({repo['source_url']}) | {counts[name]} | {repo['file_count']} | {license_evidence} |\n")
    lines.extend(["\nMIT, BSD and Apache terms differ from GPL/LGPL. Research copies do not change the vendor licence. Preserve notices and apply the actual licence terms before integration or redistribution. GPL/LGPL source is kept separately from ForexSAI runtime code.\n\n",
                  "The archive omits MyTT and CZSC code because the collected licensing evidence is incomplete for redistribution. Their pinned links, function indexes and local research copies remain identifiable. No proprietary, invite-only, leaked or paywall-bypassed source is included.\n"])
    (ROOT / "SOURCES_AND_LICENSES.md").write_text(''.join(lines))

    previous = Path('/private/tmp/tradingview_catalog_2026-10-25/TradingView_Indikator_Katalogu_TR.md')
    if previous.exists():
        shutil.copy2(previous, ROOT / 'TRADINGVIEW_BUILTINS_239.md')

    payload = {'families': families, 'code': code, 'tradingview': tv}
    data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    shell = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Indicator Research Atlas — 25 October 2026</title>
<style>
:root{color-scheme:light dark;--bg:light-dark(#f4f5f7,#13171d);--fg:light-dark(#172331,#e5ebf3);--card:light-dark(#fff,#1e2630);--line:light-dark(#d1d8e1,#394657);--muted:light-dark(#526275,#aebdd0);--link:light-dark(#125bb4,#8dbfff)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:28px}h1{font-size:29px;margin-bottom:6px}p{max-width:950px;color:var(--muted)}a{color:var(--link)}nav{display:flex;gap:10px;flex-wrap:wrap}button,input,select{font:inherit;padding:10px 14px;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:7px}button{cursor:pointer}button[aria-pressed=true]{outline:2px solid var(--link)}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}input{flex:1;min-width:230px}.entry{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:18px;margin:13px 0}.entry h2{font-size:19px;margin:0 0 5px}.meta{color:var(--muted);font-size:13px}.entry p{margin:7px 0}#more{margin-top:15px}code{overflow-wrap:anywhere}details{margin-top:10px}summary{cursor:pointer}header{padding-bottom:16px}#count{margin:10px 0}footer{margin-top:35px;color:var(--muted)}
</style></head><body><main><header><h1>Indicator Research Atlas</h1><p>25 October 2026 · Gold, WTI crude oil, DAX and Nasdaq-100. A source research catalogue: 120 method families, code implementations and public TradingView discoveries. Counts are records, not unique profitable indicators.</p>
<nav><a href="REPORT.md">Research report</a><a href="SOURCES_AND_LICENSES.md">Provenance & licences</a><a href="TRADINGVIEW_BUILTINS_239.md">239 built-in help pages</a><a href="README.md">Scope & usage</a></nav></header>
<nav aria-label="Catalogue section"><button data-tab="families" aria-pressed="true">Method families</button><button data-tab="code" aria-pressed="false">Source code</button><button data-tab="tradingview" aria-pressed="false">TradingView publications</button></nav>
<div class="controls"><input id="query" type="search" aria-label="Search" placeholder="Search: Ichimoku, KDJ, 缠论, Ehlers, VWAP…"><select id="repo" aria-label="Source repository"><option value="">All repositories</option></select></div><div id="count" aria-live="polite"></div><div id="results"></div><button id="more">Show 80 more</button>
<footer>No vendor code runs here. Source-code presence, an open-source badge and profitability are different claims. Some local research sources are omitted from the ZIP; use pinned upstream links in those cases.</footer>
<script id="atlas-data" type="application/json">PAYLOAD</script><script>
const data=JSON.parse(document.getElementById('atlas-data').textContent);
let tab='families',limit=80;const byId=new Map(data.code.map(r=>[r.id,r]));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=(url,label)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(label)+'</a>';
for(const name of [...new Set(data.code.map(r=>r.repository))].sort()){const o=document.createElement('option');o.value=name;o.textContent=name;document.getElementById('repo').appendChild(o)}
function card(r){
 if(tab==='families'){const sources=r.implementations.map(id=>byId.get(id));return '<article class="entry"><h2>'+esc(r.name)+'</h2><div class="meta">'+esc(r.id+' · '+r.family+' · '+r.inputs)+'</div><p>'+esc(r.explanation)+'</p><p><strong>Implementation detail:</strong> '+esc(r.caveat)+'</p><details><summary>'+sources.length+' exact-name source matches</summary>'+sources.map(s=>'<p>'+esc(s.repository+' / '+s.name)+' · '+link(s.source_url,'Pinned source')+' · '+link(s.local_path,'Local file')+' <span class="meta">'+esc(s.status)+'</span></p>').join('')+'</details></article>'}
 if(tab==='code')return '<article class="entry"><h2>'+esc(r.name)+'</h2><div class="meta">'+esc(r.id+' · '+r.repository+' · '+r.language+' · '+r.family+' · '+r.record_kind)+'</div><p>'+esc(r.description_from_source||'Formula is in the linked source file; no separate prose description was extracted.')+'</p><p>'+link(r.source_url,'Pinned upstream source')+' · '+link(r.local_path,'Local source file')+'</p><details><summary>Signature, licence and review flags</summary><p><code>'+esc(r.signature)+'</code></p><p>'+esc(r.license)+' · '+esc(r.status)+'</p><p>'+esc(r.temporal_review_triggers.join(', ')||'No listed lexical trigger; this is not a causality certification.')+'</p></details></article>';
 return '<article class="entry"><h2>'+link(r.url,r.title||r.script_id)+'</h2><div class="meta">'+esc((r.topics||[]).join(', ')+' · '+(r.code_access||'Listing only; code access not checked'))+'</div><p>'+esc(r.description_excerpt)+'</p><div class="meta">Author description excerpt; performance claims unverified. Source code not downloaded for this publication record.</div></article>';
}
function render(){const q=document.getElementById('query').value.trim().toLocaleLowerCase();const repo=document.getElementById('repo').value;document.getElementById('repo').disabled=tab!=='code';const rows=data[tab].filter(r=>(tab!=='code'||!repo||r.repository===repo)&&(!q||JSON.stringify(r).toLocaleLowerCase().includes(q)));document.getElementById('count').textContent=rows.length+' records · showing '+Math.min(rows.length,limit);document.getElementById('results').innerHTML=rows.slice(0,limit).map(card).join('');document.getElementById('more').hidden=rows.length<=limit}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.tab;limit=80;document.querySelectorAll('[data-tab]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render()}));
document.getElementById('query').addEventListener('input',()=>{limit=80;render()});document.getElementById('repo').addEventListener('change',()=>{limit=80;render()});document.getElementById('more').addEventListener('click',()=>{limit+=80;render()});render();
</script></main></body></html>'''
    (ROOT / 'catalog.html').write_text(shell.replace('PAYLOAD', data))
    print(f"Published {len(families)} family cards, {len(code)} source records, {len(tv)} TradingView publications.")


if __name__ == '__main__':
    main()
