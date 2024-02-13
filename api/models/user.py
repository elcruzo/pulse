"""
User and authentication models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base

class User(Base):
    """User accounts and profiles"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile information
    company = Column(String(200), nullable=True)
    job_title = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Subscription and permissions
    subscription_tier = Column(String(20), default="free")  # free, basic, pro, enterprise
    max_portfolios = Column(Integer, default=1)
    max_api_calls_per_day = Column(Integer, default=100)
    
    # Trading preferences
    risk_tolerance = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    preferred_sectors = Column(JSON, nullable=True)  # List of preferred sectors
    trading_experience = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    signal_notifications = Column(Boolean, default=True)
    portfolio_alerts = Column(Boolean, default=True)
    
    # Usage tracking
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    api_calls_today = Column(Integer, default=0)
    last_api_call_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"

class APIKey(Base):
    """API keys for programmatic access"""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Key information
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)  # Hashed API key
    key_prefix = Column(String(20), nullable=False)  # First few characters for display
    
    # Permissions
    permissions = Column(JSON, nullable=True)  # List of allowed endpoints/actions
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=1000)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    requests_today = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    last_request_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # IP restrictions
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP addresses
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.key_name}, active={self.is_active})>"

class UserSession(Base):
    """User session tracking"""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session information
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Security
    device_fingerprint = Column(String(255), nullable=True)
    location_country = Column(String(5), nullable=True)
    location_city = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"

class AuditLog(Base):
    """Audit trail for user actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # login, create_signal, execute_trade, etc.
    resource_type = Column(String(50), nullable=True)  # user, portfolio, signal, trade
    resource_id = Column(String(100), nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    api_key_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Additional context
    details = Column(JSON, nullable=True)  # Additional action-specific data
    before_state = Column(JSON, nullable=True)  # State before the action
    after_state = Column(JSON, nullable=True)   # State after the action
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, timestamp={self.timestamp})>"