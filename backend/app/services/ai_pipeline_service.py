import json
import os
import requests
import google.genai as genai
from typing import Dict, Any, List
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini API client
# Note: API key is passed when creating the client or model

def download_image(url: str, save_path: str) -> bool:
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logger.error(f"   ❌ Failed to download image {url}: {e}")
        return False

def extract_family_coins_from_image(image_path: str) -> Dict[str, Any]:
    """Extract family coins amount from receipt image using Gemini"""
    try:
        # Create client with API key
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = """
        You are analyzing a receipt image. Your task is to find and extract the "family coins" amount from this receipt.
        
        Please carefully examine the image and look for:
        1. Any text that mentions "family coins", "Family Coins", "FAMILY COINS", or similar variations
        2. The numerical value associated with family coins
        3. Any related information about coins or rewards
        
        After analyzing the image, provide your response in the following JSON format:
        {
            "family_coins": [numeric_value]
        }
        
        If you cannot find family coins in the image, set the value to null:
        {
            "family_coins": null
        }
        
        Be very careful and accurate. Only extract the exact number you see for family coins.
        """
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Generate content using the client
        # The new google-genai package uses Client with models.generate_content
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                genai.types.Part.from_bytes(data=image_data, mime_type='image/jpeg'),
                prompt
            ]
        )
        
        raw_response = response.text.strip()
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(raw_response)
            return {
                "success": True,
                "family_coins": result.get("family_coins"),
                "raw_response": raw_response
            }
        except json.JSONDecodeError:
            # Try to extract number from text response
            import re
            numbers = re.findall(r'\d+', raw_response)
            if numbers:
                return {
                    "success": True,
                    "family_coins": int(numbers[0]),
                    "raw_response": raw_response
                }
            return {
                "success": False,
                "family_coins": None,
                "raw_response": raw_response
            }
            
    except Exception as e:
        logger.error(f"   ❌ Gemini API error: {e}")
        return {
            "success": False,
            "family_coins": None,
            "raw_response": str(e)
        }

def categorize_difference(difference: int) -> str:
    """Categorize the difference between dataset coins and extracted coins"""
    if difference == 0:
        return "exact_match"
    elif abs(difference) <= 10:
        return "low_rank"
    elif abs(difference) <= 30:
        return "medium_rank"
    elif abs(difference) <= 70:
        return "critical_rank"
    else:
        return "critical_rank"

