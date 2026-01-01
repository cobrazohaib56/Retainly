from fastapi import APIRouter, HTTPException, Path
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisResponse, AnalysisDataResponse
from typing import Literal

router = APIRouter()

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str = Path(..., description="Analysis ID")):
    """Get analysis by ID"""
    analysis = await AnalysisService.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(**analysis)

@router.get("/{analysis_id}/category/{category}")
async def get_category_entries(
    analysis_id: str = Path(..., description="Analysis ID"),
    category: Literal["exact", "low", "medium", "critical", "error"] = Path(..., description="Category")
):
    
    analysis = await AnalysisService.get_analysis_by_id(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    category_map = {
        "exact": "exact_match",
        "low": "low_rank",
        "medium": "medium_rank",
        "critical": "critical_rank",
        "error": "errors"
    }
    
    data_key = category_map.get(category)
    if not data_key:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    entries = analysis.get("data", {}).get(data_key, [])
    
    return {
        "analysis_id": analysis_id,
        "category": category,
        "entries": entries,
        "count": len(entries)
    }

@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str = Path(..., description="Analysis ID")):
    """Delete an analysis"""
    success = await AnalysisService.delete_analysis(analysis_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {"message": "Analysis deleted successfully", "analysis_id": analysis_id}
