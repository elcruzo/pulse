"""
Redis client configuration and utilities
"""

import redis.asyncio as redis
from .config import settings
import json
import pickle
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper with convenience methods"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.default_ttl = settings.REDIS_CACHE_TTL
        self.client = redis.from_url(self.redis_url, decode_responses=False)
    
    async def ping(self):
        """Test Redis connection"""
        return await self.client.ping()
    
    async def close(self):
        """Close Redis connection"""
        await self.client.close()
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store JSON serializable data"""
        try:
            json_data = json.dumps(value)
            return await self.client.set(
                key, 
                json_data, 
                ex=ttl or self.default_ttl
            )
        except Exception as e:
            logger.error(f"Error setting JSON data for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve JSON data"""
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Error getting JSON data for key {key}: {e}")
            return None
    
    async def set_pickle(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store Python objects using pickle"""
        try:
            pickled_data = pickle.dumps(value)
            return await self.client.set(
                key,
                pickled_data,
                ex=ttl or self.default_ttl
            )
        except Exception as e:
            logger.error(f"Error setting pickled data for key {key}: {e}")
            return False
    
    async def get_pickle(self, key: str) -> Optional[Any]:
        """Retrieve pickled Python objects"""
        try:
            data = await self.client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting pickled data for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a key"""
        try:
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        try:
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    async def flushdb(self):
        """Clear all keys in current database"""
        try:
            return await self.client.flushdb()
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            return False
    
    # Trading-specific cache methods
    async def cache_market_data(self, symbol: str, data: dict, ttl: int = 300):
        """Cache market data for a symbol (5 min default TTL)"""
        key = f"market_data:{symbol}"
        return await self.set_json(key, data, ttl)
    
    async def get_cached_market_data(self, symbol: str) -> Optional[dict]:
        """Get cached market data for a symbol"""
        key = f"market_data:{symbol}"
        return await self.get_json(key)
    
    async def cache_satellite_analysis(self, image_id: str, analysis: dict, ttl: int = 86400):
        """Cache satellite analysis results (24 hour default TTL)"""
        key = f"satellite_analysis:{image_id}"
        return await self.set_json(key, analysis, ttl)
    
    async def get_cached_satellite_analysis(self, image_id: str) -> Optional[dict]:
        """Get cached satellite analysis"""
        key = f"satellite_analysis:{image_id}"
        return await self.get_json(key)
    
    async def cache_trading_signal(self, signal_id: str, signal: dict, ttl: int = 3600):
        """Cache trading signal (1 hour default TTL)"""
        key = f"trading_signal:{signal_id}"
        return await self.set_json(key, signal, ttl)
    
    async def get_cached_trading_signal(self, signal_id: str) -> Optional[dict]:
        """Get cached trading signal"""
        key = f"trading_signal:{signal_id}"
        return await self.get_json(key)

# Create global Redis client instance
redis_client = RedisClient()