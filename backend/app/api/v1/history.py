from fastapi import APIRouter, Query, HTTPException
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import HistoryResponse, AnalysisResponse
from typing import List

router = APIRouter()

@router.get("", response_model=HistoryResponse)
async def get_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get analysis history"""
    analyses = await AnalysisService.get_all_analyses(skip=skip, limit=limit)
    
    return HistoryResponse(
        analyses=[AnalysisResponse(**analysis) for analysis in analyses],
        total=len(analyses)
    )

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_history_item(analysis_id: str):
    """Get a specific analysis from history"""
    analysis = await AnalysisService.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(**analysis)
