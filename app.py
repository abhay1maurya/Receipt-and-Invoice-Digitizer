import streamlit as st
from PIL import Image
import os
import tempfile


# PAGE CONFIG
st.set_page_config(
    page_title="Receipt & Invoice Digitizer",
    layout="wide"
)

# HEADER
st.title("📄 Receipt & Invoice Digitizer")
st.caption("Milestone 1: Document Ingestion & OCR")

st.divider()

# FILE UPLOAD
uploaded_file = st.file_uploader(
    "Upload a receipt or invoice (Image or PDF)",
    type=["jpg", "jpeg", "png", "pdf"]
)

if uploaded_file is None:
    st.info("Please upload an image or PDF to begin.")
    st.stop()

# SAVE TEMP FILE
with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    tmp_file.write(uploaded_file.read())
    temp_path = tmp_file.name

st.success("File uploaded successfully.")

# DISPLAY ORIGINAL IMAGE (IMAGE ONLY)
if uploaded_file.type != "application/pdf":
    original_image = Image.open(temp_path)

    st.subheader("Original Document")
    st.image(original_image, use_container_width=True)

else:
    st.warning("PDF uploaded. Image preview will be added later.")


os.remove(temp_path)
