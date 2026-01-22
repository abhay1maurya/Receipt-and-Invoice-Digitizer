# Receipt and Invoice Digitizer - Project Flow Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Module Structure](#module-structure)
4. [Complete Workflow](#complete-workflow)
5. [Function Reference](#function-reference)
6. [Use Cases & Scenarios](#use-cases--scenarios)

---

## Project Overview

**Receipt and Invoice Digitizer** is a multi-page Streamlit web application that automates the extraction and storage of receipt/invoice data using Google Gemini AI OCR. The system processes scanned documents, extracts structured data, validates amounts, detects duplicates, and persists data in SQLite.

### Key Features:
- 📸 Image & PDF upload support
- 🤖 AI-powered OCR using Google Gemini 2.5 Flash
- 💾 Automatic duplicate detection (hard & soft matching)
- 💱 Multi-currency support with conversion to USD
- 📊 Dashboard with spending analytics
- 📋 History tracking of all digitized documents

---

## System Architecture

### Data Flow Pipeline
```
Upload Document 
    ↓
Ingest & Hash Check
    ↓
Preprocess Image (Noise Removal, Contrast Enhancement)
    ↓
Gemini OCR Extraction (JSON + Fallback OCR Text)
    ↓
Field Extraction (3-Tier Fallback)
    ├─ TIER 1: Gemini Fields
    ├─ TIER 2: Regex Patterns
    └─ TIER 3: spaCy NER (Vendor Extraction) ← NEW!
    ↓
Normalization & Type Conversion
    ↓
Currency Conversion to USD
    ↓
Validation (Amount + Duplicate Check)
    ↓
Amount Correction (if needed)
    ↓
Re-validate Duplicates
    ↓
Database Persistence
    ↓
Display Results & Update Cache
```

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **OCR Engine**: Google Gemini 2.5 Flash AI
- **NLP/NER**: spaCy 3.7.2+ (Named Entity Recognition for vendor extraction)
- **Database**: SQLite (file-based, serverless)
- **Image Processing**: PIL, OpenCV
- **PDF Handling**: pdf2image (Poppler-based)
- **Analytics**: Plotly, Pandas

---

## Module Structure

### Core Modules

| Module | Purpose | Key Functions |
|--------|---------|----------------|
| `app.py` | Main Streamlit app & page routing | `page_upload_process()`, `page_history()` |
| `database.py` | SQLite CRUD operations | `init_db()`, `insert_bill()`, `get_all_bills()` |
| `ocr.py` | Gemini API integration & extraction | `run_ocr_and_extract_bill()` |
| `ingestion.py` | File upload & format handling | `ingest_document()`, `generate_file_hash()` |
| `preprocessing.py` | Image enhancement for OCR | `preprocess_image()` |
| `validation.py` | Amount & duplicate validation | `validate_bill_complete()`, `validate_bill_amounts()` |
| `duplicate.py` | Duplicate detection logic | `detect_duplicate_bill_logical()` |
| `extraction/field_extractor.py` | Regex-based field extraction | `extract_fields_from_ocr()`, `is_field_weak()` |
| `extraction/vendor_extractor.py` | NLP-based vendor extraction (Tier 2) | `extract_vendor_name_nlp()` |
| `extraction/vendor_extractor_spacy.py` | spaCy NER vendor extraction (Tier 3) | `extract_vendor_spacy()` |
| `extraction/normalizer.py` | Data standardization | `normalize_extracted_fields()` |
| `extraction/currency_converter.py` | Multi-currency conversion | `convert_to_usd()` |

---

## Complete Workflow

### Main Entry Point: `app.py`

#### Phase 1: App Initialization
1. **Session State Setup** (Lines 51-110)
   - Initialize navigation state (`current_page`)
   - Setup file processing state variables
   - Initialize per-page processing arrays for multi-page PDFs
   - Create document-level state for extraction results

2. **Database Initialization** (Line 114)
   - Call `init_db()` to create tables if not exist
   - Creates `bills` table (header data)
   - Creates `lineitems` table (individual items)
   - Creates performance indexes

3. **Sidebar Navigation** (Lines 118-154)
   - Accept Gemini API key input
   - Display navigation buttons (Dashboard, Upload & Process, History)
   - Show system information

#### Phase 2: Page Routing (Lines 620-626)
```python
if current_page == "Dashboard":
    page_dashboard()  # Show analytics
elif current_page == "Upload & Process":
    page_upload_process()  # Show document processing UI
elif current_page == "History":
    page_history()  # Show all saved bills
```

---

## Function Reference

### 🟦 DATABASE LAYER (`database.py`)

#### `get_connection() -> sqlite3.Connection`
- **Purpose**: Create SQLite database connection
- **Returns**: Connection object with dict-like row access
- **Note**: Thread-safe for Streamlit (`check_same_thread=False`)

#### `init_db() -> None`
- **Purpose**: Initialize database schema on app start
- **Creates**:
  - `bills` table (15 columns for header data)
  - `lineitems` table (6 columns for items)
  - Performance indexes on `purchase_date`, `vendor_name`, `bill_id`
- **Error Handling**: Wraps in try-finally to ensure connection closure

#### `insert_bill(bill_data: Dict, user_id: int = 1, currency: str = "USD", file_path: Optional[str] = None) -> int`
- **Purpose**: Insert bill header and items into database
- **Input**:
  - `bill_data`: Normalized bill dictionary from OCR
  - `user_id`: Default 1 (for multi-user support)
  - `currency`: Target currency (usually USD after conversion)
- **Process**:
  1. Extract bill fields with sensible defaults
  2. Extract currency conversion fields (preserved originals)
  3. Insert bill header into `bills` table
  4. Loop through items array and insert each into `lineitems`
  5. Commit transaction
- **Output**: `bill_id` (primary key of inserted row)
- **Error Handling**: Rollback on exception

#### `get_all_bills() -> List[Dict]`
- **Purpose**: Fetch all bills from database, newest first
- **Fields Returned**:
  - Basic: `id`, `invoice_number`, `vendor_name`, `purchase_date`, `purchase_time`
  - Amounts: `subtotal`, `tax_amount`, `total_amount` (converted to float)
  - Currency: `currency`, `original_currency`, `original_total_amount`, `exchange_rate`
  - Other: `payment_method`
- **Output**: List of dictionaries, newest first

#### `get_bill_items(bill_id: int) -> List[Dict]`
- **Purpose**: Fetch all line items for a specific bill
- **Fields per Item**:
  - `s_no`: Sequential number (1-indexed)
  - `item_name`: Description
  - `quantity`, `unit_price`, `item_total` (converted to float)
- **Output**: List of item dictionaries, sorted by insertion order

#### `get_bill_details(bill_id: int) -> Optional[Dict]`
- **Purpose**: Fetch complete bill (header + items)
- **Output**: Combined dictionary with header fields + `items` array, or None if not found

#### `delete_bill(bill_id: int) -> bool`
- **Purpose**: Delete bill and cascade-delete items
- **Returns**: True if deleted, False if not found
- **Note**: Items deleted automatically via CASCADE constraint

---

### 🟦 OCR & EXTRACTION LAYER (`ocr.py`)

#### `run_ocr_and_extract_bill(image: Image.Image, api_key: str) -> Dict`
- **Purpose**: Extract structured bill data from image using Gemini AI with multi-tier fallback
- **Process**:
  1. **Validation**: Check API key and image validity
  2. **Gemini API Call**: Send image + prompt requesting JSON + OCR text
  3. **JSON Parsing**: Parse structured response
  4. **Regex Fallback (TIER 2)**: If JSON invalid or fields weak, extract from OCR text using regex patterns
  5. **spaCy NER Fallback (TIER 3)**: If vendor still missing/weak, use Named Entity Recognition
  6. **Normalization**: Standardize data types and formats
  7. **Currency Conversion**: Convert to USD
- **Three-Tier Extraction Pipeline**:
  ```
  TIER 1: Gemini AI (Primary) → Parse JSON response
      ↓ (if vendor_name weak/empty)
  TIER 2: Regex Fallback (Secondary) → Pattern-based extraction
      ↓ (if vendor_name still weak/empty)
  TIER 3: spaCy NER (Tertiary) → ORG entity recognition
      ↓ (if not found)
  Result: vendor_name (or remains empty)
  ```
- **spaCy Integration Details**:
  - Uses `en_core_web_sm` model (Named Entity Recognition)
  - Identifies ORG entities from OCR text
  - Filters by quality (length > 2) and sorts by length (shorter = cleaner names)
  - Lazy-loaded singleton pattern (Streamlit-safe, fast reuse)
  - Graceful fallback if model unavailable
- **Returns**: 
  - Success: Dictionary with extracted bill data (normalized & converted)
  - Failure: `{"error": "error message", "raw_response": "..."}` (on JSON parse failure)
- **Key Fields Extracted**:
  - `invoice_number`, `vendor_name`, `purchase_date`, `purchase_time`
  - `currency`, `total_amount`, `tax_amount`, `subtotal`
  - `items[]` (array of line items)
  - `payment_method`
- **Fallback Logic**:
  - Triggers when JSON parsing fails OR critical fields are weak/empty
  - Uses `extract_fields_from_ocr()` for regex extraction (TIER 2)
  - Uses `extract_vendor_spacy()` for NER extraction (TIER 3)

---

### 🟦 INGESTION LAYER (`ingestion.py`)

#### `generate_file_hash(file_input: FileInput) -> str`
- **Purpose**: Generate SHA256 hash for change detection
- **Input**: File path, BytesIO, or Streamlit UploadedFile
- **Process**:
  1. Handle different input types (path vs. stream)
  2. For streams: Remember position, seek to 0, read, restore position
  3. Update hasher with file bytes
- **Output**: 64-character hex hash string
- **Use Case**: Detect when user uploads different file to avoid re-processing

#### `ingest_document(file_input: FileInput, filename: str = "") -> Tuple[List[Image.Image], Dict]`
- **Purpose**: Convert uploaded file to PIL images with metadata
- **Input**:
  - `file_input`: File path, BytesIO, or UploadedFile
  - `filename`: Original filename for format detection
- **Process**:
  1. Determine file type from extension
  2. Validate file size (max 5MB for security)
  3. For images: Load image, convert to RGB
  4. For PDFs: Extract pages with `convert_from_bytes()` (max 5 pages)
  5. Collect metadata (format, pages, dimensions, etc.)
- **Output**:
  - `List[Image.Image]`: One PIL Image per page
  - `Dict`: Metadata (format, num_pages, dimensions, size_bytes)
- **Error Handling**: Catch format errors, malformed files, missing Poppler

#### `load_image(file_input: FileInput) -> Image.Image`
- **Purpose**: Load image with security checks
- **Process**:
  1. Reset stream cursor if applicable
  2. Open image to verify format
  3. Convert to RGB (removes transparency/palette)
  4. Validate EXIF orientation and fix upside-down images
- **Security**: 
  - Detects decompression bombs (max 10 megapixels)
  - Validates file format before processing

---

### 🟦 PREPROCESSING LAYER (`preprocessing.py`)

#### `preprocess_image(image_input: Union[str, Image.Image]) -> Image.Image`
- **Purpose**: Enhance image for OCR accuracy
- **Process**:
  1. **Load Image**: Handle file path or PIL Image input
  2. **Fix EXIF Rotation**: Correct upside-down mobile phone photos
  3. **Handle Transparency**: Convert RGBA to RGB with white background
  4. **Grayscale Conversion**: Simplify to single channel
  5. **Contrast Enhancement**: Boost light/dark separation (factor: 1.8)
  6. **Binarization**: Apply Otsu thresholding (black/white only)
  7. **Noise Removal**: Median blur to remove dust/speckles
  8. **Resizing**: Scale down if larger than 1800x1800 (preserve text clarity)
- **Output**: Grayscale PIL Image optimized for OCR
- **Note**: Critical for Gemini accuracy; poor preprocessing = weak extraction

---

### 🟦 VALIDATION LAYER (`validation.py`)

#### `validate_bill_amounts(bill_data: Dict, tolerance: float = 0.02) -> Dict`
- **Purpose**: Validate bill total amounts match items
- **Process**:
  1. Sum all item totals (`items[].item_total`)
  2. Get `tax_amount` and `total_amount` from bill header
  3. Test two models:
     - **Inclusive**: `items_sum ≈ total_amount` (tax included in item prices)
     - **Exclusive**: `items_sum + tax_amount ≈ total_amount` (tax separate)
  4. Accept if either model matches (tolerance: ±0.02)
- **Returns**:
  ```python
  {
      "is_valid": bool,
      "items_sum": float,
      "tax_amount": float,
      "total_amount": float,
      "errors": [{"type": "AMOUNT_MISMATCH", ...}]
  }
  ```
- **Use Case**: Detect OCR extraction errors (e.g., wrong total amount)

#### `validate_bill_complete(bill_data: Dict, user_id: int = 1) -> Dict`
- **Purpose**: Unified validation for amounts + duplicates
- **Process**:
  1. Call `validate_bill_amounts()`
  2. Call `detect_duplicate_bill_logical()`
  3. Set `can_save` flag
  4. Collect warnings
- **Returns**:
  ```python
  {
      "amount_validation": {...},  # Result from validate_bill_amounts
      "duplicate_check": {...},    # Result from detect_duplicate_bill_logical
      "can_save": bool,            # Amounts valid AND no hard duplicate
      "warnings": [...]            # List of warning messages
  }
  ```

---

### 🟦 DUPLICATE DETECTION (`duplicate.py`)

#### `detect_duplicate_bill_logical(bill_data: Dict, user_id: int) -> Dict`
- **Purpose**: Detect duplicate bills by matching invoice_number/vendor/date/amount
- **Process**:
  1. Extract key fields: `invoice_number`, `vendor_name`, `purchase_date`, `total_amount`
  2. Validate sufficient data (need vendor + date)
  3. **Hard Match** (blocks save):
     - If `invoice_number` present: Query for matching invoice + vendor + date + amount (±0.02)
     - Returns `duplicate: True` if found
  4. **Soft Match** (warns user):
     - No `invoice_number`: Query for matching vendor + date + amount (±0.02)
     - Returns `soft_duplicate: True` if found
- **Returns**:
  ```python
  {
      "duplicate": bool,      # Hard duplicate found (blocks save)
      "soft_duplicate": bool, # Soft duplicate found (warn only)
      "reason": "..."         # Explanation message
  }
  ```
- **Database Queries**: Uses SQLite with LOWER() for case-insensitive vendor matching

---

### 🟦 FIELD EXTRACTION (`extraction/field_extractor.py`)

#### `extract_fields_from_ocr(ocr_text: str) -> Dict`
- **Purpose**: Regex-based fallback extraction when Gemini JSON is weak
- **Regex Patterns** for:
  - Invoice number: Common patterns like `#`, `Invoice`, `Receipt`
  - Dates: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
  - Amounts: Currency symbols ($, ₹, €) + numeric patterns
  - Tax: Keywords `tax`, `GST`, `VAT`, `service charge`
- **Output**: Dictionary with extracted fields
- **Use Case**: Recovery when Gemini fails or returns incomplete data

#### `is_field_weak(value: Any) -> bool`
- **Purpose**: Check if field is missing or unreliable for fallback triggering
- **Weak Conditions**:
  - `None` or empty string
  - String with only whitespace
  - `"null"` or `"undefined"` strings (from Gemini)
  - Zero values for amounts
- **Returns**: True if weak, False if strong

---

### 🟦 NORMALIZATION (`extraction/normalizer.py`)

#### `normalize_extracted_fields(extracted: Dict) -> Dict`
- **Purpose**: Standardize data types and formats for database compatibility
- **Normalizations**:
  - **Dates**: Convert to YYYY-MM-DD format
  - **Times**: Convert to HH:MM:SS format
  - **Amounts**: Convert strings to float, round to 2 decimals
  - **Vendors**: Truncate to VARCHAR(255) limit
  - **Items**: Ensure `quantity` is integer
- **Defaults**:
  - Missing `vendor_name`: `"Unknown"`
  - Missing `purchase_date`: Today's date
  - Missing `currency`: `"USD"`
  - Missing amounts: `0.0`
- **Tax Amount Calculation**:
  - If `tax_amount` missing but `subtotal` and `total_amount` present:
    - Calculate: `tax_amount = total_amount - subtotal`
  - If items present but no total:
    - Calculate: `total_amount = items_sum + tax_amount`
- **Output**: Normalized dictionary ready for database insertion

---

### 🟦 CURRENCY CONVERSION (`extraction/currency_converter.py`)

#### `convert_to_usd(bill_data: Dict) -> Dict`
- **Purpose**: Convert all monetary values to USD while preserving originals
- **Exchange Rates**:
  - USD: 1.0
  - INR: 0.012
  - EUR: 1.08
  - GBP: 1.27
  - MYR: 0.21
  - RM: 0.21
- **Process**:
  1. Extract currency code (defaults to "USD")
  2. Look up exchange rate
  3. If unknown currency: Add warning, don't convert
  4. Preserve originals: `original_currency`, `original_total_amount`
  5. Apply rate to all amounts: `subtotal`, `tax_amount`, `total_amount`
  6. Apply rate to item prices: `unit_price`, `item_total`
  7. Set `currency` field to "USD"
- **Output**: Dictionary with USD amounts + original currency info

---

### 🟦 VENDOR EXTRACTION (`extraction/vendor_extractor.py`)

#### `extract_vendor_name_nlp(ocr_text: str) -> Optional[str]`
- **Purpose**: Heuristic vendor extraction from OCR text (TIER 2 fallback)
- **Logic**:
  1. Search for keywords: INVOICE, RECEIPT, STORE, FROM, TO
  2. Extract text near these keywords
  3. Parse as vendor name
  4. Clean punctuation and normalize case
- **Output**: Vendor name string or None if extraction fails

---

### 🟦 SPACY NER VENDOR EXTRACTION (`extraction/vendor_extractor_spacy.py`)

#### `_load_spacy_model() -> Optional[Language]`
- **Purpose**: Lazy load spaCy model with error handling
- **Features**:
  - Singleton pattern (load once, reuse)
  - Streamlit-safe (handles reruns)
  - Error handling for missing model
  - Logging for debugging
- **Output**: spaCy Language model or None if unavailable
- **Note**: Called internally by `extract_vendor_spacy()`

#### `extract_vendor_spacy(ocr_text: str) -> Optional[str]`
- **Purpose**: Extract vendor name using spaCy Named Entity Recognition (TIER 3 fallback)
- **Process**:
  1. **Input Validation**: Check text length (minimum 10 characters)
  2. **Model Loading**: Lazy-load `en_core_web_sm` model
  3. **NER Pipeline**: Process text through spaCy entity recognition
  4. **Entity Extraction**: Find all ORG (Organization) entities
  5. **Filtering**: Keep entities with length > 2 characters
  6. **Sorting**: Prefer shorter names (often cleaner: "Walmart" vs "Walmart Supercenter Downtown Store")
  7. **Return Result**: Best matching vendor name or None
- **Model Details**:
  - Model: `en_core_web_sm` (12 MB, English-only)
  - Entity Types: ORG (Organization), PERSON, GPE (Geographic), LOC (Location)
  - Pipeline: Tokenization, POS tagging, Dependency parsing, NER
- **Performance**:
  - First call: 1-2 seconds (model loading)
  - Subsequent calls: 50-100 milliseconds
  - Memory: +50 MB (model resident)
- **Error Handling**:
  - Model not found → Log warning, return None (graceful fallback)
  - Processing exception → Log error, return None (safe failure)
  - Empty/short text → Return None immediately (no overhead)
- **When It's Used**:
  - Vendor name missing from Gemini extraction
  - Vendor name empty after regex fallback
  - OCR text available for entity recognition
- **Advantages Over Regex**:
  - Handles complex organization names
  - Resilient to OCR errors and typos
  - Understands context and structure
  - Better for noisy or incomplete text
- **Example**:
  ```
  OCR Text: "WALMART SUPERCENTER #4521 123 Main St Downtown..."
  spaCy NER: Identifies "WALMART SUPERCENTER" as ORG entity
  Result: "WALMART SUPERCENTER"
  ```

---

## Use Cases & Scenarios

### 🎯 Use Case 1: Single Image Upload (Success Path)

**User Actions:**
1. Click "Upload & Process" in sidebar
2. Upload single JPG receipt
3. Click "Save My Bill"

**Flow:**
```
app.py: page_upload_process()
├─ File upload detection → generate_file_hash()
├─ Ingest document → ingestion.ingest_document()
│  └─ Load single JPG → preprocessing.preprocess_image()
├─ Display preprocessed image
├─ User clicks "Save My Bill"
├─ OCR extraction → ocr.run_ocr_and_extract_bill()
│  ├─ Gemini API call
│  ├─ JSON parse + normalization
│  └─ Currency conversion
├─ Validation → validation.validate_bill_complete()
│  ├─ Amount validation passes
│  ├─ Duplicate check: no match
├─ Database insert → database.insert_bill()
│  ├─ Insert bill header
│  └─ Insert line items
├─ Display success message
└─ Rerun app → Show updated bills table
```

**Database State:**
- `bills` table: 1 new row (id, vendor_name, amounts, etc.)
- `lineitems` table: N new rows (bill_id = last inserted bill_id)

---

### 🎯 Use Case 2: Multi-Page PDF Upload

**User Actions:**
1. Upload 3-page PDF
2. Navigate between pages using page selector buttons
3. Click "Save My Bill - Page 1"
4. Click "Save My Bill - Page 2"
5. Skip Page 3 (click something else)

**Flow per Page:**
```
app.py: page_upload_process() [PDF branch]
├─ File ingestion: Extract 3 PIL images + metadata
├─ Display page navigation buttons (1, 2, 3)
├─ User selects Page 1
├─ Display preprocessed Page 1 image
├─ User clicks "Save My Bill - Page 1"
├─ OCR extraction for Page 1
├─ Validation (amount + duplicate)
├─ IF valid: Insert Page 1 to database
└─ Rerun to show updated state

[Repeat for Page 2]
[Page 3 skipped - no save]
```

**Database State After:**
- `bills`: 2 new rows (one per saved page)
- `lineitems`: Items for both pages

---

### 🎯 Use Case 3: Amount Validation Fails (Correction Flow)

**Scenario:**
- OCR extracts: items=$100, tax=$10, total=$107 (mismatch: should be $110)
- Amount validation fails (doesn't match inclusive or exclusive model)

**Flow:**
```
app.py: page_upload_process()
├─ OCR extraction
├─ Validation fails:
│  ├─ items_sum: $100
│  ├─ tax_amount: $10
│  ├─ extracted_total: $107
│  └─ INVALID (neither 100=107 nor 100+10=107)
├─ WARNING displayed: "Using calculated subtotal, tax, and total"
├─ CORRECTION applied:
│  ├─ bill_data["subtotal"] = 100 (items_sum)
│  ├─ bill_data["tax_amount"] = 10
│  ├─ bill_data["total_amount"] = 110 (100+10)
├─ RE-RUN duplicate detection with corrected total_amount
├─ Validation re-check (now valid: 100+10=110)
├─ Database insert with corrected amounts
└─ Success message
```

**Key Insight:**
- Corrected `total_amount` used for duplicate detection (prevents false matches)
- Amounts corrected, but bill still saved (warning issued, not blocked)

---

### 🎯 Use Case 4: Duplicate Detection (Blocked)

**Scenario:**
- User uploads same receipt twice
- First upload saves successfully
- Second upload is exact duplicate (same vendor, date, amount)

**Flow First Upload:**
```
OCR + Validation
├─ Amount validation: PASS
├─ Duplicate check: No match (first in DB)
├─ DATABASE INSERT → bill_id = 1
└─ Success
```

**Flow Second Upload:**
```
OCR + Validation
├─ Amount validation: PASS
├─ Duplicate check: HARD MATCH
│  ├─ Query: invoice_number=ABC + vendor=Walmart + date=2024-01-15 + amount±0.02
│  ├─ Result: Found bill_id=1
│  └─ Returns: duplicate=True, reason="Invoice #ABC from Walmart already exists"
├─ save_allowed = False
├─ WARNING displayed: "Duplicate bill detected. Bill not saved."
└─ NO DATABASE INSERT
```

---

### 🎯 Use Case 5: Soft Duplicate Detection (Warning)

**Scenario:**
- User has receipt from store without invoice number
- Uploads second receipt from same store, same date, similar amount
- Exact invoice number not available to do hard match

**Flow:**
```
OCR + Validation
├─ Amount validation: PASS
├─ Duplicate check:
│  ├─ invoice_number: NULL or empty
│  ├─ Query: vendor=Costco + date=2024-01-15 + amount±0.02
│  ├─ Result: Found similar bill_id=5
│  └─ Returns: soft_duplicate=True, reason="Similar bill from Costco on 2024-01-15 already exists"
├─ save_allowed = False
├─ WARNING displayed: "Duplicate bill detected (soft match). Bill not saved."
└─ NO DATABASE INSERT
```

---

### 🎯 Use Case 6: Currency Conversion (Multi-Currency)

**Scenario:**
- User uploads receipt from India (INR)
- OCR extracts: currency="INR", total_amount=5000

**Flow:**
```
ocr.run_ocr_and_extract_bill()
├─ Extraction: currency="INR", total_amount=5000, subtotal=4500, tax=500
├─ Normalization: Pass through
├─ Currency Conversion:
│  ├─ Lookup exchange rate: INR → 0.012
│  ├─ Store originals:
│  │  ├─ original_currency: "INR"
│  │  ├─ original_total_amount: 5000
│  │  └─ exchange_rate: 0.012
│  ├─ Convert amounts:
│  │  ├─ subtotal: 4500 * 0.012 = 54.00
│  │  ├─ tax_amount: 500 * 0.012 = 6.00
│  │  ├─ total_amount: 5000 * 0.012 = 60.00
│  ├─ Convert item prices:
│  │  └─ unit_price and item_total multiplied by rate
│  └─ Set currency: "USD"
└─ Database insert:
   ├─ Stored amounts in USD (54, 6, 60)
   ├─ Original currency info preserved
   └─ Allows historical tracking of original prices
```

**Database State:**
```sql
INSERT INTO bills (
    subtotal=54.00, tax_amount=6.00, total_amount=60.00, currency="USD",
    original_currency="INR", original_total_amount=5000, exchange_rate=0.012
)
```

---

### 🎯 Use Case 7: Regex Fallback (Weak JSON)

**Scenario:**
- Gemini OCR returns partial JSON
- `vendor_name` is missing or "null"
- `total_amount` is empty string

**Flow:**
```
ocr.run_ocr_and_extract_bill()
├─ JSON parse: Success but fields weak
├─ Fallback trigger check:
│  ├─ is_field_weak(vendor_name): True (null)
│  ├─ is_field_weak(total_amount): True (empty)
│  └─ weak_fields = ["vendor_name", "total_amount"]
├─ Regex fallback:
│  ├─ extract_fields_from_ocr(ocr_text)
│  └─ Find vendor from OCR text via regex
├─ Vendor NLP fallback:
│  └─ extract_vendor_name_nlp(ocr_text)
├─ Merge results into bill_data
├─ Normalization + Currency conversion
└─ Continue to validation
```

**Recovery Examples:**
- `vendor_name` regex extracts "Walmart" from OCR text
- `total_amount` regex finds "$42.50" pattern
- Bills saves with recovered data

---

### 🎯 Use Case 8: Dashboard Analytics

**User Actions:**
1. Click "Dashboard" in sidebar

**Flow:**
```
app.py: page_dashboard() [from dashboard.py]
├─ Load all bills: database.get_all_bills()
├─ Calculate metrics:
│  ├─ Total spent: SUM(total_amount)
│  ├─ Average bill: Total / count
│  ├─ Unique vendors: COUNT(DISTINCT vendor_name)
│  └─ Total bills: COUNT(*)
├─ Display metric cards
├─ Generate charts:
│  ├─ Spending by vendor (bar chart)
│  ├─ Spending over time (line chart)
│  ├─ Category breakdown (pie chart, if category field added)
│  └─ Top vendors (ranked)
└─ Show key insights
```

---

### 🎯 Use Case 9: History Page View

**User Actions:**
1. Click "History" in sidebar

**Flow:**
```
app.py: page_history()
├─ Fetch all bills: database.get_all_bills()
├─ Calculate metrics (same as dashboard)
├─ Display metric cards in 4-column layout
├─ Display all bills table:
│  ├─ Columns: id, invoice_number, vendor_name, purchase_date, original_total_amount, original_currency
│  └─ Sorted: newest first
├─ Dropdown to select bill for item details
├─ Fetch items: database.get_bill_items(selected_bill_id)
├─ Display detailed items table
│  └─ Columns: s_no, item_name, quantity, unit_price, item_total
└─ Allow export (future feature)
```

---

### 🎯 Use Case 10: Error Handling - Gemini API Fails

**Scenario:**
- User has invalid API key
- Or network error
- Or API quota exceeded

**Flow:**
```
ocr.run_ocr_and_extract_bill()
├─ Validate API key: FAIL
├─ Return: {"error": "API key is required"}
[OR]
├─ Make Gemini request: EXCEPTION
├─ Catch exception
├─ Return: {"error": "Gemini request failed: {exception message}"}

app.py: page_upload_process()
├─ Check if "error" in bill_data: YES
├─ Display error: "❌ Extraction failed: [error message]"
├─ Set save_allowed = False
├─ Call st.stop() to halt execution
└─ User must fix issue and try again
```

---

## Session State Flow Diagram

```
Session State Lifecycle
=======================

1. App Start
   ├─ current_page = "Dashboard"
   ├─ api_key = None
   ├─ file_type = None
   ├─ images = None
   ├─ ingestion_done = False
   ├─ document_processed = False
   ├─ extracted_bill_data = None
   └─ bill_saved = False

2. User Navigates to Upload & Process
   └─ current_page = "Upload & Process"

3. User Uploads File
   ├─ Generates hash
   ├─ If new file:
   │  ├─ Reset all processing state
   │  ├─ Ingest document
   │  ├─ Store images, metadata in session
   │  ├─ ingestion_done = True
   │  ├─ document_processed = True
   │  └─ Preprocess images
   └─ Display preprocessed image

4. User Clicks "Save My Bill"
   ├─ Run OCR extraction
   ├─ Validate amounts
   ├─ Check duplicates
   ├─ IF valid:
   │  ├─ Insert to database
   │  ├─ extracted_bill_data = {bill data}
   │  ├─ bill_saved = True
   │  └─ st.rerun() → Refresh UI
   └─ ELSE:
      └─ st.stop() → Halt

5. After Rerun (Success)
   ├─ Display results table
   ├─ Show bill items dropdown
   └─ All data preserved in session_state
```

---

## Data Schema

### Bills Table
```sql
CREATE TABLE bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,
    invoice_number VARCHAR(100),
    vendor_name VARCHAR(255) NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_time TIME,
    subtotal DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'USD',
    original_currency VARCHAR(10),
    original_total_amount DECIMAL(10, 2),
    exchange_rate DECIMAL(10, 6),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Line Items Table
```sql
CREATE TABLE lineitems (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    unit_price DECIMAL(10, 2) DEFAULT 0,
    total_price DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
);
```

### Indexes
```sql
CREATE INDEX idx_bills_purchase_date ON bills(purchase_date);
CREATE INDEX idx_bills_vendor ON bills(vendor_name);
CREATE INDEX idx_lineitems_bill_id ON lineitems(bill_id);
```

---

## Error Handling Strategy

| Layer | Error Type | Handling |
|-------|-----------|----------|
| **Ingestion** | Invalid file format | Return error message, ask user to retry |
| **Ingestion** | File too large | Block with error, max 5MB |
| **Preprocessing** | Image corruption | Log warning, use original image |
| **OCR** | Invalid API key | Return error, ask user to enter key |
| **OCR** | JSON parse failure | Attempt regex fallback, warn if recovery unsuccessful |
| **Validation** | Amount mismatch | Warn user, correct using calculated amounts |
| **Validation** | Duplicate detected | Warn user, block save |
| **Database** | Insert failure | Rollback transaction, show error message |

---

## Performance Considerations

- **PDF Limit**: Max 5 pages per PDF to prevent RAM exhaustion
- **Image Size**: Max 10 megapixels to prevent decompression bombs
- **Caching**: Streamlit auto-refreshes cache after 60 seconds
- **Database Indexes**: Query optimization on `purchase_date`, `vendor_name`
- **Session State**: Preserves data across reruns (no redundant API calls)

---

## Security Measures

1. **File Upload Security**:
   - Validate file format before processing
   - Check file size (max 5MB)
   - Limit PDF pages (max 5)
   - Validate image dimensions

2. **API Security**:
   - API key input as password field (masked)
   - No key logging or storage in logs
   - Key validated before API calls

3. **Database Security**:
   - Parameterized queries (prevent SQL injection)
   - LOWER() for case-insensitive vendor matching
   - Foreign key constraints

4. **Data Privacy**:
   - Original currency preserved (no data loss)
   - Exchange rates logged for audit trail
   - Soft duplicates warn without blocking

---

## Future Enhancement Ideas

1. **Multi-User Support**: Use `user_id` field for per-user bill isolation
2. **Categories**: Add `category` field to bills for expense categorization
3. **Export**: CSV/Excel export of bills and items
4. **Batch Upload**: Process multiple files simultaneously
5. **Advanced Analytics**: Spending trends, budget alerts
6. **Mobile App**: Native mobile version
7. **Receipt OCR Improvements**: Custom ML model for domain-specific extraction
8. **Real-Time Notifications**: Alert user when duplicate detected
9. **Edit Bills**: Allow manual correction of OCR extraction
10. **Receipt Templates**: Match bills to vendor templates for better extraction

---

## Troubleshooting

### Issue: "Extraction failed" Error
**Causes**:
- Invalid API key
- Network connectivity issue
- API quota exceeded

**Solution**: Verify API key, check internet, wait for quota reset

### Issue: Duplicate Not Detected
**Causes**:
- Amounts differ by > 0.02 (tolerance exceeded)
- Invoice number changed
- Vendor name capitalization differs

**Solution**: Check amount accuracy, use same invoice number, normalization handles case

### Issue: Amount Validation Fails Repeatedly
**Causes**:
- Poor OCR quality
- Incorrect item extraction
- Tax included in item prices (unparseable)

**Solution**: Re-upload with clearer image, manual correction coming in v2

### Issue: PDF Processing Fails
**Causes**:
- Poppler not installed (required for pdf2image)
- PDF corrupted
- More than 5 pages

**Solution**: Install Poppler, check PDF integrity, split large PDFs

---

## Version History

- **v1.0.0-beta** (Current)
  - Core OCR functionality
  - Amount validation & duplicate detection
  - Multi-currency support
  - Dashboard analytics
  - History tracking

---

**Last Updated**: January 22, 2026  
**Project**: Receipt and Invoice Digitizer  
**Author**: Development Team
