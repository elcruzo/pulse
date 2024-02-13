"""
Trading engine API endpoints
"""

from fastapi import APIRouter, HTTPException

from ..services.trading_service import TradingService

router = APIRouter()

@router.get("/status")
async def get_trading_service_status():
    """Get trading service status and metrics"""
    try:
        service = TradingService()
        return await service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trading status: {str(e)}")

@router.get("/strategies")
async def get_available_strategies():
    """Get available trading strategies"""
    service = TradingService()
    strategies = {}
    
    for name, config in service.strategies.items():
        strategies[name] = {
            'name': config.name,
            'symbols': config.symbols,
            'sector': config.sector,
            'confidence_threshold': config.confidence_threshold,
            'max_position_size': config.max_position_size,
            'stop_loss_pct': config.stop_loss_pct,
            'target_profit_pct': config.target_profit_pct
        }
    
    return {
        'total_strategies': len(strategies),
        'strategies': strategies
    }