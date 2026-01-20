
# 📄 Receipt & Invoice Digitizer

**AI-Powered Document Digitization & Multi-Currency Support**

---

## 📌 Project Overview

The **Receipt & Invoice Digitizer** is a Streamlit-based web application that converts physical receipts and invoices into structured digital records with intelligent data extraction and normalization capabilities.

The system automates:
- Document ingestion (JPG, PNG, PDF)
- Image preprocessing and enhancement
- OCR and structured data extraction using **Google Gemini AI**
- Multi-currency transaction handling with automatic USD conversion
- Text normalization for data consistency
- Persistent storage in **SQLite database**

This project addresses the real-world challenges of **manual bill entry**, **expense tracking**, **multi-currency transactions**, and **data loss from physical receipts**.

---

## 🎯 Core Objectives

Build a **reliable, intelligent, and extensible document digitization pipeline** that:

* Ingests multiple document formats (**JPG, PNG, PDF**)
* Converts documents into **OCR-ready image formats**
* Automatically preprocesses images for optimal OCR accuracy
* Performs **OCR and structured data extraction** using Google Gemini AI
* Handles **multi-currency transactions** with automatic USD conversion
* Normalizes all text data for **consistent querying and analysis**
* Validates extracted data for accuracy
* Provides **persistent storage** with relational integrity
* Implements **controlled error handling** and graceful failures

---

## 🏗️ System Architecture

```
User Upload (JPG / PNG / PDF)
        ↓
Ingestion Layer (Format Conversion & Hash Generation)
        ↓
Preprocessing Layer (Enhancement & Binarization)
        ↓
OCR & Structured Extraction (Gemini AI)
        ↓
Normalization Layer (Uppercase Conversion & Standardization)
        ↓
Currency Conversion (Multi-Currency → USD)
        ↓
Validation Layer (Data Consistency Checks)
        ↓
SQLite Database (Bills & Line Items with Currency Metadata)
```

---

## 🧩 Core Modules

### 1️⃣ Ingestion Module (`src/ingestion.py`)

**Purpose:**
Safely converts uploaded files into standardized image inputs.

**Key Features:**

* Supports JPG, PNG, and multi-page PDF documents
* Converts PDFs to page-wise images using `pdf2image`
* Generates **SHA-256 file hash** to detect duplicate uploads
* Enforces security limits (page limits, file size checks)
* Returns list of PIL Image objects with metadata

**Security & Performance:**

* Maximum file size validation
* Page limit enforcement for PDFs
* Memory-efficient processing

**Output:**
Normalized PIL Image objects ready for preprocessing.

---

### 2️⃣ Preprocessing Module (`src/preprocessing.py`)

**Purpose:**
Enhances image quality to maximize OCR accuracy.

**Processing Pipeline:**

1. **EXIF-based orientation correction** – Fixes rotated images
2. **Transparency removal** – Converts RGBA to RGB with white background
3. **Grayscale conversion** – Reduces complexity
4. **Contrast enhancement (CLAHE)** – Improves text visibility
5. **Otsu binarization** – Converts to black-and-white
6. **Noise removal** – Median filtering to clean artifacts
7. **Large image resizing** – Optimizes performance for high-resolution images

**Result:**
Clean, binarized, OCR-ready images with enhanced text clarity.

---

### 3️⃣ OCR & Extraction Module (`src/ocr.py`)

**Purpose:**
Performs OCR and structured data extraction in a **single AI call** using Google Gemini AI.

**Key Design:**

* **One-call extraction** – Reduces latency and API costs
* **Strict JSON-only prompt** – Enforces structured output
* **Schema-controlled extraction** – Consistent field names

**Extracted Fields:**

* `vendor_name` – Merchant/vendor identification
* `invoice_number` – Bill/receipt number
* `purchase_date` – Transaction date (YYYY-MM-DD)
* `purchase_time` – Transaction time (HH:MM:SS)
* `currency` – Original transaction currency code
* `payment_method` – Payment type (CASH, CARD, UPI, etc.)
* `subtotal` – Pre-tax amount
* `tax_amount` – Tax charged
* `total_amount` – Final amount
* `items` – Array of line items:
  - `item_name` – Product/service description
  - `quantity` – Units purchased
  - `unit_price` – Price per unit
  - `total_price` – Line total

**Failure Handling:**
Invalid JSON or AI errors trigger controlled exceptions without crashing the application.

---

### 4️⃣ Normalization Module (`src/extraction/normalizer.py`)

**Purpose:**
Standardizes extracted data for consistent storage and querying.

**Text Normalization:**

All text fields are converted to **UPPERCASE** to prevent case-sensitivity issues:

* `vendor_name` → **UPPERCASE**
* `invoice_number` → **UPPERCASE**
* `payment_method` → **UPPERCASE**
* `currency` → **UPPERCASE**
* `item_name` (all line items) → **UPPERCASE**

**Benefits:**

* Eliminates case-matching bugs in database queries
* Ensures consistent vendor/item grouping
* Simplifies search and filtering operations
* Prevents duplicate entries due to case variations (e.g., "Walmart" vs "WALMART")

