"""
Trading signals API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any

from ..core.database import database
from ..services.trading_service import TradingService

router = APIRouter()

@router.get("/active")
async def get_active_signals(limit: int = 50):
    """Get currently active trading signals"""
    try:
        service = TradingService()
        signals = await service.get_active_signals(limit)
        return {
            'total': len(signals),
            'signals': signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving signals: {str(e)}")

@router.get("/performance")
async def get_signals_performance(days: int = 30):
    """Get trading signals performance metrics"""
    try:
        query = """
        SELECT 
            strategy_name,
            signal_type,
            COUNT(*) as total_signals,
            AVG(confidence_score) as avg_confidence,
            COUNT(CASE WHEN status = 'executed' THEN 1 END) as executed_count,
            AVG(realized_pnl) as avg_realized_pnl
        FROM trading_signals 
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY strategy_name, signal_type
        ORDER BY strategy_name, signal_type
        """ % days
        
        results = await database.fetch_all(query)
        
        performance = []
        for row in results:
            performance.append({
                'strategy': row['strategy_name'],
                'signal_type': row['signal_type'],
                'total_signals': row['total_signals'],
                'avg_confidence': float(row['avg_confidence'] or 0),
                'execution_rate': float(row['executed_count'] / max(1, row['total_signals'])),
                'avg_realized_pnl': float(row['avg_realized_pnl'] or 0)
            })
        
        return {
            'period_days': days,
            'strategy_performance': performance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance: {str(e)}")

@router.post("/generate")
async def generate_new_signals():
    """Manually trigger signal generation"""
    try:
        service = TradingService()
        signals = await service.generate_signals()
        return {
            'message': 'Signal generation completed',
            'signals_generated': len(signals),
            'signals': signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signals: {str(e)}")