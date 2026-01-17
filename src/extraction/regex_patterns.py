# Regular expression patterns for extracting structured data from receipt/invoice images
# These patterns are used by the extraction module to identify and parse key fields
# All patterns are case-insensitive and support multiple common formats

import re

# DATE_PATTERNS: Regex patterns to match various date formats commonly found on receipts
# Used to extract purchase date from OCR text
# Supports multiple international date formats with different separators
DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",          # Format: 2026-01-15 (ISO 8601 format, most common in databases)
    r"\b(\d{2}/\d{2}/\d{4})\b",          # Format: 15/01/2026 (DD/MM/YYYY, common in India/EU)
    r"\b(\d{2}-\d{2}-\d{4})\b",          # Format: 15-01-2026 (DD-MM-YYYY, alternative format)
    r"\b(\d{2}\.\d{2}\.{4})\b",          # Format: 15.01.2026 (DD.MM.YYYY, common in Germany/Europe)
]

# TIME_PATTERNS: Regex patterns to match time formats found on receipts
# Used to extract transaction time (purchase_time) from OCR text
# Supports both HH:MM and HH:MM:SS formats
TIME_PATTERNS = [
    r"\b(\d{2}:\d{2})\b",                # Format: 14:32 (HH:MM, basic time format)
    r"\b(\d{2}:\d{2}:\d{2})\b",          # Format: 14:32:10 (HH:MM:SS, with seconds)
]

# INVOICE_PATTERNS: Regex patterns to match invoice/bill/receipt numbers
# Different receipts use different labeling conventions (Invoice, Bill, Receipt, INV, etc.)
# Extracts the number/ID that uniquely identifies the transaction
INVOICE_PATTERNS = [
    r"(invoice|bill|receipt)[\s:#-]*([A-Z0-9\-\/]+)",  # Match "Invoice: ABC123" or "Bill #456" patterns
    r"\bINV[\s\-:]?([A-Z0-9]+)\b",                      # Match "INV 001" or "INV-123" format
    r"\bBILL[\s\-:]?([A-Z0-9\-\/]+)\b",                 # Match "BILL 789" or "BILL-456" format
]

# CURRENCY_PATTERNS: Dictionary mapping currency codes to their regex patterns
# Each entry contains patterns for both currency symbol and currency code
# Used to identify and normalize currency (e.g., USD, INR, EUR, GBP, MYR)
CURRENCY_PATTERNS = {
    "USD": r"\bUSD\b|\$",                               # Match "USD" text or "$" symbol
    "INR": r"\bINR\b|₹",                                # Match "INR" text or "₹" symbol (Indian Rupee)
    "MYR": r"\bMYR\b|\bRM\b",                            # Match "MYR" text or "RM" symbol (Malaysian Ringgit)
    "EUR": r"\bEUR\b|€",                                # Match "EUR" text or "€" symbol (Euro)
    "GBP": r"\bGBP\b|£",                                # Match "GBP" text or "£" symbol (British Pound)
}

# PAYMENT_METHOD_PATTERNS: Dictionary mapping payment methods to their regex patterns
# Used to identify how the payment was made (cash, card, digital wallets, etc.)
# Note: Key has typo "PATERNS" kept for backward compatibility with existing code
PAYMENT_METHOD_PATERNS = {
    "CASH": r"\bCASH\b",                                # Match "CASH" payment method
    "CARD": r"\bCARD\b|\bCREDIT\b|\bDEBIT\b",          # Match "CARD", "CREDIT", or "DEBIT" card payments
    "UPI": r"\bUPI\b",                                  # Match "UPI" (Unified Payments Interface, India)
    "NET BANKING": r"\bNET BANKING\b|\bONLINE\b",      # Match "NET BANKING" or "ONLINE" payment methods
    "WALLET": r"\bPAYTM\b|\bPHONEPE\b|\bGPAY\b",       # Match digital wallets (Paytm, PhonePe, Google Pay)
}

# TAX_PATTERNS: Regex patterns to match various tax-related labels on receipts
# Different regions use different tax terms (GST, VAT, CGST, SGST, IGST, etc.)
# Used to identify tax line items in the receipt text
TAX_PATTERNS = [
    r"\bTAX\b",                                         # Generic "TAX" label
    r"\bGST\b",                                         # "GST" (Goods and Services Tax, India)
    r"\bVAT\b",                                         # "VAT" (Value Added Tax, Europe)
    r"\bCGST\b",                                        # "CGST" (Central GST, India)
    r"\bSGST\b",                                        # "SGST" (State GST, India)
    r"\bIGST\b",                                        # "IGST" (Integrated GST, India)
]

# TOTAL_LABEL_PATTERNS: Regex patterns to match total amount labels
# Used to identify the final amount to be paid (after tax and discounts)
# Different receipts use different terminology (TOTAL, AMOUNT DUE, GRAND TOTAL, etc.)
TOTAL_LABEL_PATTERNS = [
    r"\bTOTAL\b",                                       # Match "TOTAL" label
    r"\bAMOUNT DUE\b",                                  # Match "AMOUNT DUE" label
    r"\bGRAND TOTAL\b",                                 # Match "GRAND TOTAL" label
]

# SUBTOTAL_LABEL_PATTERNS: Regex patterns to match subtotal labels
# Subtotal is the amount before tax and additional charges are applied
# Used to distinguish between subtotal and final total in receipt parsing
SUBTOTAL_LABEL_PATTERNS = [
    r"\bSUBTOTAL\b",                                    # Match "SUBTOTAL" (one word)
    r"\bSUB TOTAL\b",                                   # Match "SUB TOTAL" (two words)
]

# AMOUNT_PATTERN: Regex pattern to match monetary amounts with optional thousand separators
# Matches amounts like: 100, 1,000, 1,000.00, 99.99
# Used for extracting prices, totals, taxes, and other monetary values
AMOUNT_PATTERN = r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b"

# LINE_ITEM_PATTERN: Regex pattern to match individual line items in receipt
# Captures: item number/code, item name, quantity, unit price, and total price
# Pattern expects format: SERNO  ITEMNAME  QTY  UNITPRICE
# Note: This pattern may need adjustment based on specific receipt format variations
LINE_ITEM_PATTERN = r"(\d+)\s+([A-Z0-9\s\-\.]+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)"