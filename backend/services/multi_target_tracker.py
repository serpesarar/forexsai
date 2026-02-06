"""
Multi-Target Tracking Service
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SYMBOL_TARGETS = {
    'NDX.INDX': {'TP1': 15, 'TP2': 25, 'TP3': 45, 'TP4': 80, 'TP5': None, 'SL': 35},
    'XAUUSD': {'TP1': 5, 'TP2': 10, 'TP3': 25, 'TP4': 30, 'TP5': 50, 'SL': 8}
}

@dataclass
class TargetConfig:
    tp1_price: float
    tp2_price: float
    tp3_price: float
    tp4_price: Optional[float]
    tp5_price: Optional[float]
    sl_price: float
    tp1_pips: float
    tp2_pips: float
    tp3_pips: float
    tp4_pips: Optional[float]
    tp5_pips: Optional[float]
    sl_pips: float


class MultiTargetTracker:
    def __init__(self):
        self._supabase = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            from config import settings
            from supabase import create_client
            self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._supabase
    
    def calculate_targets(self, symbol: str, direction: str, entry_price: float) -> TargetConfig:
        config = SYMBOL_TARGETS.get(symbol, {'TP1': 10, 'TP2': 20, 'TP3': 35, 'TP4': 50, 'TP5': None, 'SL': 25})
        mult = 1 if direction == 'BUY' else -1
        
        return TargetConfig(
            tp1_price=entry_price + (config['TP1'] * mult),
            tp2_price=entry_price + (config['TP2'] * mult),
            tp3_price=entry_price + (config['TP3'] * mult),
            tp4_price=entry_price + (config['TP4'] * mult) if config['TP4'] else None,
            tp5_price=entry_price + (config['TP5'] * mult) if config.get('TP5') else None,
            sl_price=entry_price - (config['SL'] * mult),
            tp1_pips=config['TP1'], tp2_pips=config['TP2'], tp3_pips=config['TP3'],
            tp4_pips=config['TP4'], tp5_pips=config.get('TP5'), sl_pips=config['SL']
        )
    
    async def create_tracking(self, prediction_id: str, symbol: str, strategy: str, 
                              direction: str, entry_price: float) -> Dict:
        try:
            targets = self.calculate_targets(symbol, direction, entry_price)
            data = {
                'prediction_id': prediction_id, 'symbol': symbol, 'strategy': strategy,
                'direction': direction, 'entry_price': entry_price,
                'tp1_price': targets.tp1_price, 'tp1_pips': targets.tp1_pips,
                'tp2_price': targets.tp2_price, 'tp2_pips': targets.tp2_pips,
                'tp3_price': targets.tp3_price, 'tp3_pips': targets.tp3_pips,
                'tp4_price': targets.tp4_price, 'tp4_pips': targets.tp4_pips,
                'tp5_price': targets.tp5_price, 'tp5_pips': targets.tp5_pips,
                'sl_price': targets.sl_price, 'sl_pips': targets.sl_pips,
                'is_active': True, 'final_result': 'OPEN'
            }
            result = self.supabase.table('multi_target_predictions').insert(data).execute()
            return {'success': True, 'id': result.data[0]['id'], 'targets': data}
        except Exception as e:
            logger.error(f"Create tracking error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_price(self, symbol: str, current_price: float) -> List[Dict]:
        hits = []
        try:
            result = self.supabase.table('multi_target_predictions').select('*').eq(
                'symbol', symbol).eq('is_active', True).execute()
            
            for t in result.data or []:
                direction, entry = t['direction'], float(t['entry_price'])
                pips = (current_price - entry) if direction == 'BUY' else (entry - current_price)
                updates = {'max_pips_reached': max(pips, float(t.get('max_pips_reached') or 0))}
                
                # SL check
                sl = float(t['sl_price'])
                if (direction == 'BUY' and current_price <= sl) or (direction == 'SELL' and current_price >= sl):
                    updates.update({'sl_hit': True, 'final_result': 'SL', 'is_active': False})
                    hits.append({'id': t['id'], 'level': 'SL', 'pips': -float(t['sl_pips'])})
                else:
                    # TP checks
                    for i in range(1, 6):
                        tp_price = t.get(f'tp{i}_price')
                        if tp_price and not t.get(f'tp{i}_hit'):
                            tp_price = float(tp_price)
                            if (direction == 'BUY' and current_price >= tp_price) or \
                               (direction == 'SELL' and current_price <= tp_price):
                                updates[f'tp{i}_hit'] = True
                                updates['final_result'] = f'TP{i}'
                                hits.append({'id': t['id'], 'level': f'TP{i}', 'pips': float(t[f'tp{i}_pips'])})
                
                self.supabase.table('multi_target_predictions').eq('id', t['id']).update(updates)
            return hits
        except Exception as e:
            logger.error(f"Update price error: {e}")
            return hits
    
    async def get_strategy_analysis(self, symbol: str, strategy: str = None, days: int = 30) -> Dict:
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            query = self.supabase.table('multi_target_predictions').select('*').eq('symbol', symbol).gte('created_at', since)
            if strategy:
                query = query.eq('strategy', strategy)
            data = query.execute().data or []
            
            total = len(data)
            if total == 0:
                return {'symbol': symbol, 'total': 0}
            
            tp_hits = {f'TP{i}': sum(1 for d in data if d.get(f'tp{i}_hit')) for i in range(1, 6)}
            sl_hits = sum(1 for d in data if d.get('sl_hit'))
            
            return {
                'symbol': symbol, 'strategy': strategy, 'total': total,
                'tp1_rate': tp_hits['TP1'] / total, 'tp2_rate': tp_hits['TP2'] / total,
                'tp3_rate': tp_hits['TP3'] / total, 'sl_rate': sl_hits / total,
                'best_target': max(tp_hits, key=tp_hits.get)
            }
        except Exception as e:
            return {'error': str(e)}


tracker = MultiTargetTracker()
