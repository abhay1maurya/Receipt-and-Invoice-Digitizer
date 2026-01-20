# NLP-based heuristic vendor name extraction (Improved)
# Designed for receipts/invoices with noisy OCR output

import re
from typing import List, Tuple

STOPWORDS = {
    "INVOICE", "RECEIPT", "TAX", "GST", "VAT", "TOTAL",
    "BILL", "DATE", "TIME", "CASH", "CARD", "AMOUNT",
    "CHANGE", "BALANCE"
}

LEGAL_SUFFIXES = {
    "LTD", "LIMITED", "PVT", "PRIVATE", "LLP",
    "INC", "CORP", "CO", "COMPANY", "SDN", "BHD"
}

ADDRESS_KEYWORDS = {
    "ROAD", "STREET", "ST", "RD", "AVE", "AVENUE",
    "LANE", "JALAN", "NAGAR", "SECTOR",
    "CITY", "STATE", "COUNTRY", "PIN", "ZIP"
}

PUNCTUATION_RE = re.compile(r"[^\w\s&\-.]")

def _normalize_line(line: str) -> str:
    """Clean OCR noise while preserving business naming style."""
    line = PUNCTUATION_RE.sub("", line)
    return re.sub(r"\s{2,}", " ", line).strip()


def score_line(line: str, index: int) -> float:
    """
    Assign a heuristic score estimating likelihood of being a vendor name.
    """
    score = 0.0
    line = _normalize_line(line)

    if not line:
        return 0.0

    tokens = line.split()
    token_count = len(tokens)

    # 1. Positional bias (top-heavy)
    score += max(0, 12 - index)

    # 2. Penalize numeric-heavy lines
    digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
    if digit_ratio > 0.15:
        score -= 4

    # 3. Address detection (strong penalty)
    if any(tok.upper() in ADDRESS_KEYWORDS for tok in tokens):
        score -= 5

    # 4. Case structure (ALL CAPS or Title Case)
    if line.isupper():
        score += 4
    elif line.istitle():
        score += 2

    # 5. Legal suffix bonus
    if any(tok.upper() in LEGAL_SUFFIXES for tok in tokens):
        score += 4

    # 6. STOPWORDS penalty (soft)
    stopword_hits = sum(tok.upper() in STOPWORDS for tok in tokens)
    score -= stopword_hits * 1.5

    # 7. Length heuristic
    if 2 <= token_count <= 6:
        score += 3
    elif token_count > 10:
        score -= 4

    # 8. Symbol-heavy penalty
    if re.search(r"[#@:]", line):
        score -= 2

    return round(score, 2)


def extract_vendor_name_nlp(ocr_text: str) -> str:
    """
    Extract vendor name using NLP heuristics from OCR text.
    """
    if not ocr_text:
        return ""

    lines = [
        _normalize_line(line)
        for line in ocr_text.splitlines()
        if len(line.strip()) >= 3
    ]

    if not lines:
        return ""

    candidates: List[Tuple[float, str]] = [
        (score_line(line, idx), line)
        for idx, line in enumerate(lines[:20])
    ]

    candidates.sort(key=lambda x: x[0], reverse=True)

    best_score, best_line = candidates[0]

    # Confidence gate
    if best_score < 4:
        return ""

    return best_line
