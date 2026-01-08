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
        generation_config = {
            'temperature': 0.0,
            'top_p':0.1,
            "max_output_tokens": 2048
        }
        # 1. Configure the API
        genai.configure(api_key=api_key)
        
        # 2. Select Model
        # 'gemini-2.5-flash' is fast, cheap (free tier), and great at vision.
        model = genai.GenerativeModel(model_name='gemini-2.5-flash', generation_config=generation_config)
        
        # 3. Create the Prompt
        # We must be very specific so it acts like an OCR engine, not a chat bot.
        prompt = """
        You are a strict OCR engine.
        Do NOT summarize, interpret, or correct text.
        Do NOT fix spelling or grammar.
        Preserve original casing, numbers, symbols, and line breaks.
        If text is unclear, output it as-is.
        Return ONLY the extracted text.

        """
        
        # 4. Generate Content
        # Gemini handles PIL images natively
        response = model.generate_content([prompt, image])
        
        # 5. Extract Text
        extracted_text = response.text if response.text else ""
        
        return extracted_text

    except genai.types.BlockedPromptException:
        return "Error: Prompt blocked by safety filters.", 0.0

    except TimeoutError:
        return "Error: OCR request timed out.", 0.0

    except ValueError as e:
        # API key, config, or invalid input
        return f"Configuration Error: {e}", 0.0

    except Exception as e:
        # Network issues, quota, unknown Gemini errors
        return f"OCR Failed: {e}", 0.0