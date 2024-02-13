"""
Market data service for real-time and historical data
"""

import asyncio
import logging
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.config import settings
from ..core.redis_client import redis_client
from ..models.market_data import MarketData, PriceHistory
from ..core.database import database

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching and managing market data"""
    
    def __init__(self):
        self.tracked_symbols = [
            # Agricultural
            'CORN', 'ZC=F', 'ZS=F', 'ZW=F', 'ADM', 'BG', 'CF',
            # Construction 
            'CAT', 'DE', 'VMC', 'MLM', 'CX', 'EME', 'BLDR',
            # Energy
            'XOM', 'CVX', 'CL=F', 'NG=F', 'EPD', 'KMI', 'ENB',
            # Maritime
            'FXI', 'EEMS', 'DAC', 'STNG', 'SB', 'ZIM',
            # Benchmarks
            'SPY', 'QQQ', 'IWM', 'VTI'
        ]
        
    async def update_real_time_data(self):
        """Update real-time market data for tracked symbols"""
        try:
            logger.info(f"Updating real-time data for {len(self.tracked_symbols)} symbols")
            
            for symbol in self.tracked_symbols:
                try:
                    data = await self._fetch_current_data(symbol)
                    if data:
                        await self._store_market_data(symbol, data)
                        await redis_client.cache_market_data(symbol, data, ttl=300)
                        
                except Exception as e:
                    logger.error(f"Error updating data for {symbol}: {e}")
                    continue
                    
            logger.info("Real-time data update completed")
            
        except Exception as e:
            logger.error(f"Error in update_real_time_data: {e}")
    
    async def _fetch_current_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current market data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get recent data
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
                
            # Get the latest data point
            latest = hist.iloc[-1]
            
            # Get basic info
            info = ticker.info
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow(),
                'open_price': float(hist.iloc[0]['Open']),
                'high_price': float(hist['High'].max()),
                'low_price': float(hist['Low'].min()),
                'close_price': float(latest['Close']),
                'volume': float(latest['Volume']),
                'price': float(latest['Close']),  # For caching
                'exchange': info.get('exchange', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield')
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def _store_market_data(self, symbol: str, data: Dict[str, Any]):
        """Store market data in database"""
        try:
            query = """
            INSERT INTO market_data (
                symbol, timestamp, open_price, high_price, low_price,
                close_price, volume, exchange, data_source, created_at
            ) VALUES (
                :symbol, :timestamp, :open_price, :high_price, :low_price,
                :close_price, :volume, :exchange, :data_source, :created_at
            )
            """
            
            values = {
                'symbol': symbol,
                'timestamp': data['timestamp'],
                'open_price': data['open_price'],
                'high_price': data['high_price'],
                'low_price': data['low_price'],
                'close_price': data['close_price'],
                'volume': data['volume'],
                'exchange': data.get('exchange', 'Unknown'),
                'data_source': 'yfinance',
                'created_at': datetime.utcnow()
            }
            
            await database.execute(query, values)
            
        except Exception as e:
            logger.error(f"Error storing market data for {symbol}: {e}")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Check cache first
            cached_data = await redis_client.get_cached_market_data(symbol)
            if cached_data and 'price' in cached_data:
                return float(cached_data['price'])
            
            # Fetch from source
            data = await self._fetch_current_data(symbol)
            if data:
                return data['price']
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical price data"""
        try:
            query = """
            SELECT symbol, timestamp, open_price, high_price, low_price,
                   close_price, volume
            FROM market_data
            WHERE symbol = :symbol 
            AND timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
            """ % days
            
            results = await database.fetch_all(query, values={'symbol': symbol})
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get market data service status"""
        try:
            # Get data freshness statistics
            freshness_query = """
            SELECT 
                COUNT(DISTINCT symbol) as symbols_tracked,
                MAX(created_at) as last_update,
                COUNT(*) as total_records_today
            FROM market_data
            WHERE DATE(created_at) = CURRENT_DATE
            """
            
            stats = await database.fetch_one(freshness_query)
            
            return {
                'service': 'market_data',
                'status': 'active',
                'symbols_tracked': stats['symbols_tracked'] or 0,
                'last_update': stats['last_update'].isoformat() if stats['last_update'] else None,
                'records_today': stats['total_records_today'] or 0,
                'configured_symbols': len(self.tracked_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error getting market data service status: {e}")
            return {
                'service': 'market_data',
                'status': 'error',
                'error': str(e)
            }