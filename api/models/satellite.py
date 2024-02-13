"""
Satellite imagery and analysis database models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..core.database import Base

class SatelliteImage(Base):
    """Satellite image metadata and storage information"""
    
    __tablename__ = "satellite_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)  # landsat, sentinel, planet, maxar
    satellite_id = Column(String(100), nullable=False)  # e.g., "LC08_L1TP_044034_20231201_20231208_02_T1"
    acquisition_date = Column(DateTime, nullable=False)
    cloud_coverage = Column(Float, default=0.0)
    
    # Geographic bounds
    bbox_north = Column(Float, nullable=False)
    bbox_south = Column(Float, nullable=False)
    bbox_east = Column(Float, nullable=False)
    bbox_west = Column(Float, nullable=False)
    
    # Image properties
    resolution_meters = Column(Float, nullable=True)
    bands = Column(JSON, nullable=True)  # Available spectral bands
    file_path = Column(String(500), nullable=True)  # Local storage path
    remote_url = Column(String(1000), nullable=True)  # Original source URL
    file_size_bytes = Column(Integer, nullable=True)
    
    # Processing status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = relationship("SatelliteAnalysis", back_populates="image")

class SatelliteAnalysis(Base):
    """Results of satellite image analysis using ML models"""
    
    __tablename__ = "satellite_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("satellite_images.id"), nullable=False)
    
    # Model information
    model_version = Column(String(50), nullable=False)
    model_name = Column(String(100), default="unet_segmentation")
    processing_time_seconds = Column(Float, nullable=True)
    
    # Segmentation results
    segmentation_mask_path = Column(String(500), nullable=True)  # Path to segmentation mask
    class_counts = Column(JSON, nullable=True)  # Pixel counts for each class
    class_percentages = Column(JSON, nullable=True)  # Percentage coverage for each class
    
    # Economic indicators derived from analysis
    building_density = Column(Float, nullable=True)  # Buildings per square km
    vegetation_index = Column(Float, nullable=True)  # NDVI or similar
    water_coverage = Column(Float, nullable=True)    # Water body percentage
    road_network_density = Column(Float, nullable=True)  # Road density
    construction_activity = Column(Float, nullable=True)  # Construction indicator
    
    # Confidence metrics
    overall_confidence = Column(Float, nullable=True)  # Model confidence (0-1)
    class_confidences = Column(JSON, nullable=True)   # Per-class confidence scores
    
    # Change detection (if comparing to previous analysis)
    change_detection_enabled = Column(Boolean, default=False)
    previous_analysis_id = Column(UUID(as_uuid=True), ForeignKey("satellite_analyses.id"), nullable=True)
    change_metrics = Column(JSON, nullable=True)  # Changes from previous analysis
    
    # Economic impact estimates
    economic_activity_score = Column(Float, nullable=True)  # Overall economic activity (0-100)
    sector_impacts = Column(JSON, nullable=True)  # Estimated impacts by economic sector
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    image = relationship("SatelliteImage", back_populates="analyses")
    trading_signals = relationship("TradingSignal", back_populates="satellite_analysis")
    
    def __repr__(self):
        return f"<SatelliteAnalysis(id={self.id}, image_id={self.image_id}, model={self.model_name})>"

class EconomicRegion(Base):
    """Geographic regions for economic analysis"""
    
    __tablename__ = "economic_regions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    region_type = Column(String(50), nullable=False)  # country, state, city, agricultural_zone, etc.
    
    # Geographic bounds
    bbox_north = Column(Float, nullable=False)
    bbox_south = Column(Float, nullable=False) 
    bbox_east = Column(Float, nullable=False)
    bbox_west = Column(Float, nullable=False)
    
    # Economic metadata
    population = Column(Integer, nullable=True)
    gdp_usd = Column(Float, nullable=True)
    primary_industries = Column(JSON, nullable=True)  # List of primary economic sectors
    
    # Trading relevance
    related_symbols = Column(JSON, nullable=True)  # Stock/commodity symbols affected by this region
    monitoring_enabled = Column(Boolean, default=True)
    priority_score = Column(Float, default=1.0)  # Monitoring priority (0-10)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EconomicRegion(id={self.id}, name={self.name}, type={self.region_type})>"