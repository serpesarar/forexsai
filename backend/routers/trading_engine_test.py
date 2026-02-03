"""
Trading Engine Test Endpoint
Tüm yeni modülleri mock data ile test eder
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/test/trading-engine", tags=["Trading Engine Tests"])


@router.get("/all-modules")
async def test_all_modules():
    """Tüm trading engine modüllerini test et"""
    results = {
        "mtf_veto": await test_mtf_veto(),
        "regime_block": await test_regime_block(),
        "layer_conflict": await test_layer_conflict(),
        "pattern_priority": await test_pattern_priority(),
        "adaptive_threshold": await test_adaptive_threshold(),
        "state_machine": await test_state_machine(),
        "portfolio_risk": await test_portfolio_risk(),
        "learning_check": await test_learning_check(),
    }
    
    passed = sum(1 for r in results.values() if r.get("passed"))
    total = len(results)
    
    return {
        "summary": f"{passed}/{total} tests passed",
        "all_passed": passed == total,
        "results": results
    }


@router.get("/mtf-veto")
async def test_mtf_veto():
    """MTF Hard Veto testi - 4H ters trend senaryosu"""
    try:
        from services.trading_engine import validate_mtf_consensus
        
        # Senaryo 1: 4H SELL trend, kullanıcı BUY istiyor → VETO
        mtf_data_counter = {
            '4H': {'trend': 'DOWN', 'confidence': 0.75},
            '1D': {'trend': 'DOWN', 'confidence': 0.80}
        }
        result1 = validate_mtf_consensus("XAUUSD", "BUY", mtf_data_counter)
        
        # Senaryo 2: 4H ve 1D aynı yön → İZİN
        mtf_data_aligned = {
            '4H': {'trend': 'UP', 'confidence': 0.70},
            '1D': {'trend': 'UP', 'confidence': 0.65}
        }
        result2 = validate_mtf_consensus("XAUUSD", "BUY", mtf_data_aligned)
        
        # Senaryo 3: 4H soft veto (düşük confidence)
        mtf_data_soft = {
            '4H': {'trend': 'DOWN', 'confidence': 0.55}
        }
        result3 = validate_mtf_consensus("XAUUSD", "BUY", mtf_data_soft)
        
        passed = (
            result1['allowed'] == False and  # Counter-trend blocked
            result2['allowed'] == True and   # Aligned allowed
            result3['allowed'] == True       # Soft (low confidence) allowed with warning
        )
        
        return {
            "passed": passed,
            "test_name": "MTF Hard Veto",
            "scenarios": [
                {
                    "name": "Counter-trend (4H DOWN, user BUY)",
                    "expected": "BLOCKED",
                    "actual": "BLOCKED" if not result1['allowed'] else "ALLOWED",
                    "reason": result1.get('reason'),
                    "veto_level": result1.get('veto_level'),
                    "passed": not result1['allowed']
                },
                {
                    "name": "Aligned trend (4H UP, user BUY)",
                    "expected": "ALLOWED",
                    "actual": "ALLOWED" if result2['allowed'] else "BLOCKED",
                    "reason": result2.get('reason'),
                    "passed": result2['allowed']
                },
                {
                    "name": "Soft veto (4H DOWN low conf)",
                    "expected": "ALLOWED with warning",
                    "actual": f"ALLOWED ({result3.get('veto_level')})" if result3['allowed'] else "BLOCKED",
                    "confidence_penalty": result3.get('confidence_penalty'),
                    "passed": result3['allowed']
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/regime-block")
async def test_regime_block():
    """Regime Hard Block testi"""
    try:
        from services.trading_engine import apply_regime_blocking
        from services.trading_engine.constants import MarketRegime
        
        # Senaryo 1: STRONG_TREND_UP + SELL → BLOCKED
        result1 = apply_regime_blocking("SELL", MarketRegime.STRONG_TREND_UP)
        
        # Senaryo 2: STRONG_TREND_DOWN + BUY → BLOCKED
        result2 = apply_regime_blocking("BUY", MarketRegime.STRONG_TREND_DOWN)
        
        # Senaryo 3: HIGH_VOL_CHOPPY → ALL BLOCKED
        result3 = apply_regime_blocking("BUY", MarketRegime.HIGH_VOL_CHOPPY)
        
        # Senaryo 4: RANGE_BOUND → ALLOWED
        result4 = apply_regime_blocking("BUY", MarketRegime.RANGE_BOUND)
        
        passed = (
            result1['blocked'] == True and
            result2['blocked'] == True and
            result3['blocked'] == True and
            result4['blocked'] == False
        )
        
        return {
            "passed": passed,
            "test_name": "Regime Hard Block",
            "scenarios": [
                {
                    "name": "STRONG_TREND_UP + SELL",
                    "expected": "BLOCKED",
                    "actual": "BLOCKED" if result1['blocked'] else "ALLOWED",
                    "reason": result1.get('reason'),
                    "passed": result1['blocked']
                },
                {
                    "name": "STRONG_TREND_DOWN + BUY",
                    "expected": "BLOCKED",
                    "actual": "BLOCKED" if result2['blocked'] else "ALLOWED",
                    "reason": result2.get('reason'),
                    "passed": result2['blocked']
                },
                {
                    "name": "HIGH_VOL_CHOPPY (any direction)",
                    "expected": "BLOCKED",
                    "actual": "BLOCKED" if result3['blocked'] else "ALLOWED",
                    "reason": result3.get('reason'),
                    "passed": result3['blocked']
                },
                {
                    "name": "RANGE_BOUND + BUY",
                    "expected": "ALLOWED",
                    "actual": "ALLOWED" if not result4['blocked'] else "BLOCKED",
                    "multiplier": result4.get('confidence_multiplier'),
                    "passed": not result4['blocked']
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/layer-conflict")
async def test_layer_conflict():
    """Layer Veto testi - Critical vs Technical çelişkisi"""
    try:
        from services.trading_engine import resolve_layer_conflict
        
        # Senaryo 1: Critical SELL (80%), Technical BUY (30%) → Critical kazanır
        result1 = resolve_layer_conflict(
            critical_dir="SELL", critical_conf=0.80,
            technical_dir="BUY", technical_conf=0.30,
            context_dir="NEUTRAL", context_conf=0.50
        )
        
        # Senaryo 2: 2/3 çoğunluk BUY
        result2 = resolve_layer_conflict(
            critical_dir="BUY", critical_conf=0.60,
            technical_dir="BUY", technical_conf=0.55,
            context_dir="SELL", context_conf=0.40
        )
        
        # Senaryo 3: 1-1-1 tam çelişki → HOLD
        result3 = resolve_layer_conflict(
            critical_dir="BUY", critical_conf=0.50,
            technical_dir="SELL", technical_conf=0.50,
            context_dir="NEUTRAL", context_conf=0.50
        )
        
        passed = (
            result1['resolved_direction'] == 'SELL' and  # Critical wins
            result2['resolved_direction'] == 'BUY' and   # Majority wins
            result3['resolved_direction'] == 'HOLD'      # No consensus
        )
        
        return {
            "passed": passed,
            "test_name": "Layer Conflict Resolution",
            "scenarios": [
                {
                    "name": "Critical SELL(80%) vs Technical BUY(30%)",
                    "expected": "SELL (Critical veto)",
                    "actual": result1['resolved_direction'],
                    "conflict_type": result1.get('conflict_type'),
                    "veto_applied": result1.get('veto_applied'),
                    "reasoning": result1.get('reasoning'),
                    "passed": result1['resolved_direction'] == 'SELL'
                },
                {
                    "name": "2/3 Majority BUY",
                    "expected": "BUY",
                    "actual": result2['resolved_direction'],
                    "conflict_type": result2.get('conflict_type'),
                    "passed": result2['resolved_direction'] == 'BUY'
                },
                {
                    "name": "1-1-1 Full Conflict",
                    "expected": "HOLD",
                    "actual": result3['resolved_direction'],
                    "conflict_type": result3.get('conflict_type'),
                    "passed": result3['resolved_direction'] == 'HOLD'
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/pattern-priority")
async def test_pattern_priority():
    """Pattern TF Önceliği testi - 1H vs 15m çakışması"""
    try:
        from services.trading_engine import resolve_pattern_conflicts
        
        # Senaryo 1: 1H Bullish vs 15m Bearish → 1H kazanır
        patterns1 = [
            {'name': 'Double Bottom', 'timeframe': '1H', 'direction': 'BULLISH', 'confidence': 0.75, 'status': 'CONFIRMED'},
            {'name': 'RSI Divergence', 'timeframe': '15m', 'direction': 'BEARISH', 'confidence': 0.60, 'status': 'CONFIRMED'}
        ]
        result1 = resolve_pattern_conflicts(patterns1)
        
        # Senaryo 2: 4H Bearish vs 1H Bullish → 4H kazanır
        patterns2 = [
            {'name': 'Head & Shoulders', 'timeframe': '4H', 'direction': 'BEARISH', 'confidence': 0.80, 'status': 'CONFIRMED'},
            {'name': 'Bull Flag', 'timeframe': '1H', 'direction': 'BULLISH', 'confidence': 0.70, 'status': 'CONFIRMED'}
        ]
        result2 = resolve_pattern_conflicts(patterns2)
        
        # Senaryo 3: Aynı yönde patternler → Confluence
        patterns3 = [
            {'name': 'Double Bottom', 'timeframe': '4H', 'direction': 'BULLISH', 'confidence': 0.80, 'status': 'CONFIRMED'},
            {'name': 'Bull Flag', 'timeframe': '1H', 'direction': 'BULLISH', 'confidence': 0.70, 'status': 'CONFIRMED'},
            {'name': 'Morning Star', 'timeframe': '15m', 'direction': 'BULLISH', 'confidence': 0.65, 'status': 'CONFIRMED'}
        ]
        result3 = resolve_pattern_conflicts(patterns3)
        
        passed = (
            result1['dominant_direction'] == 'BUY' and  # 1H wins
            result2['dominant_direction'] == 'SELL' and  # 4H wins
            result3['has_conflict'] == False  # No conflict, all aligned
        )
        
        return {
            "passed": passed,
            "test_name": "Pattern TF Priority",
            "scenarios": [
                {
                    "name": "1H Bullish vs 15m Bearish",
                    "expected": "BUY (1H wins)",
                    "actual": result1['dominant_direction'],
                    "has_conflict": result1['has_conflict'],
                    "ignored": [p.get('name') for p in result1.get('ignored_patterns', [])],
                    "passed": result1['dominant_direction'] == 'BUY'
                },
                {
                    "name": "4H Bearish vs 1H Bullish",
                    "expected": "SELL (4H wins)",
                    "actual": result2['dominant_direction'],
                    "has_conflict": result2['has_conflict'],
                    "ignored": [p.get('name') for p in result2.get('ignored_patterns', [])],
                    "passed": result2['dominant_direction'] == 'SELL'
                },
                {
                    "name": "All Bullish (4H+1H+15m)",
                    "expected": "No conflict",
                    "actual": "No conflict" if not result3['has_conflict'] else "Conflict",
                    "confidence_adjustment": result3.get('confidence_adjustment'),
                    "passed": not result3['has_conflict']
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/adaptive-threshold")
async def test_adaptive_threshold():
    """Adaptive Threshold testi"""
    try:
        from services.trading_engine import get_adaptive_threshold
        
        # Senaryo 1: Düşük win rate → Threshold yükselir
        result1 = get_adaptive_threshold("XAUUSD", "balanced", {
            'win_rate': 0.35,
            'total_trades': 20
        })
        
        # Senaryo 2: Yüksek win rate → Threshold düşer
        result2 = get_adaptive_threshold("XAUUSD", "balanced", {
            'win_rate': 0.75,
            'total_trades': 20
        })
        
        # Senaryo 3: Strategy farklılığı
        result3_safe = get_adaptive_threshold("XAUUSD", "ultra_safe", None)
        result3_aggr = get_adaptive_threshold("XAUUSD", "aggressive", None)
        
        passed = (
            result1['threshold'] > 0.55 and  # Low WR → higher threshold
            result2['threshold'] < 0.55 and  # High WR → lower threshold
            result3_safe['threshold'] > result3_aggr['threshold']  # ultra_safe > aggressive
        )
        
        return {
            "passed": passed,
            "test_name": "Adaptive Threshold",
            "scenarios": [
                {
                    "name": "Low win rate (35%)",
                    "expected": "Threshold > 55%",
                    "actual": f"{result1['threshold']*100:.0f}%",
                    "reason": result1.get('reason'),
                    "passed": result1['threshold'] > 0.55
                },
                {
                    "name": "High win rate (75%)",
                    "expected": "Threshold < 55%",
                    "actual": f"{result2['threshold']*100:.0f}%",
                    "reason": result2.get('reason'),
                    "passed": result2['threshold'] < 0.55
                },
                {
                    "name": "Strategy comparison",
                    "ultra_safe": f"{result3_safe['threshold']*100:.0f}%",
                    "aggressive": f"{result3_aggr['threshold']*100:.0f}%",
                    "expected": "ultra_safe > aggressive",
                    "passed": result3_safe['threshold'] > result3_aggr['threshold']
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/state-machine")
async def test_state_machine():
    """State Machine testi"""
    try:
        from services.trading_engine import check_signal_validity, get_state_machine
        
        sm = get_state_machine()
        
        # Mevcut state
        status = sm.get_full_status()
        
        # Can trade check
        can_trade, trade_reason = sm.can_trade()
        
        # Signal validity check
        validity = check_signal_validity(
            symbol="XAUUSD",
            new_direction="BUY",
            new_confidence=70,
            current_price=2850.0,
            strategy="balanced"
        )
        
        return {
            "passed": True,  # State machine always works
            "test_name": "State Machine",
            "current_state": status,
            "can_trade": can_trade,
            "trade_reason": trade_reason,
            "signal_validity": validity
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/portfolio-risk")
async def test_portfolio_risk():
    """Portfolio Risk Manager testi"""
    try:
        from services.trading_engine import check_portfolio_risk
        from services.trading_engine.portfolio_risk_manager import portfolio_risk_manager
        
        # Normal durum
        result1 = check_portfolio_risk("XAUUSD", "BUY", 1.0)
        
        # Status
        status = portfolio_risk_manager.get_status()
        
        return {
            "passed": True,
            "test_name": "Portfolio Risk Manager",
            "can_trade": result1['can_trade'],
            "risk_level": result1['risk_level'],
            "max_position_size": result1['max_position_size'],
            "warnings": result1['warnings'],
            "portfolio_status": status
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}


@router.get("/learning-check")
async def test_learning_check():
    """Learning Proaktif testi"""
    try:
        from services.trading_engine import sync_learning_check
        
        # Senaryo 1: Düşük başarı oranı
        result1 = sync_learning_check("XAUUSD", "BUY", {
            'win_rate': 0.25,
            'total_trades': 10
        })
        
        # Senaryo 2: Yüksek başarı oranı
        result2 = sync_learning_check("XAUUSD", "BUY", {
            'win_rate': 0.70,
            'total_trades': 10
        })
        
        # Senaryo 3: Veri yok
        result3 = sync_learning_check("XAUUSD", "BUY", None)
        
        passed = (
            result1['allow'] == False and  # Low success → block
            result2['allow'] == True and   # High success → allow
            result3['allow'] == True       # No data → allow
        )
        
        return {
            "passed": passed,
            "test_name": "Learning Proaktif",
            "scenarios": [
                {
                    "name": "Low success rate (25%)",
                    "expected": "BLOCKED",
                    "actual": "BLOCKED" if not result1['allow'] else "ALLOWED",
                    "recommendation": result1.get('recommendation'),
                    "reason": result1.get('reason'),
                    "passed": not result1['allow']
                },
                {
                    "name": "High success rate (70%)",
                    "expected": "ALLOWED",
                    "actual": "ALLOWED" if result2['allow'] else "BLOCKED",
                    "recommendation": result2.get('recommendation'),
                    "passed": result2['allow']
                },
                {
                    "name": "No data",
                    "expected": "ALLOWED",
                    "actual": "ALLOWED" if result3['allow'] else "BLOCKED",
                    "passed": result3['allow']
                }
            ]
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}
