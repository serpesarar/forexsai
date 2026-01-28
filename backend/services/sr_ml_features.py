"""
Support/Resistance ML Feature Engine
=====================================
5 Katmanlı S/R Feature hesaplama sistemi:
1. Mesafe (Distance)
2. Güç (Strength)
3. Confluence (Multi-Timeframe)
4. Regime Alignment
5. Cluster Density

ML modeline doğrudan feature olarak giriyor.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# =========================================================================
# GLOBAL S/R CACHE (15 dakikada bir güncellenir)
# =========================================================================
_sr_cache: Dict[str, dict] = {}
_sr_cache_lock = threading.Lock()
_SR_CACHE_TTL_SECONDS = 900  # 15 dakika


@dataclass
class SRLevel:
    """Tek bir S/R seviyesi"""
    price: float
    level_type: str  # 'support' or 'resistance'
    timeframe: str
    strength: float  # 0-100
    touch_count: int
    rejection_count: int
    volume_confirmation: float  # 0-1
    first_touch_date: datetime
    is_broken: bool = False
    # YENİ: Age ve Freshness alanları
    last_touch_bars_ago: int = 0  # Son test kaç bar önce
    age_days: int = 0  # Seviye kaç gün önce oluştu


@dataclass 
class SRFeatures:
    """ML modeline girecek S/R feature'ları"""
    sr_distance_score: float  # 0-1, yakınlık
    sr_strength_score: float  # 0-1, güç
    sr_timeframe_confluence: float  # 0-1, MTF uyumu
    sr_regime_alignment: float  # 0-1, trend uyumu
    sr_cluster_density: float  # 0-1, yoğunluk
    sr_dynamic_weight: float  # 0-1, final ağırlık
    
    # Detaylı feature'lar
    sr_nearest_resistance_distance: float  # pips
    sr_nearest_resistance_strength: float  # 0-100
    sr_nearest_support_distance: float  # pips
    sr_nearest_support_strength: float  # 0-100
    sr_touch_count_avg: float
    sr_rejection_count_total: int
    sr_volume_confirmation_avg: float
    
    # YENİ: Freshness feature'ları
    sr_freshness_score: float  # 0-1, tazelik (son test ne kadar yakın)
    sr_age_score: float  # 0-1, yaş skoru
    
    # Regime bilgisi
    sr_regime_type: str  # RANGING, TRENDING_BULL, TRENDING_BEAR
    sr_is_clustered: bool


