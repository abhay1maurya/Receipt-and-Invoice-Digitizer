import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables (Create a .env file with GOOGLE_API_KEY="AIza...")
load_dotenv()

def run_ocr(image):
    """
    Extracts text using Google Gemini 1.5 Flash (via AI Studio).
    
    Args:
        image (PIL.Image): The input image.
        
    Returns:
        tuple: (full_text (str), confidence (float))
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return "Error: Missing GOOGLE_API_KEY in .env file.", 0.0

    try:
        # 1. Configure the API
        genai.configure(api_key=api_key)
        
        # 2. Select Model
        # 'gemini-1.5-flash' is fast, cheap (free tier), and great at vision.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 3. Create the Prompt
        # We must be very specific so it acts like an OCR engine, not a chat bot.
        prompt = """
        You are an OCR engine. 
        Extract all text from this receipt image exactly as it appears. 
        Preserve line breaks and relative positioning. 
        Do not explain anything. Just output the raw text.
        """
        
        # 4. Generate Content
        # Gemini handles PIL images natively
        response = model.generate_content([prompt, image])
        
        # 5. Extract Text
        extracted_text = response.text
        
        # Gemini doesn't give a numerical confidence score like Tesseract.
        # We assume high confidence if it generates a non-empty response.
        return extracted_text, 95.0

    except Exception as e:
        return f"Gemini OCR Failed: {str(e)}", 0.0