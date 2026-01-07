import google.generativeai as genai
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
        # 1. Configure the API
        genai.configure(api_key=api_key)
        
        # 2. Select Model
        # 'gemini-2.5-flash' is fast, cheap (free tier), and great at vision.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 3. Create the Prompt
        # We must be very specific so it acts like an OCR engine, not a chat bot.
        prompt = """
        You are an OCR engine. 
        Extract all text from this receipt or invoice image exactly as it appears. 
        Preserve line breaks and relative positioning. 
        Do not explain anything. Just output the raw text.
        """
        
        # 4. Generate Content
        # Gemini handles PIL images natively
        response = model.generate_content([prompt, image])
        
        # 5. Extract Text
        extracted_text = response.text if response.text else ""
        
        # Gemini doesn't give a numerical confidence score like Tesseract.
        # We estimate confidence based on response quality.
        if extracted_text and len(extracted_text.strip()) > 0:
            confidence = 95.0
        else:
            confidence = 0.0
            extracted_text = "Warning: No text extracted from image."
        
        return extracted_text, confidence

    except ValueError as e:
        # API key or configuration errors
        return f"Configuration Error: {str(e)}", 0.0
    except Exception as e:
        # Catch-all for other errors (network, API limits, etc.)
        return f"OCR Failed: {str(e)}", 0.0