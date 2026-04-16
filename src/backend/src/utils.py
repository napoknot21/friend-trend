from __future__ import annotations


import datetime as dt
import re
from typing import Optional, List 


EMAIL_ADDRESS_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
FORWARDED_FROM_PATTERNS = [
    re.compile(r"^\s*(?:from|de)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
]


def str_to_date (date : Optional[str | dt.datetime | dt.date], format : str = "%Y-%m-%d") -> Optional[dt.date] :

    if date is None :
        return dt.date.today()
    
    if isinstance(date, dt.datetime) :
        return date.date()
    
    if isinstance(date, dt.date) :
        return date
    
    if isinstance(date, str) :
        return dt.datetime.strptime(date, format).date()
    
    raise TypeError(f"Unsupported date type: {type(x)}")


def date_to_str (date : Optional[str | dt.date | dt.datetime] = None, format : str = "%Y-%m-%d") -> str :
    """
    Convert a date or datetime object to a string in "YYYY-MM-DD" format.

    Args:
        date (str | datetime): The input date.

    Returns:
        str: Date string in "YYYY-MM-DD" format.
    """
    if date is None:
        date_obj = dt.datetime.now()

    elif isinstance(date, dt.datetime):
        date_obj = date

    elif isinstance(date, dt.date):  # handles plain date (without time)
        date_obj = dt.datetime.combine(date, dt.time.min) # This will add 00 for the time

    elif isinstance(date, str) :

        try:
            date_obj = dt.datetime.strptime(date, format)

        except ValueError :
            
            try :
                date_obj = dt.datetime.fromisoformat(date)
            
            except ValueError :
                raise ValueError(f"Unrecognized date format: '{date}'")
    
    else :
        raise TypeError("date must be a string, datetime, or None")

    return date_obj.strftime(format)


def clean_for_llm(text: str) -> str:
    """
    Cleans raw email text to save LLM tokens and remove noise.
    - Removes URLs
    - Removes forwarded email headers (">")
    - Removes excessive newlines
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove standard forwarded headers
    text = re.sub(r'(From|To|Sent|Subject):.*', '', text, flags=re.IGNORECASE)
    
    # Remove lines starting with >
    lines = [line.strip() for line in text.split('\n') if not line.strip().startswith('>')]
    
    # Rejoin and remove excessive blank lines
    cleaned = '\n'.join(lines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def extract_email_address(text: str) -> Optional[str]:
    if not text:
        return None
    match = EMAIL_ADDRESS_RE.search(text)
    if not match:
        return None
    return match.group(0).lower()


def extract_forwarded_sender(text: str) -> Optional[str]:
    if not text:
        return None

    for pattern in FORWARDED_FROM_PATTERNS:
        for match in pattern.finditer(text):
            email = extract_email_address(match.group(1))
            if email:
                return email

    return None


def resolve_sender_hint(sender: str, text: str = "") -> str:
    return extract_forwarded_sender(text) or str(sender or "")
