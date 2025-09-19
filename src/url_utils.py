"""
URL normalization utilities for the event parser.
"""

import re
from urllib.parse import urlsplit
from typing import List, Optional

SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*://')
DOMAIN_LIKE_RE = re.compile(r'^[\w.-]+\.[a-zA-Z]{2,}(/.*)?$')


def normalize_url(u: str) -> Optional[str]:
    """
    Normalize a URL string.
    
    Args:
        u: URL string to normalize
        
    Returns:
        Normalized URL or None if invalid
    """
    if not u:
        return None
    u = u.strip()
    if SCHEME_RE.match(u):
        return u
    if DOMAIN_LIKE_RE.match(u):
        return f'https://{u}'
    return None


def normalize_urls(urls: List[str]) -> List[str]:
    """
    Normalize a list of URLs, removing duplicates and invalid ones.
    
    Args:
        urls: List of URL strings
        
    Returns:
        List of normalized, unique URLs
    """
    seen = set()
    out = []
    for u in urls or []:
        v = normalize_url(u)
        if v and urlsplit(v).netloc and v not in seen:
            out.append(v)
            seen.add(v)
    return out