async def process_dataset(file_path: str, analysis_id: str = None) -> Dict[str, Any]:
    """Process the dataset file and extract family coins from images"""
    
    logger.info(f"📂 Loading dataset from: {file_path}")
    
    # Load dataset
    with open(file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a JSON array")
    
    total_entries = len(dataset)
    logger.info(f"📊 Found {total_entries} entries to process")
    
    # Initialize result structure
    exact_match = []
    low_rank = []
    medium_rank = []
    critical_rank = []
    errors = []
    
    processed = 0
    
    # Process each entry
    for entry_idx, entry in enumerate(dataset, 1):
        try:
            receipt_number = entry.get("receiptNumber", f"entry_{entry_idx}")
            receipt_photo_url = entry.get("receiptPhotoUrl", "")
            dataset_coins = entry.get("coins", 0)
            to_user = entry.get("toUser", "Unknown")
            from_merchant = entry.get("fromMerchant")
            
            logger.info(f"   🔄 [{entry_idx}/{total_entries}] Processing: {receipt_number}")
            logger.info(f"      📊 Dataset coins: {dataset_coins}")
            
            if not receipt_photo_url:
                logger.warning(f"      ⚠️  No receipt photo URL, skipping")
                errors.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "error": "No receipt photo URL",
                    "receipt_photo_url": "",
                    "dataset_coins": dataset_coins
                })
                continue
            
            # Download image
            image_filename = f"{receipt_number}_{entry_idx}.jpg"
            image_path = os.path.join(settings.UPLOAD_DIR, "images", image_filename)
            
            logger.info(f"      📥 Downloading image from: {receipt_photo_url}")
            if not download_image(receipt_photo_url, image_path):
                errors.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "error": "Failed to download image",
                    "receipt_photo_url": receipt_photo_url,
                    "dataset_coins": dataset_coins
                })
                continue
            
            logger.info(f"      ✅ Image downloaded: {image_path}")
            
            # Extract family coins using Gemini
            logger.info(f"      🤖 Analyzing image with Gemini...")
            extraction_result = extract_family_coins_from_image(image_path)
            
            if not extraction_result["success"] or extraction_result["family_coins"] is None:
                logger.warning(f"      ⚠️  Could not extract family coins")
                errors.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "error": f"Failed to extract family coins: {extraction_result.get('raw_response', 'Unknown error')}",
                    "receipt_photo_url": receipt_photo_url,
                    "dataset_coins": dataset_coins
                })
                continue
            
            extracted_coins = extraction_result["family_coins"]
            logger.info(f"      💰 Extracted family coins: {extracted_coins}")
            
            # Calculate difference
            difference = dataset_coins - extracted_coins
            logger.info(f"      📈 Difference: {difference} coins")
            
            # Categorize
            category = categorize_difference(difference)
            logger.info(f"      📈 Category: {category.upper()} | Difference: {difference} coins")
            
            # Create entry
            entry_data = {
                "entry_id": str(entry_idx),
                "receipt_number": receipt_number,
                "to_user": to_user,
                "from_merchant": from_merchant,
                "dataset_coins": dataset_coins,
                "extracted_family_coins": extracted_coins,
                "difference": difference,
                "category": category,
                "receipt_photo_url": receipt_photo_url,
                "image_path": image_path,
                "gemini_raw_response": extraction_result.get("raw_response")
            }
            
            # Add to appropriate category
            if category == "exact_match":
                exact_match.append(entry_data)
            elif category == "low_rank":
                low_rank.append(entry_data)
            elif category == "medium_rank":
                medium_rank.append(entry_data)
            elif category == "critical_rank":
                critical_rank.append(entry_data)
            
            processed += 1
            
            # Progress update
            progress = (entry_idx / total_entries) * 100
            logger.info(f"      ✅ Progress: {progress:.1f}% ({processed}/{total_entries} processed)")
            
            # Update progress in database if analysis_id is provided
            if analysis_id:
                try:
                    from app.services.analysis_service import AnalysisService
                    await AnalysisService.update_analysis_status(analysis_id, "processing", progress)
                except Exception as e:
                    logger.warning(f"      ⚠️  Failed to update progress: {e}")
            
        except Exception as e:
            logger.error(f"   ❌ Error processing entry {entry_idx}: {e}")
            errors.append({
                "entry_id": str(entry_idx),
                "receipt_number": entry.get("receiptNumber", f"entry_{entry_idx}"),
                "to_user": entry.get("toUser", "Unknown"),
                "error": str(e),
                "receipt_photo_url": entry.get("receiptPhotoUrl", ""),
                "dataset_coins": entry.get("coins", 0)
            })
    
    # Create summary
    summary = {
        "total_entries": total_entries,
        "processed": processed,
        "errors": len(errors),
        "exact_match_count": len(exact_match),
        "low_rank_count": len(low_rank),
        "medium_rank_count": len(medium_rank),
        "critical_rank_count": len(critical_rank),
        "error_count": len(errors)
    }
    
    logger.info(f"✅ Processing complete!")
    logger.info(f"   📊 Summary:")
    logger.info(f"      Total: {summary['total_entries']}")
    logger.info(f"      Processed: {summary['processed']}")
    logger.info(f"      Exact Match: {summary['exact_match_count']}")
    logger.info(f"      Low Rank: {summary['low_rank_count']}")
    logger.info(f"      Medium Rank: {summary['medium_rank_count']}")
    logger.info(f"      Critical Rank: {summary['critical_rank_count']}")
    logger.info(f"      Errors: {summary['error_count']}")
    
    return {
        "summary": summary,
        "exact_match": exact_match,
        "low_rank": low_rank,
        "medium_rank": medium_rank,
        "critical_rank": critical_rank,
        "errors": errors
    }
