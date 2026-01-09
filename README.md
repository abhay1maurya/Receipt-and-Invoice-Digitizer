

# 📥 Ingestion Module (`ingestion.py`)

## Overview

The **ingestion module** is the entry point of the document processing pipeline.
Its job is to **safely accept uploaded files (images or PDFs)** and convert them into a **standardized list of PIL `Image` objects** that downstream modules (preprocessing & OCR) can reliably consume.

This module is intentionally strict, defensive, and security-aware.

---

## Responsibilities

The ingestion layer guarantees the following:

* ✅ Accepts multiple input types (file paths, Streams, Streamlit uploads)
* ✅ Detects and validates file formats
* ✅ Converts PDFs → images (page-by-page)
* ✅ Standardizes all outputs to **RGB PIL Images**
* ✅ Generates cryptographic file hashes (duplicate detection)
* ✅ Protects against decompression bombs & memory exhaustion
* ✅ Limits resource usage (page caps, pixel caps)

---

## Supported Inputs

### File Input Types

```python
Union[str, io.BytesIO, BinaryIO]
```

| Input        | Example              | Source           |
| ------------ | -------------------- | ---------------- |
| File path    | `"invoice.pdf"`      | Local disk       |
| BytesIO      | `io.BytesIO(...)`    | In-memory buffer |
| UploadedFile | `st.file_uploader()` | Streamlit        |

---

## Supported Formats

### Images

```
.jpg .jpeg .png .bmp .tiff .webp
```

### PDFs

```
.pdf
```

Unsupported formats fail **early and loudly**.

---

## Security & Resource Limits

| Protection         | Value       | Purpose                            |
| ------------------ | ----------- | ---------------------------------- |
| `MAX_IMAGE_PIXELS` | 100,000,000 | Prevent decompression bomb attacks |
| `MAX_PDF_PAGES`    | 5           | Prevent OOM & excessive processing |
| Hashing            | SHA256      | Detect duplicate uploads           |
| `image.verify()`   | Enabled     | Detect corrupted / fake images     |

---

## Module Components

### 1️⃣ File Hash Generation

**Function:** `generate_file_hash()`

Creates a **SHA256 fingerprint** of file content.

**Why this matters:**

* Detects duplicate uploads
* Enables safe session-state resets
* Prevents mixing results across files

**Key design decisions:**

* Chunked reading (8KB) → memory safe
* Stream cursor reset → safe reuse of file objects

---

### 2️⃣ Image Loader

**Function:** `load_image()`

Safely loads and validates image files.

**Pipeline:**

```
seek(0)
↓
Image.open()        (lazy metadata load)
↓
image.verify()     (structure validation)
↓
seek(0)
↓
Image.open()        (real load)
↓
convert("RGB")     (standard output)
```

**Why RGB standardization?**

* Removes transparency ambiguity
* Ensures predictable preprocessing
* Simplifies OCR behavior

---

### 3️⃣ PDF Conversion

**Function:** `convert_pdf()`

Converts PDFs into **high-quality PIL Images** using Poppler.

**Key settings:**

* DPI = **300** (OCR-optimized)
* Page limit = **5**
* Supports both file paths and byte streams

**Why limit pages?**

* Prevents memory exhaustion
* Prevents runaway OCR costs
* Keeps UI responsive

---

### 4️⃣ Main Ingestion Entry Point

**Function:** `ingest_document()`

This is the **only function** the UI layer calls.

#### Input

```python
(file_input, filename="unknown")
```

#### Output

```python
(List[PIL.Image], metadata: dict)
```

---

## Metadata Structure

```json
{
  "filename": "invoice.pdf",
  "file_type": "pdf",
  "file_hash": "a3f8e5d2c1b4...",
  "num_pages": 3,
  "truncated": false
}
```

| Field       | Meaning                 |
| ----------- | ----------------------- |
| `filename`  | Original file name      |
| `file_type` | `"image"` or `"pdf"`    |
| `file_hash` | SHA256 content hash     |
| `num_pages` | Pages processed         |
| `truncated` | PDF exceeded page limit |

---

## Processing Logic (Simplified)

```
User uploads file
        ↓
Validate file size & extension
        ↓
Generate SHA256 hash
        ↓
Detect file type
        ↓
If image:
    └─ load_image()
If PDF:
    └─ convert_pdf()
        ↓
Validate extracted images
        ↓
Return images + metadata
```

---

## Example Workflows

### 🖼️ Single Image Upload

* Returns 1 PIL Image
* `file_type = "image"`
* Single-step OCR downstream

---

### 📄 Multi-Page PDF (≤ 5 pages)

* Returns list of images
* `file_type = "pdf"`
* Page-by-page OCR enabled

---

### ⚠️ Large PDF (> 5 pages)

* Only first 5 pages processed
* `metadata["truncated"] = True`
* UI can warn user safely

---

## Error Handling Philosophy

* ❌ Fail early
* ❌ Fail loudly
* ❌ Never return partial or undefined states

All errors:

* Preserve original exception context
* Are wrapped with user-readable explanations
* Are logged for debugging

---

## Why This Module Is Production-Grade

✔ Stream-safe
✔ Memory-safe
✔ Secure by default
✔ Deterministic behavior
✔ Clean separation of concerns
✔ Predictable outputs

Downstream modules **never need to guess** what they’ll receive.

---

## Summary

The ingestion module acts as a **trusted gatekeeper**:

* It converts **anything user-provided** into **safe, validated, predictable data**
* It protects the system from malformed, malicious, or oversized files
* It enables efficient session-based workflows in Streamlit
* It keeps preprocessing and OCR logic clean and focused

This is exactly how ingestion **should** be designed in real-world document pipelines.


