"""
Satellite analysis API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from ..core.database import database
from ..services.satellite_service import SatelliteAnalysisService

router = APIRouter()

@router.get("/status")
async def get_satellite_service_status():
    """Get satellite analysis service status"""
    # This would be injected via dependency in production
    service = SatelliteAnalysisService()
    return await service.get_status()

@router.get("/analyses", response_model=List[Dict[str, Any]])
async def get_recent_analyses(limit: int = 20, offset: int = 0):
    """Get recent satellite analyses"""
    try:
        query = """
        SELECT sa.id, sa.image_id, sa.model_version, sa.processing_time_seconds,
               sa.building_density, sa.vegetation_index, sa.water_coverage,
               sa.construction_activity, sa.economic_activity_score,
               sa.overall_confidence, sa.created_at,
               si.source, si.acquisition_date, si.bbox_north, si.bbox_south,
               si.bbox_east, si.bbox_west
        FROM satellite_analyses sa
        JOIN satellite_images si ON sa.image_id = si.id
        ORDER BY sa.created_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        results = await database.fetch_all(
            query, 
            values={'limit': limit, 'offset': offset}
        )
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analyses: {str(e)}")

@router.get("/analysis/{analysis_id}")
async def get_analysis_details(analysis_id: str):
    """Get detailed results for a specific analysis"""
    try:
        query = """
        SELECT sa.*, si.source, si.acquisition_date, si.file_path,
               si.bbox_north, si.bbox_south, si.bbox_east, si.bbox_west
        FROM satellite_analyses sa
        JOIN satellite_images si ON sa.image_id = si.id
        WHERE sa.id = :analysis_id
        """
        
        result = await database.fetch_one(query, values={'analysis_id': analysis_id})
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return dict(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@router.post("/analyze/{image_id}")
async def analyze_image(image_id: str, background_tasks: BackgroundTasks):
    """Trigger analysis of a satellite image"""
    try:
        # Verify image exists
        image_query = "SELECT id, status FROM satellite_images WHERE id = :image_id"
        image = await database.fetch_one(image_query, values={'image_id': image_id})
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if image['status'] == 'processing':
            return {"message": "Image is already being processed", "image_id": image_id}
        
        # Add analysis to background tasks
        service = SatelliteAnalysisService()
        background_tasks.add_task(service.analyze_satellite_image, image_id)
        
        # Update image status
        await database.execute(
            "UPDATE satellite_images SET status = 'processing' WHERE id = :image_id",
            values={'image_id': image_id}
        )
        
        return {
            "message": "Analysis started",
            "image_id": image_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")

@router.get("/economic-indicators")
async def get_economic_indicators_summary(days: int = 30):
    """Get summary of economic indicators from recent analyses"""
    try:
        query = """
        SELECT 
            DATE(sa.created_at) as date,
            AVG(sa.building_density) as avg_building_density,
            AVG(sa.vegetation_index) as avg_vegetation_index,
            AVG(sa.water_coverage) as avg_water_coverage,
            AVG(sa.construction_activity) as avg_construction_activity,
            AVG(sa.economic_activity_score) as avg_economic_score,
            COUNT(*) as analyses_count
        FROM satellite_analyses sa
        WHERE sa.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(sa.created_at)
        ORDER BY date DESC
        """ % days
        
        results = await database.fetch_all(query)
        
        summary = []
        for row in results:
            summary.append({
                'date': row['date'].isoformat(),
                'building_density': float(row['avg_building_density'] or 0),
                'vegetation_index': float(row['avg_vegetation_index'] or 0),
                'water_coverage': float(row['avg_water_coverage'] or 0),
                'construction_activity': float(row['avg_construction_activity'] or 0),
                'economic_activity_score': float(row['avg_economic_score'] or 0),
                'analyses_count': row['analyses_count']
            })
        
        return {
            'period_days': days,
            'total_summaries': len(summary),
            'daily_summaries': summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting economic indicators: {str(e)}")

@router.get("/images")
async def get_satellite_images(
    limit: int = 20,
    offset: int = 0,
    source: Optional[str] = None,
    status: Optional[str] = None
):
    """Get satellite images with optional filtering"""
    try:
        where_conditions = []
        params = {'limit': limit, 'offset': offset}
        
        if source:
            where_conditions.append("source = :source")
            params['source'] = source
            
        if status:
            where_conditions.append("status = :status")  
            params['status'] = status
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
        SELECT id, source, satellite_id, acquisition_date, cloud_coverage,
               bbox_north, bbox_south, bbox_east, bbox_west, resolution_meters,
               status, processed_at, created_at
        FROM satellite_images
        {where_clause}
        ORDER BY acquisition_date DESC
        LIMIT :limit OFFSET :offset
        """
        
        results = await database.fetch_all(query, values=params)
        
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving images: {str(e)}")