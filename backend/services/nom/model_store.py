"""NOM — model paketi (sürüm) deposu: kaydet / yükle / terfi / geri al.

Dizin: backend/models/nom/<sürüm>/
  meta.json                 sürüm, veri sürümü, eğitim sonu, özellik listesi, hedef başına istatistik + eşik + bant
  <ufuk>_<yön>_<geom>.txt   LightGBM modeli
  <ufuk>_<yön>_<geom>.cal.json   sınıf başına isotonic eşikler (x, y)
backend/models/nom/ACTIVE   etkin sürüm adı (terfi/geri alma = bu dosyayı değiştirmek)
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import lightgbm as lgb
import numpy as np

ROOT = Path(__file__).resolve().parents[2] / 'models' / 'nom'
ACTIVE = ROOT / 'ACTIVE'
HISTORY = ROOT / 'HISTORY.jsonl'
EPS = 1e-6


@dataclass
class Calibrator:
    xs: list[list[float]]
    ys: list[list[float]]

    def apply(self, p: np.ndarray) -> np.ndarray:
        out = np.empty_like(p)
        for k in range(p.shape[1]):
            out[:, k] = np.interp(p[:, k], self.xs[k], self.ys[k])
        out = np.clip(out, EPS, None)
        return out / out.sum(1, keepdims=True)

    @classmethod
    def from_isotonic(cls, isos: list) -> 'Calibrator':
        return cls([list(map(float, i.X_thresholds_)) for i in isos], [list(map(float, i.y_thresholds_)) for i in isos])


@dataclass
class Bundle:
    version: str
    meta: dict
    models: dict = field(default_factory=dict)
    cals: dict = field(default_factory=dict)

    def target(self, hz: str, d: str, gk: str) -> tuple[lgb.Booster, Calibrator, dict]:
        key = f'{hz}_{d}_{gk}'
        if key not in self.models:
            raise KeyError(f'model yok: {key}')
        return self.models[key], self.cals[key], self.meta['targets'][key]


def save_bundle(version: str, meta: dict, models: dict, cals: dict) -> Path:
    d = ROOT / version
    d.mkdir(parents=True, exist_ok=True)
    for k, m in models.items():
        m.save_model(str(d / f'{k}.txt'))
        c = cals[k]
        (d / f'{k}.cal.json').write_text(json.dumps({'xs': c.xs, 'ys': c.ys}))
    (d / 'meta.json').write_text(json.dumps(meta, indent=1, default=float))
    return d


def load_bundle(version: str | None = None) -> Bundle:
    version = version or active_version()
    if not version:
        raise FileNotFoundError('etkin NOM model sürümü yok (backend/models/nom/ACTIVE)')
    d = ROOT / version
    meta = json.loads((d / 'meta.json').read_text())
    b = Bundle(version, meta)
    for k in meta['targets']:
        b.models[k] = lgb.Booster(model_file=str(d / f'{k}.txt'))
        c = json.loads((d / f'{k}.cal.json').read_text())
        b.cals[k] = Calibrator(c['xs'], c['ys'])
    return b


def active_version() -> str | None:
    return ACTIVE.read_text().strip() if ACTIVE.exists() else None


def promote(version: str, reason: str) -> None:
    """Yeni sürümü etkin yap; önceki sürüm HISTORY'ye yazılır (geri alma için)."""
    if not (ROOT / version / 'meta.json').exists():
        raise FileNotFoundError(version)
    prev = active_version()
    ROOT.mkdir(parents=True, exist_ok=True)
    ACTIVE.write_text(version)
    import time
    with HISTORY.open('a') as f:
        f.write(json.dumps({'ts': time.time(), 'from': prev, 'to': version, 'reason': reason}) + '\n')


def rollback() -> str | None:
    """HISTORY'deki son terfiden önceki sürüme dön."""
    if not HISTORY.exists():
        return None
    lines = [json.loads(x) for x in HISTORY.read_text().splitlines() if x.strip()]
    if not lines or not lines[-1].get('from'):
        return None
    prev = lines[-1]['from']
    promote(prev, f"rollback from {lines[-1]['to']}")
    return prev


def delete_version(version: str) -> None:
    if version == active_version():
        raise RuntimeError('etkin sürüm silinemez')
    shutil.rmtree(ROOT / version, ignore_errors=True)
