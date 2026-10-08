"""İşlem başına teşhis: etiketler → öncelik sıralı ANA NEDEN → Türkçe kart.

Etiketler kurala dayalıdır (eşikler settings.py'de, sonuca bakılmadan sabit). "Ana neden"
bir hükümdür, kanıt değil: tek işlemde nedensellik kanıtlanamaz; toplu tablolar
hangi mekanizmanın SİSTEMATİK olduğunu söyler.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S

TR_OFFSET = pd.Timedelta(hours=3)
PRE_RED_FLAGS = ("TERS_TREND_1H", "KOVALAMA", "RSI_DIV_KARSI", "HACIMSIZ_UC", "UCTA_GIRIS",
                 "MTF_CELISKI", "VIX_KARSI", "KAYIP_SONRASI_TEKRAR")


def tr_num(x: float, nd: int = 2, sign: bool = False) -> str:
    """Türkçe sayı biçimi: binlik nokta, ondalık virgül, gerçek eksi işareti."""
    if x is None or not np.isfinite(x):
        return "—"
    x = round(float(x), nd) + 0.0          # −0,00 → 0,00
    if x == 0:
        x = 0.0
    s = f"{x:{'+' if sign else ''},.{nd}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return s.replace("-", "−")


def _f(r: pd.Series, k: str) -> float:
    v = r.get(k, np.nan)
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def pre_tags(r: pd.Series) -> list[tuple[str, str]]:
    t: list[tuple[str, str]] = []
    ret15 = _f(r, "pre_ret_15")
    if ret15 >= S.CHASE_RET15_ATR5:
        t.append(("KOVALAMA", f"girişten önceki 15 dk'da {tr_num(ret15, 1)} ATR5 lehte hareket (kovalama)"))
    elif ret15 <= S.DIP_RET15_ATR5:
        t.append(("DONUS_GIRISI", f"son 15 dk {tr_num(ret15, 1)} ATR5 aleyhte gelmişti (dönüş girişi)"))
    if _f(r, "pre_trend_align_1h") == 0:
        t.append(("TERS_TREND_1H", f"1h EMA50'nin ters tarafında ({tr_num(_f(r, 'pre_dist_ema50_1h'), 1, True)} ATR1h)"))
    if _f(r, "pre_mtf_agree") <= S.MTF_WEAK:
        t.append(("MTF_CELISKI", f"4 zaman diliminin yalnız {int(_f(r, 'pre_mtf_agree'))}'i yönle uyumlu"))
    if _f(r, "pre_div_rsi_against") == 1:
        t.append(("RSI_DIV_KARSI", "RSI diverjansı işlemin ALEYHİNE (fiyat yeni uç, RSI teyit etmiyor)"))
    if _f(r, "pre_div_rsi_for") == 1:
        t.append(("RSI_DIV_LEHTE", "RSI diverjansı işlemin LEHİNE (aleyhte uç RSI'da teyitsiz)"))
    if _f(r, "pre_voldiv_against") == 1:
        t.append(("HACIMSIZ_UC", "lehte yeni uç sönen hacimle yapılmış (hacim diverjansı)"))
    if _f(r, "pre_voldiv_for") == 1:
        t.append(("TUKENME_LEHTE", "aleyhte uç sönen hacimle (satış/alış tükenmesi)"))
    vs = _f(r, "pre_vol_seas_15")
    if vs < S.VOL_LOW_SEAS:
        t.append(("HACIMSIZ_GIRIS", f"giriş öncesi hacim saatine göre düşük (×{tr_num(vs)})"))
    elif vs >= S.VOL_HIGH_SEAS:
        t.append(("HACIM_PATLAMASI", f"giriş öncesi hacim saatine göre yüksek (×{tr_num(vs)})"))
    if _f(r, "pre_range_pos_4h") >= S.RANGE_EDGE:
        t.append(("UCTA_GIRIS", f"4s aralığın yön tarafındaki ucunda (%{tr_num(_f(r, 'pre_range_pos_4h') * 100, 0)})"))
    if _f(r, "pre_sl_beyond_struct") == 0:
        t.append(("STOP_YAPI_ICINDE", f"SL 30 dk yapı ucunun İÇİNDE ({tr_num(_f(r, 'pre_sl_struct_margin'), 1)} ATR1)"))
    if _f(r, "geo_sl_atr5") < S.TIGHT_SL_ATR5:
        t.append(("DAR_STOP", f"SL = {tr_num(_f(r, 'geo_sl_atr5'))}×ATR5 (gürültü içinde)"))
    rr, sla = _f(r, "geo_rr"), _f(r, "geo_sl_atr5")
    if (np.isfinite(rr) and not S.GEO_ANOMALY_RR[0] <= rr <= S.GEO_ANOMALY_RR[1]) or sla > S.GEO_ANOMALY_SL_ATR5:
        be = 1 / (1 + rr) if np.isfinite(rr) and rr > 0 else np.nan
        t.append(("GEOMETRI_ANOMALI", f"olağan dışı kurulum: RR {tr_num(rr)} (başabaş %{tr_num(be * 100, 0)}), "
                  f"SL {tr_num(sla, 1)}×ATR5 — tasarım mı, besleme/fiyat-tabanı hatası mı kontrol et (defter E21)"))
    if _f(r, "pre_vix_favors") == 0:
        t.append(("VIX_KARSI", f"VIX {tr_num(_f(r, 'pre_vix_prev'), 1)}: VIX rejimi bu yönü desteklemiyor"))
    if (_f(r, "ctx_prev_win") == 0 and _f(r, "ctx_prev_same_dir") == 1
            and _f(r, "ctx_min_since_prev") <= S.REVENGE_WINDOW_MIN):
        t.append(("KAYIP_SONRASI_TEKRAR", f"aynı yönde kayıptan {tr_num(_f(r, 'ctx_min_since_prev'), 0)} dk sonra yeniden giriş"))
    return t


def path_tags(r: pd.Series) -> list[tuple[str, str]]:
    t: list[tuple[str, str]] = []
    out, mfe = r["outcome"], _f(r, "path_mfe_r")
    if out == "SL" and _f(r, "path_dur_min") <= S.FAST_SL_MIN:
        t.append(("HIZLI_SL", f"{tr_num(_f(r, 'path_dur_min'), 0)} dk'da stop"))
    if out == "SL" and mfe < S.NEVER_WORKED_MFE_R:
        t.append(("HIC_CALISMADI", f"en iyi nokta yalnız {tr_num(mfe, 2, True)}R"))
    if out == "SL" and _f(r, "path_mfe_frac_tp") >= S.NEAR_TP_FRAC:
        t.append(("NEREDEYSE_TP", f"hedefin %{tr_num(_f(r, 'path_mfe_frac_tp') * 100, 0)}'ine geldi"))
    elif out == "SL" and mfe >= S.WENT_GREEN_R:
        t.append(("ONCE_YESIL", f"önce {tr_num(mfe, 2, True)}R kâra geçti ({tr_num(_f(r, 'path_t_mfe_min'), 0)}. dk)"))
    for key, lab, txt in (("path_t_struct_break", "YAPI_KIRILDI", "giriş öncesi yapı ucu kapanışla kırıldı"),
                          ("path_t_vol_shock_adv", "TERS_HACIM_SOKU", "aleyhte hacim şoku"),
                          ("path_t_flip5", "5M_DONUS", "5m trend aleyhe döndü")):
        if np.isfinite(_f(r, key)):
            t.append((lab, f"{txt} ({tr_num(_f(r, key), 0)}. dk)"))
    if _f(r, "path_vol_last_vs_first") < S.VOL_FADE_RATIO:
        t.append(("HACIM_SONDU", f"işlem boyunca hacim söndü (son/ilk üçte bir ×{tr_num(_f(r, 'path_vol_last_vs_first'))})"))
    if _f(r, "path_final_leg_vol") >= S.LEG_VOL_HEAVY:
        t.append(("HACIMLI_SON_BACAK", f"çıkışa götüren bacak ilk bacaktan ×{tr_num(_f(r, 'path_final_leg_vol'))} hacimli"))
    if _f(r, "path_mfe_vol_vs_start") < S.VOL_FADE_RATIO and out == "SL":
        t.append(("MFE_HACIMSIZ", "en iyi noktaya sönen hacimle ulaştı (itki tükendi)"))
    if _f(r, "path_overnight") == 1:
        t.append(("GECE", f"günlük kapanışı (17:00 NY) geçti, swap {tr_num(_f(r, 'swap'), 2)} $"))
    if _f(r, "path_spike_stop") == 1:
        t.append(("IGNE_STOP", "stop tek geniş mumun iğnesiyle alındı, mum geri kapandı"))
    if _f(r, "path_exit_slip_r") < -S.SLIP_R:
        t.append(("KAYMA", f"çıkış SL'nin {tr_num(-_f(r, 'path_exit_slip_r'), 2)}R ötesinden"))
    return t


def post_tags(r: pd.Series) -> list[tuple[str, str]]:
    t: list[tuple[str, str]] = []
    v = r.get("sl_verdict", "")
    if v == "YON_DOGRU":
        t.append(("YON_DOGRU", f"çıkıştan sonra TP seviyesine gitti; yaşatacak stop ≈ {tr_num(-_f(r, 'post240_needed_sl_r'), 2)}R"))
    elif v == "YON_YANLIS":
        t.append(("YON_YANLIS", f"SL'den sonra {tr_num(_f(r, 'post240_max_adv_r'), 2, True)}R'ye kadar devam etti"))
    elif v == "KARARSIZ":
        t.append(("KARARSIZ", "ne hedefe döndü ne belirgin devam etti"))
    if r["outcome"] == "TP":
        mae = _f(r, "path_mae_r")
        if mae > -S.CLEAN_TP_MAE_R:
            t.append(("TEMIZ_TP", f"en kötü {tr_num(mae, 2, True)}R"))
        elif mae <= -S.PAINFUL_TP_MAE_R:
            t.append(("ACI_CEKTIREN_TP", f"önce {tr_num(mae, 2, True)}R geri çekildi"))
        if _f(r, "post240_run_beyond_tp_r") >= S.EARLY_TP_RUN_R:
            t.append(("ERKEN_TP", f"TP sonrası {tr_num(_f(r, 'post240_run_beyond_tp_r'), 2, True)}R daha gitti"))
        if _f(r, "post240_hit_sl0") == 1:
            t.append(("SANSLI_TP", "TP'den sonraki 4 saatte SL seviyesine de gitti"))
    return t


CAUSE_LABELS = {
    "GECE_KAYMA": "gece boşluğu/kayma: stop seviyesinin ötesinden doldu",
    "IGNE_STOP": "iğne stop — yön doğruydu, tek mumluk sıçrama stopu aldı",
    "YON_DOGRU_DAR_STOP": "yön doğru, stop gürültü/yapı içindeydi",
    "YON_DOGRU_ERKEN": "yön doğru, zamanlama erken: önce stop, sonra hedef",
    "NEREDEYSE_TP": "hedefe çok yaklaşıp döndü — hedef/çıkış sorunu",
    "HIC_CALISMADI": "işlem hiç çalışmadı (MFE<0,15R) — giriş anı yanlış; bayrakların gerçekten etkili olup olmadığı bayrak-sıklığı tablosunda",
    "HACIMLI_KIRILIM": "yapı hacimli ters akışla kırıldı — gerçek karşı baskı",
    "YON_YANLIS": "yön yanlıştı — stop sonrası da ters devam etti",
    "HACIM_SONDU": "itki/hacim söndü, fiyat yavaşça stopa eridi",
    "GURULTU": "belirgin tek neden yok — stop gürültü içinde vuruldu",
    "TP_SANSLI": "şanslı zamanlama: derin geri çekilme + sonra SL seviyesi de görüldü",
    "TP_TEMIZ": "temiz TP: ciddi geri çekilme olmadan hedef",
    "TP_ACI": "acı çektiren TP: derin geri çekilmeden döndü",
    "TP_NORMAL": "normal TP",
    "BE": "stop başabaşa taşınmıştı — yönetim kuralı çıkardı",
    "IZ_SL": "iz süren stop kârda kapattı",
    "KISMI_SL": "taşınmış stop zararda kapattı",
    "DIGER": "bot/manuel kapanış",
}


def root_cause(r: pd.Series, tags: set) -> tuple[str, str]:
    """(kod, metin). Öncelik sırası sabittir; metin kırmızı bayrakları ayrıntılandırır."""
    out = r["outcome"]
    if out == "TP":
        code = ("TP_SANSLI" if {"SANSLI_TP", "ACI_CEKTIREN_TP"} <= tags else "TP_TEMIZ" if "TEMIZ_TP" in tags
                else "TP_ACI" if "ACI_CEKTIREN_TP" in tags else "TP_NORMAL")
        return code, CAUSE_LABELS[code]
    if out != "SL":
        code = out if out in CAUSE_LABELS else "DIGER"
        return code, CAUSE_LABELS[code]
    red = [x for x in PRE_RED_FLAGS if x in tags]
    code = _sl_code(tags, red)
    text = CAUSE_LABELS[code]
    if red and code in ("HIC_CALISMADI", "YON_YANLIS"):
        text += f" [giriş bayrakları: {', '.join(red)}]"
    return code, text


def _sl_code(tags: set, red: list) -> str:
    if {"KAYMA", "GECE"} <= tags:
        return "GECE_KAYMA"
    if {"YON_DOGRU", "IGNE_STOP"} <= tags:
        return "IGNE_STOP"
    if "YON_DOGRU" in tags:
        return "YON_DOGRU_DAR_STOP" if {"DAR_STOP", "STOP_YAPI_ICINDE"} & tags else "YON_DOGRU_ERKEN"
    if "NEREDEYSE_TP" in tags:
        return "NEREDEYSE_TP"
    if "HIC_CALISMADI" in tags:
        return "HIC_CALISMADI"
    if "YAPI_KIRILDI" in tags and {"TERS_HACIM_SOKU", "HACIMLI_SON_BACAK"} & tags:
        return "HACIMLI_KIRILIM"
    if "YON_YANLIS" in tags:
        return "YON_YANLIS"
    if "HACIM_SONDU" in tags:
        return "HACIM_SONDU"
    return "GURULTU"


def _when(ts: pd.Timestamp) -> str:
    return f"{(ts + TR_OFFSET):%d.%m %H:%M} TSİ"


def card(r: pd.Series) -> tuple[str, str, str]:
    """(ana neden kodu, ana neden metni, markdown kart)."""
    pre, path, post = pre_tags(r), path_tags(r), post_tags(r)
    tags = {k for k, _ in pre + path + post}
    code, cause = root_cause(r, tags)
    sym = str(r["broker_symbol"])
    head = (f"#### {r['outcome']} · {sym} {r['direction']} · {r['family']} · {_when(r['entry_utc'])} → "
            f"{_when(r['exit_utc'])} ({tr_num(_f(r, 'path_dur_min'), 0)} dk) · {tr_num(_f(r, 'net'), 0)} $ · "
            f"{tr_num(_f(r, 'r_exit'), 2, True)}R · #{r['pid']}")
    lines = [head, f"**Ana neden:** {cause}"]
    lines.append("- **Giriş bağlamı:** " + _context_line(r) + (" · " + " · ".join(t for _, t in pre) if pre else ""))
    lines.append("- **Yol:** " + _path_line(r) + (" · " + " · ".join(t for _, t in path) if path else ""))
    if post:
        lines.append("- **Çıkış sonrası (240 dk):** " + " · ".join(t for _, t in post)
                     + ("" if _f(r, "post240_complete") == 1 else " _(pencere henüz tamamlanmadı)_"))
    lines.append("- Etiketler: " + " ".join(f"`{k}`" for k in sorted(tags)))
    return code, cause, "\n".join(lines)


def _context_line(r: pd.Series) -> str:
    return (f"SL {tr_num(_f(r, 'geo_sl_atr5'))}×ATR5, RR {tr_num(_f(r, 'geo_rr'))} (başabaş %{tr_num(_f(r, 'geo_be_wr') * 100, 0)}), "
            f"5m RSI(yön) {tr_num(_f(r, 'pre_rsi5'), 0)}, son 15 dk {tr_num(_f(r, 'pre_ret_15'), 1, True)} ATR5, "
            f"hacim ×{tr_num(_f(r, 'pre_vol_seas_15'))} (saatine göre)")


def _path_line(r: pd.Series) -> str:
    return (f"MFE {tr_num(_f(r, 'path_mfe_r'), 2, True)}R ({tr_num(_f(r, 'path_t_mfe_min'), 0)}. dk), "
            f"MAE {tr_num(_f(r, 'path_mae_r'), 2, True)}R ({tr_num(_f(r, 'path_t_mae_min'), 0)}. dk), "
            f"ilk gelen ±0,5R: {r.get('path_first_hit', '—')}")


def annotate(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    res = [card(r) for _, r in t.iterrows()]
    t["ana_neden_kod"] = [c for c, _, _ in res]
    t["ana_neden"] = [x for _, x, _ in res]
    t["kart"] = [k for _, _, k in res]
    for col, fn in (("etiket_giris", pre_tags), ("etiket_yol", path_tags), ("etiket_sonra", post_tags)):
        t[col] = [" ".join(sorted({k for k, _ in fn(r)})) for _, r in t.iterrows()]
    return t


MIN_FLAG_N = 15                  # bayrağın geçmiş ağırlığı ancak bu kadar olayla anlamlı
FLAG_MEANINGFUL_PP = 8.0         # |fark| bunun altıysa "etkisiz" yazılır


def add_flag_weights(t: pd.DataFrame, freq: pd.DataFrame) -> pd.DataFrame:
    """Her kartın giriş bayraklarına tüm dönemde ölçülen SL-oranı farkını ekler.

    Tek işlemin anlatısı ("ters trende girdi") ancak o bayrak TOPLUCA SL oranını
    artırıyorsa açıklayıcıdır; aksi hâlde bayrak TP'lerde de aynı sıklıktadır.
    """
    if freq is None or freq.empty:
        return t
    f = freq[freq["evre"].str.startswith("giriş")].set_index("etiket")
    t = t.copy()
    lines = []
    for _, r in t.iterrows():
        tags = [x for x in str(r.get("etiket_giris", "")).split() if x]
        parts = []
        for tag in tags:
            if tag not in f.index or f.at[tag, "n"] < MIN_FLAG_N:
                parts.append(f"{tag} (az örnek)")
                continue
            pp = float(f.at[tag, "fark_pp"])
            mark = "etkili" if abs(pp) >= FLAG_MEANINGFUL_PP else "etkisiz"
            parts.append(f"{tag} {tr_num(pp, 0, True)}pp ({mark}, n={int(f.at[tag, 'n'])})")
        lines.append(("- **Bayrakların geçmiş ağırlığı** (SL oranına katkı, tüm dönem): " + " · ".join(parts)) if parts else "")
    t["kart"] = [k.replace("\n- Etiketler:", ("\n" + ln + "\n- Etiketler:") if ln else "\n- Etiketler:")
                 for k, ln in zip(t["kart"], lines)]
    return t
