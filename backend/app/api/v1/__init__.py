from fastapi import APIRouter
from app.api.v1 import analysis, upload, history, images

router = APIRouter()

router.include_router(upload.router, prefix="/upload", tags=["upload"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
router.include_router(history.router, prefix="/history", tags=["history"])
router.include_router(images.router, prefix="/images", tags=["images"])