**Currency Standardization:**

* Currency codes normalized to ISO format (USD, EUR, INR, etc.)
* Supports automatic conversion from local currencies to USD
* Preserves original currency metadata for audit trails

**Numeric Handling:**

* All monetary values preserved with decimal precision
* Quantities and prices maintained as floats
* No modification to numeric data during normalization

---

### 5️⃣ Currency Conversion (`src/extraction/normalizer.py`)

**Purpose:**
Handles multi-currency transactions with automatic USD conversion.

**Features:**

* Detects non-USD currencies in extracted data
* Fetches real-time exchange rates from external API
* Converts all amounts to USD for standardized reporting
* **Preserves original currency data** in separate fields:
  - `original_currency` – Original currency code
  - `original_total_amount` – Original transaction amount
  - `exchange_rate` – Conversion rate used

**Database Storage:**

All bills stored with both:
- **Converted values** (in USD for analytics)
- **Original values** (for transparency and audit)

**Benefits:**

* Unified currency reporting across all transactions
* Full audit trail with original currency preserved
* Accurate exchange rate tracking
* Support for international receipts and invoices

---

### 6️⃣ Validation Module (`src/validation.py`)

**Purpose:**
Ensures numerical consistency and data quality.

**Validation Checks:**

* **Subtotal calculation** – Sums all line item totals
* **Total consistency** – Verifies `subtotal + tax = total`
* **Tolerance handling** – Allows marginal differences for rounding/OCR errors
* **Missing data detection** – Flags incomplete extractions

**Behavior:**

* Warnings displayed in UI for validation failures
* Does **not block** saving to database (user decision)
* Provides transparency for data quality issues

---

### 7️⃣ Database Module (`src/database.py`)

**Purpose:**
Provides serverless, persistent storage with relational integrity.

**Technology:** SQLite (file-based, zero-configuration)

**Schema Design:**

#### **Bills Table**
```sql
bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    invoice_number TEXT,
    vendor_name TEXT,
    purchase_date TEXT,
    purchase_time TEXT,
    subtotal REAL,
    tax_amount REAL,
    total_amount REAL,
    currency TEXT DEFAULT 'USD',
    original_currency TEXT,
    original_total_amount REAL,
    exchange_rate REAL,
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_bills_purchase_date` – Fast date filtering
- `idx_bills_vendor` – Vendor-based queries

#### **Line Items Table**
```sql
lineitems (
    lineitem_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER,
    item_name TEXT,
    quantity REAL,
    unit_price REAL,
    total_price REAL,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
)
```

**Key Features:**

* **Foreign key constraints** – Enforces referential integrity
* **CASCADE deletion** – Removing a bill deletes its line items
* **Automatic timestamps** – Tracks record creation
* **Currency metadata** – Stores original and converted values
* **Indexed columns** – Optimized for common queries

**Operations:**

* `init_db()` – Creates schema on first run
* `save_bill()` – Inserts bill with line items in transaction
* `get_all_bills()` – Retrieves all bills with currency data
* `delete_bill()` – Removes bill and cascades to line items

---

### 8️⃣ Streamlit UI Module (`app.py`)

**Purpose:**
Provides an interactive multi-page web interface.

**Pages:**

* **📤 Upload & Process** – Upload documents, preview preprocessing, extract data, save to database
* **📊 Dashboard** – Analytics and insights *(separate implementation)*
* **📜 History** – View all stored bills and their line items

**Upload & Process Features:**

* Drag-and-drop file upload
* Real-time preprocessing preview
* One-click extraction
* Validation warnings display
* Database save confirmation
* Session state management across reruns

**History Features:**

* Searchable bill listing
* Detailed bill view with line items
* Currency conversion transparency
* Date-based filtering

---

## 🛡️ Error Handling & Reliability

**Input Validation:**
* File format checking (JPG, PNG, PDF only)
* File size limits enforcement
* PDF page count restrictions

**AI Robustness:**
* JSON parsing error handling
* Fallback for malformed responses
* Graceful degradation on API failures

**Database Integrity:**
* Foreign key constraints
* Transaction-based saves (atomic operations)
* Automatic schema initialization

**UI Resilience:**
* Session state preservation across reruns
* Warning-based feedback (no crashes)
* Clear error messaging

---

## ⚙️ Tech Stack

| Layer                 | Technology                      |
| --------------------- | ------------------------------- |
| Frontend              | Streamlit                       |
| OCR & AI              | Google Gemini AI (gemini-1.5-flash) |
| Image Processing      | OpenCV, PIL (Pillow)            |
| PDF Processing        | pdf2image, poppler              |
| Backend Logic         | Python 3.12+                    |
| Database              | SQLite3                         |
| Data Handling         | Pandas, NumPy                   |
| Currency Conversion   | External Exchange Rate API      |
| File Operations       | os, hashlib, base64             |

---

## 🚀 Installation & Setup

### Prerequisites

