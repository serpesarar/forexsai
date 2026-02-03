"""
Layered Decision Maker - 5 Katmanlı Karar Sistemi
Katman 5: Portföy -> Katman 1: Execution
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from .constants import MarketRegime, SignalState
from .regime_detector import RegimeAnalysis
from .mtf_analyzer import TimeframeAnalysis
from .confluence_engine import ConfluenceResult, ConfluenceEngine
from .signal_state_machine import SignalStateMachine, SetupSignal, SetupType


@dataclass
class LayeredDecision:
    """5 Katmanlı Karar Sonucu"""
    # Katman 5: Portföy
    portfolio_status: str
    max_risk_available: float
    
    # Katman 4: Rejim
    regime: MarketRegime
    regime_confidence: float
    allowed_directions: List[str]
    
    # Katman 3: Setup
    has_setup: bool
    setup_quality: float
    setup_direction: Optional[str]
    
    # Katman 2: Mikro Yapı
    micro_status: str
    optimal_entry: Optional[float]
    refined_stop: Optional[float]
    
    # Katman 1: Final
    final_action: str  # BUY, SELL, HOLD, WAIT, NO_TRADE
    final_direction: str  # LONG, SHORT, NEUTRAL
    position_size: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)


class LayeredDecisionMaker:
    """
    5 Katmanlı Karar Sistemi
    
    Katman 5: Portföy Yönetimi (Aylık)
    Katman 4: Rejim Tespiti (Günlük)
    Katman 3: Setup Tespiti (4H)
    Katman 2: Mikro Yapı (1H)
    Katman 1: Execution (15m)
    """
    
    def __init__(self):
        self.confluence_engine = ConfluenceEngine()
        self.state_machine = SignalStateMachine()
        
        # Portfolio state (simulated)
        self.max_daily_risk = 0.02  # 2%
        self.current_drawdown = 0.0
        self.monthly_loss = 0.0
    
    def make_decision(
        self,
        symbol: str,
        current_price: float,
        tf_analyses: Dict[str, TimeframeAnalysis],
        regime: RegimeAnalysis,
        patterns: Optional[List[Dict]] = None
    ) -> LayeredDecision:
        """5 katmanlı karar al"""
        
        reasoning = []
        
        # ═══════════════════════════════════════════════════════════════
        # KATMAN 5: PORTFÖY YÖNETİMİ
        # ═══════════════════════════════════════════════════════════════
        portfolio_status, max_risk = self._layer5_portfolio()
        reasoning.append(f"L5 Portföy: {portfolio_status}")
        
        if portfolio_status == "NO_NEW_TRADES":
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=0,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=[],
                has_setup=False,
                setup_quality=0,
                setup_direction=None,
                micro_status="BLOCKED",
                optimal_entry=None,
                refined_stop=None,
                final_action="NO_TRADE",
                final_direction="NEUTRAL",
                position_size=0,
                confidence=0,
                reasoning=reasoning
            )
        
        # ═══════════════════════════════════════════════════════════════
        # KATMAN 4: REJİM TESPİTİ
        # ═══════════════════════════════════════════════════════════════
        allowed_directions = self._layer4_regime(regime)
        reasoning.append(f"L4 Rejim: {regime.regime.value}, izin: {allowed_directions}")
        
        if not allowed_directions:
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=max_risk,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=[],
                has_setup=False,
                setup_quality=0,
                setup_direction=None,
                micro_status="REGIME_BLOCKED",
                optimal_entry=None,
                refined_stop=None,
                final_action="NO_TRADE",
                final_direction="NEUTRAL",
                position_size=0,
                confidence=regime.confidence,
                reasoning=reasoning
            )
        
        # ═══════════════════════════════════════════════════════════════
        # KATMAN 3: SETUP TESPİTİ
        # ═══════════════════════════════════════════════════════════════
        best_confluence = None
        best_direction = None
        
        for direction in allowed_directions:
            confluence = self.confluence_engine.calculate(
                direction=direction,
                tf_analyses=tf_analyses,
                regime=regime,
                current_price=current_price,
                patterns=patterns
            )
            
            if confluence.minimums_met and confluence.total_score >= 0.55:
                if best_confluence is None or confluence.total_score > best_confluence.total_score:
                    best_confluence = confluence
                    best_direction = direction
        
        if best_confluence is None:
            reasoning.append("L3 Setup: Yeterli konfluans yok")
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=max_risk,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=allowed_directions,
                has_setup=False,
                setup_quality=0,
                setup_direction=None,
                micro_status="NO_SETUP",
                optimal_entry=None,
                refined_stop=None,
                final_action="WAIT",
                final_direction="NEUTRAL",
                position_size=0,
                confidence=0,
                reasoning=reasoning
            )
        
        reasoning.append(f"L3 Setup: {best_direction} konfluans={best_confluence.total_score:.2f}")
        reasoning.extend(best_confluence.supporting_factors)
        
        # ═══════════════════════════════════════════════════════════════
        # KATMAN 2: MİKRO YAPI
        # ═══════════════════════════════════════════════════════════════
        micro_status, optimal_entry, refined_stop = self._layer2_micro(
            best_direction, tf_analyses, current_price
        )
        reasoning.append(f"L2 Mikro: {micro_status}")
        
        if micro_status == "INVALIDATED":
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=max_risk,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=allowed_directions,
                has_setup=True,
                setup_quality=best_confluence.total_score,
                setup_direction=best_direction,
                micro_status=micro_status,
                optimal_entry=None,
                refined_stop=None,
                final_action="WAIT",
                final_direction="NEUTRAL",
                position_size=0,
                confidence=best_confluence.total_score * 100,
                reasoning=reasoning
            )
        
        # ═══════════════════════════════════════════════════════════════
        # KATMAN 1: EXECUTION
        # ═══════════════════════════════════════════════════════════════
        can_trade, trade_reason = self.state_machine.can_trade()
        
        if not can_trade:
            reasoning.append(f"L1 Execution: {trade_reason}")
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=max_risk,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=allowed_directions,
                has_setup=True,
                setup_quality=best_confluence.total_score,
                setup_direction=best_direction,
                micro_status=micro_status,
                optimal_entry=optimal_entry,
                refined_stop=refined_stop,
                final_action="COOLDOWN",
                final_direction=best_direction,
                position_size=0,
                confidence=best_confluence.total_score * 100,
                reasoning=reasoning
            )
        
        # Direction change check
        can_change, change_reason = self.state_machine.can_change_direction(
            best_direction, best_confluence.total_score * 100, current_price
        )
        
        if not can_change:
            reasoning.append(f"L1: {change_reason}")
            return LayeredDecision(
                portfolio_status=portfolio_status,
                max_risk_available=max_risk,
                regime=regime.regime,
                regime_confidence=regime.confidence,
                allowed_directions=allowed_directions,
                has_setup=True,
                setup_quality=best_confluence.total_score,
                setup_direction=best_direction,
                micro_status="STABILITY_BLOCK",
                optimal_entry=optimal_entry,
                refined_stop=refined_stop,
                final_action="HOLD",
                final_direction=self.state_machine.get_state().last_signal_direction or "NEUTRAL",
                position_size=0,
                confidence=best_confluence.total_score * 100,
                reasoning=reasoning
            )
        
        # Final decision
        final_action = "BUY" if best_direction == "LONG" else "SELL"
        position_size = self._calculate_position_size(
            best_confluence.total_score,
            regime.position_size_multiplier,
            max_risk
        )
        
        reasoning.append(f"L1 Final: {final_action} size={position_size:.1%}")
        
        return LayeredDecision(
            portfolio_status=portfolio_status,
            max_risk_available=max_risk,
            regime=regime.regime,
            regime_confidence=regime.confidence,
            allowed_directions=allowed_directions,
            has_setup=True,
            setup_quality=best_confluence.total_score,
            setup_direction=best_direction,
            micro_status=micro_status,
            optimal_entry=optimal_entry,
            refined_stop=refined_stop,
            final_action=final_action,
            final_direction=best_direction,
            position_size=position_size,
            confidence=best_confluence.total_score * 100,
            reasoning=reasoning
        )
    
    def _layer5_portfolio(self) -> Tuple[str, float]:
        """Katman 5: Portföy durumu"""
        if self.monthly_loss > 0.10:
            return "NO_NEW_TRADES", 0.0
        elif self.current_drawdown > 0.15:
            return "DEFENSIVE", self.max_daily_risk * 0.3
        elif self.current_drawdown > 0.10:
            return "DEFENSIVE", self.max_daily_risk * 0.5
        else:
            return "NORMAL", self.max_daily_risk
    
    def _layer4_regime(self, regime: RegimeAnalysis) -> List[str]:
        """Katman 4: İzin verilen yönler"""
        if regime.regime == MarketRegime.HIGH_VOL_CHOPPY:
            return []
        elif regime.regime == MarketRegime.STRONG_TREND_UP:
            return ["LONG"]
        elif regime.regime == MarketRegime.STRONG_TREND_DOWN:
            return ["SHORT"]
        elif regime.regime == MarketRegime.TREND_EXHAUSTING:
            return []  # Bekle
        elif regime.counter_trend_allowed:
            return ["LONG", "SHORT"]
        elif regime.trend_direction:
            return [regime.trend_direction]
        else:
            return ["LONG", "SHORT"]
    
    def _layer2_micro(
        self, 
        direction: str, 
        tf_analyses: Dict[str, TimeframeAnalysis],
        current_price: float
    ) -> Tuple[str, Optional[float], Optional[float]]:
        """Katman 2: Mikro yapı analizi"""
        
        h1 = tf_analyses.get("1H")
        if not h1:
            return "READY_FOR_ENTRY", current_price, None
        
        # EMA20'ye yakınlık kontrolü
        ema20 = h1.key_levels.get("ema20", current_price)
        distance_pct = abs(current_price - ema20) / current_price * 100
        
        if direction == "LONG":
            if current_price < ema20 * 0.99:  # EMA altında
                return "WAIT_FOR_PULLBACK", ema20, h1.key_levels.get("last_swing_low")
            elif distance_pct > 1.0:  # Çok uzakta
                return "WAIT_FOR_PULLBACK", ema20, h1.key_levels.get("last_swing_low")
        else:
            if current_price > ema20 * 1.01:
                return "WAIT_FOR_PULLBACK", ema20, h1.key_levels.get("last_swing_high")
            elif distance_pct > 1.0:
                return "WAIT_FOR_PULLBACK", ema20, h1.key_levels.get("last_swing_high")
        
        # Structure invalidation check
        if h1.structure.value == "chaotic":
            return "INVALIDATED", None, None
        
        return "READY_FOR_ENTRY", current_price, h1.key_levels.get(
            "last_swing_low" if direction == "LONG" else "last_swing_high"
        )
    
    def _calculate_position_size(
        self, 
        confluence_score: float,
        regime_mult: float,
        max_risk: float
    ) -> float:
        """Pozisyon boyutu hesapla"""
        base = 0.5
        
        if confluence_score >= 0.80:
            base = 1.0
        elif confluence_score >= 0.70:
            base = 0.75
        elif confluence_score >= 0.60:
            base = 0.5
        else:
            base = 0.25
        
        return min(1.0, base * regime_mult * (max_risk / self.max_daily_risk))
