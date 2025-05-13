import re

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone number validation (international format)"""
    pattern = r'^\+?[0-9\s\-\(\)]{7,}$'
    return re.match(pattern, phone) is not None