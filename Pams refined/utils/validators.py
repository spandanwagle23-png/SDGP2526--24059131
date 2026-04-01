import re
from datetime import datetime

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(r'^\+?[\d]{10,13}$', cleaned))

def validate_ni_number(ni):
    """UK NI number: 2 letters, 6 digits, 1 letter (A-D)"""
    pattern = r'^[A-CEGHJ-PR-TW-Z]{2}[0-9]{6}[A-D]$'
    return bool(re.match(pattern, ni.upper().replace(" ", "")))

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit."
    return True, ""

def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False

def format_currency(amount):
    return f"£{amount:,.2f}"

def format_date(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return str(dt)
