"""Sıralı K1K2 kolu (EK-0'da tanıya düşen okuma) için kontroller — post-hoc, hüküm dışı."""
import importlib.util
import json

import numpy as np
import pandas as pd

import akn as A

spec = importlib.util.spec_from_file_location("akn_run", A.HERE / "run.py")
RN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RN)

B = A.load()
cx = A.build(B)
t = pd.read_parquet(A.HERE / "results" / "islemler.parquet")
out = {}
for em, col in (("E50", "RT1"), ("E1", "RT1"), ("E50", "RT2"), ("E50", "R1")):
    df = t[(t.chain == "K1K2") & (t.ltf_v == "C53") & (t.giris == em)].reset_index(drop=True)
    mir, pl = A.mirror(cx, df, col), RN.placebo(cx, df, col)
    sp = A.run(cx, "K1K2", "C53", em, spm=1.5)
    op = RN.one_pos(df, col)
    r = df[col]
    out[f"{em}-{col}"] = {
        "n": len(df), "ortR": round(r.mean(), 3), "medyan": round(r.median(), 3),
        "en_buyuk_cikinca": round(r.drop(r.idxmax()).mean(), 3), "ayna": round(float(mir.mean()), 3),
        "plasebo_ort": round(float(pl.mean()), 3), "plasebo_yuzdelik": float((pl < r.mean()).mean() * 100),
        "sp15": round(sp[col].mean(), 3), "tekpoz": round(op[col].mean(), 3), "yil_basi_islem": round(len(df) / 8.9, 1),
        "yillar_arti": f"{int((df.groupby(df.day.str[:4])[col].mean() > 0).sum())}/{df.day.str[:4].nunique()}"}
print(json.dumps(out, indent=1, ensure_ascii=False))
(A.HERE / "results" / "sirali_tani.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
