# OCR and structured data extraction using Google Gemini AI
# This module handles text extraction from receipt/invoice images
# and parses the extracted data into structured JSON format matching database schema

from typing import Dict
from google import genai
from PIL import Image
import json
import re

# Import normalizer for data standardization after Gemini extraction
from .extraction.normalizer import normalize_extracted_fields
from .extraction.currency_converter import convert_to_usd

def run_ocr_and_extract_bill(image: Image.Image, api_key: str) -> Dict:
    """Extract structured bill data from image using Gemini AI.
    
    This function combines OCR and data extraction in a single API call.
    Gemini analyzes the image and returns structured JSON matching our schema.
    
    Args:
        image: PIL Image object of receipt or invoice
        api_key: Google Gemini API key for authentication
    
    Returns:
        Dictionary containing extracted bill data with normalized fields,
        or error dictionary if extraction fails.
    
    Process:
        1. Validate inputs (API key and image)
        2. Send image to Gemini with structured prompt
        3. Parse JSON response
        4. Normalize data types and add calculated fields
    """
    # Early validation to fail fast without wasting API quota
    if not api_key or not api_key.strip():
        return {"error": "API key is required"}

    if not isinstance(image, Image.Image):
        return {"error": "Invalid image provided"}

    client = genai.Client(api_key=api_key)

    # Enforce deterministic JSON output to prevent Gemini hallucinations and markdown wrapping
    prompt = (
        "Extract receipt/invoice data.\n"
        "Return ONLY valid JSON.\n"
        "Do NOT include explanations.\n"
        "If a field is missing, use defaults.\n\n"
        "Schema:\n"
        "{"
        "\"invoice_number\": string,"  # Invoice/Receipt ID or number
        "\"vendor_name\": string,"  # Store or business name
        "\"purchase_date\": \"YYYY-MM-DD\","  # Date format for database DATE type
        "\"purchase_time\": \"HH:MM\","  # Optional time of purchase
        "\"currency\": \"USD\","  # ISO currency code (USD, INR, EUR, etc.)
        "\"items\": ["  # Array of line items
        " {\"s_no\": int, \"item_name\": string, \"quantity\": number, "
        "  \"unit_price\": number, \"item_total\": number}"
        "],"
        "\"tax_amount\": number,"  # Total tax amount
        "\"total_amount\": number,"  # Grand total including tax
        "\"payment_method\": string"  # Cash, Card, UPI, etc.
        "}"
    )


    # Make API request to Gemini with image and prompt
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Fast model optimized for document understanding
            contents=[prompt, image],  # Send both text prompt and image
            config={
                "temperature": 0.0,  # Deterministic output for consistent extraction
                "max_output_tokens": 4096,  # Enough for large receipts with many items
                "response_mime_type": "application/json"  # Force JSON response format
            },
        )

    except Exception as e:
        # API call failed - network error, quota exceeded, invalid key, etc.
        return {"error": f"Gemini request failed: {e}"}

    # Parse JSON response from Gemini
    try:
        bill_data = json.loads(response.text)
    except Exception as e:
        # Gemini returned malformed JSON - return error with partial response
        return {
            "error": "Gemini returned invalid JSON (hard failure)",
            "raw_response": response.text[:1000]  # First 1000 chars for debugging
        }

    # NORMALIZATION STEP - Use normalizer module to standardize all fields
    # This ensures consistent formatting for database storage and validation
    # Normalizer handles:
    #   - Date/time format conversion (YYYY-MM-DD, HH:MM:SS)
    #   - Numeric conversions (string to float, rounding)
    #   - Field length constraints (VARCHAR limits)
    #   - Default values for missing fields
    #   - Type safety (safe conversions with fallbacks)
    normalized_data = normalize_extracted_fields(bill_data)
    # Ensure backward compatibility for converter expecting 'tax' key
    if "tax" not in normalized_data:
        normalized_data["tax"] = normalized_data.get("tax_amount", 0)

    # Currency conversion: convert monetary fields to USD while preserving originals
    converted_data = convert_to_usd(normalized_data)
    
    # Return fully normalized and currency-converted data ready for validation/storage
    return converted_data
