import re
import logging
from typing import Optional, List
from schema import ParsedEvent

logger = logging.getLogger(__name__)


class PostProcessor:
    """Post-processing heuristics for improving parsed event data."""
    
    @staticmethod
    def normalize_time(time_str: Optional[str]) -> Optional[str]:
        """
        Normalize time string to HH:MM format.
        
        Args:
            time_str: Time string in various formats
            
        Returns:
            Normalized time string in HH:MM format or None
        """
        if not time_str:
            return None
            
        # Remove extra whitespace
        time_str = time_str.strip()
        
        # Handle various time formats
        patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)',  # 12-hour format
            r'(\d{1,2}):(\d{2})',  # 24-hour format
            r'(\d{1,2})\s*(am|pm|AM|PM)',  # Hour only with am/pm
        ]
        
        for pattern in patterns:
            match = re.search(pattern, time_str, re.IGNORECASE)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                
                # Check if we have minutes (pattern 1 and 2 have minutes)
                if len(groups) >= 2 and groups[1].isdigit():
                    minute = int(groups[1])
                else:
                    minute = 0
                
                # Check if we have AM/PM (patterns 1 and 3 have AM/PM)
                am_pm = None
                if len(groups) >= 3 and groups[2] in ['am', 'pm', 'AM', 'PM']:
                    am_pm = groups[2]
                elif len(groups) >= 2 and groups[1] in ['am', 'pm', 'AM', 'PM']:
                    am_pm = groups[1]
                
                # Convert to 24-hour format
                if am_pm and am_pm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif am_pm and am_pm.lower() == 'am' and hour == 12:
                    hour = 0
                
                # Validate hour and minute ranges
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
        
        return None

    @staticmethod
    def infer_end_time(start_time: Optional[str], description: Optional[str]) -> Optional[str]:
        """
        Infer end time from start time and description.
        
        Args:
            start_time: Start time in HH:MM format
            description: Event description
            
        Returns:
            Inferred end time in HH:MM format or None
        """
        if not start_time or not description:
            return None
            
        # Look for duration patterns
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?',
            r'(\d+)-(\d+)',  # Time range like "5-6 PM"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                if '-' in pattern:  # Time range
                    try:
                        start_hour = int(match.group(1))
                        end_hour = int(match.group(2))
                        # Handle PM times in range
                        if "PM" in description.upper() and end_hour < 12:
                            end_hour += 12
                        return f"{end_hour:02d}:00"
                    except (ValueError, IndexError):
                        continue
                else:  # Duration
                    try:
                        duration = int(match.group(1))
                        if 'hour' in pattern or 'hr' in pattern:
                            # Add hours to start time
                            start_hour, start_minute = map(int, start_time.split(':'))
                            end_hour = (start_hour + duration) % 24
                            return f"{end_hour:02d}:{start_minute:02d}"
                        elif 'minute' in pattern or 'min' in pattern:
                            # Add minutes to start time
                            start_hour, start_minute = map(int, start_time.split(':'))
                            total_minutes = start_hour * 60 + start_minute + duration
                            end_hour = (total_minutes // 60) % 24
                            end_minute = total_minutes % 60
                            return f"{end_hour:02d}:{end_minute:02d}"
                    except (ValueError, IndexError):
                        continue
        
        return None

    @staticmethod
    def normalize_location(location: Optional[str]) -> Optional[str]:
        """
        Normalize location string.
        
        Args:
            location: Raw location string
            
        Returns:
            Normalized location string
        """
        if not location:
            return None
            
        # Remove extra whitespace and normalize
        location = re.sub(r'\s+', ' ', location.strip())
        
        # Remove common prefixes/suffixes that don't add value
        location = re.sub(r'^(location|venue):\s*', '', location, flags=re.IGNORECASE)
        location = re.sub(r'\s*\(.*?\)$', '', location)  # Remove trailing parenthetical info
        
        return location if location else None

    @staticmethod
    def extract_food_info(description: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Extract food type and quantity hint from description.
        
        Args:
            description: Event description
            
        Returns:
            Tuple of (food_type, food_quantity_hint)
        """
        if not description:
            return None, None
            
        description_lower = description.lower()
        
        # Known food vendors/brands
        food_vendors = [
            'bonchon', 'pizza', 'sushi', 'chinese', 'indian', 'mexican', 
            'italian', 'thai', 'korean', 'japanese', 'mediterranean',
            'subway', 'chipotle', 'panera', 'starbucks', 'dunkin'
        ]
        
        food_type = None
        quantity_hint = None
        
        # Check for specific vendors
        for vendor in food_vendors:
            if vendor in description_lower:
                food_type = vendor.title()
                break
        
        # If no specific vendor found, check for generic food mentions
        if not food_type:
            generic_food_patterns = [
                r'dinner\s+provided',
                r'lunch\s+provided',
                r'breakfast\s+provided',
                r'food\s+provided',
                r'refreshments\s+provided',
                r'catered\s+by',
                r'catering\s+by',
                r'light\s+snacks',
                r'limited\s+snacks',
            ]
            
            for pattern in generic_food_patterns:
                if re.search(pattern, description_lower):
                    food_type = "Catered"
                    break
        
        # Extract quantity hints
        quantity_patterns = [
            r'dinner\s+provided',
            r'lunch\s+provided',
            r'light\s+snacks',
            r'heavy\s+snacks',
            r'refreshments\s+provided',
            r'limited\s+snacks',
            r'while\s+supplies\s+last',
            r'first\s+come\s+first\s+served',
        ]
        
        for pattern in quantity_patterns:
            match = re.search(pattern, description_lower)
            if match:
                quantity_hint = match.group(0)
                break
        
        return food_type, quantity_hint

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        Extract URLs from text.
        
        Args:
            text: Text to search for URLs
            
        Returns:
            List of found URLs
        """
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates

    @classmethod
    def process_event(cls, event: ParsedEvent) -> ParsedEvent:
        """
        Apply all post-processing heuristics to an event.
        
        Args:
            event: ParsedEvent to process
            
        Returns:
            Processed ParsedEvent
        """
        # Normalize times
        if event.time_start:
            event.time_start = cls.normalize_time(event.time_start)
        
        if event.time_end:
            event.time_end = cls.normalize_time(event.time_end)
        elif event.time_start and event.description:
            # Try to infer end time
            event.time_end = cls.infer_end_time(event.time_start, event.description)
        
        # Normalize location
        if event.location:
            event.location = cls.normalize_location(event.location)
        
        # Extract food information
        if event.description:
            food_type, food_quantity_hint = cls.extract_food_info(event.description)
            if food_type and not event.food_type:
                event.food_type = food_type
            if food_quantity_hint and not event.food_quantity_hint:
                event.food_quantity_hint = food_quantity_hint
        
        # Extract additional URLs from description
        if event.description:
            additional_urls = cls.extract_urls(event.description)
            for url in additional_urls:
                if url not in [str(u) for u in event.urls]:
                    try:
                        from pydantic import HttpUrl
                        event.urls.append(HttpUrl(url))
                    except Exception:
                        logger.warning(f"Invalid URL found: {url}")
        
        return event
