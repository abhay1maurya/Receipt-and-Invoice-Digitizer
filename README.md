
# 📄 Receipt and Invoice Digitizer

A robust, multi-stage document digitization system that converts physical receipts and invoices into validated, normalized, and analytics-ready structured data using **Google Gemini AI**, **spaCy NLP**, and **SQLite**.

---

## 🚀 Project Overview

**Receipt and Invoice Digitizer** is a Streamlit-based web application designed to automate the end-to-end processing of receipts and invoices.
It handles document ingestion, OCR, structured data extraction, validation, duplicate detection, currency normalization, and persistent storage — all with a focus on **correctness, reliability, and extensibility**.

This project is intentionally engineered as a **foundation system**, not a quick OCR demo. Every layer is modular, deterministic, and designed to scale to future analytics and enterprise use cases.

---

## ✨ Key Features

* 📸 **Image & PDF Upload Support** (JPG, PNG, PDF)
* 🤖 **AI-Powered OCR** using Google Gemini 2.5 Flash
* 🧠 **Multi-Tier Field Extraction Pipeline**

  * Gemini Structured JSON
  * Regex-based fallback
  * spaCy Named Entity Recognition (Vendor extraction)
* 💱 **Multi-Currency Support** with automatic conversion to USD
* ✅ **Safe Amount Validation**

  * Supports tax-inclusive and tax-exclusive pricing models
* 🔁 **Duplicate Detection**

  * Hard duplicate (invoice-level)
  * Soft duplicate (logical similarity)
* 🗃️ **SQLite Persistent Storage**
* 📊 **Dashboard Analytics**
* 🕒 **History & Audit View**
* 🔐 **Security-Conscious Design**
* 🧱 **Extensible Modular Architecture**

---

## 🧠 System Architecture

### High-Level Data Flow

```
Upload Document
    ↓
Ingestion & Hash-Based Change Detection
    ↓
Image Preprocessing (OCR Optimization)
    ↓
Gemini OCR (Structured JSON + Raw OCR Text)
    ↓
Field Extraction (Multi-Tier)
    ├─ Tier 1: Gemini Structured Output
    ├─ Tier 2: Regex-Based Extraction
    └─ Tier 3: spaCy NER (Vendor Name)
    ↓
Normalization & Type Safety
    ↓
Currency Conversion → USD
    ↓
Validation (Amounts + Duplicates)
    ↓
SQLite Persistence
    ↓
Dashboard & History Views
```

---

## 🧰 Technology Stack

| Layer            | Technology               |
| ---------------- | ------------------------ |
| Frontend         | Streamlit                |
| OCR Engine       | Google Gemini 2.5 Flash  |
| NLP / NER        | spaCy (`en_core_web_sm`) |
| Image Processing | PIL, OpenCV              |
| PDF Processing   | pdf2image                |
| Database         | SQLite                   |
| Analytics        | Pandas, Plotly           |
| Language         | Python 3.10+             |

---

## 📁 Project Structure

```
Receipt-and-Invoice-Digitizer/
│
├── app.py                         # Main Streamlit application
├── dashboard.py                   # Analytics dashboard
│
├── src/
│   ├── ingestion.py               # File ingestion & hashing
│   ├── preprocessing.py           # Image preprocessing
│   ├── ocr.py                     # Gemini OCR orchestration
│   ├── validation.py              # Amount + duplicate validation
│   ├── duplicate.py               # Logical duplicate detection
│   ├── database.py                # SQLite persistence
│   │
│   └── extraction/
│       ├── field_extractor.py     # Regex-based extraction
│       ├── vendor_extractor_spacy.py  # spaCy NER vendor extraction
│       ├── normalizer.py          # Data normalization
│       └── currency_converter.py  # Currency conversion to USD
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🔍 Core Design Principles

* **Fail-safe over fail-fast**
* **Never trust OCR blindly**
* **No silent data corruption**
* **Deterministic fallbacks**
* **Session-safe Streamlit design**
* **Database-ready normalized output**

---

## 🔄 Multi-Tier Extraction Strategy

### Why Multi-Tier?

OCR systems are probabilistic. This project avoids brittle assumptions by layering extraction logic:

#### Tier 1 – Gemini AI (Primary)

* Structured JSON extraction
* Semantic understanding
* Fast and accurate in most cases

#### Tier 2 – Regex Fallback

* Deterministic recovery
* Handles missing or weak fields
* Used only when Tier 1 is unreliable

#### Tier 3 – spaCy Named Entity Recognition

* ML-based vendor name extraction
* Detects `ORG` entities from OCR text
* Robust to formatting noise and OCR errors

> ❌ No heuristic scoring
> ❌ No rule-based NLP hacks
> ✅ Only ML-backed NER where needed

---

## 💱 Currency Handling

* Supports INR, EUR, GBP, MYR, USD (extensible)
* Converts **all monetary values to USD**
* Preserves:

  * Original currency
  * Original total amount
  * Exchange rate used
* Ensures analytics consistency across regions

---

## ✅ Validation Logic

### Amount Validation

Supports both:

* **Tax-inclusive pricing**
* **Tax-exclusive pricing**

Accepts data if **either model matches** within tolerance (±0.02).

### Duplicate Detection

* **Hard Duplicate**

  * Invoice number + vendor + date + amount
  * Blocks save
* **Soft Duplicate**

  * Vendor + date + amount
  * Warns but prevents accidental duplication

---

## 🗃️ Database Schema

### Bills Table

```sql
CREATE TABLE bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,
    invoice_number VARCHAR(100),
    vendor_name VARCHAR(255) NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_time TIME,
    subtotal DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    currency VARCHAR(10),
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
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
);
```

---

## 🧪 Error Handling Strategy

| Layer         | Strategy                        |
| ------------- | ------------------------------- |
| Ingestion     | File size & format validation   |
| Preprocessing | Safe fallback to original image |
| OCR           | Graceful API failure handling   |
| Extraction    | Regex & NLP recovery            |
| Validation    | Non-destructive warnings        |
| Database      | Transaction rollback on failure |

---

## 🔐 Security & Stability

* File size limits enforced (5MB)
* PDF page limits enforced
* No API keys logged or stored
* No untrusted file writes
* Hash-based file change detection
* Defensive JSON parsing
* SQLite parameterized queries

---

## 📊 Dashboard Capabilities

* Total spending overview
* Average bill value
* Vendor-wise spending
* Time-based trends
* Historical audit table

---

## 🛣️ Future Enhancements

* Multi-user support
* Manual bill editing
* Batch uploads
* Export to CSV/Excel
* Expense categorization
* Budget alerts
* Mobile-friendly UI
* Vendor templates
* Receipt confidence scoring

---

## 🏁 Current Status

**Version**: `v1.0.0-beta`
**Milestones Completed**:

* Core ingestion & OCR pipeline
* Multi-tier extraction
* Validation & duplicate detection
* Currency conversion
* SQLite persistence
* Dashboard & history views

---

## 📌 Final Notes

This project is **not a toy OCR app**.
It is a **correctness-first, architecture-driven system** designed to handle real-world document variability.

If someone asks *“why this design?”*, you have a clear, defensible answer for every layer.



