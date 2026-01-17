from datetime import datetime

def normalize_vendor(name: str):
    if not name:
        return "UNKNOWN"
    return " ".join(name.upper().split())

def normalize_currency(value: str):
    if not value:
        return "USD"
    return value.upper()


def normalize_date(date_str: str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue
    return ""

