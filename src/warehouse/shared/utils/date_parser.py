"""
Date parsing utilities for flexible date format handling.
"""

import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)


def parse_date(date_string: str) -> date:
    """
    Parse date from various formats with fallback to today.

    Args:
        date_string: Date string in various formats

    Returns:
        Parsed date object, today's date if parsing fails

    Supported formats:
        - DD.MM.YYYY (German format)
        - DD/MM/YYYY
        - YYYY-MM-DD (ISO format)
        - DD-MM-YYYY
        - DD.MM.YY (2-digit year)
        - DD/MM/YY (2-digit year)
    """
    if not date_string or date_string.strip().lower() in ['', 'null', 'none']:
        logger.debug("Empty or null date string, using today's date")
        return date.today()

    date_string = date_string.strip()

    # Various date formats to try
    formats = [
        '%d.%m.%Y',    # DD.MM.YYYY (German format)
        '%d/%m/%Y',    # DD/MM/YYYY
        '%Y-%m-%d',    # YYYY-MM-DD (ISO format)
        '%d-%m-%Y',    # DD-MM-YYYY
        '%d.%m.%y',    # DD.MM.YY (2-digit year)
        '%d/%m/%y',    # DD/MM/YY (2-digit year)
        '%m/%d/%Y',    # MM/DD/YYYY (US format)
        '%m-%d-%Y',    # MM-DD-YYYY (US format)
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_string, fmt).date()
            logger.debug(f"Successfully parsed '{date_string}' as {parsed_date} using format {fmt}")
            return parsed_date
        except ValueError:
            continue

    # Fallback to today's date
    logger.warning(f"Could not parse date: '{date_string}' - using today's date")
    return date.today()


def parse_date_optional(date_string: str) -> Optional[date]:
    """
    Parse date from various formats with optional return.

    Args:
        date_string: Date string in various formats

    Returns:
        Parsed date object or None if parsing fails
    """
    if not date_string or date_string.strip().lower() in ['', 'null', 'none']:
        return None

    try:
        # Use the main parse_date function but catch today's date fallback
        today = date.today()
        parsed = parse_date(date_string)

        # If it's today and we didn't explicitly pass today, it was a fallback
        if parsed == today and date_string.strip() != today.strftime('%Y-%m-%d'):
            return None

        return parsed
    except Exception:
        return None


def format_date_german(date_obj: date) -> str:
    """
    Format date in German format (DD.MM.YYYY).

    Args:
        date_obj: Date object to format

    Returns:
        Formatted date string
    """
    return date_obj.strftime('%d.%m.%Y')


def format_date_iso(date_obj: date) -> str:
    """
    Format date in ISO format (YYYY-MM-DD).

    Args:
        date_obj: Date object to format

    Returns:
        Formatted date string
    """
    return date_obj.strftime('%Y-%m-%d')