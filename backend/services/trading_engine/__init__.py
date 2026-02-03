"""
Advanced Trading Engine Package
================================
Multi-Timeframe Hiyerarşisi, Rejim Tespiti, Konfluans Motoru,
5 Katmanlı Karar Yapısı ve Sinyal State Machine

Yeni Modüller (EKSİK #1-10):
- MTF Validator (Hard Veto)
- Regime Blocker (Hard Block)
- Pattern Prioritizer (TF Önceliği)
- Layer Conflict Resolver (Veto Mekanizması)
- Adaptive Threshold (Dinamik Confidence)
- Portfolio Risk Manager (Risk Limitleri)
"""
from .constants import (
    MarketRegime, PriceStructure, SignalState, SetupType,
    TIMEFRAME_WEIGHTS, CONFLUENCE_WEIGHTS, TF_APPROVAL_MATRIX,
    MIN_SIGNAL_DURATION_HOURS, TF_PRIORITY, NULL_SIGNAL_REASONS, NULL_RETRY_TIMES,
    ADAPTIVE_THRESHOLD_CONFIG, PORTFOLIO_RISK_CONFIG
)
from .helpers import ema, atr, adx, rsi, find_swing_points, analyze_price_structure, extract_ohlcv
from .regime_detector import MarketRegimeDetector, RegimeAnalysis
from .mtf_analyzer import MultiTimeframeAnalyzer, TimeframeAnalysis
from .confluence_engine import ConfluenceEngine, ConfluenceResult
from .signal_state_machine import (
    SignalStateMachine, TradingSystemState, SetupSignal,
    get_state_machine, check_signal_validity
)
from .decision_layers import LayeredDecisionMaker, LayeredDecision

# Yeni modüller
from .mtf_validator import MTFValidator, validate_mtf_consensus, MTFValidationResult
from .regime_blocker import RegimeBlocker, apply_regime_blocking, RegimeBlockResult
from .pattern_prioritizer import PatternPrioritizer, resolve_pattern_conflicts, PatternResolutionResult
from .layer_conflict_resolver import LayerConflictResolver, resolve_layer_conflict, LayerConflictResult
from .adaptive_threshold import AdaptiveThresholdManager, get_adaptive_threshold
from .portfolio_risk_manager import PortfolioRiskManager, check_portfolio_risk
from .learning_integration import LearningIntegration, sync_learning_check, pre_prediction_learning_check

__all__ = [
    # Constants
    'MarketRegime', 'PriceStructure', 'SignalState', 'SetupType',
    'TIMEFRAME_WEIGHTS', 'CONFLUENCE_WEIGHTS', 'TF_APPROVAL_MATRIX',
    'MIN_SIGNAL_DURATION_HOURS', 'TF_PRIORITY', 'NULL_SIGNAL_REASONS', 'NULL_RETRY_TIMES',
    'ADAPTIVE_THRESHOLD_CONFIG', 'PORTFOLIO_RISK_CONFIG',
    # Helpers
    'ema', 'atr', 'adx', 'rsi', 'find_swing_points', 'analyze_price_structure', 'extract_ohlcv',
    # Core Classes
    'MarketRegimeDetector', 'RegimeAnalysis',
    'MultiTimeframeAnalyzer', 'TimeframeAnalysis', 
    'ConfluenceEngine', 'ConfluenceResult',
    'SignalStateMachine', 'TradingSystemState', 'SetupSignal',
    'get_state_machine', 'check_signal_validity',
    'LayeredDecisionMaker', 'LayeredDecision',
    # EKSİK #2: MTF Validator
    'MTFValidator', 'validate_mtf_consensus', 'MTFValidationResult',
    # EKSİK #6: Regime Blocker
    'RegimeBlocker', 'apply_regime_blocking', 'RegimeBlockResult',
    # EKSİK #5: Pattern Prioritizer
    'PatternPrioritizer', 'resolve_pattern_conflicts', 'PatternResolutionResult',
    # EKSİK #8: Layer Conflict Resolver
    'LayerConflictResolver', 'resolve_layer_conflict', 'LayerConflictResult',
    # EKSİK #4: Adaptive Threshold
    'AdaptiveThresholdManager', 'get_adaptive_threshold',
    # EKSİK #9: Portfolio Risk Manager
    'PortfolioRiskManager', 'check_portfolio_risk',
    # EKSİK #7: Learning Integration
    'LearningIntegration', 'sync_learning_check', 'pre_prediction_learning_check',
]
