"""Evidence-backed comparison against the 120 atlas cards, excluding vendor code."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ATLAS = OUT.parent


def evidence(path: str, text: str) -> dict:
    lines = (ROOT / path).read_text().splitlines()
    matches = [i + 1 for i, line in enumerate(lines) if text in line]
    assert matches, (path, text)
    return {"path": path, "line": matches[0], "matched_text": text}


def main() -> None:
    rows = {f['id']: {"id": f['id'], "name": f['name'], "backend": "not_found_in_audited_paths",
                       "bot": "not_found_in_audited_paths", "decider": "not_found_in_audited_paths",
                       "evidence": [], "notes": []} for f in json.loads((ATLAS / 'FAMILIES.json').read_text())}

    def put(num: int, component: str, status: str, path: str, needle: str, note: str = '') -> None:
        row = rows[f'FAM-{num:03}']
        row[component] = status
        row['evidence'].append({"component": component, **evidence(path, needle)})
        if note:
            row['notes'].append(note)

    legacy = 'backend/services/ml_prediction_service.py'
    core = {20:'sma_20 =',21:'ema_20 =',45:'rsi_14 =',46:'stoch_k, stoch_d =',52:'macd_line, macd_signal, macd_hist =',
            53:'momentum_3 =',61:'adx_val =',69:'boll_upper, boll_lower',73:'atr_14 =',74:'vol_20 ='}
    for num, needle in core.items():
        put(num,'backend','decision_calculation',legacy,needle,
            'Connected to EMEL/Pulse via _compute_technical_indicators; model input use depends on artifact contract. Multiple periods do not count as new families.')
    extras = [
        (79,'decision_calculation','backend/services/xauusd_v2_service.py','sar = _parabolic_sar','Gold v2 calculates SAR; legacy psar model columns alone are fallback values.'),
        (83,'decision_calculation','backend/services/rebound_filter_service.py','obv = calculate_obv','OBV only: this does not establish PVT or ADL. Legacy ML OBV inputs are placeholders.'),
        (85,'decision_calculation',legacy,'mfi_val =','MFI only in main prediction path; Force Index appears in research batch calculations.'),
        (87,'decision_calculation','backend/services/oil_analysis_service.py','def calculate_nymex_vwap','OHLCV/tick-volume weighted benchmark; not a claim of centralized market volume.'),
        (89,'decision_calculation','backend/routers/emel_pulse.py','vol_last / vol_avg','Relative volume only; clock-time-matched RVOL is not established.'),
        (90,'decision_calculation','backend/services/oil_analysis_service.py','def calculate_volume_profile','OHLCV histogram approximation; no exchange price-level tape.'),
        (92,'proxy_calculation','backend/services/oil_analysis_service.py','def calculate_synthetic_cvd','Synthetic signed candle volume, not actual aggressor-classified CVD.'),
        (95,'context_calculation','backend/services/price_projection_service.py','def compute_orb','Projection snapshot enters debate prompt; no standalone ORB edge inferred.'),
        (96,'context_calculation','backend/services/mtf_analysis_service.py','def _calculate_pivot_points','Fibonacci/classic/Camarilla levels; CPR not separately established.'),
        (97,'decision_calculation','backend/order_block_detector_v2.py','class SwingDetector','Confirmed swings in canonical SMC and regime/rebound paths; not every fractal/Zigzag variant.'),
        (98,'decision_calculation','backend/order_block_detector_v2.py','class MarketStructureAnalyzer','Canonical BOS/CHoCH rules; does not establish equivalence to a specific TradingView author.'),
        (99,'decision_calculation','backend/services/order_block_service.py','async def detect(','Canonical SMC order blocks consumed by panel/service.'),
        (100,'decision_calculation','backend/order_block_detector_v2.py','class FVG','FVG support; not a full inverse-FVG implementation claim.'),
        (101,'decision_calculation','backend/services/rebound_filter_service.py','def _liquidity_sweep','Sweep bonus in rebound; equal-high/low pools also exist in smc_calculator_service.'),
        (103,'decision_calculation','backend/services/xauusd_v2_service.py','chan = _linreg_channel','Regression channel plus Fibonacci in projection/SMC; Pitchfork not established.'),
        (104,'decision_calculation','backend/services/harmonic_pattern_service.py','def _detect_harmonic_patterns','Eight named harmonic patterns and confidence adjustment; pattern counts are not win rates.'),
        (108,'decision_calculation',legacy,'from services.candlestick_pattern_service import get_candlestick_adjustment','Rule-based candle patterns; not all TA-Lib patterns implied.'),
        (112,'decision_calculation',legacy,'from services.cot_report_service import get_cot_adjustment','Confidence adjustment is strategy/preset and data dependent; COT service can use fallback data.'),
        (113,'context_calculation','backend/services/cot_report_service.py','oi_change_pct =','COT open-interest context, not a full live derivatives price/OI regime engine.'),
        (115,'decision_calculation','backend/services/xauusd_v2_service.py','base_ret.rolling(60).corr','Actual gold macro correlations; many legacy correlation feature names are fallback only.'),
        (116,'decision_calculation','backend/routers/deepseek_analysis.py','def generate_setup_recommendation','Seasonality enters smart-setup recommendation and oil temporal modifiers; not all calendar methods.'),
        (118,'decision_calculation','backend/services/xauusd_v2_service.py','for name in ("DXY", "US10Y", "VIX")','Partial family: dollar/nominal US10Y/VIX; no claim that real yields or GVZ are model inputs.'),
    ]
    for num,status,path,needle,note in extras:
        put(num,'backend',status,path,needle,note)

    recorder = 'yeni deneme/indicators.py'
    recorder_map = {20:'"sma20":',21:'ema20 =',45:'"rsi14":',46:'stoch_k, stoch_d =',52:'macd, macd_sig, macd_hist =',
                    61:'adx14, pdi, mdi =',69:'bb_up, bb_mid, bb_lo',73:'atr14 =',79:'sar = _sar',87:'out["vwap_z"]'}
    for num,needle in recorder_map.items():
        put(num,'bot','recorder_only',recorder,needle,'compute_all is called by data_recorder, not directly by the main order-entry loop.')
    for num,path,needle,note in [
        (21,'yeni deneme/entry_gate.py','ema200 =','Direct local EMA checks, conditional on relevant gate/scope flags.'),
        (53,'yeni deneme/entry_gate.py','last - c[-61]','Local directional return/stretch checks; not an independent ML forecast.'),
        (61,'yeni deneme/entry_gate.py','adx1, _, _ =','Local ADX gate; channel-reversion also calls adx_from_bars.'),
        (73,'yeni deneme/forexsai_demo_bot.py','def _atr_distances','ATR supports risk geometry and filters; several smoothing variants coexist.'),
        (74,'yeni deneme/caprev_live.py','dvol = math.sqrt','CAPREV daily return volatility, not the recorder ATR percentage.'),
        (87,'yeni deneme/channel_filter.py','def is_mean_reversion','VWAP z-score can qualify local channel-reversion entries.'),
        (102,'yeni deneme/caprev_live.py','pdl = days[pd_day]','Prior-session low in CAPREV; weekly high/low not separately established.'),
        (103,'yeni deneme/channel_filter.py','def channel_zscore','Linear-regression channel; not Fibonacci/Pitchfork locally.'),
        (120,'yeni deneme/caprev_live.py','"GDAXI.INDX": {"tz": "EU"','DAX-specific CAPREV session profile; breadth and DAX implied-volatility are not implied.'),
    ]:
        put(num,'bot','decision_calculation',path,needle,note)
    put(45,'bot','shadow_or_disabled','yeni deneme/forexsai_demo_bot.py','r = pr.rsi','SELL RSI check is in the shadow measurement branch; also recorded by compute_all.')
    put(71,'bot','shadow_or_disabled','yeni deneme/forexsai_demo_bot.py','donch_high_now =','Donchian+EMA200 USOIL scope defaults to shadow; XAU swing shadow also uses a rolling high breakout.')

    for num,path,needle,note in [
        (21,'claude_decider/free_context.py','ema20 = _ema','EMA context is supplied to the decision prompt.'),
        (53,'claude_decider/free_context.py','chg = (w[-1]','100-bar return in decision context.'),
        (61,'claude_decider/free_context.py','adx = _adx','ADX context; not proof it independently chooses direction.'),
        (73,'claude_decider/free_context.py','atr5 = _atr','ATR for context and geometry.'),
        (87,'claude_decider/free_context.py','vz = vwap_zscore','VWAP z-score in decision/evidence context.'),
        (89,'claude_decider/forensics.py','vol_ratio =','Relative volume is passed in forensics and entry-quality logic; default entry-quality blocking is shadow.'),
        (97,'claude_decider/free_context.py','def _pivots','Fractal support/resistance computed from known bars.'),
        (103,'claude_decider/free_context.py','cz = channel_zscore','Regression-channel z-score in decision context.'),
        (118,'claude_decider/free_context.py','"macro": {"vix": vix','Raw VIX/DXY context; source explicitly rejects treating the historical macro→gold relation as directional proof.'),
    ]:
        put(num,'decider','context_calculation',path,needle,note)

    for component,path in [('backend',legacy),('bot',recorder)]:
        put(22,component,'smoothing_helper',path,"alpha = 1.0 / period" if component=='backend' else 'def _rma','Internal Wilder smoothing, not an extra independent directional signal.')
    put(1,'backend','placeholder_only',legacy,'elif "ichimoku" in feat.lower()','No Ichimoku computation found in audited production paths; feature name defaulted, not a cloud implementation.')
    put(84,'backend','placeholder_only',legacy,'elif "cmf" in feat.lower()','CMF feature defaults to zero; no actual Chaikin/CMF production computation found in scope.')
    put(54,'backend','research_only','backend/services/permutation_batch_service.py','df["cci_20"]','CCI is calculated by permutation research batch, not established in the main live direction engine.')
    put(43,'backend','related_not_equivalent','backend/services/technical_indicators.py','def rolling_mad','MAD outlier cleaning is related to robust statistics, not proof of a moving-median/Hampel indicator.')
    put(72,'bot','related_not_equivalent','yeni deneme/phase_rules.py','def squeeze_ratio','ATR14/ATR100 compression is not the Bollinger-inside-Keltner TTM/LazyBear squeeze.')
    put(117,'backend','unavailable_feed','backend/services/oil_analysis_service.py','async def fetch_eia_inventory','This EIA fetch returns None by design; EIA calendar context elsewhere is not an actual inventory-surprise feed.')
    put(110,'backend','related_not_equivalent','backend/services/cortex_memory.py','Analog retrieval (kNN)','CORTEX analog kNN is a different algorithm from Lorentzian Classification; current injection flag not runtime verified.')
    put(9,'backend','related_not_equivalent','backend/services/xauusd_v2_service.py','dist_ema{n}_atr','ATR-normalized EMA displacement is not the percentage BIAS formula.')
    put(114,'backend','related_not_equivalent','backend/services/xauusd_v2_service.py','for name in ("DXY", "US10Y", "VIX")','Using a VIX reference does not establish an options-chain IV/skew/gamma engine.')
    put(15,'backend','alias_not_separately_counted',legacy,'ema_20 =','EXPMA duplicates the EMA family at this taxonomy level; no separately named EXPMA implementation counted.')
    put(16,'bot','alias_not_separately_counted','yeni deneme/forexsai_demo_bot.py','donch_high_now =','TAQ is a Donchian-type alias; no separate TAQ implementation counted.')

    connected = {'decision_calculation','context_calculation','proxy_calculation'}
    for row in rows.values():
        states = {row[x] for x in ('backend','bot','decider')}
        if states & connected:
            overall = 'connected_calculation_or_context'
        elif 'shadow_or_disabled' in states:
            overall = 'shadow_only_match'
        elif 'placeholder_only' in states:
            overall = 'placeholder_only'
        elif 'research_only' in states:
            overall = 'research_only'
        elif 'smoothing_helper' in states:
            overall = 'smoothing_helper'
        elif 'related_not_equivalent' in states:
            overall = 'related_not_equivalent'
        elif 'unavailable_feed' in states:
            overall = 'unavailable_feed'
        elif 'alias_not_separately_counted' in states:
            overall = 'alias_not_separately_counted'
        else:
            overall = 'not_found_in_audited_paths'
        row['overall'] = overall
    values = list(rows.values())
    summary = {'atlas_cards':len(values),'overall_counts':dict(Counter(r['overall'] for r in values)),
               'connected_by_component':{c:sum(r[c] in connected for r in values) for c in ('backend','bot','decider')},
               'recorder_distinct_families':len(recorder_map),'legacy_core_families_including_williams_r':12,
               'scope':'Checked-out source and local artifacts only. Partial card matches count once, aliases do not inflate counts; live deployment/config not verified.'}
    result = {'summary':summary,'rows':values}
    (OUT/'USAGE_MATRIX.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    lines=['# Atlas × ForexSAI / bot / Decider\n\n',summary['scope']+'\n\n',
           'A positive row can cover only one member of a grouped card (e.g. OBV without PVT/ADL). “Not found” is limited to audited production paths and excludes the downloaded vendor atlas, offline research trees, tests and historical backups.\n\n',
           '| ID / family | Backend | Bot local calculation | Decider | Evidence and limitation |\n|---|---|---|---|---|\n']
    for row in values:
        refs=' · '.join(f"[{e['component']}:{Path(e['path']).name}:{e['line']}]({ROOT / e['path']}:{e['line']})" for e in row['evidence'])
        notes=' '.join(row['notes']).replace('|','/')
        lines.append(f"| {row['id']} {row['name']} | {row['backend']} | {row['bot']} | {row['decider']} | {refs} {notes} |\n")
    (OUT/'USAGE_MATRIX.md').write_text(''.join(lines))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
