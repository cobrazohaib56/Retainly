import os
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.analysis_service import AnalysisService
from app.services.ai_pipeline_service import process_dataset
from app.core.config import settings
from app.schemas.analysis import AnalysisResponse
from typing import Set
from bson import ObjectId


router = APIRouter()
logger = logging.getLogger(__name__)

# Track background tasks for graceful shutdown
background_tasks_set: Set[asyncio.Task] = set()

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "Upload API is working", "status": "ok"}

@router.post("", response_model=AnalysisResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a JSON or CSV file and start processing"""
    
    # Validate file type
    if not (file.filename.endswith('.json') or file.filename.endswith('.csv')):
        raise HTTPException(status_code=400, detail="Only JSON and CSV files are allowed")
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    try:
        # Read and save file
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"📁 File uploaded: {file.filename} ({len(contents)} bytes)")
        
        # Create analysis document with initial status
        initial_data = {
            "summary": {
                "total_entries": 0,
                "processed": 0,
                "errors": 0,
                "exact_match_count": 0,
                "low_rank_count": 0,
                "medium_rank_count": 0,
                "critical_rank_count": 0,
                "error_count": 0,
                "no_image_count": 0
            },
            "exact_match": [],
            "low_rank": [],
            "medium_rank": [],
            "critical_rank": [],
            "errors": [],
            "no_image": []
        }
        
        analysis_id = await AnalysisService.create_analysis(file.filename, initial_data)
        logger.info(f"📝 Created analysis document: {analysis_id}")
        
        # Start background processing - FastAPI will run this in the same event loop
        background_tasks.add_task(
            process_file_background,
            file_path, analysis_id, file.filename
        )
        
        # Return initial response
        analysis = await AnalysisService.get_analysis_by_id(analysis_id)
        return AnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

async def process_file_background(file_path: str, analysis_id: str, filename: str):
    """Background task to process the uploaded file"""
    
    # Get current task for tracking
    current_task = asyncio.current_task()
    if current_task:
        background_tasks_set.add(current_task)
    
    try:
        logger.info(f"🚀 Starting background processing for: {filename}")
        
        # Update status to processing
        await AnalysisService.update_analysis_status(analysis_id, "processing", 0.0)
        
        # Process dataset with analysis_id for progress tracking
        result = await process_dataset(file_path, analysis_id)
        
        # Update analysis with results
        from app.core.database import get_database
        
        db = get_database()
        collection = db["analyses"]
        
        await collection.update_one(
            {"_id": ObjectId(analysis_id)},
            {
                "$set": {
                    "data": result,
                    "status": "completed",
                    "progress": 100.0,
                    "current_entry": None
                }
            }
        )
        
        logger.info(f"✅ Background processing completed for: {filename}")
        
    except asyncio.CancelledError:
        logger.info(f"🛑 Background task cancelled for: {filename}")
        # Update status to failed
        try:
            await AnalysisService.update_analysis_status(analysis_id, "failed", None)
        except:
            pass
        raise
    except Exception as e:
        logger.error(f"❌ Background processing failed for {filename}: {e}")
        # Update status to failed
        try:
            await AnalysisService.update_analysis_status(analysis_id, "failed", None)
        except:
            pass
    finally:
        # Remove from tracking set
        if current_task:
            background_tasks_set.discard(current_task)

        # Remove uploaded dataset file after processing so it isn't persisted
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Removed uploaded dataset file: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to remove uploaded file {file_path}: {e}")

@router.get("/status/{analysis_id}", response_model=AnalysisResponse)
async def get_processing_status(analysis_id: str):
    """Get processing status of an analysis"""
    
    analysis = await AnalysisService.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(**analysis)
