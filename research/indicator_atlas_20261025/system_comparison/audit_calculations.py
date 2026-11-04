"""Read-only source/model-contract audit and synthetic formula comparison.

No service module, broker, environment configuration or vendor atlas code is run.
Only selected pure functions from this project's own source are executed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import logging
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def pure_functions(relative: str, names: set[str]) -> dict:
    tree = ast.parse((ROOT / relative).read_text())
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    nodes.extend(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names)
    assert {node.name for node in nodes if isinstance(node, ast.FunctionDef)} == names
    namespace = {"np": np, "pd": pd, "logger": logging.getLogger("audit")}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), relative, "exec"), namespace)
    return namespace


def main() -> None:
    legacy_path = "backend/services/ml_prediction_service.py"
    bot_path = "yeni deneme/indicators.py"
    xau_path = "backend/services/xauusd_v2_service.py"
    legacy = pure_functions(legacy_path, {"_compute_technical_indicators", "_build_feature_vector"})
    bot = pure_functions(bot_path, {"_ema", "_rma", "_rsi", "_true_range", "_atr", "_adx", "_stoch", "_macd", "_bollinger", "_sar", "compute_all"})
    xau = pure_functions(xau_path, {"_ema", "_rsi", "_atr", "_macd", "_bbands", "_parabolic_sar", "_linreg_channel", "_adx", "_build_tf_features"})
    n = 400
    rng = np.random.default_rng(20261025)
    moves = rng.normal(0.04, 0.7, n) + 0.5 * np.sin(np.arange(n) / 13)
    c = 1000 + np.cumsum(moves)
    o = np.r_[c[0] - .2, c[:-1]]
    h = np.maximum(o, c) + rng.uniform(.1, 1.4, n)
    l = np.minimum(o, c) - rng.uniform(.1, 1.4, n)
    v = rng.integers(100, 2000, n).astype(float)
    a = legacy["_compute_technical_indicators"](c, h, l, v)
    b = bot["compute_all"](o, h, l, c, v)
    pairs = [("EMA20", "ema_20", "ema20"), ("SMA20", "sma_20", "sma20"),
             ("RSI14", "rsi_14", "rsi14"), ("ATR14", "atr_14", "atr14"),
             ("ADX14", "adx", "adx14"), ("MACD line", "macd_line", "macd"),
             ("MACD signal", "macd_signal", "macd_signal"), ("MACD histogram", "macd_hist", "macd_hist"),
             ("Stochastic K", "stoch_k", "stoch_k"), ("Stochastic D", "stoch_d", "stoch_d"),
             ("Bollinger upper", "boll_upper", "bb_upper"), ("Bollinger lower", "boll_lower", "bb_lower")]
    comparisons = [{"measure": title, "legacy_panel": float(a[ka]), "bot_recorder": float(b[kb]),
                    "absolute_difference": abs(float(a[ka]) - float(b[kb]))} for title, ka, kb in pairs]
    xau_check = {
        "RSI14": float(xau["_rsi"](pd.Series(c), 14).iloc[-1]),
        "ATR14": float(xau["_atr"](pd.Series(h), pd.Series(l), pd.Series(c), 14).iloc[-1]),
        "MACD histogram": float(xau["_macd"](pd.Series(c))[2].iloc[-1]),
    }
    for row in comparisons:
        if row['measure'] in xau_check:
            row['gold_v2'] = xau_check[row['measure']]
    assert abs(a['ema_20'] - b['ema20']) < 1e-5
    assert a['macd_signal'] == 0.0 and a['macd_hist_diff'] == 0.0
    assert a['macd_line'] == a['macd_hist']
    assert a['stoch_k'] == a['stoch_d']
    assert abs(a['macd_hist'] - b['macd_hist']) > .01
    assert abs(a['rsi_14'] - b['rsi14']) > .01

    frame = pd.DataFrame({'open': o, 'high': h, 'low': l, 'close': c, 'volume': v},
                         index=pd.date_range('2020-01-01', periods=n, freq='30min', tz='UTC'))
    xau_features = xau['_build_tf_features'](frame, 'M30')
    # Contract mappings are from AST dictionary keys, not keyword hits.
    function = next(node for node in ast.parse((ROOT / legacy_path).read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == '_build_feature_vector')
    mapped = set()
    ohlcv = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            if any(isinstance(t, ast.Name) and t.id in ('indicator_map', 'ohlcv_map') for t in node.targets):
                keys = {k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                mapped |= keys
                if any(isinstance(t, ast.Name) and t.id == 'ohlcv_map' for t in node.targets):
                    ohlcv |= keys
    warnings.filterwarnings('ignore')
    models = {}
    for name in ('model_lgbm_nasdaq.joblib', 'model_lgbm_xauusd.joblib'):
        model_path = ROOT / 'backend/models' / name
        model = joblib.load(model_path)
        features = list(model.feature_names_in_)
        calculated = [f for f in features if f in mapped]
        categorical = [f for f in features if f in {'components', 'route', 'signal'}]
        fallback = [f for f in features if f not in mapped and f not in categorical]
        legacy['resolve_ml_model_symbol'] = lambda symbol: symbol
        legacy['_load_model'] = lambda symbol: object()
        legacy['_model_features'] = {'audit': features}
        example = legacy['_build_feature_vector']('audit', a,
                 [{'open': float(o[-1]), 'high': float(h[-1]), 'low': float(l[-1]), 'close': float(c[-1]), 'volume': float(v[-1])}], a, a)
        assert list(example.columns) == features
        assert len(calculated) + len(categorical) + len(fallback) == len(features)
        transformed = list(model.named_steps['preprocess'].get_feature_names_out())
        importances = model.named_steps['model'].feature_importances_
        assert len(transformed) == len(importances)
        models[name] = {'input_columns': len(features), 'mapped_columns': len(calculated),
                        'categorical_defaults_or_trend_label': categorical,
                        'fallback_columns_count': len(fallback), 'mapped_columns_list': calculated,
                        'fallback_columns': fallback,
                        'htf_ohlcv_keys_copied_from_last_primary_bar': [f for f in calculated if f in ohlcv and f.endswith(('_H1', '_H4'))],
                        'synthetic_fallback_examples': {f: float(example[f].iloc[0]) for f in fallback[:20]},
                        'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
                        'transformed_model_inputs': len(transformed),
                        'transformed_inputs_with_nonzero_split_count': int(sum(importances > 0)),
                        'split_count_is_not_forecast_accuracy': True}
    gold_path = ROOT / 'backend/models/model_xauusd_v2.joblib'
    bundle = joblib.load(gold_path)
    gold_features = bundle['feature_columns']
    models['model_xauusd_v2.joblib'] = {'input_columns': len(gold_features),
        'feature_columns': gold_features, 'per_timeframe_builder_columns': list(xau_features.columns),
        'buy_nonzero_split_inputs': int(sum(bundle['buy_model'].feature_importances_ > 0)),
        'sell_nonzero_split_inputs': int(sum(bundle['sell_model'].feature_importances_ > 0)),
        'model_sha256': hashlib.sha256(gold_path.read_bytes()).hexdigest(),
        'note': 'Gold runtime routing is first-choice v2; legacy is exception fallback. Macro availability not tested.'}
    routing_functions = {'normalize_ml_market_symbol', 'resolve_ml_model_symbol', 'get_ml_model_filename',
                         '_load_model', '_build_feature_vector'}
    routing = pure_functions(legacy_path, routing_functions)
    tree = ast.parse((ROOT / legacy_path).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('ML_MARKET_SYMBOL_ALIASES', 'ML_MODEL_FAMILY_BY_SYMBOL', 'ML_MODEL_FILES'):
                    routing[target.id] = ast.literal_eval(node.value)
    routing.update({'Path':Path, '__file__':str(ROOT / legacy_path), '_models':{}, '_model_features':{}})
    resolved = {}
    for symbol in ('NDX.INDX','GDAXI.INDX','USOIL.FOREX','XAUUSD'):
        loaded = routing['_load_model'](symbol)
        family = routing['resolve_ml_model_symbol'](symbol)
        vector = routing['_build_feature_vector'](symbol,a,[{'close':float(c[-1])}],a,a)
        resolved[symbol] = {'generic_family':family, 'generic_model_filename':routing['get_ml_model_filename'](symbol),
                            'generic_loaded_type':type(loaded).__name__,
                            'generic_feature_names_length':len(routing['_model_features'].get(family,[])),
                            'generic_builder_returns_none':vector is None,
                            'early_gold_v2_route_applies':symbol=='XAUUSD'}
    assert resolved['USOIL.FOREX']['generic_loaded_type']=='dict'
    assert resolved['USOIL.FOREX']['generic_builder_returns_none']
    assert resolved['NDX.INDX']['generic_feature_names_length']==810
    # The 150-column legacy artifact is present on disk but is NOT selected by current routing.
    models['model_lgbm_xauusd.joblib']['selected_by_current_generic_model_map'] = False
    cot = pure_functions('backend/services/cot_report_service.py', {'_normalize_symbol'})
    cot_routing = {symbol: cot['_normalize_symbol'](symbol) for symbol in resolved}
    assert cot_routing['GDAXI.INDX'] == 'NASDAQ'
    assert cot_routing['USOIL.FOREX'] == 'XAUUSD'
    result = {'scope': 'Local checked-out source and local model artifacts; deployed flags/processes not verified.',
              'sample': '400 deterministic synthetic OHLCV bars; seed 20261025; invented prices, not historical market data.',
              'comparison': comparisons, 'models': models, 'fresh_load_routing': resolved,
              'cot_symbol_normalization':cot_routing,
              'source_hashes': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (legacy_path, bot_path, xau_path)},
              'not_tested': ['predictive accuracy', 'profitability', 'deployed model identity', 'live bot configuration']}
    (OUT / 'CALCULATION_AND_MODEL_AUDIT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    for row in comparisons:
        print(row['measure'], 'legacy=', round(row['legacy_panel'], 5), 'bot_recorder=', round(row['bot_recorder'], 5))
    for name, model in models.items():
        print(name, {k: v for k, v in model.items() if isinstance(v, int)})
    print('Fresh-load USOIL generic route:',resolved['USOIL.FOREX'])


if __name__ == '__main__':
    main()
