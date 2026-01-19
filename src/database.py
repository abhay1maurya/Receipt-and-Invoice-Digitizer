# Database persistence layer for receipt and invoice data
# Handles SQLite connections and CRUD operations for invoices and line items
# Schema: bills table (header data) + lineitems table (individual items)
# Uses SQLite for lightweight, serverless database storage

import os
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

# SQLite database file location - can be overridden via environment variable
# Defaults to 'receipt_invoice.db' in the current directory
DB_PATH = os.getenv("SQLITE_DB_PATH", "receipt_invoice.db")


def get_connection():
    """Create a new SQLite database connection.
    Returns a connection object that must be closed after use.
    SQLite is thread-safe with check_same_thread=False for Streamlit compatibility."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Allow dict-like access to rows
    return conn


def init_db():
    """Initialize SQLite database with required schema.
    Creates bills and lineitems tables if they don't exist.
    Safe to call multiple times - tables created only if missing."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Create bills table (invoice header data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
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
                payment_method VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create lineitems table (individual line items)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lineitems (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                unit_price DECIMAL(10, 2) DEFAULT 0,
                total_price DECIMAL(10, 2) DEFAULT 0,
                FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bills_purchase_date 
            ON bills(purchase_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lineitems_bill_id 
            ON lineitems(bill_id)
        """)
        
        conn.commit()
    finally:
        conn.close()

def detect_duplicate_bill_logical(bill_data: dict, user_id: int) -> bool:
    invoice_number = bill_data.get("invoice_number")
    vendor = bill_data.get("vendor_name")
    purchase_date = bill_data.get("purchase_date")
    total_amount = float(bill_data.get("total_amount", 0))

    if not invoice_number or not vendor or not purchase_date:
        return False  # Cannot reliably detect duplicate

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bill_id
            FROM bills
            WHERE invoice_number = ?
              AND LOWER(vendor_name) = LOWER(?)
              AND purchase_date = ?
              AND ABS(total_amount - ?) <= 0.02
            LIMIT 1
            """,
            (invoice_number, vendor, purchase_date, total_amount)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def insert_bill(bill_data: Dict, user_id: int = 1, currency: str = "USD", file_path: Optional[str] = None) -> int:
    """Insert a bill and its line items into SQLite database.

    Tables:
        - bills(bill_id, user_id, vendor_name, purchase_date, purchase_time, total_amount, tax_amount, currency, payment_method)
        - lineitems(item_id, bill_id, description, quantity, unit_price, total_price)

    Returns the newly created bill_id.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Provide sensible defaults because OCR extraction can be incomplete or inconsistent
        invoice_number = bill_data.get("invoice_number") or None
        vendor = bill_data.get("vendor_name") or "Unknown"
        
        # Schema requires purchase_date; use today if OCR didn't detect it
        purchase_date = bill_data.get("purchase_date") or datetime.today().strftime("%Y-%m-%d")
        purchase_time = bill_data.get("purchase_time") or None
        
        tax_amount = bill_data.get("tax_amount", 0) or 0
        total_amount = bill_data.get("total_amount", 0) or 0
        # Normalizer already calculated subtotal; extract it
        subtotal = bill_data.get("subtotal", 0) or 0
        currency_value = bill_data.get("currency", currency)
        payment_method = bill_data.get("payment_method") or None

        # Insert bill header data into bills table (SQLite uses ? placeholders)
        cursor.execute(
            """
            INSERT INTO bills (user_id, invoice_number, vendor_name, purchase_date, purchase_time, subtotal, tax_amount, total_amount, currency, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, invoice_number, vendor, purchase_date, purchase_time, subtotal, tax_amount, total_amount, currency_value, payment_method),
        )
        # Get auto-generated bill_id for linking line items
        bill_id = cursor.lastrowid

        # Process items from OCR output
        items = bill_data.get("items", []) or []
        for s_no, item in enumerate(items, 1):
            description = item.get("item_name", "")
            
            # OCR often returns quantity as string; convert safely with rounding for fractional quantities
            qty_val = item.get("quantity") or 0
            try:
                qty = int(round(float(qty_val)))
            except Exception:
                qty = 0
                
            unit_price = item.get("unit_price") or 0
            
            # Use item_total if available; calculate fallback to catch OCR math errors
            total_price = item.get("item_total") or (qty * unit_price)
            
            # Insert line item row
            cursor.execute(
                """
                INSERT INTO lineitems (bill_id, description, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (bill_id, description, qty, unit_price, total_price),
            )

        # Commit transaction - preserves atomicity if bill_id is needed downstream
        conn.commit()
        return bill_id
    except Exception as e:
        # Rollback ensures partial inserts don't corrupt database if any step fails
        conn.rollback()
        raise e  # Re-raise exception for caller to handle
    finally:
        # Always close connection to free resources
        conn.close()


def get_all_bills() -> List[Dict]:
    """Fetch all bills from database with app-friendly key mapping.
    Returns rows sorted by newest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bill_id AS id,
                   invoice_number,
                   vendor_name,
                   purchase_date,
                   total_amount,
                   tax_amount,
                   currency,
                   payment_method,
                   purchase_time
            FROM bills
            ORDER BY bill_id DESC
            """
        )
        rows = cursor.fetchall()
        bills = []
        # Transform each row to ensure consistent data types and handle nulls
        for r in rows:
            bills.append(
                {
                    "id": r["id"],
                    "invoice_number": r["invoice_number"],
                    "vendor_name": r["vendor_name"],
                    "purchase_date": r["purchase_date"],  # May be None if not provided
                    "total_amount": float(r["total_amount"] or 0),  # Convert to float
                    "tax_amount": float(r["tax_amount"] or 0),
                    "currency": r["currency"] or "USD",
                    "payment_method": r["payment_method"],
                    "purchase_time": r["purchase_time"],
                }
            )
        return bills
    finally:
        conn.close()


def get_bill_items(bill_id: int) -> List[Dict]:
    """Fetch all line items for a specific invoice.
    
    Args:
        bill_id: Primary key of bill to fetch items for
    
    Returns:
        List of dictionaries containing line item data with renamed columns:
        - description -> item_name (matches OCR extraction keys)
        - total_price -> item_total (consistent with app naming)
        - s_no added as sequential number for display purposes
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT item_id AS id,
                   description AS item_name,
                   quantity,
                   unit_price,
                   total_price AS item_total
            FROM lineitems
            WHERE bill_id = ?
            ORDER BY item_id
            """,
            (bill_id,),
        )
        rows = cursor.fetchall()
        items = []
        # Add sequential numbering for display in tables
        for idx, r in enumerate(rows, 1):
            items.append(
                {
                    "s_no": idx,  # Serial number for table display
                    "item_name": r["item_name"] or "",
                    "quantity": r["quantity"] or 0,
                    "unit_price": float(r["unit_price"] or 0),  # Convert to float
                    "item_total": float(r["item_total"] or 0),
                }
            )
        return items
    finally:
        conn.close()


def get_bill_details(bill_id: int) -> Optional[Dict]:
    """Fetch complete bill data including invoice header and all line items.
    
    Args:
        bill_id: Primary key of bill to fetch
    
    Returns:
        Dictionary containing complete bill data with both header and items,
        or None if bill_id not found.
    
    Note: Includes calculated fields (subtotal) and placeholder fields
    (purchase_time, payment_method) for backward compatibility.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bill_id AS id,
                   vendor_name,
                   purchase_date,
                   purchase_time,
                   subtotal,
                   total_amount,
                   tax_amount,
                   currency,
                   payment_method
            FROM bills
            WHERE bill_id = ?
            """,
            (bill_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None  # Bill not found in database

        # Build complete bill dictionary with stored and placeholder fields
        bill = {
            "id": row["id"],
            "vendor_name": row["vendor_name"],
            "purchase_date": row["purchase_date"],
            "purchase_time": row["purchase_time"],
            "subtotal": float(row["subtotal"] or 0),
            "discount": 0.0,  # Not stored in current schema
            "tax_amount": float(row["tax_amount"] or 0),
            "total_amount": float(row["total_amount"] or 0),
            "payment_method": row["payment_method"] or "",
            "currency": row["currency"] or "USD",
        }
        # Attach line items to complete the bill details
        bill["items"] = get_bill_items(bill_id)
        return bill
    finally:
        conn.close()


def delete_bill(bill_id: int) -> bool:
    """Delete a bill from the database.
    
    Args:
        bill_id: Primary key of bill to delete
    
    Returns:
        True if bill was deleted, False if bill_id not found
    
    Note: Line items are automatically deleted via CASCADE constraint
    defined in the database schema.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Execute delete query with bill_id parameter
        cursor.execute("DELETE FROM bills WHERE bill_id = ?", (bill_id,))
        conn.commit()
        # Check if any rows were deleted (rowcount > 0 means bill existed)
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()  # Undo changes on error
        raise e  # Re-raise for caller to handle
    finally:
        conn.close()
