import pytesseract
from PIL import Image
import sys
import os

def run_ocr(image):
    """
    Extracts text from a processed image using Tesseract OCR.

    Args:
        image (PIL.Image): The processed image.

    Returns:
        tuple: (extracted_text (str), average_confidence (float))
    """
    try:
        # 1. Get detailed data (text + confidence scores)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # 2. Extract Text
        # Filter out empty strings/whitespace results
        text_list = [word for word in data['text'] if word.strip()]
        full_text = " ".join(text_list)
        
        # 3. Calculate Confidence
        # 'conf' is a list of integers (0-100). Filter out -1 (which means no text found in block)
        confidences = [int(c) for c in data['conf'] if int(c) != -1]
        
        if not confidences:
            return "", 0.0
            
        avg_confidence = sum(confidences) / len(confidences)
        
        return full_text, round(avg_confidence, 2)

    except pytesseract.TesseractNotFoundError:
        raise EnvironmentError("Tesseract is not installed or not found in PATH.")
    except Exception as e:
        return f"Error during OCR: {str(e)}", 0.0