* Python 3.12 or higher
* Conda or virtualenv (recommended)
* Google Gemini API key
* Poppler (for PDF processing)

### Step 1: Create Virtual Environment

```bash
# Using Conda
conda create -n ridvenv python=3.12
conda activate ridvenv

# Or using venv
python -m venv ridvenv
source ridvenv/bin/activate  # On Windows: ridvenv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
```
streamlit
google-generativeai
pillow
opencv-python
pdf2image
pandas
numpy
requests
```

### Step 3: Install Poppler (for PDF support)

**Windows:**
Download from [https://github.com/oschwartz10612/poppler-windows/releases/](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH

**macOS:**
```bash
brew install poppler
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

### Step 4: Configure API Key

Create a `.env` file or set environment variable:
```bash
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

Or configure directly in the app settings.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

---

## 📁 Project Structure

```
Receipt-and-Invoice-Digitizer/
│
├── app.py                          # Main Streamlit application
├── dashboard.py                    # Analytics dashboard (separate)
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
│
├── data/                           # Document storage
│   └── raw/                        # Raw uploaded files
│
├── src/                            # Core modules
│   ├── __init__.py
│   ├── ingestion.py                # File upload & conversion
│   ├── preprocessing.py            # Image enhancement
│   ├── ocr.py                      # Gemini AI extraction
│   ├── validation.py               # Data consistency checks
│   ├── database.py                 # SQLite operations
│   │
│   └── extraction/                 # Data normalization
│       ├── __init__.py
│       ├── normalizer.py           # Text & currency normalization
│       ├── field_extractor.py      # Field parsing utilities
│       ├── regex_patterns.py       # Pattern matching
│       └── validator.py            # Field validation
│
└── receipt_invoice.db              # SQLite database (auto-created)
```

---

## 📌 Key Features Implemented

### ✅ Document Processing
- [x] Multi-format support (JPG, PNG, PDF)
- [x] Multi-page PDF handling
- [x] EXIF orientation correction
- [x] Advanced image preprocessing (CLAHE, Otsu binarization)
- [x] Duplicate detection via SHA-256 hashing

### ✅ AI-Powered Extraction
- [x] Single-call OCR + structured extraction
- [x] JSON schema enforcement
- [x] Vendor, invoice, date, time extraction
- [x] Line item extraction (name, quantity, price)
- [x] Tax and total calculation
- [x] Payment method detection

### ✅ Data Normalization
- [x] **Uppercase text conversion** for all fields
- [x] Currency code standardization (ISO format)
- [x] Multi-currency support with USD conversion
- [x] Original currency preservation
- [x] Exchange rate tracking

### ✅ Database Management
- [x] SQLite relational schema
- [x] Bills and line items tables
- [x] Foreign key constraints with CASCADE delete
- [x] Currency metadata storage
- [x] Indexed columns for performance
- [x] Transaction-based saves

### ✅ Validation & Quality
- [x] Subtotal verification
- [x] Tax + subtotal = total validation
- [x] Tolerance for rounding errors
- [x] Warning-based feedback (non-blocking)

### ✅ User Interface
- [x] Multi-page Streamlit app
- [x] Upload & Process workflow
- [x] History viewer
- [x] Session state management
- [x] Real-time preprocessing preview

---

## 🔄 Workflow Example

1. **Upload Document** – User uploads receipt image or PDF
2. **Preprocessing** – System enhances image quality automatically
3. **AI Extraction** – Gemini AI extracts structured data in JSON format
4. **Normalization** – Text converted to uppercase, currency standardized
5. **Currency Conversion** – Non-USD amounts converted with rate tracking
6. **Validation** – System checks numerical consistency
7. **Database Save** – Bill and line items stored with full metadata
8. **View History** – User can browse all saved bills with currency details

---

## 🧪 Testing Scenarios

**Supported Document Types:**
* Standard retail receipts
* Restaurant bills
* Invoice documents
* Multi-page PDF invoices
* International receipts (multiple currencies)

**Edge Cases Handled:**
* Missing fields (graceful degradation)
* Malformed JSON responses (error recovery)
* OCR inaccuracies (validation warnings)
* Currency conversion failures (fallback logic)
* Duplicate uploads (hash-based detection)

---

## 🔮 Future Enhancements

* User authentication & access control
* Advanced data validation & fraud detection
* Export to CSV/Excel/PDF
* Cloud deployment
* AI confidence scoring
* Category-wise expense analytics
* Multi-user support
* Receipt categorization & tagging
* Budgeting and spending alerts
* Mobile app integration
* API endpoints for third-party integration

---

## 🏁 Summary

The **Receipt & Invoice Digitizer** delivers a **production-ready digitization pipeline** with:

* Modular architecture
* AI-powered structured extraction
* Multi-currency transaction support
* Intelligent text normalization
* Persistent storage
* Robust error handling
* Extensible design for future enhancements

This system provides a solid foundation for **enterprise-grade expense management** and **document intelligence solutions**, with scalable architecture and comprehensive data handling capabilities.


