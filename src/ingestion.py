import os
import hashlib
import io
import logging
from typing import List, Tuple, Union, Dict, BinaryIO
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for file inputs (supports file paths, BytesIO, and Streamlit UploadedFile)
FileInput = Union[str, io.BytesIO, BinaryIO]

# Security & Limits
MAX_PDF_PAGES = 5          # Limit pages to prevent RAM explosion
Image.MAX_IMAGE_PIXELS = 100_000_000  # Prevent Decompression Bomb (100MP limit)

# Supported formats map
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
SUPPORTED_PDF_TYPES = {".pdf"}

def generate_file_hash(file_input: FileInput) -> str:
    """
    Generates SHA256 hash for file integrity.
    Handles file paths, BytesIO, and Streamlit UploadedFile objects safely.
    """
    hasher = hashlib.sha256()

    try:
        if isinstance(file_input, str):
            with open(file_input, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        else:
            # Handle both BytesIO and Streamlit UploadedFile
            # Check if object has 'tell' method (BytesIO does, UploadedFile doesn't always)
            if hasattr(file_input, 'tell') and hasattr(file_input, 'seek'):
                try:
                    start_pos = file_input.tell()
                    file_input.seek(0)
                    hasher.update(file_input.read())
                    file_input.seek(start_pos)
                except (OSError, io.UnsupportedOperation):
                    # Fallback for objects that don't support tell()
                    file_input.seek(0)
                    hasher.update(file_input.read())
                    file_input.seek(0)
            else:
                # For Streamlit UploadedFile or similar objects
                file_input.seek(0)
                hasher.update(file_input.read())
                file_input.seek(0)  # Reset for next read
            
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Hashing failed: {e}")
        raise

def load_image(file_input: FileInput) -> Image.Image:
    """Loads an image safely with format verification."""
    try:
        # 1. Reset cursor if it's a stream
        if hasattr(file_input, 'seek'):
            file_input.seek(0)
            
        # 2. Open and Verify (Lazy Load)
        image = Image.open(file_input)
        
        # 3. Security Check: Verify it's actually an image
        image.verify() 
        
        # 4. Re-open for processing (Verify closes the file pointer in PIL)
        if hasattr(file_input, 'seek'):
            file_input.seek(0)
        
        image = Image.open(file_input)
            
        # 5. Convert to RGB (standardize format)
        return image.convert("RGB")
        
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image file. PIL could not read it. Details: {e}")

def convert_pdf(file_input: FileInput) -> List[Image.Image]:
    """Converts PDF to images with page limits."""
    try:
        # Enforce page limit to prevent OOM
        # We only grab the first N pages.
        if isinstance(file_input, str):
            return convert_from_path(file_input, dpi=300, last_page=MAX_PDF_PAGES)
        else:
            # Read bytes and reset stream for potential reuse
            file_input.seek(0)
            pdf_bytes = file_input.read()
            file_input.seek(0)  # Reset for potential reuse
            return convert_from_bytes(pdf_bytes, dpi=300, last_page=MAX_PDF_PAGES)
            
    except PDFInfoNotInstalledError:
        raise EnvironmentError(
            "Poppler is not installed. Install it to process PDFs.\n"
            "Windows: Download binary -> Add bin/ to PATH.\n"
            "Mac: brew install poppler\n"
            "Linux: sudo apt install poppler-utils"
        )
    except Exception as e:
        raise RuntimeError(f"PDF Conversion failed: {e}")

def ingest_document(file_input: FileInput, filename: str = "unknown") -> Tuple[List[Image.Image], Dict]:
    """
    Main Entry Point: Ingests a document safely.
    """
    
    # 1. Validate file is not empty
    if isinstance(file_input, str):
        if os.path.getsize(file_input) == 0:
            raise ValueError("Cannot process empty file")
        ext = os.path.splitext(file_input)[1].lower()
        filename = os.path.basename(file_input)
    else:
        # Check for empty files in stream objects
        if hasattr(file_input, 'size') and file_input.size == 0:
            raise ValueError("Cannot process empty file")
        ext = os.path.splitext(filename)[1].lower()

    # 2. Generate Integrity Hash
    file_hash = generate_file_hash(file_input)

    # 3. Processing Logic
    images = []
    file_type = "unknown"

    try:
        if ext in SUPPORTED_IMAGE_TYPES:
            images.append(load_image(file_input))
            file_type = "image"
            
        elif ext in SUPPORTED_PDF_TYPES:
            images = convert_pdf(file_input)
            file_type = "pdf"
            
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    except Exception as e:
        logger.error(f"Failed to ingest {filename}: {e}")
        raise

    if not images:
        raise RuntimeError("File processed but no images were extracted.")

    metadata = {
        "filename": filename,
        "file_type": file_type,
        "file_hash": file_hash,
        "num_pages": len(images),
        "truncated": len(images) == MAX_PDF_PAGES # Flag if we cut off pages
    }

    return images, metadata