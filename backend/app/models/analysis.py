from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

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

class AnalysisEntry(BaseModel):
    entry_id: str
    receipt_number: str
    to_user: str
    from_merchant: Optional[str] = None
    dataset_coins: int
    extracted_family_coins: Optional[int] = None
    difference: Optional[int] = None
    category: str
    receipt_photo_url: str
    image_path: Optional[str] = None
    azure_raw_response: Optional[str] = None
    extraction_confidence: Optional[float] = None

class ErrorEntry(BaseModel):
    entry_id: str
    receipt_number: str
    to_user: str
    error: str
    receipt_photo_url: str
    dataset_coins: int

class AnalysisSummary(BaseModel):
    total_entries: int
    processed: int
    errors: int
    exact_match_count: int
    low_rank_count: int
    medium_rank_count: int
    critical_rank_count: int
    error_count: int

class AnalysisData(BaseModel):
    summary: AnalysisSummary
    exact_match: List[AnalysisEntry]
    low_rank: List[AnalysisEntry]
    medium_rank: List[AnalysisEntry]
    critical_rank: List[AnalysisEntry]
    errors: List[ErrorEntry]

class AnalysisDocument(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id", exclude=True)
    filename: str
    timestamp: datetime = Field(default_factory=get_gmt_plus_5_now)
    data: AnalysisData
    status: str = "completed"  # processing, completed, failed
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