class SRFeatureEngine:
    """
    Destek/Direnç noktalarını ML modeline hazırlayan engine.
    5 katman: Mesafe, Güç, Confluence, Regime, Cluster
    
    Cache: 15 dakikada bir güncellenir (DBSCAN maliyetli)
    """
    
    def __init__(self, symbol: str = 'XAUUSD'):
        self.symbol = symbol.upper()
        self.pip_value = 0.1 if 'XAU' in self.symbol else (1.0 if 'NDX' in self.symbol or 'NAS' in self.symbol else 0.0001)
        self._atr_cache: Dict[str, float] = {}
    
    def _get_cached_sr(self) -> Optional[dict]:
        """Cache'den S/R verilerini al (15 dk TTL)"""
        cache_key = f"sr_{self.symbol}"
        with _sr_cache_lock:
            if cache_key in _sr_cache:
                cached = _sr_cache[cache_key]
                age = (datetime.utcnow() - cached['timestamp']).total_seconds()
                if age < _SR_CACHE_TTL_SECONDS:
                    logger.debug(f"S/R cache hit for {self.symbol} (age: {age:.0f}s)")
                    return cached['data']
        return None
    
    def _set_cached_sr(self, data: dict):
        """S/R verilerini cache'e yaz"""
        cache_key = f"sr_{self.symbol}"
        with _sr_cache_lock:
            _sr_cache[cache_key] = {
                'timestamp': datetime.utcnow(),
                'data': data
            }
        logger.debug(f"S/R cache set for {self.symbol}")
    
    async def generate_sr_features(self, current_price: float) -> SRFeatures:
        """
        Şuanki fiyat için tüm S/R feature'larını üret
        """
        try:
            # 1. Tüm timeframe'lerden S/R çek
            sr_data = await self._fetch_all_timeframe_sr(current_price)
            
            if not sr_data or all(len(levels) == 0 for levels in sr_data.values()):
                return self._default_features()
            
            # 2. Mesafe feature'ları
            distance_features = self._calculate_distance_features(current_price, sr_data)
            
            # 3. Güç feature'ları
            strength_features = self._calculate_strength_features(sr_data, current_price)
            
            # 4. Multiple timeframe confluence
            confluence_feature = self._calculate_confluence(sr_data)
            
            # 5. Regime alignment
            regime_feature = await self._calculate_regime_alignment(sr_data)
            
            # 6. Cluster density
            cluster_feature = self._calculate_cluster_density(sr_data)
            
            # 7. Final dynamic weight
            final_weight = self._calculate_dynamic_weight(
                distance_features,
                strength_features,
                confluence_feature,
                regime_feature,
                cluster_feature
            )
            
            return SRFeatures(
                sr_distance_score=distance_features['normalized_distance'],
                sr_strength_score=strength_features['weighted_strength'],
                sr_timeframe_confluence=confluence_feature['confluence_score'],
                sr_regime_alignment=regime_feature['alignment_score'],
                sr_cluster_density=cluster_feature['density_score'],
                sr_dynamic_weight=final_weight,
                sr_nearest_resistance_distance=distance_features['nearest_resistance']['distance_pips'],
                sr_nearest_resistance_strength=distance_features['nearest_resistance']['strength'],
                sr_nearest_support_distance=distance_features['nearest_support']['distance_pips'],
                sr_nearest_support_strength=distance_features['nearest_support']['strength'],
                sr_touch_count_avg=strength_features['avg_touch_count'],
                sr_rejection_count_total=strength_features['total_rejection_count'],
                sr_volume_confirmation_avg=strength_features['avg_volume_confirmation'],
                sr_freshness_score=strength_features.get('avg_freshness_score', 0.5),
                sr_age_score=strength_features.get('avg_age_score', 0.5),
                sr_regime_type=regime_feature['regime_type'],
                sr_is_clustered=cluster_feature['is_dense']
            )
            
        except Exception as e:
            logger.error(f"Error generating S/R features: {e}")
            return self._default_features()
    
    def _default_features(self) -> SRFeatures:
        """Default feature'lar (veri yoksa)"""
        return SRFeatures(
            sr_distance_score=0.5,
            sr_strength_score=0.5,
            sr_timeframe_confluence=0.0,
            sr_regime_alignment=0.5,
            sr_cluster_density=0.0,
            sr_dynamic_weight=0.3,
            sr_nearest_resistance_distance=100.0,
            sr_nearest_resistance_strength=50.0,
            sr_nearest_support_distance=100.0,
            sr_nearest_support_strength=50.0,
            sr_touch_count_avg=0.0,
            sr_rejection_count_total=0,
            sr_volume_confirmation_avg=0.0,
            sr_freshness_score=0.5,
            sr_age_score=0.5,
            sr_regime_type="UNKNOWN",
            sr_is_clustered=False
        )
    
    # =========================================================================
    # S/R VERİ ÇEKME
    # =========================================================================
    async def _fetch_all_timeframe_sr(self, current_price: float) -> Dict[str, List[SRLevel]]:
        """Tüm timeframe'lerden S/R seviyelerini çek"""
        from services.mtf_analysis_service import get_mtf_analysis
        
        sr_data = {}
        timeframes = ['M15', 'M30', 'H1', 'H4', 'D1']
        
        try:
            # MTF analysis'ten pivot noktalarını al
            mtf_result = await get_mtf_analysis(self.symbol)
            
            if mtf_result.get("success") and "advanced" in mtf_result:
                adv = mtf_result["advanced"]
                pivots = adv.get("pivot_points", {})
                
                # Pivot noktalarını S/R seviyelerine çevir
                pivot = pivots.get("pivot", current_price)
                s1 = pivots.get("s1", current_price - 30 * self.pip_value)
                s2 = pivots.get("s2", current_price - 60 * self.pip_value)
                s3 = pivots.get("s3", current_price - 90 * self.pip_value)
                r1 = pivots.get("r1", current_price + 30 * self.pip_value)
                r2 = pivots.get("r2", current_price + 60 * self.pip_value)
                r3 = pivots.get("r3", current_price + 90 * self.pip_value)
                
                # Her timeframe için S/R seviyeleri oluştur
                for tf in timeframes:
                    tf_weight = {'M15': 0.3, 'M30': 0.5, 'H1': 0.7, 'H4': 0.85, 'D1': 1.0}.get(tf, 0.5)
                    
                    levels = []
                    
                    # Supports
                    for i, (price, name) in enumerate([(s1, 'S1'), (s2, 'S2'), (s3, 'S3')]):
                        strength = (100 - i * 15) * tf_weight
                        levels.append(SRLevel(
                            price=price,
                            level_type='support',
                            timeframe=tf,
                            strength=strength,
                            touch_count=3 - i,
                            rejection_count=2 - i,
                            volume_confirmation=0.7 - i * 0.1,
                            first_touch_date=datetime.utcnow() - timedelta(days=7 * (i + 1)),
                            is_broken=current_price < price
                        ))
                    
                    # Resistances
                    for i, (price, name) in enumerate([(r1, 'R1'), (r2, 'R2'), (r3, 'R3')]):
                        strength = (100 - i * 15) * tf_weight
                        levels.append(SRLevel(
                            price=price,
                            level_type='resistance',
                            timeframe=tf,
                            strength=strength,
                            touch_count=3 - i,
                            rejection_count=2 - i,
                            volume_confirmation=0.7 - i * 0.1,
                            first_touch_date=datetime.utcnow() - timedelta(days=7 * (i + 1)),
                            is_broken=current_price > price
                        ))
                    
                    # Pivot noktası (hem destek hem direnç)
                    levels.append(SRLevel(
                        price=pivot,
                        level_type='support' if current_price > pivot else 'resistance',
                        timeframe=tf,
                        strength=85 * tf_weight,
                        touch_count=5,
                        rejection_count=3,
                        volume_confirmation=0.8,
                        first_touch_date=datetime.utcnow() - timedelta(days=1),
                        is_broken=False
                    ))
                    
                    sr_data[tf] = levels
                    
        except Exception as e:
            logger.warning(f"Failed to fetch S/R data: {e}")
            # Fallback: basit S/R seviyeleri oluştur
            for tf in timeframes:
                sr_data[tf] = self._generate_fallback_levels(current_price, tf)
        
        return sr_data
    
    def _generate_fallback_levels(self, price: float, timeframe: str) -> List[SRLevel]:
        """Fallback S/R seviyeleri"""
        tf_weight = {'M15': 0.3, 'M30': 0.5, 'H1': 0.7, 'H4': 0.85, 'D1': 1.0}.get(timeframe, 0.5)
        atr_estimate = price * 0.005  # ~0.5% ATR tahmini
        
        levels = []
        for i in range(1, 4):
            # Supports
            levels.append(SRLevel(
                price=price - i * atr_estimate,
                level_type='support',
                timeframe=timeframe,
                strength=(80 - i * 10) * tf_weight,
                touch_count=max(1, 3 - i),
                rejection_count=max(0, 2 - i),
                volume_confirmation=0.5,
                first_touch_date=datetime.utcnow() - timedelta(days=i * 3),
                is_broken=False
            ))
            # Resistances
            levels.append(SRLevel(
                price=price + i * atr_estimate,
                level_type='resistance',
                timeframe=timeframe,
                strength=(80 - i * 10) * tf_weight,
                touch_count=max(1, 3 - i),
                rejection_count=max(0, 2 - i),
                volume_confirmation=0.5,
                first_touch_date=datetime.utcnow() - timedelta(days=i * 3),
                is_broken=False
            ))
        return levels
    
    # =========================================================================
    # KATMAN 1: MESAFE HESAPLAMA
    # =========================================================================
    def _calculate_distance_features(self, price: float, sr_data: Dict[str, List[SRLevel]]) -> dict:
        """Fiyatın her S/R'ye olan mesafesini hesapla"""
        
        all_distances = []
        resistances = []
        supports = []
        
        for timeframe, levels in sr_data.items():
            atr = self._get_atr_estimate(timeframe)
            
            for level in levels:
                distance_pips = abs(price - level.price) / self.pip_value
                normalized = max(0, min(1, 1 - (distance_pips / (atr * 1.5))))
                
                entry = {
                    'timeframe': timeframe,
                    'price': level.price,
                    'type': level.level_type,
                    'distance_pips': distance_pips,
                    'normalized_distance': normalized,
                    'strength': level.strength,
                    'is_broken': level.is_broken
                }
                
                all_distances.append(entry)
                if level.level_type == 'resistance':
                    resistances.append(entry)
                else:
                    supports.append(entry)
        
        # En yakın destek/direnç
        nearest_resistance = min(resistances, key=lambda x: x['distance_pips']) if resistances else {
            'distance_pips': 100, 'strength': 50, 'normalized_distance': 0.5
        }
        nearest_support = min(supports, key=lambda x: x['distance_pips']) if supports else {
            'distance_pips': 100, 'strength': 50, 'normalized_distance': 0.5
        }
        
        # Toplam mesafe skoru
        if all_distances:
            total_distance_score = sum(d['normalized_distance'] for d in all_distances) / len(all_distances)
        else:
            total_distance_score = 0.5
        
        return {
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'normalized_distance': total_distance_score,
            'all_distances': all_distances
        }
    
    def _get_atr_estimate(self, timeframe: str) -> float:
        """Timeframe için ATR tahmini (pips)"""
        base_atr = {
            'M15': 15,
            'M30': 25,
            'H1': 40,
            'H4': 80,
            'D1': 150
        }
        return base_atr.get(timeframe, 50)
    
    # =========================================================================
    # KATMAN 2: GÜÇ HESAPLAMA
    # =========================================================================
    def _calculate_strength_features(self, sr_data: Dict[str, List[SRLevel]], current_price: float) -> dict:
        """Her S/R noktasının gücünü hesapla"""
        
        all_strengths = []
        total_touch = 0
        total_rejection = 0
        total_volume_conf = 0
        count = 0
        
        for timeframe, levels in sr_data.items():
            tf_weight = {'M15': 0.3, 'M30': 0.5, 'H1': 0.7, 'H4': 0.85, 'D1': 1.0}.get(timeframe, 0.5)
            
            for level in levels:
                # Güç bileşenleri
                touch_score = min(level.touch_count / 5, 1.0)
                volume_score = level.volume_confirmation
                rejection_score = min(level.rejection_count / 3, 1.0)
                
                # YENİ: Freshness skoru (son test ne kadar yakın)
                # 10 bar önce = %100, 20 bar = %50, 40+ bar = %25
                bars_ago = max(1, level.last_touch_bars_ago)
                freshness_score = min(10 / bars_ago, 1.0)
                
                # YENİ: Age skoru (yaş - daha eski = daha güçlü, ama çok eski = zayıf)
                # 7-30 gün = optimal, <7 gün = çok yeni, >60 gün = eski
                age_days = level.age_days if level.age_days > 0 else (datetime.utcnow() - level.first_touch_date).days
                if age_days < 7:
                    age_score = age_days / 7 * 0.7  # Çok yeni, güç %70'e kadar
                elif age_days <= 30:
                    age_score = 1.0  # Optimal yaş = %100
                elif age_days <= 60:
                    age_score = 1.0 - (age_days - 30) / 60  # Yavaş düşüş
                else:
                    age_score = 0.5  # 60+ gün = %50 güç
                
                # Toplam strength (freshness eklendi)
                total_strength = (
                    touch_score * 0.20 +
                    volume_score * 0.20 +
                    rejection_score * 0.20 +
                    freshness_score * 0.15 +  # YENİ
                    age_score * 0.15 +
                    tf_weight * 0.10
                )
                
                # Mesafe ağırlığı
                distance = abs(current_price - level.price) / self.pip_value
                distance_weight = 1 / (1 + distance / 50)
                
                all_strengths.append({
                    'level': level.price,
                    'strength': total_strength,
                    'distance_weight': distance_weight,
                    'weighted_strength': total_strength * distance_weight,
                    'freshness_score': freshness_score,
                    'age_score': age_score
                })
                
                total_touch += level.touch_count
                total_rejection += level.rejection_count
                total_volume_conf += level.volume_confirmation
                count += 1
        
        # Ağırlıklı strength
        if all_strengths:
            weighted_strength = sum(s['weighted_strength'] for s in all_strengths) / len(all_strengths)
            avg_freshness = sum(s['freshness_score'] for s in all_strengths) / len(all_strengths)
            avg_age_score = sum(s['age_score'] for s in all_strengths) / len(all_strengths)
        else:
            weighted_strength = 0.5
            avg_freshness = 0.5
            avg_age_score = 0.5
        
        return {
            'weighted_strength': weighted_strength,
            'avg_touch_count': total_touch / max(count, 1),
            'total_rejection_count': total_rejection,
            'avg_volume_confirmation': total_volume_conf / max(count, 1),
            'avg_freshness_score': avg_freshness,
            'avg_age_score': avg_age_score,
            'all_strengths': all_strengths
        }
    
    # =========================================================================
    # KATMAN 3: CONFLUENCE (MTF UYUMU)
    # =========================================================================
    def _calculate_confluence(self, sr_data: Dict[str, List[SRLevel]]) -> dict:
        """Aynı seviyede farklı timeframe'lerden S/R var mı?"""
        
        all_prices = []
        for timeframe, levels in sr_data.items():
            for level in levels:
                all_prices.append({
                    'price': level.price,
                    'timeframe': timeframe,
                    'strength': level.strength
                })
        
        if len(all_prices) < 2:
            return {'confluence_score': 0.0, 'cluster_count': 0}
        
        # Basit clustering (±10 pips tolerance)
        tolerance = 10 * self.pip_value
        clusters = []
        used = set()
        
        for i, p1 in enumerate(all_prices):
            if i in used:
                continue
            cluster = [p1]
            used.add(i)
            
            for j, p2 in enumerate(all_prices):
                if j in used:
                    continue
                if abs(p1['price'] - p2['price']) <= tolerance:
                    cluster.append(p2)
                    used.add(j)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        # Confluence skoru
        confluence_score = 0
        for cluster in clusters:
            tf_count = len(set(p['timeframe'] for p in cluster))
            confluence_score += (tf_count ** 2) * 0.1
        
        confluence_score = min(confluence_score / 2.0, 1.0)
        
        return {
            'confluence_score': confluence_score,
            'cluster_count': len(clusters)
        }
    
    # =========================================================================
    # KATMAN 4: REGIME UYUMU
    # =========================================================================
    async def _calculate_regime_alignment(self, sr_data: Dict[str, List[SRLevel]]) -> dict:
        """S/R seviyeleri mevcut regime ile uyumlu mu?"""
        
        try:
            from services.mtf_analysis_service import get_mtf_analysis
            mtf = await get_mtf_analysis(self.symbol)
            
            if mtf.get("success") and "advanced" in mtf:
                regime_info = mtf["advanced"].get("market_regime", {})
                regime_type = regime_info.get("regime", "UNKNOWN")
            else:
                regime_type = "UNKNOWN"
        except:
            regime_type = "UNKNOWN"
        
        # Regime'e göre S/R önemini ayarla
        if regime_type == "RANGING":
            alignment_score = 1.0  # Range'de S/R çok önemli
        elif regime_type == "TRENDING_UP" or regime_type == "TRENDING":
            # Bullish'de destekler daha önemli
            support_count = sum(1 for tf in sr_data.values() for l in tf if l.level_type == 'support')
            resistance_count = sum(1 for tf in sr_data.values() for l in tf if l.level_type == 'resistance')
            alignment_score = 0.7 if support_count >= resistance_count else 0.5
        elif regime_type == "TRENDING_DOWN":
            # Bearish'de dirençler daha önemli
            support_count = sum(1 for tf in sr_data.values() for l in tf if l.level_type == 'support')
            resistance_count = sum(1 for tf in sr_data.values() for l in tf if l.level_type == 'resistance')
            alignment_score = 0.7 if resistance_count >= support_count else 0.5
        else:
            alignment_score = 0.5
        
        return {
            'alignment_score': alignment_score,
            'regime_type': regime_type
        }
    
    # =========================================================================
    # KATMAN 5: CLUSTER DENSITY
    # =========================================================================
    def _calculate_cluster_density(self, sr_data: Dict[str, List[SRLevel]]) -> dict:
        """S/R seviyeleri ne kadar yoğun?"""
        
        all_prices = []
        for levels in sr_data.values():
            for level in levels:
                all_prices.append(level.price)
        
        if len(all_prices) < 2:
            return {'density_score': 0.0, 'is_dense': False}
        
        price_range = max(all_prices) - min(all_prices)
        
        # Clustering
        tolerance = 10 * self.pip_value
        cluster_count = 1
        sorted_prices = sorted(all_prices)
        
        for i in range(1, len(sorted_prices)):
            if sorted_prices[i] - sorted_prices[i-1] > tolerance:
                cluster_count += 1
        
        # Density = cluster sayısı / fiyat aralığı
        if price_range > 0:
            density = cluster_count / (price_range / (50 * self.pip_value))
        else:
            density = 0
        
        if density > 1.5:
            density_score = 1.0
        elif density > 1.0:
            density_score = 0.7
        elif density > 0.5:
            density_score = 0.4
        else:
            density_score = 0.2
        
        return {
            'density_score': density_score,
            'cluster_count': cluster_count,
            'is_dense': density > 0.7
        }
    
    # =========================================================================
    # FINAL: DYNAMIC WEIGHT
    # =========================================================================
    def _calculate_dynamic_weight(
        self,
        distance: dict,
        strength: dict,
        confluence: dict,
        regime: dict,
        cluster: dict
    ) -> float:
        """Tüm S/R feature'larını birleştir"""
        
        weights = {
            'distance': 0.30,
            'strength': 0.25,
            'confluence': 0.20,
            'regime': 0.15,
            'cluster': 0.10
        }
        
        distance_score = distance['normalized_distance']
        strength_score = strength['weighted_strength']
        confluence_score = confluence['confluence_score']
        regime_score = regime['alignment_score']
        cluster_score = cluster['density_score']
        
        final_weight = (
            distance_score * weights['distance'] +
            strength_score * weights['strength'] +
            confluence_score * weights['confluence'] +
            regime_score * weights['regime'] +
            cluster_score * weights['cluster']
        )
        
        # Ayarlamalar
        if distance_score < 0.3 and strength_score > 0.8:
            final_weight *= 0.5  # Uzak ama güçlü
        
        if distance_score > 0.8 and strength_score < 0.5:
            final_weight *= 1.3  # Yakın ama zayıf
        
        return max(0, min(1, final_weight))


