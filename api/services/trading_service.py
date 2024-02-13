"""
Trading service for generating signals from satellite analysis
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import json
import yfinance as yf
from dataclasses import dataclass

from ..core.config import settings
from ..core.redis_client import redis_client
from ..models.trading import TradingSignal, SignalType, SignalStatus
from ..models.satellite import SatelliteAnalysis
from ..core.database import database

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    name: str
    symbols: List[str]
    confidence_threshold: float
    max_position_size: float
    stop_loss_pct: float
    target_profit_pct: float
    min_economic_activity: float
    sector: str

class TradingService:
    """
    Service for generating trading signals from satellite analysis
    
    Implements various alternative data trading strategies using satellite imagery insights
    """
    
    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.signal_generators = {
            'agricultural_alpha': self._generate_agricultural_signals,
            'construction_activity': self._generate_construction_signals,
            'energy_infrastructure': self._generate_energy_signals,
            'maritime_trade': self._generate_maritime_signals
        }
        
    def _initialize_strategies(self) -> Dict[str, StrategyConfig]:
        """Initialize trading strategies configuration"""
        return {
            'agricultural_alpha': StrategyConfig(
                name='Agricultural Alpha Strategy',
                symbols=['CORN', 'ZC=F', 'ZS=F', 'ZW=F', 'ADM', 'BG', 'CF'],  # Corn, Soy, Wheat futures + Ag companies
                confidence_threshold=0.7,
                max_position_size=0.02,  # 2% of portfolio
                stop_loss_pct=0.03,      # 3% stop loss
                target_profit_pct=0.08,  # 8% target profit
                min_economic_activity=20.0,  # Minimum vegetation index
                sector='agriculture'
            ),
            
            'construction_activity': StrategyConfig(
                name='Construction Activity Strategy', 
                symbols=['CAT', 'DE', 'VMC', 'MLM', 'CX', 'EME', 'BLDR'],  # Construction equipment and materials
                confidence_threshold=0.75,
                max_position_size=0.025, # 2.5% of portfolio
                stop_loss_pct=0.04,      # 4% stop loss
                target_profit_pct=0.12,  # 12% target profit
                min_economic_activity=15.0,  # Minimum building density
                sector='construction'
            ),
            
            'energy_infrastructure': StrategyConfig(
                name='Energy Infrastructure Strategy',
                symbols=['XOM', 'CVX', 'CL=F', 'NG=F', 'EPD', 'KMI', 'ENB'],  # Oil, gas futures + pipeline companies
                confidence_threshold=0.65,
                max_position_size=0.03,  # 3% of portfolio  
                stop_loss_pct=0.05,      # 5% stop loss
                target_profit_pct=0.15,  # 15% target profit
                min_economic_activity=10.0,  # Minimum infrastructure activity
                sector='energy'
            ),
            
            'maritime_trade': StrategyConfig(
                name='Maritime Trade Strategy',
                symbols=['FXI', 'EEMS', 'DAC', 'STNG', 'SB', 'ZIM'],  # Shipping ETFs and companies
                confidence_threshold=0.70,
                max_position_size=0.02,  # 2% of portfolio
                stop_loss_pct=0.06,      # 6% stop loss  
                target_profit_pct=0.18,  # 18% target profit
                min_economic_activity=5.0,   # Minimum water coverage
                sector='maritime'
            )
        }
    
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """
        Main method to generate trading signals from recent satellite analyses
        
        Returns:
            List of generated trading signals
        """
        try:
            logger.info("Starting trading signal generation")
            
            # Get recent satellite analyses that haven't been processed for signals
            recent_analyses = await self._get_recent_unprocessed_analyses()
            
            if not recent_analyses:
                logger.info("No new satellite analyses to process for signals")
                return []
            
            generated_signals = []
            
            for analysis in recent_analyses:
                try:
                    # Generate signals for each strategy
                    for strategy_name, generator in self.signal_generators.items():
                        signals = await generator(analysis)
                        generated_signals.extend(signals)
                        
                    # Mark analysis as processed for signal generation
                    await self._mark_analysis_processed(analysis['id'])
                    
                except Exception as e:
                    logger.error(f"Error generating signals for analysis {analysis['id']}: {e}")
                    continue
            
            logger.info(f"Generated {len(generated_signals)} trading signals")
            return generated_signals
            
        except Exception as e:
            logger.error(f"Error in generate_signals: {e}")
            return []
    
    async def _get_recent_unprocessed_analyses(self) -> List[Dict[str, Any]]:
        """Get recent satellite analyses that haven't been processed for signals"""
        query = """
        SELECT sa.id, sa.image_id, sa.building_density, sa.vegetation_index,
               sa.water_coverage, sa.construction_activity, sa.economic_activity_score,
               sa.overall_confidence, sa.created_at,
               si.bbox_north, si.bbox_south, si.bbox_east, si.bbox_west,
               si.source, si.acquisition_date
        FROM satellite_analyses sa
        JOIN satellite_images si ON sa.image_id = si.id
        WHERE sa.created_at >= NOW() - INTERVAL '24 hours'
        AND NOT EXISTS (
            SELECT 1 FROM trading_signals ts 
            WHERE ts.satellite_analysis_id = sa.id
        )
        ORDER BY sa.created_at DESC
        LIMIT 50
        """
        
        results = await database.fetch_all(query)
        return [dict(row) for row in results]
    
    async def _mark_analysis_processed(self, analysis_id: str):
        """Mark analysis as processed for signal generation"""
        # This could be a flag in the database or just tracking via existing signals
        pass
    
    async def _generate_agricultural_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate agricultural commodity signals based on vegetation analysis"""
        signals = []
        
        try:
            vegetation_index = analysis['vegetation_index']
            confidence = analysis['overall_confidence']
            economic_score = analysis['economic_activity_score']
            
            strategy = self.strategies['agricultural_alpha']
            
            # Only generate signals if vegetation index is significant
            if vegetation_index < strategy.min_economic_activity:
                return signals
            
            # Determine signal direction based on vegetation health changes
            # High vegetation = good crop yields = bearish for commodity prices
            # Low vegetation = poor crop yields = bullish for commodity prices
            
            if vegetation_index > 70:  # Very healthy vegetation
                signal_type = SignalType.SELL  # Bearish for commodity prices
                signal_strength = min(1.0, (vegetation_index - 50) / 50)
            elif vegetation_index < 30:  # Poor vegetation health
                signal_type = SignalType.BUY   # Bullish for commodity prices  
                signal_strength = min(1.0, (50 - vegetation_index) / 50)
            else:
                return signals  # Neutral vegetation, no signal
            
            confidence_score = confidence * signal_strength * 100
            
            # Only proceed if confidence is above threshold
            if confidence_score < strategy.confidence_threshold * 100:
                return signals
            
            # Generate signals for relevant symbols
            for symbol in strategy.symbols:
                try:
                    # Get current market data for price targets
                    current_price = await self._get_current_price(symbol)
                    if not current_price:
                        continue
                    
                    # Calculate position sizing
                    position_size = self._calculate_position_size(
                        confidence_score / 100, 
                        strategy.max_position_size
                    )
                    
                    # Calculate price targets
                    if signal_type == SignalType.BUY:
                        target_price = current_price * (1 + strategy.target_profit_pct)
                        stop_loss_price = current_price * (1 - strategy.stop_loss_pct)
                    else:  # SELL
                        target_price = current_price * (1 - strategy.target_profit_pct)
                        stop_loss_price = current_price * (1 + strategy.stop_loss_pct)
                    
                    signal = await self._create_signal(
                        analysis_id=analysis['id'],
                        symbol=symbol,
                        signal_type=signal_type,
                        confidence_score=confidence_score,
                        signal_strength=signal_strength,
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss_price=stop_loss_price,
                        position_size=position_size,
                        strategy=strategy,
                        economic_indicator='vegetation_index',
                        indicator_value=vegetation_index
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.error(f"Error generating agricultural signal for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in _generate_agricultural_signals: {e}")
            return []
    
    async def _generate_construction_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate construction/real estate signals based on building density"""
        signals = []
        
        try:
            building_density = analysis['building_density']
            construction_activity = analysis['construction_activity']
            confidence = analysis['overall_confidence']
            
            strategy = self.strategies['construction_activity']
            
            # Check minimum activity threshold
            if building_density < strategy.min_economic_activity:
                return signals
            
            # High construction activity = bullish for construction companies
            # Combine building density with construction activity indicator
            combined_indicator = (building_density + construction_activity * 2) / 3
            
            if combined_indicator > 25:  # High construction activity
                signal_type = SignalType.BUY
                signal_strength = min(1.0, combined_indicator / 50)
            else:
                return signals  # Low construction activity, no signal
            
            confidence_score = confidence * signal_strength * 100
            
            if confidence_score < strategy.confidence_threshold * 100:
                return signals
            
            # Generate signals for construction-related stocks
            for symbol in strategy.symbols:
                try:
                    current_price = await self._get_current_price(symbol)
                    if not current_price:
                        continue
                    
                    position_size = self._calculate_position_size(
                        confidence_score / 100,
                        strategy.max_position_size
                    )
                    
                    target_price = current_price * (1 + strategy.target_profit_pct)
                    stop_loss_price = current_price * (1 - strategy.stop_loss_pct)
                    
                    signal = await self._create_signal(
                        analysis_id=analysis['id'],
                        symbol=symbol,
                        signal_type=signal_type,
                        confidence_score=confidence_score,
                        signal_strength=signal_strength,
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss_price=stop_loss_price,
                        position_size=position_size,
                        strategy=strategy,
                        economic_indicator='building_density',
                        indicator_value=combined_indicator
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.error(f"Error generating construction signal for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in _generate_construction_signals: {e}")
            return []
    
    async def _generate_energy_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate energy sector signals based on infrastructure analysis"""
        signals = []
        
        try:
            # Energy signals could be based on infrastructure development,
            # industrial activity, or oil storage facility analysis
            building_density = analysis['building_density']
            economic_score = analysis['economic_activity_score']
            confidence = analysis['overall_confidence']
            
            strategy = self.strategies['energy_infrastructure']
            
            # Industrial/energy infrastructure indicator
            energy_indicator = min(100, building_density * 0.7 + economic_score * 0.3)
            
            if energy_indicator < strategy.min_economic_activity:
                return signals
            
            # High industrial activity = bullish for energy demand
            if energy_indicator > 30:
                signal_type = SignalType.BUY
                signal_strength = min(1.0, energy_indicator / 70)
            else:
                return signals
            
            confidence_score = confidence * signal_strength * 100
            
            if confidence_score < strategy.confidence_threshold * 100:
                return signals
            
            # Generate signals for energy stocks
            for symbol in strategy.symbols:
                try:
                    current_price = await self._get_current_price(symbol)
                    if not current_price:
                        continue
                    
                    position_size = self._calculate_position_size(
                        confidence_score / 100,
                        strategy.max_position_size
                    )
                    
                    target_price = current_price * (1 + strategy.target_profit_pct)
                    stop_loss_price = current_price * (1 - strategy.stop_loss_pct)
                    
                    signal = await self._create_signal(
                        analysis_id=analysis['id'],
                        symbol=symbol,
                        signal_type=signal_type,
                        confidence_score=confidence_score,
                        signal_strength=signal_strength,
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss_price=stop_loss_price,
                        position_size=position_size,
                        strategy=strategy,
                        economic_indicator='energy_infrastructure',
                        indicator_value=energy_indicator
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.error(f"Error generating energy signal for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in _generate_energy_signals: {e}")
            return []
    
    async def _generate_maritime_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate maritime/shipping signals based on port activity"""
        signals = []
        
        try:
            water_coverage = analysis['water_coverage']
            building_density = analysis.get('building_density', 0)  # Port infrastructure
            confidence = analysis['overall_confidence']
            
            strategy = self.strategies['maritime_trade']
            
            # Port activity indicator (water + nearby infrastructure)
            port_activity = water_coverage + (building_density * 0.3)  # Ports need both water and infrastructure
            
            if water_coverage < strategy.min_economic_activity:
                return signals
            
            # High port activity = bullish for shipping
            if port_activity > 15:
                signal_type = SignalType.BUY
                signal_strength = min(1.0, port_activity / 40)
            else:
                return signals
            
            confidence_score = confidence * signal_strength * 100
            
            if confidence_score < strategy.confidence_threshold * 100:
                return signals
            
            # Generate signals for shipping/maritime stocks
            for symbol in strategy.symbols:
                try:
                    current_price = await self._get_current_price(symbol)
                    if not current_price:
                        continue
                    
                    position_size = self._calculate_position_size(
                        confidence_score / 100,
                        strategy.max_position_size
                    )
                    
                    target_price = current_price * (1 + strategy.target_profit_pct)
                    stop_loss_price = current_price * (1 - strategy.stop_loss_pct)
                    
                    signal = await self._create_signal(
                        analysis_id=analysis['id'],
                        symbol=symbol,
                        signal_type=signal_type,
                        confidence_score=confidence_score,
                        signal_strength=signal_strength,
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss_price=stop_loss_price,
                        position_size=position_size,
                        strategy=strategy,
                        economic_indicator='port_activity',
                        indicator_value=port_activity
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.error(f"Error generating maritime signal for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in _generate_maritime_signals: {e}")
            return []
    
    def _calculate_position_size(self, confidence: float, max_size: float) -> float:
        """Calculate position size based on confidence and risk limits"""
        # Use Kelly Criterion-inspired sizing with confidence adjustment
        base_size = max_size * confidence
        return min(base_size, max_size)
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Check cache first
            cached_data = await redis_client.get_cached_market_data(symbol)
            if cached_data and 'price' in cached_data:
                return float(cached_data['price'])
            
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            
            # Cache the price
            await redis_client.cache_market_data(symbol, {'price': current_price}, ttl=300)
            
            return current_price
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def _create_signal(self, analysis_id: str, symbol: str, signal_type: SignalType,
                           confidence_score: float, signal_strength: float, current_price: float,
                           target_price: float, stop_loss_price: float, position_size: float,
                           strategy: StrategyConfig, economic_indicator: str,
                           indicator_value: float) -> Dict[str, Any]:
        """Create and save a trading signal"""
        try:
            signal_id = str(uuid.uuid4())
            
            # Calculate expiration (signals expire in 24 hours)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            query = """
            INSERT INTO trading_signals (
                id, satellite_analysis_id, symbol, signal_type, status,
                entry_price, target_price, stop_loss_price, current_price,
                confidence_score, signal_strength, recommended_position_size,
                strategy_name, strategy_version, economic_indicator,
                geographic_region, sector, generated_at, expires_at,
                model_features, created_at
            ) VALUES (
                :id, :analysis_id, :symbol, :signal_type, :status,
                :entry_price, :target_price, :stop_loss_price, :current_price,
                :confidence_score, :signal_strength, :position_size,
                :strategy_name, :strategy_version, :economic_indicator,
                :geographic_region, :sector, :generated_at, :expires_at,
                :model_features, :created_at
            )
            """
            
            model_features = {
                'economic_indicator': economic_indicator,
                'indicator_value': indicator_value,
                'strategy_params': {
                    'confidence_threshold': strategy.confidence_threshold,
                    'max_position_size': strategy.max_position_size,
                    'stop_loss_pct': strategy.stop_loss_pct,
                    'target_profit_pct': strategy.target_profit_pct
                }
            }
            
            values = {
                'id': signal_id,
                'analysis_id': analysis_id,
                'symbol': symbol,
                'signal_type': signal_type.value,
                'status': SignalStatus.ACTIVE.value,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'current_price': current_price,
                'confidence_score': confidence_score,
                'signal_strength': signal_strength,
                'position_size': position_size,
                'strategy_name': strategy.name,
                'strategy_version': '1.0.0',
                'economic_indicator': economic_indicator,
                'geographic_region': 'global',  # Could be more specific with lat/lon analysis
                'sector': strategy.sector,
                'generated_at': datetime.utcnow(),
                'expires_at': expires_at,
                'model_features': json.dumps(model_features),
                'created_at': datetime.utcnow()
            }
            
            await database.execute(query, values)
            
            # Cache the signal
            signal_data = {
                'id': signal_id,
                'symbol': symbol,
                'signal_type': signal_type.value,
                'confidence_score': confidence_score,
                'current_price': current_price,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'strategy': strategy.name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            await redis_client.cache_trading_signal(signal_id, signal_data)
            
            logger.info(f"Created trading signal: {signal_type.value} {symbol} @ {current_price} (confidence: {confidence_score:.1f}%)")
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Error creating trading signal: {e}")
            raise
    
    async def get_active_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get currently active trading signals"""
        try:
            query = """
            SELECT id, symbol, signal_type, confidence_score, signal_strength,
                   entry_price, current_price, target_price, stop_loss_price,
                   strategy_name, sector, economic_indicator, generated_at,
                   expires_at, unrealized_pnl
            FROM trading_signals
            WHERE status = 'active' AND expires_at > NOW()
            ORDER BY confidence_score DESC, generated_at DESC
            LIMIT :limit
            """
            
            results = await database.fetch_all(query, values={'limit': limit})
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get trading service status and metrics"""
        try:
            # Get signal statistics
            stats_query = """
            SELECT 
                status,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM trading_signals 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY status
            """
            
            signal_stats = await database.fetch_all(stats_query)
            status_summary = {}
            for row in signal_stats:
                status_summary[row['status']] = {
                    'count': row['count'],
                    'avg_confidence': float(row['avg_confidence'] or 0)
                }
            
            # Get strategy performance
            strategy_query = """
            SELECT 
                strategy_name,
                COUNT(*) as signals_generated,
                AVG(confidence_score) as avg_confidence,
                COUNT(CASE WHEN status = 'executed' THEN 1 END) as executed_count
            FROM trading_signals 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY strategy_name
            """
            
            strategy_stats = await database.fetch_all(strategy_query)
            strategy_summary = {}
            for row in strategy_stats:
                strategy_summary[row['strategy_name']] = {
                    'signals_generated': row['signals_generated'],
                    'avg_confidence': float(row['avg_confidence'] or 0),
                    'execution_rate': float(row['executed_count'] / max(1, row['signals_generated']))
                }
            
            return {
                'service': 'trading_engine',
                'status': 'active',
                'strategies_active': len(self.strategies),
                'signal_stats': status_summary,
                'strategy_performance': strategy_summary,
                'last_signal_generation': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trading service status: {e}")
            return {
                'service': 'trading_engine',
                'status': 'error',
                'error': str(e)
            }