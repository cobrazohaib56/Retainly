import os
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse
from app.core.config import settings

router = APIRouter()

@router.get("/{receipt_number}")
async def get_receipt_image(receipt_number: str):
    """Get receipt image by receipt number"""
    
    # Search for image in uploads/images directory
    images_dir = os.path.join(settings.UPLOAD_DIR, "images")
    
    if not os.path.exists(images_dir):
        raise HTTPException(status_code=404, detail="Image directory not found")
    
    # Find image file that starts with receipt_number
    for filename in os.listdir(images_dir):
        if filename.startswith(receipt_number):
            image_path = os.path.join(images_dir, filename)
            if os.path.isfile(image_path):
                return FileResponse(
                    image_path,
                    media_type="image/jpeg",
                    filename=filename
                )
    
    raise HTTPException(status_code=404, detail="Image not found")
