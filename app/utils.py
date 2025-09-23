"""
Utility functions for text normalization and safe string operations.
"""
import re
import unicodedata
from typing import Any, Optional


def norm_text(s: Any) -> str:
    """
    Null-safe text normalization.
    
    Args:
        s: Any value to normalize
        
    Returns:
        Normalized string, empty string if input is None or not a string
    """
    if not isinstance(s, str):
        return ""
    
    # Normalize unicode and convert to lowercase
    s = unicodedata.normalize("NFKC", s).casefold()
    
    # Collapse whitespace and strip
    return re.sub(r"\s+", " ", s).strip()


def event_dedupe_key(title: Any, date_start: Any, time_start: Any, location: Any) -> str:
    """
    Generate a deterministic deduplication key for events.
    
    Args:
        title: Event title
        date_start: Event start date
        time_start: Event start time
        location: Event location
        
    Returns:
        MD5 hash of normalized event components
    """
    import hashlib
    
    base = "|".join([
        norm_text(title),
        str(date_start or ""),
        norm_text(time_start),
        norm_text(location),
    ])
    
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def safe_lower(s: Any) -> str:
    """
    Safe lowercase conversion that handles None values.
    
    Args:
        s: String to convert to lowercase
        
    Returns:
        Lowercase string, empty string if input is None
    """
    return norm_text(s)


def normalize_food_name(food_name: Any) -> str:
    """
    Normalize food name for consistent storage and lookup.
    
    Args:
        food_name: Food name to normalize
        
    Returns:
        Normalized food name
    """
    return norm_text(food_name)

