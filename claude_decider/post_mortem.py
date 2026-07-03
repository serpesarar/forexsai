"""
post_mortem.py — SL OTOPSİSİ: kaybedenleri kazananlardan AYIRAN koşulu bul.
=============================================================================
Kullanıcının "beynimdeki analiz": 5 işlemden 3'ü SL olduysa → o anki hacim neydi, VIX
neydi, trend kanalına ne kadar uzaktı, hangi TF'te hangi destek/dirence çarpıyordu,
o seviye geçmişte kaç kez tutmuştu? Bunları HER kayıttaki forensik snapshot'tan çıkarır,
WIN vs LOSS dağılımlarını kıyaslar, placebo-kapılı ayırıcıyı raporlar.

Veri: journal'daki forensics'li kayıtlar. Etiket = gerçek outcome (OPEN) VEYA cf_outcome
(WAIT counterfactual) → az-işlem sorununu counterfactual'lar çözer (bol örnek).

Yön-hizalı türetilmiş özellikler (kritik):
 - opp_sr_dist_{tf}: KARŞI seviyeye ATR-mesafe (BUY→direnç, SELL→destek). Hipotez:
   "girişte karşı S/R çok yakındı → TP'ye yer yoktu → SL".
 - opp_sr_touches_{tf}: karşı seviyenin gücü (çok dokunulmuş = sert duvar).
 - beh_sr_dist_{tf}: ARKA seviye (BUY→destek) mesafesi — stop koruması var mıydı?

Çıktı: [1] ayırıcı tablo (perm p<0.05 → aday filtre), [2] --llm ile nitel otopsi
(Fable, tek toplu çağrı, ucuz) → hipotez cümleleri, [3] --write ile LESSONS'a aday ekler.
"""
from __future__ import annotations
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decide import JOURNAL_JSONL, call_claude  # noqa: E402

random.seed(17)
PERM_M = 400
MIN_SIDE = 8          # her tarafta (win/loss) min örnek
TFS = ("1m", "5m", "30m", "1h", "4h")
LESSONS = HERE / "memory" / "LESSONS.md"


