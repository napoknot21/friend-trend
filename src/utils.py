from __future__ import annotations


import datetime as dt
from typing import Optional, List 


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