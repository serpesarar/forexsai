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


def _path_of(e, src):
    """Etiket kaynağına uygun yol metriği (real→path, cf→cf_path). ⚠ Yol metrikleri
    SONUÇTAN türetilir → _flatten'a ASLA girmez (etiket sızıntısı); yalnız segmentasyon."""
    return e.get("path") if src == "real" else e.get("cf_path")


def _subtype(lab, path):
    """Yol-tabanlı alt-tip — kaybın/kazancın KARAKTERİ (dersler zıt olduğu için ayrışır):
    LOSS_instant (mfe<0.25R, direkt SL)=GİRİŞ hatası · LOSS_reversal (mfe≥0.6R, önce
    lehte koştu)=giriş doğru ÇIKIŞ hatası · WIN_lucky (mae≥0.8R, SL'e sürtündü)=kırılgan."""
    if not path or not lab:
        return None
    if lab == "LOSS":
        m = path.get("mfe_r")
        if m is None:
            return None
        return "LOSS_instant" if m < 0.25 else ("LOSS_reversal" if m >= 0.6 else "LOSS_mid")
    if lab == "WIN":
        m = path.get("mae_r")
        if m is None:
            return None
        return "WIN_lucky" if m >= 0.8 else ("WIN_clean" if m < 0.4 else "WIN_mid")


def path_quality(rows):
    """[SL/TP YOL ANALİZİ] — 'maksimum SL/TP analizi': kayıplar NASIL kaybetti, kazançlar
    NASIL kazandı? Her pay eyleme çevrilir (giriş mi çıkış mı stop mu TP mi sorunlu)."""
    L, W = [], []
    for e in rows:
        lab, d, src = _label_dir(e)
        p = _path_of(e, src)
        if p and lab in ("WIN", "LOSS"):
            (L if lab == "LOSS" else W).append((e, p))
    print("=" * 70)
    print(f"SL/TP YOL ANALİZİ — kayıp: {len(L)}, kazanç: {len(W)} (yol-metrikli)")
    print("=" * 70)
    if len(L) < 5 and len(W) < 5:
        print("  ⏳ yol-metrikli kayıt az (YENİ alan — resolve dolduracak).")
        return
    if L:
        n = len(L)
        inst = [x for x in L if _subtype("LOSS", x[1]) == "LOSS_instant"]
        rev = [x for x in L if _subtype("LOSS", x[1]) == "LOSS_reversal"]
        near = [x for x in L if (x[1].get("tp_progress") or 0) >= 0.85]
        hunt = [x for x in L if x[1].get("sl_recovered_entry")]
        sltp = [x for x in L if x[1].get("sl_then_tp")]
        print(f"\n[KAYIPLAR NASIL KAYBETTİ] (n={n})")
        print(f"  anlık-kayıp (mfe<0.25R):    {len(inst):>3} (%{100*len(inst)/n:.0f}) → GİRİŞ sorunu (aşağıdaki entry-saflığına bak)")
        print(f"  dönüş-kaybı (mfe≥0.6R):     {len(rev):>3} (%{100*len(rev)/n:.0f}) → giriş DOĞRUYDU, ÇIKIŞ sorunu")
        if rev:
            pols = {}
            for e, _ in rev:                       # bu kayıpları hangi çıkış kurtarırdı?
                for pol, v in (e.get("exit_grades") or {}).items():
                    if isinstance(v, (int, float)):
                        pols.setdefault(pol, []).append(v)
            if pols:
                best = max(pols, key=lambda k: sum(pols[k]) / len(pols[k]))
                bavg = sum(pols[best]) / len(pols[best])
                print(f"      ↳ kurtarıcı çıkış: '{best}' bu işlemlerde ort {bavg:+.2f} ATR verirdi (exit_compare teyidi ara)")
        print(f"  TP'ye %85+ yaklaşıp döndü:  {len(near):>3} (%{100*len(near)/n:.0f}) → 'TP birazcık uzaktı' (TP kalibrasyonu)")
        print(f"  SL-AVI — SL sonrası entry'ye döndü: {len(hunt)} (%{100*len(hunt)/n:.0f}); "
              f"orijinal TP'ye ULAŞTI: {len(sltp)} (%{100*len(sltp)/n:.0f}) → yön doğru, STOP dar")
        tsl = [x[1]["bars_to_outcome"] for x in L if x[1].get("bars_to_outcome")]
        if tsl:
            print(f"  SL'e ortalama süre: {sum(tsl)/len(tsl):.0f} bar")
    if W:
        lucky = [x for x in W if _subtype("WIN", x[1]) == "WIN_lucky"]
        print(f"\n[KAZANÇLAR NASIL KAZANDI] (n={len(W)})")
        print(f"  şanslı/kırılgan (mae≥0.8R): {len(lucky)} (%{100*len(lucky)/len(W):.0f}) → bunları giriş-pattern teyidi SAYMA")
        ttp = [x[1]["bars_to_outcome"] for x in W if x[1].get("bars_to_outcome")]
        if ttp:
            print(f"  TP'ye ortalama süre: {sum(ttp)/len(ttp):.0f} bar")
    # ENTRY SAFLIĞI — en saf kıyas: anlık-kayıp vs temiz-kazanç (orta/karışık tipler dışarıda
    # → çıkış-kaynaklı gürültü elenir, giriş sinyali konsantre olur)
    pure = []
    for e in rows:
        lab, d, src = _label_dir(e)
        if _subtype(lab, _path_of(e, src)) in ("LOSS_instant", "WIN_clean"):
            pure.append(e)
    if len(pure) >= MIN_SIDE * 2:
        print()
        _report(pure, "ENTRY SAFLIĞI — anlık-kayıp vs temiz-kazanç (en saf giriş sinyali)")


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


