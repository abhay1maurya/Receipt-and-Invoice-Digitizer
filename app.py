import streamlit as st
from PIL import Image
import os
import tempfile

# Import your backend functions
# from src.preprocessing import preprocess_image
# from src.ocr import run_ocr


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Receipt & Invoice Digitizer",
    layout="wide"
)

# -----------------------------
# HEADER
# -----------------------------
st.title("📄 Receipt & Invoice Digitizer")
st.caption("Milestone 1: Document Ingestion & OCR")

st.divider()

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload a receipt or invoice (Image or PDF)",
    type=["jpg", "jpeg", "png", "pdf"]
)

if uploaded_file is None:
    st.info("Please upload an image or PDF to begin.")
    st.stop()

# -----------------------------
# SAVE TEMP FILE
# -----------------------------
with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    tmp_file.write(uploaded_file.read())
    temp_path = tmp_file.name

st.success("File uploaded successfully.")

# -----------------------------
# DISPLAY ORIGINAL IMAGE (IMAGE ONLY)
# -----------------------------
if uploaded_file.type != "application/pdf":
    original_image = Image.open(temp_path)

    st.subheader("Original Document")
    st.image(original_image, use_container_width=True)

else:
    st.warning("PDF uploaded. Image preview will be added later.")

# -----------------------------
# PREPROCESS IMAGE
# -----------------------------
st.subheader("Preprocessed Image")

try:
    processed_img = preprocess_image(temp_path)

    st.image(processed_img, use_container_width=True)
    st.success("Image preprocessing completed.")

except Exception as e:
    st.error("Preprocessing failed.")
    st.exception(e)
    st.stop()

# -----------------------------
# OCR
# -----------------------------
st.subheader("OCR Output (Raw Text)")

try:
    ocr_text = run_ocr(processed_img)

    st.text_area(
        "Extracted Text",
        ocr_text,
        height=300
    )

    st.success("OCR completed successfully.")

except Exception as e:
    st.error("OCR failed.")
    st.exception(e)

# -----------------------------
# CLEANUP
# -----------------------------
os.remove(temp_path)
