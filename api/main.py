"""
Pulse Trading Platform - Main API Application

Satellite-powered alternative data trading platform providing:
- Satellite imagery analysis for economic insights
- Real-time trading signals based on geospatial data
- Risk management and portfolio optimization
- Alternative data integration for alpha generation

Author: Ayomide Caleb Adekoya
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import Dict, List, Optional
import time

from .routers import satellite, trading, market_data, signals, portfolio
from .core.config import settings
from .core.database import database, init_db
from .core.redis_client import redis_client
from .services.satellite_service import SatelliteAnalysisService
from .services.trading_service import TradingService
from .services.market_data_service import MarketDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Pulse Trading Platform")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize Redis
    await redis_client.ping()
    logger.info("✅ Redis connected")
    
    # Initialize services
    app.state.satellite_service = SatelliteAnalysisService()
    app.state.trading_service = TradingService()
    app.state.market_data_service = MarketDataService()
    
    logger.info("✅ Services initialized")
    
    # Start background tasks
    asyncio.create_task(start_background_tasks())
    logger.info("✅ Background tasks started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Pulse Trading Platform")
    await database.disconnect()
    await redis_client.close()
    logger.info("✅ Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Pulse - Satellite Trading Platform",
    description="""
    ## 🛰️ Satellite-Powered Alternative Data Trading Platform
    
    Pulse leverages cutting-edge satellite imagery analysis and machine learning to generate 
    high-alpha trading signals from geospatial economic indicators.
    
    ### Key Features:
    - **🌍 Satellite Analysis**: Real-time semantic segmentation of satellite imagery
    - **📊 Trading Signals**: ML-powered signals from economic activity detection
    - **⚡ Real-time Data**: Live market data integration with alternative data
    - **🛡️ Risk Management**: Sophisticated portfolio risk controls
    - **📈 Performance Analytics**: Comprehensive trading performance metrics
    
    ### Use Cases:
    - **Agricultural Alpha**: Crop yield prediction for commodity trading
    - **Construction Activity**: Economic growth signals from building detection
    - **Energy Infrastructure**: Oil storage and pipeline monitoring
    - **Maritime Trade**: Port activity for shipping and logistics insights
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(satellite.router, prefix="/api/v1/satellite", tags=["Satellite Analysis"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading Engine"])
app.include_router(market_data.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["Trading Signals"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio Management"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with platform overview"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pulse - Satellite Trading Platform</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .header { margin-bottom: 40px; }
            .logo { font-size: 3em; font-weight: bold; margin-bottom: 10px; }
            .tagline { font-size: 1.2em; opacity: 0.9; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }
            .feature { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px); }
            .feature-icon { font-size: 2em; margin-bottom: 10px; }
            .cta { margin-top: 40px; }
            .btn { background: #00d4aa; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; text-decoration: none; display: inline-block; margin: 10px; transition: all 0.3s; }
            .btn:hover { background: #00c19a; transform: translateY(-2px); }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 40px 0; }
            .stat { text-align: center; }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #00d4aa; }
            .stat-label { font-size: 0.9em; opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🛰️ Pulse</div>
                <div class="tagline">Satellite-Powered Alternative Data Trading Platform</div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🌍</div>
                    <h3>Satellite Analysis</h3>
                    <p>Real-time semantic segmentation of satellite imagery for economic insights</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📊</div>
                    <h3>Trading Signals</h3>
                    <p>ML-powered trading signals from geospatial economic activity detection</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <h3>Real-time Data</h3>
                    <p>Live market data integration with alternative satellite data sources</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🛡️</div>
                    <h3>Risk Management</h3>
                    <p>Sophisticated portfolio risk controls and position sizing algorithms</p>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">85%</div>
                    <div class="stat-label">Satellite Segmentation Accuracy</div>
                </div>
                <div class="stat">
                    <div class="stat-number">2.3</div>
                    <div class="stat-label">Target Sharpe Ratio</div>
                </div>
                <div class="stat">
                    <div class="stat-number">24/7</div>
                    <div class="stat-label">Global Monitoring</div>
                </div>
            </div>
            
            <div class="cta">
                <a href="/docs" class="btn">🚀 API Documentation</a>
                <a href="/redoc" class="btn">📚 API Reference</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await database.execute("SELECT 1")
        
        # Check Redis connection  
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "database": "connected",
                "redis": "connected",
                "satellite_analysis": "active",
                "trading_engine": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/v1/status")
async def get_system_status():
    """Get comprehensive system status and metrics"""
    try:
        satellite_service = app.state.satellite_service
        trading_service = app.state.trading_service
        market_data_service = app.state.market_data_service
        
        return {
            "system": {
                "uptime": time.time() - app.extra.get("start_time", time.time()),
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT
            },
            "services": {
                "satellite_analysis": await satellite_service.get_status(),
                "trading_engine": await trading_service.get_status(), 
                "market_data": await market_data_service.get_status()
            },
            "performance": {
                "active_signals": await get_active_signals_count(),
                "processed_images_today": await get_processed_images_count(),
                "portfolio_value": await get_total_portfolio_value()
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

async def start_background_tasks():
    """Start background processing tasks"""
    logger.info("Starting background tasks...")
    
    # Start satellite data processing
    asyncio.create_task(satellite_background_processor())
    
    # Start market data streaming
    asyncio.create_task(market_data_background_processor())
    
    # Start signal generation
    asyncio.create_task(signal_generation_background_processor())

async def satellite_background_processor():
    """Background task for processing satellite imagery"""
    while True:
        try:
            # Process pending satellite imagery
            await app.state.satellite_service.process_pending_images()
            await asyncio.sleep(300)  # Process every 5 minutes
        except Exception as e:
            logger.error(f"Satellite background processor error: {e}")
            await asyncio.sleep(60)

async def market_data_background_processor():
    """Background task for market data streaming"""
    while True:
        try:
            # Update market data
            await app.state.market_data_service.update_real_time_data()
            await asyncio.sleep(60)  # Update every minute
        except Exception as e:
            logger.error(f"Market data background processor error: {e}")
            await asyncio.sleep(30)

async def signal_generation_background_processor():
    """Background task for generating trading signals"""
    while True:
        try:
            # Generate new trading signals
            await app.state.trading_service.generate_signals()
            await asyncio.sleep(900)  # Generate every 15 minutes
        except Exception as e:
            logger.error(f"Signal generation background processor error: {e}")
            await asyncio.sleep(300)

# Utility functions for status endpoint
async def get_active_signals_count() -> int:
    """Get count of active trading signals"""
    try:
        result = await database.fetch_val(
            "SELECT COUNT(*) FROM trading_signals WHERE status = 'active' AND expires_at > NOW()"
        )
        return result or 0
    except:
        return 0

async def get_processed_images_count() -> int:
    """Get count of images processed today"""
    try:
        result = await database.fetch_val(
            "SELECT COUNT(*) FROM satellite_analysis WHERE DATE(created_at) = CURRENT_DATE"
        )
        return result or 0
    except:
        return 0

async def get_total_portfolio_value() -> float:
    """Get total portfolio value across all accounts"""
    try:
        result = await database.fetch_val(
            "SELECT SUM(total_value) FROM portfolio_accounts WHERE active = true"
        )
        return float(result) if result else 0.0
    except:
        return 0.0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )