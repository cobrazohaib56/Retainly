import json
import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.core.database import get_database
from app.models.analysis import AnalysisDocument, AnalysisData, AnalysisSummary
from app.core.config import settings
from typing import List
import logging
from bson import ObjectId


# GMT+5 timezone
GMT_PLUS_5 = timezone(timedelta(hours=5))

def get_gmt_plus_5_now():
    """
    Get current datetime in GMT+5 timezone.
    Since MongoDB stores in UTC, we store UTC time that represents GMT+5 time.
    We add 5 hours to UTC so when stored, it shows as GMT+5.
    """
    # Get current UTC time
    utc_now = datetime.now(timezone.utc)
    # Add 5 hours to represent GMT+5 time
    # This way, when MongoDB stores it as UTC, it will show the correct GMT+5 time
    gmt_plus_5_time = utc_now + timedelta(hours=5)
    # Return as timezone-aware UTC (MongoDB will store this as-is)
    return gmt_plus_5_time.replace(tzinfo=timezone.utc)

logger = logging.getLogger(__name__)

class AnalysisService:
    @staticmethod
    async def create_analysis(filename: str, data: Dict[str, Any]) -> str:
        """Create a new analysis document in MongoDB"""
        try:
            db = get_database()
            if db is None:
                raise ValueError("Database not connected. Check MongoDB connection.")
            
            collection = db["analyses"]
            
            analysis_doc = AnalysisDocument(
                filename=filename,
                timestamp=get_gmt_plus_5_now(),
                data=AnalysisData(**data),
                status="processing"
            )
            
            # Exclude id field - let MongoDB auto-generate _id
            doc_dict = analysis_doc.model_dump(by_alias=True, exclude={"id"})
            
            result = await collection.insert_one(doc_dict)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Failed to create analysis: {e}")
            raise
    
    @staticmethod
    async def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID"""
        
        try:
            db = get_database()
            collection = db["analyses"]
            analysis = await collection.find_one({"_id": ObjectId(analysis_id)})
            
            if analysis:
                analysis["id"] = str(analysis["_id"])
                del analysis["_id"]
                # Convert timestamp to GMT+5 timezone for display
                if "timestamp" in analysis and analysis["timestamp"]:
                    if isinstance(analysis["timestamp"], datetime):
                        # The stored UTC time already represents GMT+5 time
                        # We just need to add the GMT+5 timezone offset for display
                        if analysis["timestamp"].tzinfo is None:
                            # If naive datetime, assume UTC
                            analysis["timestamp"] = analysis["timestamp"].replace(tzinfo=timezone.utc)
                        # Replace timezone to GMT+5 without changing the time value
                        # This makes it serialize as +05:00
                        analysis["timestamp"] = analysis["timestamp"].replace(tzinfo=GMT_PLUS_5)
                return analysis
            return None
        except Exception as e:
            logger.error(f"Error getting analysis: {e}")
            return None
    
    @staticmethod
    async def get_all_analyses(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all analyses, sorted by timestamp descending"""
        db = get_database()
        collection = db["analyses"]
        
        cursor = collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        analyses = await cursor.to_list(length=limit)
        
        for analysis in analyses:
            analysis["id"] = str(analysis["_id"])
            del analysis["_id"]
            # Convert timestamp to GMT+5 timezone for display
            if "timestamp" in analysis and analysis["timestamp"]:
                if isinstance(analysis["timestamp"], datetime):
                    # The stored UTC time already represents GMT+5 time
                    # We just need to add the GMT+5 timezone offset for display
                    if analysis["timestamp"].tzinfo is None:
                        # If naive datetime, assume UTC
                        analysis["timestamp"] = analysis["timestamp"].replace(tzinfo=timezone.utc)
                    # Replace timezone to GMT+5 without changing the time value
                    # This makes it serialize as +05:00
                    analysis["timestamp"] = analysis["timestamp"].replace(tzinfo=GMT_PLUS_5)
        
        return analyses
    
    @staticmethod
    async def delete_analysis(analysis_id: str) -> bool:
        """Delete an analysis by ID"""
        
        try:
            db = get_database()
            collection = db["analyses"]
            result = await collection.delete_one({"_id": ObjectId(analysis_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting analysis: {e}")
            return False
    
    @staticmethod
    async def update_analysis_status(analysis_id: str, status: str, progress: Optional[float] = None):
        """Update analysis processing status"""
        
        try:
            db = get_database()
            collection = db["analyses"]
            update_data = {"status": status}
            if progress is not None:
                update_data["progress"] = progress
            
            await collection.update_one(
                {"_id": ObjectId(analysis_id)},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"Error updating analysis status: {e}")
