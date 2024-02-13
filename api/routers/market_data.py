"""
Market data API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any

from ..services.market_data_service import MarketDataService

router = APIRouter()

@router.get("/current/{symbol}")
async def get_current_price(symbol: str):
    """Get current price for a symbol"""
    try:
        service = MarketDataService()
        price = await service.get_current_price(symbol)
        
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}")
        
        return {
            'symbol': symbol,
            'price': price,
            'timestamp': None  # Add current timestamp in production
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting price: {str(e)}")

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, days: int = 30):
    """Get historical price data"""
    try:
        service = MarketDataService()
        data = await service.get_historical_data(symbol, days)
        
        return {
            'symbol': symbol,
            'period_days': days,
            'data_points': len(data),
            'data': data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting historical data: {str(e)}")

@router.get("/status")
async def get_market_data_status():
    """Get market data service status"""
    try:
        service = MarketDataService()
        return await service.get_status()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

@router.post("/update")
async def trigger_data_update():
    """Manually trigger market data update"""
    try:
        service = MarketDataService()
        await service.update_real_time_data()
        return {"message": "Market data update completed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating data: {str(e)}")