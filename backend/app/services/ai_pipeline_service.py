import json
import csv
import os
import requests
from typing import Dict, Any, List
import logging
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Azure Document Intelligence client
def get_azure_client() -> DocumentIntelligenceClient:
    """Get Azure Document Intelligence client instance"""
    if not settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or not settings.AZURE_DOCUMENT_INTELLIGENCE_API_KEY:
        raise ValueError("Azure Document Intelligence credentials are not configured")
    
    return DocumentIntelligenceClient(
        endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_API_KEY)
    )

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
    """Extract family coins amount from receipt image using Azure Document Intelligence"""
    try:
        # Initialize Azure Document Intelligence client
        client = get_azure_client()
        
        if not settings.AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID:
            raise ValueError("Azure Document Intelligence model ID is not configured")
        
        # Open the image file and analyze with custom model
        with open(image_path, "rb") as f:
            # Start the analysis process using the custom trained model
            poller = client.begin_analyze_document(
                model_id=settings.AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID,
                body=f
            )
        
        # Wait for the result
        result = poller.result()
        
        # Dictionary to hold extracted data
        extracted_data = {}
        family_coins_value = None
        family_coins_confidence = None
        matched_field_name = None
        
        # Iterate through the documents found
        for document in result.documents:
            logger.debug(f"      📄 Document type: {document.doc_type}")
            
            # Extract fields from the custom model
            for field_name, field in document.fields.items():
                # Get the text content and confidence score
                value = field.content if field.content else None
                confidence = field.confidence if field.confidence else 0.0
                
                extracted_data[field_name] = {
                    "value": value,
                    "confidence": confidence
                }
                
                # Look for Family Coins field (case-insensitive matching)
                field_name_lower = field_name.lower()
                if "family" in field_name_lower and "coin" in field_name_lower:
                    if value:
                        # Try to extract numeric value from the field
                        try:
                            # Remove any non-numeric characters except minus sign
                            import re
                            numeric_str = re.sub(r'[^\d-]', '', str(value))
                            if numeric_str:
                                family_coins_value = int(numeric_str)
                                family_coins_confidence = confidence
                                matched_field_name = field_name
                                logger.debug(f"      ✅ Found Family Coins in field '{field_name}': {family_coins_value} (Confidence: {confidence:.2%})")
                        except (ValueError, TypeError):
                            logger.warning(f"      ⚠️  Could not parse Family Coins value from field '{field_name}': {value}")
        
        # If Family Coins was found, return it
        if family_coins_value is not None:
            return {
                "success": True,
                "family_coins": family_coins_value,
                "raw_response": json.dumps(extracted_data, indent=2),
                "confidence": family_coins_confidence,
                "matched_field": matched_field_name
            }
        
        # If no Family Coins found, check if we have any data at all
        if extracted_data:
            logger.warning(f"      ⚠️  Family Coins field not found in extracted data. Available fields: {list(extracted_data.keys())}")
            return {
                "success": False,
                "family_coins": None,
                "raw_response": json.dumps(extracted_data, indent=2),
                "available_fields": list(extracted_data.keys())
            }
        
        # No data extracted at all
        return {
            "success": False,
            "family_coins": None,
            "raw_response": "No data extracted from document",
            "available_fields": []
        }
            
    except ValueError as e:
        logger.error(f"   ❌ Configuration error: {e}")
        return {
            "success": False,
            "family_coins": None,
            "raw_response": f"Configuration error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"   ❌ Azure Document Intelligence API error: {e}")
        return {
            "success": False,
            "family_coins": None,
            "raw_response": f"Azure API error: {str(e)}"
        }

def _normalize_csv_key(key: str) -> str:
    """Convert snake_case to camelCase for CSV column names"""
    parts = key.strip().split("_")
    if len(parts) == 1:
        return parts[0].lower()
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load dataset from JSON or CSV file. Returns list of dicts with camelCase keys."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON file must contain an array of objects")
        return data
    
    if ext == ".csv":
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            raise ValueError("CSV file is empty or has no data rows")
        
        # Normalize keys: support both camelCase and snake_case
        # Map common variations to expected camelCase keys
        key_aliases = {
            "receiptnumber": "receiptNumber",
            "receipt_number": "receiptNumber",
            "receiptphotourl": "receiptPhotoUrl",
            "receipt_photo_url": "receiptPhotoUrl",
            "touser": "toUser",
            "to_user": "toUser",
            "frommerchant": "fromMerchant",
            "from_merchant": "fromMerchant",
            "referenceid": "referenceId",
            "reference_id": "referenceId",
            "coins": "coins",
        }
        
        result = []
        for row in rows:
            normalized = {}
            for k, v in row.items():
                key_lower = k.strip().lower().replace(" ", "").replace("-", "")
                val = v.strip() if isinstance(v, str) else v
                if key_lower in key_aliases:
                    target_key = key_aliases[key_lower]
                    normalized[target_key] = val
                else:
                    camel_key = _normalize_csv_key(k) if "_" in k or " " in k else k
                    normalized[camel_key] = val
            # Parse coins as int (required by pipeline)
            if "coins" not in normalized:
                normalized["coins"] = 0
            else:
                try:
                    normalized["coins"] = int(float(str(normalized["coins"]).replace(",", "")))
                except (ValueError, TypeError):
                    normalized["coins"] = 0
            result.append(normalized)
        
        return result
    
    raise ValueError(f"Unsupported file format: {ext}. Use .json or .csv")


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
    """Process the dataset file (JSON or CSV) and extract family coins from images"""
    
    logger.info(f"📂 Loading dataset from: {file_path}")
    
    # Load dataset (supports JSON and CSV)
    dataset = load_dataset(file_path)
    
    total_entries = len(dataset)
    logger.info(f"📊 Found {total_entries} entries to process")
    
    # Initialize result structure
    exact_match = []
    low_rank = []
    medium_rank = []
    critical_rank = []
    errors = []
    no_image = []
    
    processed = 0
    
    # Process each entry
    for entry_idx, entry in enumerate(dataset, 1):
        try:
            receipt_number = entry.get("receiptNumber", f"entry_{entry_idx}")
            receipt_photo_url = entry.get("receiptPhotoUrl", "")
            dataset_coins = entry.get("coins", 0)
            to_user = entry.get("toUser", "Unknown")
            from_merchant = entry.get("fromMerchant")
            reference_id = entry.get("referenceId") or entry.get("reference_id")
            
            # Report current entry for live frontend updates (at start of processing)
            if analysis_id:
                try:
                    from app.services.analysis_service import AnalysisService
                    progress_pct = ((entry_idx - 1) / total_entries) * 100
                    await AnalysisService.update_analysis_status(
                        analysis_id,
                        "processing",
                        progress=progress_pct,
                        current_entry={
                            "receipt_number": receipt_number,
                            "to_user": to_user,
                            "entry_index": entry_idx,
                            "total_entries": total_entries,
                            "reference_id": reference_id
                        }
                    )
                except Exception as e:
                    logger.warning(f"      ⚠️  Failed to update current entry: {e}")
            
            logger.info(f"   🔄 [{entry_idx}/{total_entries}] Processing: {receipt_number}")
            logger.info(f"      📊 Dataset coins: {dataset_coins}")
            
            if not receipt_photo_url:
                logger.warning(f"      ⚠️  No receipt photo URL, skipping")
                no_image.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "from_merchant": from_merchant,
                    "dataset_coins": dataset_coins,
                    "reference_id": reference_id
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
                    "dataset_coins": dataset_coins,
                    "reference_id": reference_id
                })
                continue
            
            logger.info(f"      ✅ Image downloaded: {image_path}")
            
            # Extract family coins using Azure Document Intelligence
            logger.info(f"      🤖 Analyzing image with Azure Document Intelligence...")
            extraction_result = extract_family_coins_from_image(image_path)
            
            if not extraction_result["success"] or extraction_result["family_coins"] is None:
                logger.warning(f"      ⚠️  Could not extract family coins")
                errors.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "error": f"Failed to extract family coins: {extraction_result.get('raw_response', 'Unknown error')}",
                    "receipt_photo_url": receipt_photo_url,
                    "dataset_coins": dataset_coins,
                    "reference_id": reference_id
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
                "azure_raw_response": extraction_result.get("raw_response"),
                "extraction_confidence": extraction_result.get("confidence")
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
                "dataset_coins": entry.get("coins", 0),
                "reference_id": entry.get("referenceId") or entry.get("reference_id")
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
        "error_count": len(errors),
        "no_image_count": len(no_image)
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
    logger.info(f"      No Image: {summary['no_image_count']}")
    
    return {
        "summary": summary,
        "exact_match": exact_match,
        "low_rank": low_rank,
        "medium_rank": medium_rank,
        "critical_rank": critical_rank,
        "errors": errors,
        "no_image": no_image
    }
