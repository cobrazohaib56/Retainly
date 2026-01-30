from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.analysis import (
    AnalysisEntry,
    ErrorEntry,
    NoImageEntry,
    AnalysisSummary
)


class AnalysisEntryResponse(BaseModel):
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


class ErrorEntryResponse(BaseModel):
    entry_id: str
    receipt_number: str
    to_user: str
    error: str
    receipt_photo_url: str
    dataset_coins: int
    reference_id: Optional[str] = None


class NoImageEntryResponse(BaseModel):
    entry_id: str
    receipt_number: str
    to_user: str
    from_merchant: Optional[str] = None
    dataset_coins: int
    reference_id: Optional[str] = None


class AnalysisSummaryResponse(BaseModel):
    total_entries: int
    processed: int
    errors: int
    exact_match_count: int
    low_rank_count: int
    medium_rank_count: int
    critical_rank_count: int
    error_count: int
    no_image_count: int


class AnalysisDataResponse(BaseModel):
    summary: AnalysisSummaryResponse
    exact_match: List[AnalysisEntryResponse]
    low_rank: List[AnalysisEntryResponse]
    medium_rank: List[AnalysisEntryResponse]
    critical_rank: List[AnalysisEntryResponse]
    errors: List[ErrorEntryResponse]
    no_image: List[NoImageEntryResponse]


class AnalysisResponse(BaseModel):
    id: str
    filename: str
    timestamp: datetime
    data: AnalysisDataResponse
    status: str
    progress: Optional[float] = None


class HistoryResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int
