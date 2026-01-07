from PIL import Image
from typing import Union
import numpy as np

def preprocess_image(image_input: Union[str, Image.Image]) -> Image.Image:
    """
    Robust preprocessing for AI APIs (Gemini/Google Vision).
    Handles transparency, file types, and resizing safely.
    """
    # 1. Safe Loading
    try:
        if isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input.copy()
        else:
            # Assume it's a file-like object (BytesIO)
            img = Image.open(image_input)
    except Exception as e:
        raise ValueError(f"Could not load image for preprocessing: {e}")

    # Validation: Check for empty images
    if img.width == 0 or img.height == 0:
        raise ValueError("Image has invalid dimensions (width or height is 0)")

    # 2. Handle Transparency (RGBA -> RGB)
    # If we just convert RGBA to RGB, transparent areas become black.
    # We must paste it onto a white background first.
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (255, 255, 255))
        # 3. Mask safety: if image has a mask, use it
        if img.mode == 'P':
            img = img.convert('RGBA')
        
        # Get the alpha channel safely (handles RGBA and LA modes)
        if img.mode == 'RGBA':
            alpha_channel = img.split()[3]  # RGBA has alpha at index 3
        elif img.mode == 'LA':
            alpha_channel = img.split()[1]  # LA has alpha at index 1
        else:
            alpha_channel = None
        
        if alpha_channel:
            background.paste(img, mask=alpha_channel)
        else:
            background.paste(img)
        
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
        
    # 3. Resize if huge (> 2000px) to speed up API upload
    # Gemini 1.5 Flash has a token limit, reducing resolution saves money and time.
    max_dimension = 2000
    if max(img.size) > max_dimension:
        # Calculate aspect ratio to avoid distortion
        scale = max_dimension / max(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        # Use LANCZOS for high-quality downsampling (backward compatible)
        img = img.resize(new_size, Image.LANCZOS)
        
    return img