# =========================================================================
# ML MODEL ENTEGRASYONU İÇİN YARDIMCI FONKSİYONLAR
# =========================================================================

async def get_sr_features_for_ml(symbol: str, current_price: float) -> dict:
    """ML modeli için S/R feature'larını dict olarak döndür"""
    engine = SRFeatureEngine(symbol)
    features = await engine.generate_sr_features(current_price)
    
    return {
        'sr_distance_score': features.sr_distance_score,
        'sr_strength_score': features.sr_strength_score,
        'sr_timeframe_confluence': features.sr_timeframe_confluence,
        'sr_regime_alignment': features.sr_regime_alignment,
        'sr_cluster_density': features.sr_cluster_density,
        'sr_dynamic_weight': features.sr_dynamic_weight,
        'sr_nearest_resistance_distance': features.sr_nearest_resistance_distance,
        'sr_nearest_resistance_strength': features.sr_nearest_resistance_strength,
        'sr_nearest_support_distance': features.sr_nearest_support_distance,
        'sr_nearest_support_strength': features.sr_nearest_support_strength,
        'sr_touch_count_avg': features.sr_touch_count_avg,
        'sr_rejection_count_total': features.sr_rejection_count_total,
        'sr_is_clustered': features.sr_is_clustered,
        'sr_regime_type': features.sr_regime_type
    }


