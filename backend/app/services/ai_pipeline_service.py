import json
import csv
import os
import re
import requests
from typing import Dict, Any, List, Optional
import logging
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

logger = logging.getLogger(__name__)

# Prebuilt Invoice model ID – has TotalDiscount, InvoiceTotal, SubTotal, TotalTax, AmountDue
PREBUILT_INVOICE_MODEL_ID = "prebuilt-invoice"

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


def _parse_total_value(value: Any) -> Optional[float]:
    """Parse Total from receipt (handles '1,200.00', 1200, etc.)"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace(" ", "")
    # Remove currency symbols and leave digits, minus, dot
    s = re.sub(r"[^\d.\-]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def extract_total_from_receipt(image_path: str) -> Dict[str, Any]:
    """Extract InvoiceTotal, TotalDiscount, SubTotal, and TotalTax from image
    using Azure Prebuilt Invoice model (prebuilt-invoice).

    The prebuilt-invoice model provides:
      - InvoiceTotal  : the headline total on the document
      - TotalDiscount : discount amount (if present)
      - SubTotal      : subtotal before tax/discount
      - TotalTax      : tax amount

    Comparison value returned as 'total':
      - If TotalDiscount exists : InvoiceTotal - TotalDiscount
      - Otherwise               : InvoiceTotal as-is
    """
    try:
        client = get_azure_client()
        with open(image_path, "rb") as f:
            poller = client.begin_analyze_document(model_id=PREBUILT_INVOICE_MODEL_ID, body=f)
        result = poller.result()

        extracted_data = {}
        invoice_total = None
        invoice_total_confidence = None
        total_discount = None
        sub_total = None
        total_tax = None
        amount_due = None

        for document in result.documents:
            logger.debug(f"      📄 Document type: {document.doc_type}")
            logger.debug(f"      📋 Available fields: {list(document.fields.keys())}")

            for field_name, field in document.fields.items():
                value = getattr(field, "content", None) or getattr(field, "value", None)
                confidence = getattr(field, "confidence", None) or 0.0
                extracted_data[field_name] = {"value": value, "confidence": confidence}

                # Log every field for debugging
                logger.debug(f"      🔍 Field '{field_name}': {value}")

                if field_name == "InvoiceTotal":
                    parsed = _parse_total_value(value)
                    if parsed is not None:
                        invoice_total = parsed
                        invoice_total_confidence = confidence
                        logger.info(f"      ✅ InvoiceTotal: {invoice_total} (confidence: {confidence:.2%})")

                elif field_name == "TotalDiscount":
                    parsed = _parse_total_value(value)
                    if parsed is not None:
                        total_discount = parsed
                        logger.info(f"      ✅ TotalDiscount: {total_discount} (confidence: {confidence:.2%})")

                elif field_name == "SubTotal":
                    parsed = _parse_total_value(value)
                    if parsed is not None:
                        sub_total = parsed
                        logger.info(f"      ✅ SubTotal: {sub_total} (confidence: {confidence:.2%})")

                elif field_name == "TotalTax":
                    parsed = _parse_total_value(value)
                    if parsed is not None:
                        total_tax = parsed
                        logger.info(f"      ✅ TotalTax: {total_tax} (confidence: {confidence:.2%})")

                elif field_name == "AmountDue":
                    parsed = _parse_total_value(value)
                    if parsed is not None:
                        amount_due = parsed
                        logger.info(f"      ✅ AmountDue: {amount_due} (confidence: {confidence:.2%})")

        # Determine the comparison value
        if invoice_total is not None:
            if total_discount is not None and total_discount > 0:
                net_amount = invoice_total - total_discount
                logger.info(f"      💰 InvoiceTotal ({invoice_total}) - TotalDiscount ({total_discount}) = {net_amount}")
            else:
                net_amount = invoice_total
                logger.info(f"      💰 No discount found, using InvoiceTotal: {net_amount}")

            return {
                "success": True,
                "total": net_amount,
                "raw_total": invoice_total,
                "subtotal": sub_total,
                "tax": total_tax,
                "discount": total_discount,
                "amount_due": amount_due,
                "raw_response": json.dumps(extracted_data, indent=2),
                "confidence": invoice_total_confidence,
            }

        # Fallback: if InvoiceTotal not found but AmountDue exists
        if amount_due is not None:
            logger.info(f"      💰 InvoiceTotal not found, falling back to AmountDue: {amount_due}")
            return {
                "success": True,
                "total": amount_due,
                "raw_total": amount_due,
                "subtotal": sub_total,
                "tax": total_tax,
                "discount": total_discount,
                "amount_due": amount_due,
                "raw_response": json.dumps(extracted_data, indent=2),
                "confidence": None,
            }

        if extracted_data:
            logger.warning(f"      ⚠️  InvoiceTotal not found. Available fields: {list(extracted_data.keys())}")
            return {
                "success": False,
                "total": None,
                "raw_response": json.dumps(extracted_data, indent=2),
                "available_fields": list(extracted_data.keys()),
            }

        return {
            "success": False,
            "total": None,
            "raw_response": "No data extracted from document",
            "available_fields": [],
        }

    except ValueError as e:
        logger.error(f"   ❌ Azure Document Intelligence configuration error: {e}")
        return {"success": False, "total": None, "raw_response": str(e)}
    except Exception as e:
        logger.error(f"   ❌ Prebuilt Invoice API error: {e}")
        return {"success": False, "total": None, "raw_response": str(e)}

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
            "fiatamount": "fiatAmount",
            "fiat_amount": "fiatAmount",
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
            for num_key in ("coins", "fiatAmount"):
                if num_key not in normalized:
                    normalized[num_key] = 0
                else:
                    try:
                        normalized[num_key] = int(float(str(normalized[num_key]).replace(",", "")))
                    except (ValueError, TypeError):
                        normalized[num_key] = 0
            result.append(normalized)
        
        return result
    
    raise ValueError(f"Unsupported file format: {ext}. Use .json or .csv")


def categorize_difference(difference: float) -> str:
    """Categorize the difference between expected fiat amount and extracted invoice total"""
    diff_int = int(round(difference))
    if diff_int == 0:
        return "exact_match"
    if abs(diff_int) <= 10:
        return "low_rank"
    if abs(diff_int) <= 30:
        return "medium_rank"
    return "critical_rank"

def _get_fiat_amount(entry: Dict[str, Any]) -> int:
    """Expected amount from JSON/CSV: fiatAmount preferred, else coins."""
    v = entry.get("fiatAmount") if entry.get("fiatAmount") is not None else entry.get("coins", 0)
    if isinstance(v, (int, float)):
        return int(round(v))
    try:
        return int(float(str(v).replace(",", "")))
    except (ValueError, TypeError):
        return 0


async def process_dataset(file_path: str, analysis_id: str = None) -> Dict[str, Any]:
    """Process the dataset file (JSON or CSV): extract Total from receipts and compare with fiatAmount."""
    
    logger.info(f"📂 Loading dataset from: {file_path}")
    
    dataset = load_dataset(file_path)
    total_entries = len(dataset)
    logger.info(f"📊 Found {total_entries} entries to process")
    
    exact_match = []
    low_rank = []
    medium_rank = []
    critical_rank = []
    errors = []
    no_image = []
    processed = 0

    for entry_idx, entry in enumerate(dataset, 1):
        image_path: Optional[str] = None
        try:
            receipt_number = entry.get("receiptNumber", f"entry_{entry_idx}")
            receipt_photo_url = entry.get("receiptPhotoUrl", "")
            fiat_amount = _get_fiat_amount(entry)
            to_user = entry.get("toUser", "Unknown")
            from_merchant = entry.get("fromMerchant")
            reference_id = entry.get("referenceId") or entry.get("reference_id")
            dataset_coins = entry.get("coins", 0)  # keep for display/backward compat

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

            logger.info(f"   🔄 [{entry_idx}/{total_entries}] Processing receipt #{receipt_number}")
            logger.info(f"      📊 Expected fiat amount (from dataset): {fiat_amount}")

            if not receipt_photo_url:
                logger.warning(f"      ⚠️  No receipt photo URL, skipping")
                no_image.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "from_merchant": from_merchant,
                    "dataset_coins": fiat_amount,
                    "reference_id": reference_id
                })
                continue

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
                    "dataset_coins": fiat_amount,
                    "reference_id": reference_id
                })
                continue

            logger.info(f"      ✅ Image downloaded: {image_path}")
            logger.info(f"      🤖 Extracting InvoiceTotal/TotalDiscount via Prebuilt Invoice model...")
            extraction_result = extract_total_from_receipt(image_path)

            if not extraction_result["success"] or extraction_result.get("total") is None:
                errors.append({
                    "entry_id": str(entry_idx),
                    "receipt_number": receipt_number,
                    "to_user": to_user,
                    "error": f"Failed to extract InvoiceTotal from document: {extraction_result.get('raw_response', 'Unknown error')}",
                    "receipt_photo_url": receipt_photo_url,
                    "dataset_coins": fiat_amount,
                    "reference_id": reference_id
                })
                continue

            extracted_total = extraction_result["total"]
            extracted_int = int(round(extracted_total))
            raw_total = extraction_result.get("raw_total")
            subtotal = extraction_result.get("subtotal")
            tax = extraction_result.get("tax")
            discount = extraction_result.get("discount")
            
            if discount and discount > 0:
                logger.info(f"      💰 Invoice: Total={raw_total}, Discount={discount}, Net={extracted_total}")
            else:
                logger.info(f"      💰 Invoice total (extracted): {extracted_total}")

            difference = fiat_amount - extracted_int
            logger.info(f"      📈 Difference (fiat amount - invoice total): {difference}")

            category = categorize_difference(difference)
            logger.info(f"      📈 Category: {category.upper()} | Amount difference: {difference}")

            entry_data = {
                "entry_id": str(entry_idx),
                "receipt_number": receipt_number,
                "to_user": to_user,
                "from_merchant": from_merchant,
                "dataset_coins": fiat_amount,
                "extracted_family_coins": extracted_int,
                "difference": difference,
                "category": category,
                "receipt_photo_url": receipt_photo_url,
                "image_path": image_path,
                "azure_raw_response": extraction_result.get("raw_response"),
                "extraction_confidence": extraction_result.get("confidence"),
                "raw_total": raw_total,
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount
            }

            if category == "exact_match":
                exact_match.append(entry_data)
            elif category == "low_rank":
                low_rank.append(entry_data)
            elif category == "medium_rank":
                medium_rank.append(entry_data)
            elif category == "critical_rank":
                critical_rank.append(entry_data)

            processed += 1
            progress = (entry_idx / total_entries) * 100
            logger.info(f"      ✅ Progress: {progress:.1f}% ({processed}/{total_entries} processed)")

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
                "dataset_coins": _get_fiat_amount(entry),
                "reference_id": entry.get("referenceId") or entry.get("reference_id")
            })
        finally:
            # Remove downloaded receipt image to avoid growing disk usage.
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.debug(f"      🧹 Removed temporary receipt image: {image_path}")
                except Exception as e:
                    logger.warning(f"      ⚠️ Failed to remove temporary image {image_path}: {e}")
    
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
    
    logger.info("✅ Invoice processing complete (Prebuilt Invoice model)")
    logger.info("   📊 Summary:")
    logger.info(f"      Total entries: {summary['total_entries']}")
    logger.info(f"      Processed: {summary['processed']}")
    logger.info(f"      Exact match (fiat = invoice total): {summary['exact_match_count']}")
    logger.info(f"      Low rank: {summary['low_rank_count']}")
    logger.info(f"      Medium rank: {summary['medium_rank_count']}")
    logger.info(f"      Critical rank: {summary['critical_rank_count']}")
    logger.info(f"      Errors: {summary['error_count']}")
    logger.info(f"      No image: {summary['no_image_count']}")
    
    return {
        "summary": summary,
        "exact_match": exact_match,
        "low_rank": low_rank,
        "medium_rank": medium_rank,
        "critical_rank": critical_rank,
        "errors": errors,
        "no_image": no_image
    }