def bh_pass(results, alpha=0.05):
    """Benjamini-Hochberg FDR: p-artan sıralı results'ta en büyük k öyle ki p_k ≤ α·k/m →
    ilk k özellik geçer. Naif p<α, m özellikte ~m·α şans-pozitifi üretir; BH bunu düzeltir."""
    m = len(results)
    bh_k = 0
    for rank, row in enumerate(results, 1):
        if row[5] <= alpha * rank / m:
            bh_k = rank
    return {results[i][0] for i in range(bh_k)}


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
    bh = bh_pass(results)
    show = 16
    print(f"\n{'özellik':<24}{'n(W/L)':>9}{'WIN ort':>9}{'LOSS ort':>9}{'p':>8}  yorum")
    print("-" * 76)
    cands = []
    for k, nw, nl, mw, ml, p in results[:show]:
        tag = ("✅✅ GÜÇLÜ" if (p < 0.01 and k in bh)
               else "✅ aday(FDR)" if k in bh
               else "⏳ izle" if p < 0.15 else "")
        print(f"{k:<24}{f'{nw}/{nl}':>9}{mw:>9.2f}{ml:>9.2f}{p:>8.3f}  {tag}")
        if k in bh:
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
    print()
    path_quality(rows)          # SL/TP yol analizi + entry-saflığı
    if cands:
        print("\n[ADAY FİLTRELER] (FDR-geçti; LESSONS'a yazmak için --write)")
        for c in cands:
            print("  •", c)
        if "--write" in sys.argv:
            write_candidates_block(cands)
            print("  → LESSONS.md POST-MORTEM bloğu GÜNCELLENDİ (replace — şişme yok; "
                  "kararı otomatik ETKİLEMEZ).")
    else:
        print("\n(FDR-geçen ayırıcı yok — kayıplar bu özelliklerle açıklanmıyor ya da veri az)")
    if "--llm" in sys.argv:
        llm_autopsy(rows)


PM_START = "<!-- POST-MORTEM AUTO START (post_mortem.py/distill üretir) -->"
PM_END = "<!-- POST-MORTEM AUTO END -->"


def write_candidates_block(lines: list[str], confirmed: list[str] | None = None,
                           title_extra: str = ""):
    """LESSONS'taki POST-MORTEM bloğunu REPLACE eder (append DEĞİL → her koşuda şişip her
    karar promptunu kirletmez). distill_journal da bu fonksiyonla aynı bloğu yönetir.
    confirmed: ≥2 ardışık distill'de FDR-geçen KANIT-TEYİTLİ dersler (karar bunlara güvenir)."""
    from datetime import datetime
    parts = [f"{PM_START}", f"### 🔬 Post-mortem ({datetime.now():%Y-%m-%d}){title_extra}"]
    if confirmed:
        parts.append("**✅ KANIT-TEYİTLİ** (≥2 ardışık FDR — karar verirken dikkate al):")
        parts += [f"- ✅ {c}" for c in confirmed]
    if lines:
        parts.append("İzlenen adaylar (henüz teyitsiz — kararı ETKİLEMEZ):")
        parts += [f"- ⏳ {c}" for c in lines]
    if not confirmed and not lines:
        parts.append("(şu an aday yok)")
    parts.append(PM_END)
    body = "\n".join(parts)
    txt = LESSONS.read_text(encoding="utf-8") if LESSONS.exists() else "# Decider LESSONS\n"
    if PM_START in txt and PM_END in txt:
        pre = txt[:txt.index(PM_START)]
        post = txt[txt.index(PM_END) + len(PM_END):]
        txt = pre + body + post
    else:
        txt = txt.rstrip() + "\n\n" + body + "\n"
    LESSONS.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