def post_process_with_sr(prediction: dict, sr_features: dict) -> dict:
    """Model tahminini S/R verileriyle son kez ayarla"""
    
    confidence = prediction.get('confidence', 50)
    direction = prediction.get('direction', 'HOLD')
    
    warnings = prediction.get('warnings', [])
    adjustments = []
    
    # BUY + Güçlü direnç yakın
    if (direction == 'BUY' and 
        sr_features.get('sr_nearest_resistance_distance', 100) < 15 and
        sr_features.get('sr_nearest_resistance_strength', 0) > 70):
        
        adjustments.append({
            'type': 'resistance_block',
            'original_confidence': confidence,
            'new_confidence': confidence * 0.5,
            'reason': f"Güçlü direnç {sr_features['sr_nearest_resistance_distance']:.0f} pip içinde"
        })
        confidence *= 0.5
        warnings.append(f"🚫 R1 çok yakın ({sr_features['sr_nearest_resistance_distance']:.0f} pips) - BUY riskli")
    
    # SELL + Güçlü destek yakın
    if (direction == 'SELL' and 
        sr_features.get('sr_nearest_support_distance', 100) < 15 and
        sr_features.get('sr_nearest_support_strength', 0) > 70):
        
        adjustments.append({
            'type': 'support_block',
            'original_confidence': confidence,
            'new_confidence': confidence * 0.5,
            'reason': f"Güçlü destek {sr_features['sr_nearest_support_distance']:.0f} pip içinde"
        })
        confidence *= 0.5
        warnings.append(f"🚫 S1 çok yakın ({sr_features['sr_nearest_support_distance']:.0f} pips) - SELL riskli")
    
    # Yüksek confluence + regime uyumu = boost
    if (sr_features.get('sr_timeframe_confluence', 0) > 0.7 and
        sr_features.get('sr_regime_alignment', 0) > 0.7):
        
        adjustments.append({
            'type': 'confluence_boost',
            'original_confidence': confidence,
            'new_confidence': min(95, confidence * 1.15),
            'reason': 'Yüksek MTF confluence + regime uyumu'
        })
        confidence = min(95, confidence * 1.15)
        warnings.append("✅ Güçlü S/R confluence tespit")
    
    # S/R kırılması (breakout)
    if sr_features.get('sr_is_clustered', False):
        warnings.append("📊 S/R cluster bölgesi - volatilite bekleniyor")
    
    return {
        **prediction,
        'confidence': round(confidence, 1),
        'warnings': warnings,
        'sr_adjustments': adjustments,
        'sr_weight': sr_features.get('sr_dynamic_weight', 0.5)
    }
