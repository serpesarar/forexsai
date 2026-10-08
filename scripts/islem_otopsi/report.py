"""rapor.md + özet.json üretimi. Sayılar → kurala dayalı Türkçe cümleler; yorum dili
kanıt düzeyine bağlı (q/p/AUC gücü) — "kanıtlandı" kelimesi bu dosyada YOK, bilerek.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings as S
from .narrative import tr_num

VOLUME_FEATURES = [
    ("pre_vol_seas_15", "giriş öncesi 15 dk hacim (saatine göre)"),
    ("pre_vol_slope_30", "giriş öncesi 30 dk hacim eğimi"),
    ("pre_vol_dir_30", "giriş öncesi lehte/aleyhte bar hacmi (log2)"),
    ("e15_vol_seas", "ilk 15 dk hacim (hâlâ açık olanlar)"),
    ("e15_vol_dir", "ilk 15 dk lehte/aleyhte hacim (log2)"),
    ("path_vol_seas", "işlem boyu ortalama hacim"),
    ("path_vol_last_vs_first", "son üçte bir / ilk üçte bir hacim"),
    ("path_vol_pre_exit10", "çıkıştan önceki 10 dk hacim"),
    ("path_vol_exit_bar", "çıkış barı hacmi"),
    ("path_final_leg_vol", "çıkışa götüren bacak / ilk bacak hacmi"),
    ("path_mfe_vol_vs_start", "en iyi noktadaki hacim / başlangıç"),
    ("path_vol_dir", "işlem boyu lehte/aleyhte hacim (log2)"),
]


def strength(a: float, q: float, p: float) -> str:
    if not np.isfinite(a):
        return "yetersiz örneklem"
    g = abs(a - 0.5)
    lab = "yok" if g < 0.05 else "zayıf" if g < 0.10 else "orta" if g < 0.20 else "güçlü"
    sig = ("çoklu-test sonrası anlamlı" if np.isfinite(q) and q < S.FDR_Q
           else "nominal p<0,05 (çoklu test sonrası değil)" if np.isfinite(p) and p < 0.05 else "tesadüf düzeyinde")
    return f"{lab} ayrım, {sig}"


def md_table(df: pd.DataFrame, fmt: dict | None = None, max_rows: int = 40) -> str:
    if df is None or df.empty:
        return "_(veri yok)_"
    fmt = fmt or {}
    d = df.head(max_rows)
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns)
    body = []
    ints = {c for c in d.columns if pd.api.types.is_integer_dtype(d[c])}
    for i in range(len(d)):
        cells = []
        for c in d.columns:
            v = d[c].iat[i]
            if c in ints and c not in fmt:
                cells.append(str(int(v)))
            elif c in fmt and isinstance(v, (int, float, np.floating, np.integer)) and np.isfinite(v):
                cells.append(fmt[c](v))
            elif isinstance(v, (float, np.floating)):
                cells.append(tr_num(v, 2))
            else:
                cells.append(str(v))
        body.append("| " + " | ".join(cells) + " |")
    return head + "\n" + "\n".join(body)


PCT = lambda v: "%" + tr_num(v * 100, 1)  # noqa: E731
USD = lambda v: tr_num(v, 0) + " $"  # noqa: E731
R2 = lambda v: tr_num(v, 2, True)  # noqa: E731
INT = lambda v: str(int(v))  # noqa: E731


def sec_gate(ctx: dict) -> str:
    al, gw = ctx["align"], ctx.get("geometry", {})
    ex = al.excluded
    lines = ["## 0. Güvenilirlik kapısı (önce bunu oku)",
             f"- **Saat ekseni:** {al.status} — işlemlerin %{tr_num(al.aligned_frac * 100, 1)}'inde giriş VE çıkış fiyatı "
             f"mumla eşleşti; kayma dağılımı (saat): {al.offset_counts}. Dışlanan: {len(ex)}"
             + (f" ({'; '.join(f'#{p}: {w}' for p, w in ex[:5])})" if ex else ""),
             f"- **Yol doğrulaması:** saf geometri yeniden oynatması gerçek TP/SL sınıfını "
             f"%{tr_num(gw.get('uyum', np.nan) * 100, 1)} tuttu → {gw.get('durum', '—')}",
             f"- **Hacim verisi:** MT5 *tick* hacmi (fiyat güncelleme sayısı, borsa hacmi DEĞİL). Mevsimsel "
             f"düzeltilmiş (×1 = o saat diliminde normal). Dinamik aralık p10–p90: {ctx['vol_range']}",
             f"- **Bayat giriş verisi:** {ctx['stale_n']} işlemde girişten önceki son bar >10 dk eski (piyasa açılışı/boşluk)",
             f"- **Dönemler:** keşif {ctx['disc_span']} · odak {ctx['focus_span']}",
             f"- **Komut:** `{ctx['command']}`"]
    return "\n".join(lines)


def sec_summary(ctx: dict) -> str:
    rows = []
    for name, s in ctx["summaries"].items():
        if not s or not s.get("n"):
            continue
        lo, hi = s["ort_r_ci"]
        wl, wh = s["wr_ci"]
        rows.append({"dönem": name, "işlem": s["n"], "karar": s["karar"], "TP": s["tp"], "SL": s["sl"],
                     "WR [95%]": f"%{tr_num(s['wr'] * 100, 1)} [{tr_num(wl * 100, 0)}–{tr_num(wh * 100, 0)}]",
                     "başabaş WR": PCT(s["basabas_wr"]) if np.isfinite(s["basabas_wr"]) else "—",
                     "ort R [95%]": f"{R2(s['ort_r'])} [{R2(lo)}…{R2(hi)}]", "P(EV>0)": PCT(s["p_ev_pos"]) if np.isfinite(s["p_ev_pos"]) else "—",
                     "toplam R": R2(s["top_r"]), "net": USD(s["net_usd"])})
    out = ["## 1. Özet", md_table(pd.DataFrame(rows)),
           "\n_WR'ı tek başına okuma: başabaş WR = SL/(SL+TP) mesafe oranı; WR bunun üstünde değilse kâr yoktur (E14)._",
           "\n**Sonuç türleri (tüm dönem):**", md_table(ctx["mix"].reset_index().rename(columns={"index": "sonuç"}),
                                                       {"net_usd": USD, "ort_r": R2, "n": INT})]
    return "\n".join(out)


def sec_breakdowns(ctx: dict) -> str:
    fm = {"wr": PCT, "wr_lo": PCT, "wr_hi": PCT, "basabas_wr": PCT, "ort_r": R2, "top_r": R2, "net_usd": USD,
          "n": INT, "karar": INT, "sl": INT, "tp": INT}
    out = ["## 2. Kırılımlar — strateji, sembol-yön, seans (tüm dönem; net $'a göre en kötüden)"]
    for title, key in (("Strateji ailesi", "family"), ("Sembol · yön", "side"), ("Seans", "session"),
                       ("Strateji · sembol-yön", ["family", "side"])):
        out += [f"\n**{title}**", md_table(ctx["groups"][title], fm)]
    return "\n".join(out)


def _cause_table(t: pd.DataFrame, outcome: str) -> pd.DataFrame:
    from .narrative import CAUSE_LABELS
    d = t[t["outcome"] == outcome]
    g = d.groupby("ana_neden_kod")
    out = pd.DataFrame({"n": g.size(), "pay": g.size() / max(len(d), 1), "net_usd": g["net"].sum(),
                        "ort_r": g["r_exit"].mean()}).sort_values("n", ascending=False).reset_index()
    out.insert(1, "açıklama", out["ana_neden_kod"].map(CAUSE_LABELS))
    return out.rename(columns={"ana_neden_kod": "kod"})


def _share(a: dict, key: str) -> str:
    v = a.get(key)
    if not v:
        return "—"
    return f"{v[0]} (%{tr_num(v[1] * 100, 0)})"


def sec_sl(ctx: dict) -> str:
    t, a = ctx["t"], ctx["anatomy"]
    fm = {"n": INT, "pay": PCT, "net_usd": USD, "ort_r": R2}
    lines = ["## 3. SL'ler neden oldu?",
             "**Ana neden dağılımı (tüm dönem, tam SL'ler; öncelik sırasıyla tek kod):**", md_table(_cause_table(t, "SL"), fm),
             "\n**Mekanizma payları** (bir SL birden fazla kutuya girebilir):",
             f"- Çıkış sonrası **yön doğruydu** (240 dk içinde TP seviyesine gitti): {_share(a, 'sl_yon_dogru')} · "
             f"**yön yanlıştı** (≥1R daha devam): {_share(a, 'sl_yon_yanlis')} · kararsız: {_share(a, 'sl_kararsiz')}",
             f"- Yön doğru olanları yaşatacak stop medyanı: {tr_num(-a.get('sl_medyan_needed_sl', np.nan), 2)}R "
             f"(şu anki 1R'ye karşı — stop genişletmenin bedeli §11'de)",
             f"- Hızlı SL (≤{S.FAST_SL_MIN} dk): {_share(a, 'sl_hizli')} · hiç çalışmadı (MFE<{tr_num(S.NEVER_WORKED_MFE_R)}R): "
             f"{_share(a, 'sl_hic_calismadi')} · önce kâra geçti (≥{tr_num(S.WENT_GREEN_R, 1)}R): {_share(a, 'sl_once_yesil')} · "
             f"hedefin %{int(S.NEAR_TP_FRAC * 100)}'ine geldi: {_share(a, 'sl_neredeyse_tp')}",
             f"- Yapı kırıldı: {_share(a, 'sl_yapi_kirildi')} · aleyhte hacim şoku: {_share(a, 'sl_ters_hacim_soku')} · "
             f"hacim söndü: {_share(a, 'sl_hacim_sondu')} · iğne stop: {_share(a, 'sl_igne')} · gece taşıma: "
             f"{_share(a, 'sl_gece')} · kayma: {_share(a, 'sl_kayma')}",
             f"- Medyan süre {tr_num(a.get('sl_medyan_sure', np.nan), 0)} dk · medyan MFE {R2(a.get('sl_medyan_mfe', np.nan))}R",
             "\n**Çıkış-sonrası hüküm × strateji/sembol-yön (tam SL'ler):**", md_table(ctx["verdicts"]),
             "\n**Bayrak sıklığı — her etiket SL'lerde mi TP'lerde mi?** `SL oranı (varken)` tabandan belirgin "
             "yüksek değilse o bayrak SL'yi AÇIKLAMAZ (TP'lerde de aynı sıklıkta vardır). Yol etiketleri teşhistir.",
             md_table(ctx["tags"], {"SL'lerde": PCT, "TP'lerde": PCT, "n": INT, "SL oranı (varken)": PCT,
                                    "taban SL oranı": PCT, "ort R (varken)": R2, "fark_pp": lambda v: tr_num(v, 1, True)},
                      max_rows=60)]
    return "\n".join(lines)


def sec_placebo(ctx: dict) -> str:
    pl = ctx.get("placebo") or {}
    out = ["## 2b. Botun giriş anı rastgeleden iyi mi? (plasebo tabanı)",
           f"Her gerçek işlem için aynı sembol, yön, UTC saati ve SL/TP fiyat mesafeleriyle ±{10} gün içinden 5 rastgele "
           "giriş; iki taraf da YÖNETİMSİZ oynatıldı. SL mekanizma payları rastgele girişte de benzer çıkıyorsa, "
           "o mekanizma botun hatası değil braketin (SL/TP geometrisinin) doğasıdır."]
    if not pl:
        return "\n".join(out + ["_Plasebo üretilemedi (yetersiz veri)._"])
    e = pl["esli_fark"]
    out.append(f"\n**Eşli fark (gerçek giriş − aynı geometride rastgele giriş):** ort {R2(e['ort'])}R/işlem, "
               f"%95 [{R2(e['ci'][0])}…{R2(e['ci'][1])}], P(fark>0) = {PCT(e['p_pozitif']) if np.isfinite(e['p_pozitif']) else '—'}, n={e['n']}")
    fm = {"n": INT, "wr": PCT, "ort_r": R2, "sl_yon_dogru": PCT, "sl_yon_yanlis": PCT, "sl_hic_calismadi": PCT,
          "sl_neredeyse_tp": PCT}
    out += ["\n**Genel:**", md_table(pl["tablo"], fm), "\n**Sembol-yön:**", md_table(pl["taraf"], fm, max_rows=30)]
    return "\n".join(out)


def sec_tp(ctx: dict) -> str:
    t, a = ctx["t"], ctx["anatomy"]
    fm = {"n": INT, "pay": PCT, "net_usd": USD, "ort_r": R2}
    return "\n".join([
        "## 4. TP'ler nasıl oldu?", md_table(_cause_table(t, "TP"), fm),
        f"\n- Temiz (MAE>−{tr_num(S.CLEAN_TP_MAE_R)}R): {_share(a, 'tp_temiz')} · acı çektiren (MAE≤−{tr_num(S.PAINFUL_TP_MAE_R, 1)}R): "
        f"{_share(a, 'tp_aci_cektiren')} · TP sonrası ≥1R daha gitti (hedef erken): {_share(a, 'tp_erken')} · "
        f"TP'den sonra SL seviyesi de görüldü (şanslı zamanlama): {_share(a, 'tp_sonra_sl_vurdu')} · hacim söndü: {_share(a, 'tp_hacim_sondu')}",
        f"- Medyan süre {tr_num(a.get('tp_medyan_sure', np.nan), 0)} dk · medyan MAE {R2(a.get('tp_medyan_mae', np.nan))}R",
    ])


def sec_volume(ctx: dict) -> str:
    fc = ctx["fc"]
    rows = []
    for col, label in VOLUME_FEATURES:
        f = fc[fc["feature"] == col]
        if f.empty:
            continue
        f = f.iloc[0]
        rows.append({"ölçü": label, "SL medyan": tr_num(f["med_sl"]), "TP medyan": tr_num(f["med_tp"]),
                     "AUC (SL>TP)": tr_num(f["auc"]), "q": tr_num(f["q"], 3), "hüküm": strength(f["auc"], f["q"], f["p"]),
                     "dönem tutarlı": f["tutarli"]})
    out = ["## 5. Hacim — SL olurken hacim düşüyor mu?",
           "Hacim mevsimsel düzeltilmiştir: ×1,00 = o 15-dk diliminde son 10 günün medyanı. "
           "AUC = rastgele bir SL'nin değerinin rastgele bir TP'ninkinden büyük olma olasılığı (0,5 = ayrım yok).",
           md_table(pd.DataFrame(rows)),
           "\n**Çıkıştan önceki pencereler (yalnız işlem içi barlar, medyan):**", ctx["exit_profile_md"]]
    if ctx.get("chart_exit_volume"):
        out.append(f"\n![çıkışa giderken hacim]({ctx['chart_exit_volume']})")
    return "\n".join(out)


def sec_breaks(ctx: dict) -> str:
    bc = ctx["binary"]
    fm = {"n": INT, "sl_orani": PCT, "ort_r": R2, "net_usd": USD}
    return "\n".join([
        "## 6. Kırılmalar ve uyumsuzluklar",
        "Karar-anı olayları (`pre_`) filtre adayı olabilir; yol olayları (`path_`) yalnız teşhistir — "
        "yapı kırılımı SL'den ÖNCE geldiği için SL'lerde neredeyse tanım gereği sık görülür; asıl soru "
        "TP'lerde ne sıklıkla görülüp kurtarıldığıdır (aşağıda 'var' satırının SL oranı).",
        md_table(bc, fm, max_rows=60)])


def sec_early(ctx: dict) -> str:
    div, ew = ctx["divergence"], ctx["early"]
    head = (f"SL ve TP işlemleri (hâlâ açık olanlar arasında) **{div['dakika']}. dakikada** belirgin ayrışıyor "
            f"(fark {R2(div['fark_r'])}R, t={tr_num(div['t'], 1)}; TP n={div['n_tp']}, SL n={div['n_sl']})."
            if div else "Açık işlemler arasında belirgin (≥0,25R, t≥2) ayrışma dakikası bulunamadı.")
    out = ["## 7. Ne zaman belli oluyor? (erken uyarı)", head,
           "\n`auc_tp_yuksek` = o dakikada TP'ye gidecek bir işlemin R'sinin SL'ye gidecek olandan yüksek olma olasılığı. "
           "`R≤−x: …` = 'o dakikada R ≤ −x ise kapat' kuralının yakaladığı SL, öldürdüğü TP ve net R etkisi "
           "(bar kapanışında çıkış — hafif iyimser). ⚠ Defter M9: 50+ BE/erken-çıkış varyantı 487 işlemde elendi; "
           "buradaki pozitif bir satır da tek dönem, örneklem-içi bulgudur.",
           md_table(ew)]
    if ctx.get("chart_divergence"):
        out.append(f"\n![ayrışma eğrisi]({ctx['chart_divergence']})")
    return "\n".join(out)


def sec_features(ctx: dict) -> str:
    fc = ctx["fc"]
    cols = ["feature", "aile", "n_sl", "n_tp", "med_sl", "med_tp", "auc", "p", "q", "auc_disc", "auc_focus", "tutarli", "registry"]
    n_tested = len(fc)
    n_nom = int((fc["p"] < 0.05).sum()) if n_tested else 0
    out = ["## 8. Her şey birbirine karşı — tüm özellik kıyası (SL vs TP)",
           f"{n_tested} özellik test edildi; p<0,05'te tesadüfen beklenen ≈{tr_num(0.05 * n_tested, 1)}, bulunan {n_nom}. "
           f"q<{tr_num(S.FDR_Q)} (Benjamini–Hochberg, aile içinde) olan: {int((fc['q'] < S.FDR_Q).sum()) if n_tested else 0}. "
           "`tutarli` = keşif ve odak dönemlerinde aynı yönde ≥0,05 ayrım. Erken (`e5_/e15_`) satırlar yalnız o dakikada açık işlemleri içerir.",
           md_table(fc[cols].head(S.TOP_FEATURES), {"n_sl": INT, "n_tp": INT, "p": lambda v: tr_num(v, 3), "q": lambda v: tr_num(v, 3)})]
    if ctx.get("chart_auc"):
        out.append(f"\n![özellik ayrımı]({ctx['chart_auc']})")
    return "\n".join(out)


def sec_interactions(ctx: dict) -> str:
    return "\n".join(["## 9. Kombinasyonlar (keşif amaçlı — en güçlü karar-anı özelliklerinin ikili bölmeleri)",
                      "Bu tablo seçilmiş hücreleri gösterir; çoklu karşılaştırma yükü yüksektir — tek başına önlem gerekçesi DEĞİLDİR (E12).",
                      md_table(ctx["interactions"], {"n": INT, "sl_orani": PCT, "taban_sl": PCT, "ort_r": R2,
                                                     "fark_pp": lambda v: tr_num(v, 1, True)})])


def sec_candidates(ctx: dict) -> str:
    vc = ctx["candidates"]
    out = ["## 10. Aday önlemler — karar anında uygulanabilir (keşifte seçildi → odakta sınandı)",
           "Eşikler keşif döneminin tertilinden; özellik seçimi keşif AUC'sinden. `kurtarilan_r` > `rastgele_beklenen_r` "
           "ise kural rastgele aynı sayıda işlemi elemekten iyidir. Odakta da pozitif değilse aday ELENİR. "
           "Pozitif olsa bile: GÖLGE → ≥150 olay → canlıya alma kartı (2. KURAL)."]
    if vc is None or vc.empty:
        out.append("_Keşif döneminde yeterli işlem yok (her grupta ≥8) — aday üretilmedi._")
    else:
        out.append(md_table(vc, {"n_donem": INT, "engellenen": INT, "engellenen_tp": INT, "engellenen_sl": INT,
                                 "kurtarilan_r": R2, "rastgele_beklenen_r": R2, "kurtarilan_usd": USD}))
    return "\n".join(out)


def sec_geometry(ctx: dict) -> str:
    g = ctx.get("geometry", {})
    out = ["## 11. Geometri karşı-olgusu (aynı girişler, farklı SL/TP — yönetimsiz)",
           f"Durum: **{g.get('durum', '—')}** (gerçek sonucu tutma oranı %{tr_num(g.get('uyum', np.nan) * 100, 1)}, n={g.get('n', 0)}). "
           "`ort_r_ayni_risk` = lot SL'ye göre ölçeklenip $ risk sabit tutulursa işlem başına R. Bot yönetimi (BE30, koştur) bu tabloda YOK."]
    if "tablo" in g:
        out.append(md_table(g["tablo"], {"n": INT, "wr": PCT, "top_r_ayni_lot": R2, "ort_r_ayni_risk": R2,
                                         "kesif_ort_r": R2, "odak_ort_r": R2}))
    return "\n".join(out)


def sec_cards(ctx: dict) -> str:
    t = ctx["t"]
    f = t[t["period"] == "focus"].sort_values("entry_utc", ascending=False)
    order = pd.concat([f[f["outcome"] == "SL"], f[f["outcome"] != "SL"]])
    out = [f"## 12. İşlem kartları — odak penceresi ({len(f)} işlem; önce SL'ler, yeniden eskiye)"]
    for _, r in order.head(ctx["max_cards"]).iterrows():
        out.append(r["kart"])
        img = ctx["trade_charts"].get(r["pid"])
        if img:
            out.append(f"\n![#{r['pid']}]({img})")
        out.append("")
    if len(order) > ctx["max_cards"]:
        out.append(f"_… {len(order) - ctx['max_cards']} kart daha `islemler.csv` içinde (`kart` sütunu)._")
    return "\n".join(out)


METHOD = """## 13. Yöntem notları ve tuzaklar
- **Zaman aileleri ayrı:** `pre_/geo_/ctx_` yalnız girişten önce KAPANMIŞ barlar (5m/15m/1h dahil, bitiş ≤ giriş).
  `e5_/e15_` girişten sonraki ilk dakikalar (hayatta-kalma koşullu). `path_` ve `post_` geleceği görür → yalnız teşhis.
