import os
import hashlib
from pdf2image import convert_from_path
from PIL import Image


SUPPORTED_IMAGE_TYPES = (".jpg", ".jpeg", ".png")
SUPPORTED_PDF_TYPES = (".pdf",)


# Utility: Generate file hash (for future duplicates)
def generate_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Utility: Check file type
def get_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext in SUPPORTED_IMAGE_TYPES:
        return "image"
    elif ext in SUPPORTED_PDF_TYPES:
        return "pdf"
    else:
        raise ValueError("Unsupported file type")


# Load image safely
def load_image(file_path):
    try:
        image = Image.open(file_path).convert("RGB")
        return image
    except Exception as e:
        raise RuntimeError(f"Failed to load image: {e}")


# Convert PDF to images (page-wise)
def convert_pdf_to_images(file_path, dpi=300):
    try:
        images = convert_from_path(file_path, dpi=dpi)
        return images
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {e}")



# Main ingestion function
def ingest_document(file_path):
    """
    Ingests a document and returns:
    - list of PIL Images (page-wise)
    - metadata dictionary
    """

    file_type = get_file_type(file_path)

    metadata = {
        "filename": os.path.basename(file_path),
        "file_type": file_type,
        "file_hash": generate_file_hash(file_path),
    }

    if file_type == "image":
        images = [load_image(file_path)]

    elif file_type == "pdf":
        images = convert_pdf_to_images(file_path)

    else:
        raise ValueError("Unsupported document type")

    if not images:
        raise RuntimeError("No images extracted from document")

    metadata["num_pages"] = len(images)

    return images, metadata
