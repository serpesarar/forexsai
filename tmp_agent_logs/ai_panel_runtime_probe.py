import asyncio
import json
import sys
from pathlib import Path

ROOT = Path('/Users/melihcanodacioglu/Desktop/panel')
BACKEND = ROOT / 'backend'
OUT = ROOT / 'tmp_agent_logs' / 'ai_panel_runtime_probe_results.json'

sys.path.insert(0, str(BACKEND))

from services.ai_panel_analysis_service import (
    _ANALYSIS_CACHE,
    _build_prompt_payload,
    _collect_symbol_extras,
    build_context_pack,
    get_ai_panel_analysis,
)
from database.supabase_client import get_supabase_client

SYMBOLS = ['NDX.INDX', 'XAUUSD', 'USOIL.FOREX', 'GDAXI.INDX']


def resolve_symbols() -> list[str]:
    requested = sys.argv[1:]
    if not requested:
        return SYMBOLS
    return requested


def db_probe(symbol: str) -> dict:
    client = get_supabase_client()
    result = {
        'cache_row_exists': False,
        'history_count': None,
        'latest_cache_updated_at': None,
        'latest_history_created_at': None,
        'error': None,
    }
    if client is None:
        result['error'] = 'no_supabase_client'
        return result
    try:
        cache_query = client.table('ai_panel_analysis_cache')
        cache_query = cache_query.select('symbol,updated_at,expires_at,prompt_version')
        cache_query = cache_query.eq('symbol', symbol)
        cache_query = cache_query.limit(1)
        cache_resp = cache_query.execute()
        cache_rows = cache_resp.get('data') or []

        hist_query = client.table('ai_panel_analysis_history')
        hist_query = hist_query.select('symbol,created_at,prompt_version')
        hist_query = hist_query.eq('symbol', symbol)
        hist_query = hist_query.order('created_at', desc=True)
        hist_query = hist_query.limit(10)
        hist_resp = hist_query.execute()
        hist_rows = hist_resp.get('data') or []

        result['cache_row_exists'] = bool(cache_rows)
        result['latest_cache_updated_at'] = cache_rows[0].get('updated_at') if cache_rows else None
        result['history_count'] = len(hist_rows)
        result['latest_history_created_at'] = hist_rows[0].get('created_at') if hist_rows else None
    except Exception as exc:
        result['error'] = repr(exc)
    return result


def prompt_summary(prompt: dict) -> dict:
    symbol_profile = prompt.get('symbol_profile') or {}
    market_state = prompt.get('market_state') or {}
    news = prompt.get('news') or {}
    calendar = prompt.get('economic_calendar') or {}
    return {
        'asset_class': symbol_profile.get('asset_class'),
        'display_name': symbol_profile.get('display_name'),
        'short_label': symbol_profile.get('short_label'),
        'session_name': symbol_profile.get('session_name'),
        'market_phase': market_state.get('phase'),
        'is_primary_session_open': market_state.get('is_primary_session_open'),
        'minutes_to_open': market_state.get('minutes_to_open'),
        'minutes_to_close': market_state.get('minutes_to_close'),
        'unified_news_present': bool(news.get('unified')),
        'headline_count': len(news.get('headlines') or []),
        'headline_titles': [item.get('title') for item in (news.get('headlines') or [])[:3]],
        'calendar_present': bool(calendar),
        'calendar_event_count': len(calendar.get('recent_or_upcoming') or []),
        'calendar_risk_level': ((calendar.get('risk') or {}).get('level')),
        'calendar_flags': calendar.get('flags') or [],
        'regime_present': bool(prompt.get('regime')),
        'comex_present': bool(news.get('comex')),
        'oil_engine_present': bool(prompt.get('oil_engine')),
        'macro_present': bool(prompt.get('macro')),
        'levels_count': len(prompt.get('levels') or []),
    }


def response_summary(result: dict) -> dict:
    claude_analysis = result.get('claude_analysis') or {}
    panel_signal = claude_analysis.get('panel_signal') or {}
    return {
        'shape': {
            'top_level_keys': list(result.keys()),
            'claude_analysis_keys': list(claude_analysis.keys()),
            'panel_signal_keys': list(panel_signal.keys()),
        },
        'ml_direction': claude_analysis.get('ml_direction'),
        'claude_direction': claude_analysis.get('claude_direction'),
        'claude_confidence': claude_analysis.get('claude_confidence'),
        'headline': panel_signal.get('headline'),
        'scalp_bias': panel_signal.get('scalp_bias'),
        'intraday_bias': panel_signal.get('intraday_bias'),
        'market_behavior': panel_signal.get('market_behavior'),
        'entry_plan': panel_signal.get('entry_plan'),
        'key_levels_sample': (panel_signal.get('key_levels') or [])[:4],
        'macro_risk': panel_signal.get('macro_risk'),
        'event_risk': panel_signal.get('event_risk'),
        'top_factors': (panel_signal.get('top_factors') or [])[:3],
        'counter_factors': (panel_signal.get('counter_factors') or [])[:3],
        'data_quality': panel_signal.get('data_quality'),
        'analysis_meta': claude_analysis.get('analysis_meta'),
        'market_context': claude_analysis.get('market_context'),
        'data_sources': claude_analysis.get('data_sources'),
    }


async def inspect_symbol(symbol: str) -> dict:
    _ANALYSIS_CACHE.pop(symbol, None)
    before = db_probe(symbol)
    context = await build_context_pack(symbol)
    extras = await _collect_symbol_extras(symbol, context)
    prompt = _build_prompt_payload(context, extras)
    fresh = await asyncio.wait_for(get_ai_panel_analysis(symbol, force_refresh=True), timeout=180)
    cached = await asyncio.wait_for(get_ai_panel_analysis(symbol, force_refresh=False), timeout=90)
    refreshed = await asyncio.wait_for(get_ai_panel_analysis(symbol, force_refresh=True), timeout=180)

    return {
        'symbol': symbol,
        'prompt_summary': prompt_summary(prompt),
        'fresh_response_summary': response_summary(fresh),
        'cached_response_summary': response_summary(cached),
        'refreshed_response_summary': response_summary(refreshed),
        'cache_behavior': {
            'fresh_cache_hit': (((fresh.get('claude_analysis') or {}).get('analysis_meta') or {}).get('cache_hit')),
            'cached_cache_hit': (((cached.get('claude_analysis') or {}).get('analysis_meta') or {}).get('cache_hit')),
            'refreshed_cache_hit': (((refreshed.get('claude_analysis') or {}).get('analysis_meta') or {}).get('cache_hit')),
            'fresh_generated_at': (((fresh.get('claude_analysis') or {}).get('analysis_meta') or {}).get('generated_at')),
            'cached_generated_at': (((cached.get('claude_analysis') or {}).get('analysis_meta') or {}).get('generated_at')),
            'refreshed_generated_at': (((refreshed.get('claude_analysis') or {}).get('analysis_meta') or {}).get('generated_at')),
        },
        'persistence': {
            'before': before,
            'after': db_probe(symbol),
        },
    }


async def main() -> None:
    results = []
    selected_symbols = resolve_symbols()
    for symbol in selected_symbols:
        try:
            results.append(await inspect_symbol(symbol))
        except Exception as exc:
            results.append({'symbol': symbol, 'error': repr(exc)})
        OUT.write_text(
            json.dumps({'results': results}, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )
        print(f'completed:{symbol}')
    OUT.write_text(json.dumps({'results': results}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(str(OUT))


if __name__ == '__main__':
    asyncio.run(main())
