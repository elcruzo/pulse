"""
Satellite imagery analysis service integrating the existing U-Net model
"""

import asyncio
import logging
import numpy as np
import cv2
import rasterio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import uuid
import json

import torch
import torch.nn as nn
import tensorflow as tf
from tensorflow import keras
from PIL import Image
from patchify import patchify
from sklearn.preprocessing import MinMaxScaler

from ..core.config import settings
from ..core.redis_client import redis_client
from ..models.satellite import SatelliteImage, SatelliteAnalysis
from ..core.database import database

logger = logging.getLogger(__name__)

class SatelliteAnalysisService:
    """
    Service for processing satellite imagery and generating economic indicators
    
    Integrates the existing U-Net semantic segmentation model with production infrastructure
    """
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.image_patch_size = 256
        self.minmaxscaler = MinMaxScaler()
        
        # Class mappings from the existing model
        self.class_labels = {
            0: "water",
            1: "land", 
            2: "road",
            3: "building",
            4: "vegetation",
            5: "unlabeled"
        }
        
        # Economic indicator weights for different land use classes
        self.economic_weights = {
            "building": 1.0,      # High economic activity
            "road": 0.7,          # Infrastructure indicator
            "vegetation": 0.3,    # Agricultural activity
            "water": 0.1,         # Ports/shipping
            "land": 0.2,          # Development potential
            "unlabeled": 0.0      # No economic value
        }
        
    async def initialize(self):
        """Initialize the satellite analysis service"""
        try:
            await self._load_segmentation_model()
            logger.info("Satellite analysis service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize satellite service: {e}")
            raise
    
    async def _load_segmentation_model(self):
        """Load the pre-trained U-Net segmentation model"""
        try:
            model_path = settings.MODEL_DIRECTORY / "satellite_segmentation.h5"
            
            if model_path.exists():
                # Load existing trained model
                self.model = keras.models.load_model(
                    str(model_path),
                    custom_objects={
                        'jaccard_coef': self._jaccard_coef,
                        'dice_loss': self._dice_loss,
                        'focal_loss': self._focal_loss
                    }
                )
                logger.info(f"Loaded existing model from {model_path}")
            else:
                # Create new model using the architecture from the notebook
                self.model = self._create_unet_model()
                logger.warning(f"No existing model found, created new model architecture")
            
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load segmentation model: {e}")
            raise
    
    def _create_unet_model(self, n_classes=6, image_height=256, image_width=256, image_channels=3):
        """
        Create U-Net model architecture (from the existing notebook)
        """
        inputs = keras.layers.Input((image_height, image_width, image_channels))
        
        # Encoder (downsampling)
        c1 = keras.layers.Conv2D(16, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(inputs)
        c1 = keras.layers.Dropout(0.2)(c1)
        c1 = keras.layers.Conv2D(16, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c1)
        p1 = keras.layers.MaxPooling2D((2,2))(c1)
        
        c2 = keras.layers.Conv2D(32, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(p1)
        c2 = keras.layers.Dropout(0.2)(c2)
        c2 = keras.layers.Conv2D(32, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c2)
        p2 = keras.layers.MaxPooling2D((2,2))(c2)
        
        c3 = keras.layers.Conv2D(64, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(p2)
        c3 = keras.layers.Dropout(0.2)(c3)
        c3 = keras.layers.Conv2D(64, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c3)
        p3 = keras.layers.MaxPooling2D((2,2))(c3)
        
        c4 = keras.layers.Conv2D(128, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(p3)
        c4 = keras.layers.Dropout(0.2)(c4)
        c4 = keras.layers.Conv2D(128, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c4)
        p4 = keras.layers.MaxPooling2D((2,2))(c4)
        
        # Bridge
        c5 = keras.layers.Conv2D(256, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(p4)
        c5 = keras.layers.Dropout(0.2)(c5)
        c5 = keras.layers.Conv2D(256, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c5)
        
        # Decoder (upsampling)
        u6 = keras.layers.Conv2DTranspose(128, (2,2), strides=(2,2), padding="same")(c5)
        u6 = keras.layers.concatenate([u6, c4])
        c6 = keras.layers.Conv2D(128, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(u6)
        c6 = keras.layers.Dropout(0.2)(c6)
        c6 = keras.layers.Conv2D(128, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c6)
        
        u7 = keras.layers.Conv2DTranspose(64, (2,2), strides=(2,2), padding="same")(c6)
        u7 = keras.layers.concatenate([u7, c3])
        c7 = keras.layers.Conv2D(64, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(u7)
        c7 = keras.layers.Dropout(0.2)(c7)
        c7 = keras.layers.Conv2D(64, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c7)
        
        u8 = keras.layers.Conv2DTranspose(32, (2,2), strides=(2,2), padding="same")(c7)
        u8 = keras.layers.concatenate([u8, c2])
        c8 = keras.layers.Conv2D(32, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(u8)
        c8 = keras.layers.Dropout(0.2)(c8)
        c8 = keras.layers.Conv2D(32, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c8)
        
        u9 = keras.layers.Conv2DTranspose(16, (2,2), strides=(2,2), padding="same")(c8)
        u9 = keras.layers.concatenate([u9, c1], axis=3)
        c9 = keras.layers.Conv2D(16, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(u9)
        c9 = keras.layers.Dropout(0.2)(c9)
        c9 = keras.layers.Conv2D(16, (3,3), activation="relu", kernel_initializer="he_normal", padding="same")(c9)
        
        outputs = keras.layers.Conv2D(n_classes, (1,1), activation="softmax")(c9)
        
        model = keras.models.Model(inputs=[inputs], outputs=[outputs])
        return model
    
    def _jaccard_coef(self, y_true, y_pred):
        """Jaccard coefficient (IoU) metric"""
        y_true_flatten = tf.keras.backend.flatten(y_true)
        y_pred_flatten = tf.keras.backend.flatten(y_pred)
        intersection = tf.keras.backend.sum(y_true_flatten * y_pred_flatten)
        return (intersection + 1.0) / (tf.keras.backend.sum(y_true_flatten) + tf.keras.backend.sum(y_pred_flatten) - intersection + 1.0)
    
    def _dice_loss(self, y_true, y_pred):
        """Dice loss function"""
        return 1 - self._jaccard_coef(y_true, y_pred)
    
    def _focal_loss(self, y_true, y_pred, alpha=0.25, gamma=2.0):
        """Focal loss for handling class imbalance"""
        epsilon = tf.keras.backend.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
        alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        focal_loss = -alpha_t * tf.pow((1 - p_t), gamma) * tf.log(p_t)
        return tf.reduce_mean(focal_loss)
    
    async def analyze_satellite_image(self, image_id: str) -> Dict[str, Any]:
        """
        Analyze a satellite image and generate economic indicators
        
        Args:
            image_id: UUID of the satellite image to analyze
            
        Returns:
            Dictionary containing analysis results and economic indicators
        """
        try:
            # Check cache first
            cached_result = await redis_client.get_cached_satellite_analysis(image_id)
            if cached_result:
                logger.info(f"Returning cached analysis for image {image_id}")
                return cached_result
            
            # Get image information from database
            image_info = await self._get_image_info(image_id)
            if not image_info:
                raise ValueError(f"Image {image_id} not found")
            
            # Load and preprocess image
            image_data = await self._load_and_preprocess_image(image_info['file_path'])
            
            # Run segmentation model
            segmentation_result = await self._run_segmentation(image_data)
            
            # Calculate economic indicators
            economic_indicators = self._calculate_economic_indicators(segmentation_result)
            
            # Store results
            analysis_result = {
                'image_id': image_id,
                'model_version': '1.0.0',
                'processing_time': segmentation_result['processing_time'],
                'segmentation_results': segmentation_result,
                'economic_indicators': economic_indicators,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Save to database
            await self._save_analysis_results(image_id, analysis_result)
            
            # Cache results
            await redis_client.cache_satellite_analysis(image_id, analysis_result)
            
            logger.info(f"Completed analysis for image {image_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing satellite image {image_id}: {e}")
            raise
    
    async def _get_image_info(self, image_id: str) -> Optional[Dict]:
        """Get satellite image information from database"""
        query = """
        SELECT id, file_path, bbox_north, bbox_south, bbox_east, bbox_west, 
               acquisition_date, source, resolution_meters
        FROM satellite_images 
        WHERE id = :image_id
        """
        result = await database.fetch_one(query, values={"image_id": image_id})
        return dict(result) if result else None
    
    async def _load_and_preprocess_image(self, file_path: str) -> np.ndarray:
        """Load and preprocess satellite image for model input"""
        try:
            # Load image
            image = cv2.imread(file_path, 1)
            if image is None:
                raise ValueError(f"Could not load image from {file_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize to model input size
            size_x = (image.shape[1] // self.image_patch_size) * self.image_patch_size
            size_y = (image.shape[0] // self.image_patch_size) * self.image_patch_size
            
            image = Image.fromarray(image)
            image = image.crop((0, 0, size_x, size_y))
            image = np.array(image)
            
            # Create patches
            patched_images = patchify(image, (self.image_patch_size, self.image_patch_size, 3), step=self.image_patch_size)
            
            # Normalize patches
            image_patches = []
            for i in range(patched_images.shape[0]):
                for j in range(patched_images.shape[1]):
                    patch = patched_images[i, j, :, :]
                    patch = self.minmaxscaler.fit_transform(patch.reshape(-1, patch.shape[-1])).reshape(patch.shape)
                    patch = patch[0]  # Remove extra dimension
                    image_patches.append(patch)
            
            return np.array(image_patches)
            
        except Exception as e:
            logger.error(f"Error preprocessing image {file_path}: {e}")
            raise
    
    async def _run_segmentation(self, image_patches: np.ndarray) -> Dict[str, Any]:
        """Run semantic segmentation on image patches"""
        try:
            start_time = datetime.utcnow()
            
            if not self.model_loaded:
                await self._load_segmentation_model()
            
            # Run inference
            predictions = self.model.predict(image_patches, batch_size=settings.BATCH_SIZE)
            
            # Convert predictions to class labels
            predicted_masks = np.argmax(predictions, axis=3)
            
            # Calculate class statistics
            class_counts = {}
            class_percentages = {}
            total_pixels = predicted_masks.size
            
            for class_id, class_name in self.class_labels.items():
                count = np.sum(predicted_masks == class_id)
                class_counts[class_name] = int(count)
                class_percentages[class_name] = float(count / total_pixels * 100)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'predicted_masks': predicted_masks,
                'class_counts': class_counts,
                'class_percentages': class_percentages,
                'processing_time': processing_time,
                'total_patches': len(image_patches),
                'model_confidence': float(np.mean(np.max(predictions, axis=3)))
            }
            
        except Exception as e:
            logger.error(f"Error running segmentation: {e}")
            raise
    
    def _calculate_economic_indicators(self, segmentation_result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate economic indicators from segmentation results"""
        try:
            class_percentages = segmentation_result['class_percentages']
            
            # Building density (proxy for economic activity)
            building_density = class_percentages.get('building', 0.0)
            
            # Vegetation index (agricultural activity)
            vegetation_index = class_percentages.get('vegetation', 0.0)
            
            # Infrastructure development (roads + buildings)
            infrastructure_index = (
                class_percentages.get('road', 0.0) + 
                class_percentages.get('building', 0.0)
            )
            
            # Water coverage (shipping/maritime activity)
            water_coverage = class_percentages.get('water', 0.0)
            
            # Construction activity (undeveloped land that might be under construction)
            construction_activity = max(0, class_percentages.get('land', 0.0) - 50.0)  # Land above 50% might indicate construction
            
            # Overall economic activity score (weighted combination)
            economic_activity_score = (
                building_density * self.economic_weights['building'] +
                class_percentages.get('road', 0.0) * self.economic_weights['road'] +
                vegetation_index * self.economic_weights['vegetation'] +
                water_coverage * self.economic_weights['water'] +
                class_percentages.get('land', 0.0) * self.economic_weights['land']
            )
            
            return {
                'building_density': building_density,
                'vegetation_index': vegetation_index,
                'infrastructure_index': infrastructure_index,
                'water_coverage': water_coverage,
                'construction_activity': construction_activity,
                'economic_activity_score': min(100.0, economic_activity_score),  # Cap at 100
                'urbanization_ratio': building_density / max(1.0, vegetation_index),  # Urban vs rural
                'development_potential': max(0, 100 - infrastructure_index)  # Available land for development
            }
            
        except Exception as e:
            logger.error(f"Error calculating economic indicators: {e}")
            raise
    
    async def _save_analysis_results(self, image_id: str, analysis_result: Dict[str, Any]) -> str:
        """Save analysis results to database"""
        try:
            analysis_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO satellite_analyses (
                id, image_id, model_version, model_name, processing_time_seconds,
                class_counts, class_percentages, building_density, vegetation_index,
                water_coverage, construction_activity, economic_activity_score,
                overall_confidence, created_at
            ) VALUES (
                :id, :image_id, :model_version, :model_name, :processing_time,
                :class_counts, :class_percentages, :building_density, :vegetation_index,
                :water_coverage, :construction_activity, :economic_activity_score,
                :overall_confidence, :created_at
            )
            """
            
            seg_results = analysis_result['segmentation_results']
            econ_indicators = analysis_result['economic_indicators']
            
            values = {
                'id': analysis_id,
                'image_id': image_id,
                'model_version': analysis_result['model_version'],
                'model_name': 'unet_segmentation',
                'processing_time': seg_results['processing_time'],
                'class_counts': json.dumps(seg_results['class_counts']),
                'class_percentages': json.dumps(seg_results['class_percentages']),
                'building_density': econ_indicators['building_density'],
                'vegetation_index': econ_indicators['vegetation_index'],
                'water_coverage': econ_indicators['water_coverage'],
                'construction_activity': econ_indicators['construction_activity'],
                'economic_activity_score': econ_indicators['economic_activity_score'],
                'overall_confidence': seg_results['model_confidence'],
                'created_at': datetime.utcnow()
            }
            
            await database.execute(query, values)
            logger.info(f"Saved analysis results for image {image_id} with ID {analysis_id}")
            
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            raise
    
    async def process_pending_images(self):
        """Background task to process pending satellite images"""
        try:
            # Get pending images
            query = """
            SELECT id, file_path, source, acquisition_date
            FROM satellite_images 
            WHERE status = 'pending' AND file_path IS NOT NULL
            ORDER BY acquisition_date DESC
            LIMIT 10
            """
            
            pending_images = await database.fetch_all(query)
            
            if not pending_images:
                return
            
            logger.info(f"Processing {len(pending_images)} pending satellite images")
            
            for image in pending_images:
                try:
                    # Update status to processing
                    await database.execute(
                        "UPDATE satellite_images SET status = 'processing' WHERE id = :id",
                        values={'id': str(image['id'])}
                    )
                    
                    # Analyze image
                    await self.analyze_satellite_image(str(image['id']))
                    
                    # Update status to completed
                    await database.execute(
                        "UPDATE satellite_images SET status = 'completed', processed_at = :processed_at WHERE id = :id",
                        values={'id': str(image['id']), 'processed_at': datetime.utcnow()}
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing image {image['id']}: {e}")
                    # Update status to failed
                    await database.execute(
                        "UPDATE satellite_images SET status = 'failed', error_message = :error WHERE id = :id",
                        values={'id': str(image['id']), 'error': str(e)}
                    )
                    
        except Exception as e:
            logger.error(f"Error in process_pending_images: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status and metrics"""
        try:
            # Get processing statistics
            stats_query = """
            SELECT 
                status,
                COUNT(*) as count
            FROM satellite_images 
            GROUP BY status
            """
            
            status_counts = await database.fetch_all(stats_query)
            status_summary = {row['status']: row['count'] for row in status_counts}
            
            # Get recent analysis metrics
            recent_query = """
            SELECT 
                COUNT(*) as analyses_today,
                AVG(processing_time_seconds) as avg_processing_time,
                AVG(economic_activity_score) as avg_economic_score
            FROM satellite_analyses 
            WHERE DATE(created_at) = CURRENT_DATE
            """
            
            recent_stats = await database.fetch_one(recent_query)
            
            return {
                'service': 'satellite_analysis',
                'status': 'active' if self.model_loaded else 'inactive',
                'model_loaded': self.model_loaded,
                'model_version': '1.0.0',
                'processing_stats': status_summary,
                'daily_metrics': {
                    'analyses_completed': recent_stats['analyses_today'] or 0,
                    'avg_processing_time_seconds': float(recent_stats['avg_processing_time'] or 0),
                    'avg_economic_activity_score': float(recent_stats['avg_economic_score'] or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting satellite service status: {e}")
            return {
                'service': 'satellite_analysis',
                'status': 'error',
                'error': str(e)
            }