def _load():
    if not JOURNAL_JSONL.exists():
        return []
    return [json.loads(l) for l in JOURNAL_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _label_dir(e):
    """(etiket WIN/LOSS/None, yön, kaynak). Gerçek OPEN öncelikli; yoksa counterfactual."""
    if e.get("outcome") in ("WIN", "LOSS"):
        return e["outcome"], (e.get("decision") or {}).get("direction"), "real"
    if e.get("cf_outcome") in ("WIN", "LOSS"):
        return e["cf_outcome"], (e.get("counterfactual") or {}).get("dir"), "cf"
    return None, None, None


def _session_of(e):
    return ((e.get("context") or {}).get("session")
            or (e.get("free_context") or {}).get("session"))


def _flatten(e, direction):
    """Forensik snapshot → düz özellik sözlüğü. TÜMÜ yön-hizalı veya yön-nötr:
    - rev_chan/rev_vwap: (−z BUY / +z SELL) → pozitif = işlem yönü LEHİNE mean-rev aşırılığı.
      HAM z havuzlanMAZ (BUY+SELL karışınca sinyali yıkar / yön-kompozisyon artefaktı üretir).
    - Kategorikler 0/1 gösterge: opp/beh_last_bounce (kullanıcı hipotezi: "seviye geçmişte
      döndü mü"), {tf}_trend_aligned, session one-hot, n_tf_trend_aligned/anti sayaçları.
    """
    fx = e.get("forensics") or {}
    tfs = fx.get("tfs") or {}
    out = {}
    mac = fx.get("macro") or {}
    if mac.get("vix") is not None:
        out["vix"] = float(mac["vix"])
    if mac.get("dxy") is not None:
        out["dxy"] = float(mac["dxy"])
    sess = _session_of(e)
    if sess:
        for s in ("NY", "Londra", "Asya"):
            out[f"session_{s}"] = 1.0 if sess == s else 0.0
    buy = str(direction or "").upper() == "BUY"
    n_al = n_anti = 0
    for tf in TFS:
        f = tfs.get(tf)
        if not f:
            continue
        # K1 — YÖN-HİZALI z (evidence.rev ile aynı tanım)
        if f.get("channel_z") is not None:
            z = float(f["channel_z"])
            out[f"{tf}_rev_chan"] = (-z) if buy else z
        if f.get("vwap_z") is not None:
            v = float(f["vwap_z"])
            out[f"{tf}_rev_vwap"] = (-v) if buy else v
        for k in ("adx", "vol_ratio"):                    # yön-nötr → ham
            if f.get(k) is not None:
                out[f"{tf}_{k}"] = float(f[k])
        # K2 — trend uyumu (kullanıcının "TF'ler uyumlu mu" sorusu)
        tr = f.get("trend")
        if tr in ("yukari", "asagi"):
            aligned = (tr == "yukari") == buy
            out[f"{tf}_trend_aligned"] = 1.0 if aligned else 0.0
            n_al += 1 if aligned else 0
            n_anti += 0 if aligned else 1
        sr = f.get("sr") or {}
        opp = sr.get("res") if buy else sr.get("sup")     # KARŞI seviye (TP yönünde duvar)
        beh = sr.get("sup") if buy else sr.get("res")     # ARKA seviye (stop tarafı)
        if opp:
            out[f"{tf}_opp_sr_dist"] = float(opp["dist_atr"])
            out[f"{tf}_opp_sr_touches"] = float(opp["touches"])
            if opp.get("last_reaction") in ("bounce", "broke"):   # K2 — kullanıcı hipotezi
                out[f"{tf}_opp_last_bounce"] = 1.0 if opp["last_reaction"] == "bounce" else 0.0
        if beh:
            out[f"{tf}_beh_sr_dist"] = float(beh["dist_atr"])
            if beh.get("last_reaction") in ("bounce", "broke"):
                out[f"{tf}_beh_last_bounce"] = 1.0 if beh["last_reaction"] == "bounce" else 0.0
    if n_al + n_anti:
        out["n_tf_trend_aligned"] = float(n_al)
        out["n_tf_trend_anti"] = float(n_anti)
    return out


def _perm_p(wins, losses, M=PERM_M):
    """|mean fark| permütasyon p."""
    obs = abs(sum(wins) / len(wins) - sum(losses) / len(losses))
    allv = wins + losses; nw = len(wins); ge = 0
    for _ in range(M):
        sh = random.sample(allv, len(allv))
        if abs(sum(sh[:nw]) / nw - sum(sh[nw:]) / len(sh[nw:])) >= obs:
            ge += 1
    return (ge + 1) / (M + 1)


def analyze(rows):
    """WIN vs LOSS ayırıcı tablo. Dönüş: [(feat, n_w, n_l, mean_w, mean_l, p), ...]"""
    feats = defaultdict(lambda: {"W": [], "L": []})
    used = 0
    for e in rows:
        lab, d, src = _label_dir(e)
        if not lab or not e.get("forensics"):
            continue
        used += 1
        for k, v in _flatten(e, d).items():
            feats[k]["W" if lab == "WIN" else "L"].append(v)
    results = []
    for k, s in feats.items():
        if len(s["W"]) >= MIN_SIDE and len(s["L"]) >= MIN_SIDE:
            mw, ml = sum(s["W"]) / len(s["W"]), sum(s["L"]) / len(s["L"])
            p = _perm_p(s["W"], s["L"])
            results.append((k, len(s["W"]), len(s["L"]), mw, ml, p))
    results.sort(key=lambda x: x[5])
    return results, used


def llm_autopsy(rows, model="claude-fable-5", max_cases=12):
    """Nitel otopsi: son kaybedenlerin snapshot'larını LLM'e ver → 'neden SL' hipotezleri.
    TEK toplu çağrı (ucuz). Çıktı = hipotez listesi (aday; istatistik teyidi post_mortem [1])."""
    cases = []
    for e in reversed(rows):
        lab, d, src = _label_dir(e)
        if lab == "LOSS" and e.get("forensics"):
            cases.append({"symbol": e.get("symbol"), "dir": d, "src": src,
                          "feats": _flatten(e, d)})
        if len(cases) >= max_cases:
            break
    if len(cases) < 4:
        print(f"  (LLM otopsi için az kayıp: {len(cases)}/4)"); return
    wins = []
    for e in reversed(rows):
        lab, d, _ = _label_dir(e)
        if lab == "WIN" and e.get("forensics"):
            wins.append({"symbol": e.get("symbol"), "dir": d, "feats": _flatten(e, d)})
        if len(wins) >= max_cases:
            break
    prompt = f"""Sen kıdemli bir trading post-mortem analistisin. Aşağıda KAYBEDEN ve KAZANAN
işlemlerin giriş-anı forensik özellikleri var (channel_z=trend kanalında konum, opp_sr_dist=
karşı destek/dirence ATR mesafe, opp_sr_touches=o seviyenin gücü, vol_ratio=hacim oranı,
vix/dxy=makro). GÖREV: kaybedenleri kazananlardan ayıran EN GÜÇLÜ 3 örüntüyü bul; her biri
için tek cümlelik FİLTRE ÖNERİSİ (ör. "4h karşı dirence <1 ATR iken BUY açma").
Uydurma — yalnız verideki farklara dayan. Çıktın SADECE şu tek-satır JSON:
{{"hypotheses":["örüntü+filtre 1","örüntü+filtre 2","örüntü+filtre 3"]}}

KAYBEDENLER ({len(cases)}):
{json.dumps(cases, ensure_ascii=False)}

KAZANANLAR ({len(wins)}):
{json.dumps(wins, ensure_ascii=False)}"""
    dec = call_claude(prompt, model=model)
    hyps = dec.get("hypotheses")
    print("\n[LLM OTOPSİ — hipotezler (istatistik teyidi şart, otomatik uygulanmaz)]")
    if isinstance(hyps, list) and hyps:
        for h in hyps:
            print("  •", h)
    else:
        print("  (parse edilemedi)", str(dec.get("_raw") or dec.get("reason") or "")[:300])
    return hyps


def _report(rows, title):
    results, used = analyze(rows)
    print("=" * 70)
    print(f"{title} (forensik'li grade'li kayıt: {used})")
    print("=" * 70)
    if not results:
        print("  ⏳ yeterli kayıt yok (her tarafta ≥%d gerek).\n" % MIN_SIDE)
        return []
    n_feat = len(results)
    # Benjamini-Hochberg FDR: p'ler artan sıralı (results zaten sıralı) →
    # en büyük k öyle ki p_k ≤ 0.05·k/m; ilk k özellik FDR-geçer. Çoklu-karşılaştırmayı
    # DÜZGÜN çözer (naif p<0.05, ~m/20 şans-pozitifi üretir).
    bh_k = 0
    for rank, (_, _, _, _, _, p) in enumerate(results, 1):
        if p <= 0.05 * rank / n_feat:
            bh_k = rank
    bh_pass = {results[i][0] for i in range(bh_k)}
    show = 16
    print(f"\n{'özellik':<24}{'n(W/L)':>9}{'WIN ort':>9}{'LOSS ort':>9}{'p':>8}  yorum")
    print("-" * 76)
    cands = []
    for k, nw, nl, mw, ml, p in results[:show]:
        tag = ("✅✅ GÜÇLÜ" if (p < 0.01 and k in bh_pass)
               else "✅ aday(FDR)" if k in bh_pass
               else "⏳ izle" if p < 0.15 else "")
        print(f"{k:<24}{f'{nw}/{nl}':>9}{mw:>9.2f}{ml:>9.2f}{p:>8.3f}  {tag}")
        if k in bh_pass:
            yon = "düşük" if ml < mw else "yüksek"
            cands.append(f"{k}: kayıplarda {yon} (W ort {mw:.2f} vs L {ml:.2f}, p={p:.3f})")
    if n_feat > show:
        print(f"  … (+{n_feat - show} özellik daha, p yüksek — gizlendi)")
    print(f"\n  ⚠ {n_feat} özellik test edildi; aday etiketi FDR-düzeltmeli (BH %5) — naif p<0.05 değil.")
    print("    Yine de tek koşuya güvenme: ✅✅ + distill/tekrar-koşu teyidi kalıcılık şartı.")
    return cands


def main():
    rows = _load()
    cands = _report(rows, "SL OTOPSİSİ — TÜM SEMBOLLER (WIN'i LOSS'tan ayıran koşul)")
    # Per-sembol: havuz karışması (ör. XAU kayıpları domine) sembol-özelliği yakalamasın
    by_sym = defaultdict(list)
    for e in rows:
        lab, _, _ = _label_dir(e)
        if lab and e.get("forensics"):
            by_sym[e.get("symbol")].append(e)
    for sym, items in sorted(by_sym.items()):
        if len(items) >= MIN_SIDE * 3:
            _report(items, f"SEMBOL: {sym}")
    if cands:
        print("\n[ADAY FİLTRELER] (placebo-geçti; LESSONS'a yazmak için --write)")
        for c in cands:
            print("  •", c)
        if "--write" in sys.argv:
            from datetime import datetime
            block = ("\n### 🔬 Post-mortem adayları (" + datetime.now().strftime("%Y-%m-%d") + ")\n"
                     + "\n".join(f"- ⏳ {c}" for c in cands) + "\n")
            LESSONS.write_text(LESSONS.read_text(encoding="utf-8") + block, encoding="utf-8")
            print("  → LESSONS.md'ye '⏳ izlenen' olarak eklendi (kararı otomatik ETKİLEMEZ).")
    else:
        print("\n(placebo-geçen ayırıcı yok — kayıplar bu özelliklerle açıklanmıyor ya da veri az)")
    if "--llm" in sys.argv:
        llm_autopsy(rows)


if __name__ == "__main__":
    main()
