import hashlib
import logging
import re
from typing import Any, Dict, Optional
import json


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def generate_dedupe_hash(event_data: Dict[str, Any]) -> str:
    """
    Generate a hash for event deduplication.
    
    Args:
        event_data: Event data dictionary
        
        Returns:
            SHA256 hash string
    """
    # Create a normalized version for hashing
    normalized = {
        'title': event_data.get('title', '').lower().strip(),
        'date_start': event_data.get('date_start', ''),
        'time_start': event_data.get('time_start', ''),
        'location': event_data.get('location', '').lower().strip() if event_data.get('location') else '',
    }
    
    # Convert to JSON string and hash
    json_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def highlight_event_fields(event_data: Dict[str, Any]) -> str:
    """
    Create a highlighted summary of event fields for CLI output.
    
    Args:
        event_data: Event data dictionary
        
        Returns:
            Formatted string with highlighted fields
    """
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    lines = []
    
    # Title (bold, white)
    title = event_data.get('title', 'No title')
    lines.append(f"{BOLD}{WHITE}Title:{END} {title}")
    
    # Date and time (green)
    date = event_data.get('date_start', 'No date')
    time_start = event_data.get('time_start', 'No start time')
    time_end = event_data.get('time_end', '')
    time_str = f"{time_start}"
    if time_end:
        time_str += f" - {time_end}"
    lines.append(f"{GREEN}When:{END} {date} at {time_str}")
    
    # Location (blue)
    location = event_data.get('location', 'No location')
    lines.append(f"{BLUE}Where:{END} {location}")
    
    # Organizer (yellow)
    organizer = event_data.get('organizer', 'No organizer')
    lines.append(f"{YELLOW}Organizer:{END} {organizer}")
    
    # Food info (magenta)
    food_type = event_data.get('food_type')
    food_quantity = event_data.get('food_quantity_hint')
    if food_type or food_quantity:
        food_str = food_type or 'Food provided'
        if food_quantity:
            food_str += f" ({food_quantity})"
        lines.append(f"{MAGENTA}Food:{END} {food_str}")
    
    # URLs (cyan)
    urls = event_data.get('urls', [])
    if urls:
        url_str = ', '.join(str(url) for url in urls)
        lines.append(f"{CYAN}Links:{END} {url_str}")
    
    # Description (truncated)
    description = event_data.get('description', '')
    if description:
        # Truncate long descriptions
        if len(description) > 100:
            description = description[:97] + "..."
        lines.append(f"Description: {description}")
    
    return '\n'.join(lines)


def extract_mailing_list_from_subject(subject: str) -> Optional[str]:
    """
    Extract mailing list name from subject line with [XXXXX] format.
    
    Args:
        subject: Email subject line
        
    Returns:
        Mailing list name if found, None otherwise
    """
    if not subject:
        return None
    
    # Match [XXXXX] at the beginning of the subject
    match = re.match(r'^\[([^\]]+)\]', subject.strip())
    if match:
        return match.group(1)
    
    return None


def format_event_summary(events: list) -> str:
    """
    Format a summary of multiple events.
    
    Args:
        events: List of event dictionaries
        
        Returns:
            Formatted summary string
    """
    if not events:
        return "No events found."
    
    lines = [f"Found {len(events)} event(s):", ""]
    
    for i, event in enumerate(events, 1):
        lines.append(f"--- Event {i} ---")
        lines.append(highlight_event_fields(event))
        lines.append("")
    
    return '\n'.join(lines)