- **R** = |giriş − ilk SL| (pozisyonu açan emrin planı). Taşınmış stoplar (BE/iz) ayrı sınıf: BE / IZ_SL / KISMI_SL.
- **Bağımsız karar:** aynı sembol+yön 2 dk içinde açılan bacaklar tek karar sayılır (E9); istatistikler ilk bacakla.
- **Hacim:** tick hacmi; gün-içi mevsimsellik 15-dk dilim × önceki 10 gün medyanıyla çıkarılır (ABD açılışı sıçraması "hacim arttı" sayılmaz).
- **Çıkış sonrası** 240 dk: SL sonrası TP seviyesine gitmek "yön doğruydu" demektir AMA daha geniş stopun bedelini
  (yön yanlış olanlarda daha büyük kayıp) §11 ölçer — bu ikisini birlikte okumadan stop genişletme önerilmez.
- **Örneklem-içi uyarısı:** §8–§10 keşiftir. Bir bulgu ancak hiç bakılmamış sonraki dönemde (`--since`) tutarsa
  aday olur; canlıya alma 2. KURAL (go_live kartı). Defter: `docs/KAPI_KAYIT_DEFTERI.md`.
"""


def write_report(ctx: dict, out_dir: Path) -> Path:
    parts = [f"# İşlem Otopsisi — {ctx['scope']}",
             f"_Üretildi {ctx['generated']} · odak: son {ctx['focus_days']} gün · taban: {ctx['base_days']} gün_",
             sec_gate(ctx), sec_summary(ctx), sec_breakdowns(ctx), sec_placebo(ctx), sec_sl(ctx), sec_tp(ctx), sec_volume(ctx),
             sec_breaks(ctx), sec_early(ctx), sec_features(ctx), sec_interactions(ctx), sec_candidates(ctx),
             sec_geometry(ctx), sec_cards(ctx), METHOD]
    path = out_dir / "rapor.md"
    path.write_text("\n\n".join(parts), encoding="utf-8")
    return path


def write_summary_json(ctx: dict, out_dir: Path) -> Path:
    fc = ctx["fc"]
    t = ctx["t"]
    js = {
        "scope": ctx["scope"], "generated": ctx["generated"], "command": ctx["command"],
        "clock": {"status": ctx["align"].status, "aligned_frac": ctx["align"].aligned_frac,
                  "offsets": ctx["align"].offset_counts, "excluded": ctx["align"].excluded},
        "replay": {k: v for k, v in ctx.get("geometry", {}).items() if k != "tablo"},
        "summaries": ctx["summaries"], "anatomy": ctx["anatomy"],
        "sl_causes": _cause_table(t, "SL").to_dict(orient="records"),
        "tp_causes": _cause_table(t, "TP").to_dict(orient="records"),
        "top_features": fc.head(S.TOP_FEATURES).to_dict(orient="records") if len(fc) else [],
        "divergence": ctx["divergence"],
        "placebo": {k: (v.to_dict(orient="records") if isinstance(v, pd.DataFrame) else v)
                    for k, v in (ctx.get("placebo") or {}).items()},
        "verdicts": ctx["verdicts"].to_dict(orient="records") if len(ctx["verdicts"]) else [],
        "tag_frequency": ctx["tags"].to_dict(orient="records") if len(ctx["tags"]) else [],
        "early_warning": ctx["early"].to_dict(orient="records") if len(ctx["early"]) else [],
        "geometry": ctx.get("geometry", {}).get("tablo", pd.DataFrame()).to_dict(orient="records"),
        "candidates": ctx["candidates"].to_dict(orient="records") if ctx["candidates"] is not None else [],
        "files": {"rapor": "rapor.md", "islemler": "islemler.csv", "ozellik_kiyas": "ozellik_kiyas.csv"},
    }
    path = out_dir / "ozet.json"
    path.write_text(json.dumps(js, ensure_ascii=False, indent=1, default=_json_default), encoding="utf-8")
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    return str(o)


def write_trade_autopsy(t: pd.DataFrame, pid: int, sbs: dict, out_dir: Path) -> Path | None:
    """Tek işlem için ayrıntılı otopsi: kart + grafik + geçmiş benzerleri + özellik konumu."""
    from . import analogs, charts
    hit = t[t["pid"] == pid]
    if hit.empty:
        print(f"#{pid} analiz tablosunda yok (filtre/dönem dışı ya da dışlandı)")
        return None
    r = hit.iloc[0]
    img = out_dir / "grafikler" / f"otopsi_{pid}.png"
    img.parent.mkdir(exist_ok=True)
    charts.trade_chart(r, sbs[r["symbol"]], img, pad_min=180)
    nb = analogs.nearest(t, r)
    pos = analogs.feature_position(t, r)
    parts = [f"# Tekil otopsi — #{pid}", r["kart"], f"\n![#{pid}](grafikler/{img.name})",
             "\n## Geçmişteki en benzer işlemler (aynı sembol-yön, bu işlemden ÖNCE kapanmış)",
             analogs.summary_line(nb, analogs.pool_sl_rate(t, r)),
             md_table(nb.assign(entry_utc=nb["entry_utc"].dt.strftime("%Y-%m-%d %H:%M")) if len(nb) else nb,
                      {"r_exit": R2, "net": USD, "mesafe": lambda v: tr_num(v, 2)}),
             "\n## Bu işlem geçmiş SL'lere mi TP'lere mi benziyor? (özellik bazında)",
             "Yüzdelik = değerin o grubun dağılımındaki yeri (50 = tam medyan). Bir grubun medyanına diğerinden "
             f"≥{int(analogs.NEAR_PCT_GAP)} puan daha yakınsa o gruba 'benziyor' denir.",
             md_table(pos, {"SL yüzdeliği": lambda v: tr_num(v, 0), "TP yüzdeliği": lambda v: tr_num(v, 0)})]
    path = out_dir / f"otopsi_{pid}.md"
    path.write_text("\n\n".join(parts), encoding="utf-8")
    return path
