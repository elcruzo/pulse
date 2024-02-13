"""
Trading-related database models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from ..core.database import Base

class SignalType(str, enum.Enum):
    """Types of trading signals"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class SignalStatus(str, enum.Enum):
    """Status of trading signals"""
    ACTIVE = "active"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class TradeStatus(str, enum.Enum):
    """Status of trades"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class TradingSignal(Base):
    """Trading signals generated from satellite analysis"""
    
    __tablename__ = "trading_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    satellite_analysis_id = Column(UUID(as_uuid=True), ForeignKey("satellite_analyses.id"), nullable=True)
    
    # Signal details
    symbol = Column(String(20), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    status = Column(Enum(SignalStatus), default=SignalStatus.ACTIVE)
    
    # Price and timing
    entry_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    
    # Signal strength and confidence
    confidence_score = Column(Float, nullable=False)  # 0-100
    signal_strength = Column(Float, nullable=False)   # 0-1
    risk_score = Column(Float, nullable=True)         # 0-100
    
    # Position sizing
    recommended_position_size = Column(Float, nullable=True)  # Percentage of portfolio
    max_position_value = Column(Float, nullable=True)        # Max dollar amount
    
    # Strategy information
    strategy_name = Column(String(100), nullable=False)
    strategy_version = Column(String(20), nullable=True)
    model_features = Column(JSON, nullable=True)  # Features that generated this signal
    
    # Economic context
    economic_indicator = Column(String(100), nullable=True)  # What indicator triggered this
    geographic_region = Column(String(100), nullable=True)   # Geographic source
    sector = Column(String(50), nullable=True)               # Economic sector
    
    # Timing
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    # Performance tracking
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    max_favorable_excursion = Column(Float, default=0.0)
    max_adverse_excursion = Column(Float, default=0.0)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    satellite_analysis = relationship("SatelliteAnalysis", back_populates="trading_signals")
    trades = relationship("Trade", back_populates="signal")
    
    def __repr__(self):
        return f"<TradingSignal(id={self.id}, symbol={self.symbol}, type={self.signal_type}, confidence={self.confidence_score})>"

class Portfolio(Base):
    """Portfolio management and tracking"""
    
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Portfolio details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(String(50), default="paper")  # paper, live
    
    # Current values
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=100000.0)  # Start with $100k paper money
    invested_value = Column(Float, default=0.0)
    
    # Performance metrics
    total_return = Column(Float, default=0.0)
    total_return_pct = Column(Float, default=0.0)
    daily_return_pct = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # Risk metrics
    value_at_risk = Column(Float, nullable=True)      # 1-day VaR at 95%
    beta = Column(Float, nullable=True)               # Beta vs SPY
    volatility = Column(Float, nullable=True)         # Annualized volatility
    
    # Configuration
    max_position_size = Column(Float, default=0.02)    # 2% max position
    max_sector_exposure = Column(Float, default=0.10)  # 10% max sector
    stop_loss_pct = Column(Float, default=0.02)        # 2% stop loss
    
    # Status
    active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name={self.name}, value=${self.total_value:,.2f})>"

class Position(Base):
    """Current positions in the portfolio"""
    
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    
    # Position details
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Position values
    market_value = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    unrealized_pnl_pct = Column(Float, nullable=False)
    
    # Risk metrics
    position_size_pct = Column(Float, nullable=False)  # Percentage of portfolio
    days_held = Column(Integer, default=0)
    max_gain = Column(Float, default=0.0)
    max_loss = Column(Float, default=0.0)
    
    # Sector and classification
    sector = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    asset_class = Column(String(50), default="equity")  # equity, commodity, forex, crypto
    
    # Timing
    opened_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(symbol={self.symbol}, quantity={self.quantity}, value=${self.market_value:,.2f})>"

class Trade(Base):
    """Individual trade executions"""
    
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("trading_signals.id"), nullable=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # quantity * price
    
    # Order details
    order_type = Column(String(20), default="market")  # market, limit, stop
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    
    # Fees and costs
    commission = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    
    # Execution details
    execution_venue = Column(String(50), nullable=True)  # Exchange or broker
    order_id = Column(String(100), nullable=True)        # External order ID
    
    # Performance (for completed trades)
    realized_pnl = Column(Float, nullable=True)
    holding_period_days = Column(Integer, nullable=True)
    return_pct = Column(Float, nullable=True)
    
    # Strategy attribution
    strategy_name = Column(String(100), nullable=True)
    signal_confidence = Column(Float, nullable=True)
    
    # Timing
    submitted_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    signal = relationship("TradingSignal", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(symbol={self.symbol}, side={self.side}, qty={self.quantity}, price=${self.price})>"

class RiskMetrics(Base):
    """Portfolio risk metrics calculated daily"""
    
    __tablename__ = "risk_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    
    # Date for these metrics
    date = Column(DateTime, nullable=False)
    
    # Value at Risk
    var_1d_95 = Column(Float, nullable=True)    # 1-day VaR at 95%
    var_1d_99 = Column(Float, nullable=True)    # 1-day VaR at 99%
    expected_shortfall = Column(Float, nullable=True)
    
    # Portfolio composition
    concentration_ratio = Column(Float, nullable=True)  # HHI concentration index
    num_positions = Column(Integer, default=0)
    sector_concentration = Column(JSON, nullable=True)  # Sector exposure breakdown
    
    # Correlation metrics
    correlation_to_spy = Column(Float, nullable=True)
    correlation_to_qqq = Column(Float, nullable=True)
    portfolio_beta = Column(Float, nullable=True)
    
    # Volatility metrics
    realized_volatility_30d = Column(Float, nullable=True)
    volatility_vs_benchmark = Column(Float, nullable=True)
    
    # Drawdown metrics
    current_drawdown = Column(Float, nullable=True)
    max_drawdown_30d = Column(Float, nullable=True)
    drawdown_duration_days = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RiskMetrics(portfolio_id={self.portfolio_id}, date={self.date.date()}, var=${self.var_1d_95})>"