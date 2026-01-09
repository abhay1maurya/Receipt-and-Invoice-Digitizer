from google import genai
from typing import Tuple
from PIL import Image

def run_ocr(image: Image.Image, api_key: str) -> Tuple[str, float]:
    """
    Extracts text using Google Gemini 2.5 Flash (via AI Studio).
    
    Args:
        image (PIL.Image): The input image.
        api_key (str): Google Gemini API key.
        
    Returns:
        tuple: (extracted_text (str), confidence (float))
    """
    # Validate inputs
    if not api_key or not api_key.strip():
        return "Error: API key is required.", 0.0
    
    if not isinstance(image, Image.Image):
        return "Error: Invalid image format. Expected PIL.Image.", 0.0
    
    if image.width == 0 or image.height == 0:
        return "Error: Image has invalid dimensions.", 0.0

    try:
        # 1. New Client API
        client = genai.Client(api_key=api_key)

        # 2. Prompt (strict OCR behavior)
        prompt = """
        You are a strict OCR engine.
        Do NOT summarize, interpret, or correct text.
        Do NOT fix spelling or grammar.
        Preserve original casing, numbers, symbols, and line breaks.
        If text is unclear, output it as-is.
        Return ONLY the extracted text.

        """

        # 3. Generate content (new SDK)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image],
            config={
                "temperature": 0.0,
                "max_output_tokens": 2048
            }
        )

        # 4. Extract Text
        extracted_text = response.text or ""

        def estimate_confidence(text: str) -> float:
            if not text or len(text.strip()) < 20:
                return 10.0

            length_score = min(len(text) / 500, 1.0) * 40
            number_score = 30 if any(char.isdigit() for char in text) else 0
            symbol_score = 20 if any(sym in text for sym in ["$", "₹", "€"]) else 0

            return round(length_score + number_score + symbol_score, 1)

        confidence = estimate_confidence(extracted_text)

        return extracted_text, confidence

    except Exception as e:
        # Network issues, config errors, quota, SDK errors
        return f"OCR Failed: {e}", 0.0