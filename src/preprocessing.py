import cv2
import numpy as np
from PIL import Image

def preprocess_image(image_input):
    """
    Prepares an image for OCR by applying grayscale, denoising, and thresholding.
    
    Args:
        image_input (str or PIL.Image): File path or PIL Image object.
        
    Returns:
        PIL.Image: The processed image ready for OCR.
    """
    # 1. Load Image (Handle both path string and PIL Object)
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, Image.Image):
        # Convert PIL to OpenCV format (RGB -> BGR)
        img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
    else:
        raise ValueError("Unsupported image format. Use path string or PIL Image.")

    # 2. Grayscale Conversion
    # Color confuses OCR. We want luminance only.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Rescaling (DPI Adjustment)
    # Tesseract works best at 300 DPI. If the image is small, upscale it.
    height, width = gray.shape
    if width < 1000:
        scale_factor = 2
        gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # 4. Noise Removal (Denoising)
    # Receipts are often grainy. Median blur smooths this out while keeping edges.
    denoised = cv2.medianBlur(gray, 3)

    # 5. Thresholding (Binarization)
    # This is the most critical step. It separates text (foreground) from paper (background).
    # We use Otsu's binarization which automatically finds the optimal threshold value.
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 6. Convert back to PIL for Tesseract compatibility
    final_image = Image.fromarray(binary)
    return final_image