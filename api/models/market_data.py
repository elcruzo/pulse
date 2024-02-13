"""
Market data models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..core.database import Base

class MarketData(Base):
    """Real-time and historical market data"""
    
    __tablename__ = "market_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Symbol information
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=True)
    asset_type = Column(String(20), default="equity")  # equity, commodity, forex, crypto
    
    # Price data
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    
    # Additional market data
    bid_price = Column(Float, nullable=True)
    ask_price = Column(Float, nullable=True)
    bid_size = Column(Float, nullable=True)
    ask_size = Column(Float, nullable=True)
    
    # Derived metrics
    vwap = Column(Float, nullable=True)  # Volume Weighted Average Price
    twap = Column(Float, nullable=True)  # Time Weighted Average Price
    
    # Metadata
    data_source = Column(String(50), nullable=True)  # alpha_vantage, iex, polygon
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_timestamp_symbol', 'timestamp', 'symbol'),
    )
    
    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, timestamp={self.timestamp}, close=${self.close_price})>"

class PriceHistory(Base):
    """Historical price data with technical indicators"""
    
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Symbol and timing
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), default="1d")  # 1m, 5m, 15m, 1h, 1d, 1w, 1M
    
    # OHLCV data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    adjusted_close = Column(Float, nullable=True)
    
    # Technical indicators
    sma_20 = Column(Float, nullable=True)   # Simple Moving Average
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)   # Exponential Moving Average
    ema_26 = Column(Float, nullable=True)
    
    # Momentum indicators
    rsi_14 = Column(Float, nullable=True)   # Relative Strength Index
    macd = Column(Float, nullable=True)     # MACD line
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    
    # Volatility indicators
    bollinger_upper = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)   # Average True Range
    
    # Volume indicators
    volume_sma_20 = Column(Float, nullable=True)
    on_balance_volume = Column(Float, nullable=True)
    
    # Price action
    daily_return = Column(Float, nullable=True)
    volatility_20d = Column(Float, nullable=True)
    
    # Support/Resistance levels
    support_level = Column(Float, nullable=True)
    resistance_level = Column(Float, nullable=True)
    
    # Metadata
    data_source = Column(String(50), nullable=True)
    indicators_calculated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_symbol_date_timeframe', 'symbol', 'date', 'timeframe'),
        Index('idx_date_symbol', 'date', 'symbol'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(symbol={self.symbol}, date={self.date.date()}, close=${self.close_price})>"

class EconomicIndicator(Base):
    """Economic indicators that may affect trading"""
    
    __tablename__ = "economic_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Indicator details
    indicator_code = Column(String(50), nullable=False, index=True)  # GDP, CPI, UNEMPLOYMENT, etc.
    indicator_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)  # economic, sentiment, policy
    
    # Geographic scope
    country_code = Column(String(5), default="US")
    region = Column(String(100), nullable=True)
    
    # Data
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    forecast_value = Column(Float, nullable=True)
    
    # Impact assessment
    surprise_index = Column(Float, nullable=True)  # (actual - forecast) / std
    market_impact_score = Column(Float, nullable=True)  # Historical market reaction
    
    # Units and metadata
    units = Column(String(50), nullable=True)
    frequency = Column(String(20), nullable=True)  # monthly, quarterly, annual
    data_source = Column(String(50), nullable=True)  # fred, bloomberg, etc.
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_indicator_date', 'indicator_code', 'date'),
        Index('idx_date_indicator', 'date', 'indicator_code'),
    )
    
    def __repr__(self):
        return f"<EconomicIndicator(code={self.indicator_code}, date={self.date.date()}, value={self.value})>"

class NewsEvent(Base):
    """News events that may impact trading"""
    
    __tablename__ = "news_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    headline = Column(String(500), nullable=False)
    summary = Column(String(2000), nullable=True)
    event_type = Column(String(100), nullable=True)  # earnings, merger, regulatory, etc.
    
    # Affected securities
    symbols = Column(JSON, nullable=True)  # List of affected symbols
    sectors = Column(JSON, nullable=True)  # Affected sectors
    
    # Sentiment analysis
    sentiment_score = Column(Float, nullable=True)  # -1 to 1 (negative to positive)
    sentiment_magnitude = Column(Float, nullable=True)  # 0 to 1 (confidence)
    
    # Event impact
    expected_impact = Column(String(20), nullable=True)  # high, medium, low
    actual_impact = Column(Float, nullable=True)  # Measured price impact
    
    # Timing
    event_timestamp = Column(DateTime, nullable=False, index=True)
    published_at = Column(DateTime, nullable=False)
    
    # Source information
    source = Column(String(100), nullable=True)  # reuters, bloomberg, etc.
    source_url = Column(String(1000), nullable=True)
    author = Column(String(200), nullable=True)
    
    # Geographic relevance
    geographic_scope = Column(JSON, nullable=True)  # Countries/regions affected
    
    # Processing status
    processed = Column(Boolean, default=False)
    impact_analyzed = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewsEvent(headline='{self.headline[:50]}...', timestamp={self.event_timestamp})>"