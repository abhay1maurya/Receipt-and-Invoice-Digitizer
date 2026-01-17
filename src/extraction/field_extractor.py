from .regex_patterns import INVOICE_PATTERNS, TIME_PATTERNS, DATE_PATTERNS, CURRENCY_PATTERNS

import re

def extract_invoice_number(text: str):
    text = text.upper()
    for pattern in INVOICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(2)
    return None

def extract_purchase_date(text: str):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(1))
    return None

def extract_purchase_time(text: str):
    for pattern in TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return normalize_time(match.group(1))
    return None

def extract_purchase_currency(text: str):
    for pattern in CURRENCY_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return normalize_currency(match.group(1))
    return None
