"""Improved event parsing logic for Harvard mailing list messages."""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import dateparser
from bs4 import BeautifulSoup

from models import GmailMessage, Event, Config


class ImprovedEventParser:
    """Improved parser for extracting event information from Gmail messages."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
        
        # Common Harvard building patterns (more comprehensive)
        self.building_patterns = [
            # Specific buildings with room numbers
            r'\b(Sever|Science Center|SEC|Maxwell-Dworkin|MD|Pierce Hall|Smith Campus Center|Sanders|Boylston|Cabot|Winthrop)\s+\d+',
            # Building names without room numbers
            r'\b(Sever|Science Center|SEC|Maxwell-Dworkin|MD|Pierce Hall|Smith Campus Center|Sanders Theatre|Boylston Hall|Cabot Science Library|Winthrop House)\b',
            # Common abbreviations
            r'\b(SEC|MD|SCC)\b',
            # Dining halls and common spaces
            r'\b(Pfoho Dining Hall|Annenberg|Dunster|Eliot|Kirkland|Leverett|Lowell|Mather|Quincy|Winthrop)\s+(Dining Hall|House|Common Room)?\b',
            # Outdoor locations
            r'\b(Harvard Yard|Science Center Plaza|Memorial Church|Widener Library|Lamont Library)\b'
        ]
        
        # Event type patterns (improved)
        self.type_patterns = {
            'info session': [
                r'\b(info session|information session|kickoff|comp)\b',
                r'\b(recruiting|recruitment)\b',
                r'\b(company presentation|corporate presentation)\b',
                r'\b(join|sign up|register)\b.*\b(comp|program|organization)\b'
            ],
            'workshop': [
                r'\b(workshop|tutorial|training|hands-on)\b',
                r'\b(learn|teach|instruction)\b.*\b(workshop|session)\b'
            ],
            'tech talk': [
                r'\b(tech talk|technical talk|lecture|presentation)\b',
                r'\b(talk|speaker|speaking)\b.*\b(ai|machine learning|computer science|cs)\b',
                r'\b(ai|machine learning|computer science|cs)\b.*\b(talk|presentation|lecture)\b'
            ],
            'career': [
                r'\b(career|careers|job fair|networking|coffee chat)\b',
                r'\b(interview|resume|cv|internship|opportunity)\b',
                r'\b(recruiting|recruitment|hiring)\b'
            ],
            'social': [
                r'\b(social|mixer|party|gathering|game night)\b',
                r'\b(food|pizza|boba|dumpling|snack|refreshment)\b',
                r'\b(pfood|drop|free meal|dinner|lunch)\b',
                r'\b(join|come|hang out|meet)\b.*\b(fun|social|community)\b'
            ],
            'application deadline': [
                r'\b(DUE|DEADLINE|deadline|due)\b',
                r'\b(application|apply)\b.*\b(deadline|due|closes)\b',
                r'\b(deadline|due)\b.*\b(application|apply|submit)\b'
            ],
            'meeting': [
                r'\b(meeting|hoco|house committee)\b',
                r'\b(tonight|tomorrow|today)\b.*\b(meeting|gathering)\b'
            ]
        }
        
        # Food keywords (expanded)
        self.food_keywords = [
            'pizza', 'boba', 'dumpling', 'snack', 'refreshment', 'cater',
            'lunch', 'dinner', 'food', 'meal', 'treat', 'drink', 'pfood',
            'drop', 'free meal', 'dining', 'eat', 'hungry'
        ]
        
        # Cost keywords (expanded)
        self.cost_keywords = [
            '$', 'ticket', 'fee', 'cost', 'price', 'charge', 'non-huid',
            'payment', 'register', 'buy', 'purchase', 'paid', 'money'
        ]
    
    def parse_message(self, message: GmailMessage) -> Event:
        """Parse a Gmail message into an Event."""
        # Extract list tag from subject (handle forwarded emails)
        list_tag, title = self.extract_list_from_subject(message.subject)
        
        # Extract actual email content (handle forwarded emails)
        actual_content = self.extract_actual_content(message.body_text, message.subject)
        
        # Parse event times
        start, end, event_type = self.parse_event_times(message.subject, actual_content, message.date)
        
        # Parse location
        location = self.parse_location(actual_content, message.subject)
        
        # Parse event type if not already determined
        if not event_type:
            event_type = self.parse_type(message.subject, actual_content)
        
        # Check for food and free status
        food = self.has_food(message.subject + " " + actual_content)
        free = self.is_free(message.subject + " " + actual_content)
        
        # Extract links
        links = self.extract_links(actual_content)
        
        # Calculate confidence score
        confidence = self.calculate_confidence(start, location, event_type)
        
        # Create raw excerpt
        raw_excerpt = self.create_excerpt(actual_content)
        
        # Generate event ID (use Gmail message ID)
        event_id = message.id
        
        # Timestamps
        now = datetime.now().isoformat()
        
        return Event(
            id=event_id,
            thread_id=message.thread_id,
            source_list_tag=list_tag,
            source_list_id=message.list_id,
            message_id=message.message_id,
            subject=message.subject,
            received_utc=message.date,
            title=title,
            start=start,
            end=end,
            timezone=self.timezone,
            location=location,
            etype=event_type,
            food=1 if food else 0,
            free=1 if free else 0,
            links=json.dumps(links),
            raw_excerpt=raw_excerpt,
            confidence=confidence,
            created_at=now,
            updated_at=now
        )
    
    def extract_list_from_subject(self, subject: str) -> Tuple[str, str]:
        """Extract list tag from subject line, handling forwarded emails."""
        # Handle forwarded emails
        if subject.startswith('Fwd:') or subject.startswith('Re:'):
            # Look for [TAG] pattern after the prefix
            match = re.search(r'\[([^\]]+)\]', subject)
            if match:
                list_tag = match.group(1).strip()
                # Clean up the title by removing the prefix and list tag
                clean_subject = re.sub(r'^(Fwd:|Re:)\s*', '', subject)
                clean_subject = re.sub(r'\[([^\]]+)\]\s*', '', clean_subject, count=1)
                return list_tag, clean_subject.strip()
        
        # Look for [TAG] pattern at the beginning
        match = re.match(r'^\[([^\]]+)\]\s*(.*)$', subject.strip())
        if match:
            list_tag = match.group(1).strip()
            clean_subject = match.group(2).strip()
            return list_tag, clean_subject
        
        # Fallback: use first word or "unknown"
        words = subject.split()
        if words:
            return words[0].strip('[]'), subject
        else:
            return "unknown", subject
    
    def extract_actual_content(self, body_text: str, subject: str) -> str:
        """Extract the actual email content, handling forwarded emails."""
        if not body_text:
            return ""
        
        # Check if this is a forwarded email
        if "---------- Forwarded message ---------" in body_text:
            # Extract the forwarded content
            parts = body_text.split("---------- Forwarded message ---------")
            if len(parts) > 1:
                forwarded_content = parts[1]
                # Remove the forwarding headers
                lines = forwarded_content.split('\n')
                content_lines = []
                skip_headers = True
                
                for line in lines:
                    if skip_headers:
                        # Skip until we find the actual content
                        if line.strip() and not line.startswith('From:') and not line.startswith('Date:') and not line.startswith('Subject:') and not line.startswith('To:'):
                            skip_headers = False
                            content_lines.append(line)
                    else:
                        content_lines.append(line)
                
                return '\n'.join(content_lines)
        
        # For regular emails, remove mailing list footers
        lines = body_text.split('\n')
        content_lines = []
        
        for line in lines:
            # Skip mailing list footers
            if any(footer in line.lower() for footer in [
                'mailing list', 'unsubscribe', 'to unsubscribe', '_________________________________',
                'pfoho-open mailing list', 'hcs-discuss mailing list'
            ]):
                break
            content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def parse_event_times(self, subject: str, body_text: str, received_dt: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse event start and end times from subject and body."""
        text = f"{subject} {body_text}"
        
        # Check for deadline pattern first
        deadline_match = re.search(r'\b(DUE|DEADLINE)\s+.*?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', text, re.IGNORECASE)
        if deadline_match:
            time_str = deadline_match.group(2)
            try:
                parsed_time = dateparser.parse(
                    time_str,
                    settings={
                        'PREFER_DATES_FROM': 'future',
                        'TIMEZONE': self.timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                if parsed_time:
                    start = parsed_time.isoformat()
                    end = (parsed_time + timedelta(minutes=1)).isoformat()
                    return start, end, "application deadline"
            except Exception:
                pass
        
        # Look for time patterns in subject first
        subject_times = self._extract_times_from_text(subject)
        if subject_times:
            start_time = subject_times[0]
            end_time = subject_times[1] if len(subject_times) > 1 else None
            return start_time, end_time, None
        
        # Look for time patterns in body
        body_times = self._extract_times_from_text(body_text)
        if body_times:
            start_time = body_times[0]
            end_time = body_times[1] if len(body_times) > 1 else None
            return start_time, end_time, None
        
        return None, None, None
    
    def _extract_times_from_text(self, text: str) -> List[Optional[str]]:
        """Extract time information from text."""
        times = []
        
        # Look for explicit time markers
        time_patterns = [
            r'🗓️\s*(.*?)(?:\n|$)',
            r'🕒\s*(.*?)(?:\n|$)',
            r'When:\s*(.*?)(?:\n|$)',
            r'Date:\s*(.*?)(?:\n|$)',
            r'Time:\s*(.*?)(?:\n|$)',
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
            r'(\d{1,2}/\d{1,2}(?:\/\d{2,4})?)',
            r'(\w+day,?\s+\w+\s+\d{1,2})',
            r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
            r'(tonight|tomorrow|today)\b',
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*(?:ET|EST|EDT)?)'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                time_text = match.group(1) if match.groups() else match.group(0)
                parsed_time = self._parse_time_string(time_text, text)
                if parsed_time:
                    times.append(parsed_time)
                    if len(times) >= 2:  # We only need start and end
                        break
            if times:
                break
        
        return times
    
    def _parse_time_string(self, time_str: str, context: str = "") -> Optional[str]:
        """Parse a time string to ISO format."""
        try:
            # Handle relative times
            if time_str.lower() in ['tonight', 'today']:
                # Use current date
                base_date = datetime.now()
                if time_str.lower() == 'tonight':
                    # Assume evening time
                    parsed = base_date.replace(hour=19, minute=0, second=0, microsecond=0)
                else:
                    parsed = base_date
                return parsed.isoformat()
            
            if time_str.lower() == 'tomorrow':
                # Use tomorrow's date
                base_date = datetime.now() + timedelta(days=1)
                parsed = base_date.replace(hour=19, minute=0, second=0, microsecond=0)
                return parsed.isoformat()
            
            # Handle month/day format without year (e.g., "9/16", "9/18")
            month_day_match = re.match(r'^(\d{1,2})/(\d{1,2})$', time_str.strip())
            if month_day_match:
                month = int(month_day_match.group(1))
                day = int(month_day_match.group(2))
                now = datetime.now()
                
                # Create date for this year first
                try:
                    parsed = datetime(now.year, month, day, 19, 0, 0)  # Default to 7 PM
                    # Only move to next year if the date is more than 30 days in the past
                    # This handles cases like "meeting notes 9/16" which might be recent
                    if parsed < now - timedelta(days=30):
                        parsed = datetime(now.year + 1, month, day, 19, 0, 0)
                    return parsed.isoformat()
                except ValueError:
                    pass  # Invalid date, fall through to dateparser
                return None  # Don't fall through to dateparser for month/day format
            
            # Parse with dateparser
            parsed = dateparser.parse(
                time_str,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'TIMEZONE': self.timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'RELATIVE_BASE': datetime.now()
                }
            )
            
            if parsed:
                # Ensure the date is reasonable (not more than 1 year in the future)
                now = datetime.now()
                if parsed.year > now.year + 1:
                    # Adjust year to current year or next year if it's a reasonable date
                    if parsed.month < now.month or (parsed.month == now.month and parsed.day < now.day):
                        parsed = parsed.replace(year=now.year + 1)
                    else:
                        parsed = parsed.replace(year=now.year)
                elif parsed.year < now.year:
                    # If it's in the past, assume it's next year
                    parsed = parsed.replace(year=now.year + 1)
                return parsed.isoformat()
        except Exception:
            pass
        return None
    
    def parse_location(self, body_text: str, subject: str = "") -> Optional[str]:
        """Parse event location from body text and subject."""
        text = f"{subject} {body_text}"
        
        # Look for explicit location markers
        location_patterns = [
            r'📍\s*(.*?)(?:\n|$)',
            r'Where:\s*(.*?)(?:\n|$)',
            r'Location:\s*(.*?)(?:\n|$)',
            r'Venue:\s*(.*?)(?:\n|$)',
            r'Address:\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                location = match.group(1).strip()
                if location and len(location) > 2:
                    return location
        
        # Look for common Harvard buildings
        for pattern in self.building_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(0)
                # Clean up the location
                location = re.sub(r'[:\*\s]+', ' ', location).strip()
                return location
        
        return None
    
    def parse_type(self, subject: str, body_text: str, fallback: Optional[str] = None) -> Optional[str]:
        """Parse event type from subject and body."""
        text = f"{subject} {body_text}".lower()
        
        for event_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return event_type
        
        return fallback
    
    def has_food(self, text: str) -> bool:
        """Check if event mentions food."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.food_keywords)
    
    def is_free(self, text: str) -> bool:
        """Check if event is free."""
        text_lower = text.lower()
        return not any(keyword in text_lower for keyword in self.cost_keywords)
    
    def extract_links(self, text: str) -> List[str]:
        """Extract links from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        links = re.findall(url_pattern, text)
        
        # Prioritize Eventbrite, Google Forms, and registration links
        prioritized_links = []
        other_links = []
        
        for link in links:
            if any(domain in link.lower() for domain in ['eventbrite', 'google.com/forms', 'forms.gle', 'signup', 'register', 'rsvp']):
                prioritized_links.append(link)
            else:
                other_links.append(link)
        
        # Return up to 5 links, prioritizing registration forms
        return (prioritized_links + other_links)[:5]
    
    def calculate_confidence(self, start: Optional[str], location: Optional[str], event_type: Optional[str]) -> int:
        """Calculate confidence score (0-3)."""
        score = 0
        if start:
            score += 1
        if location:
            score += 1
        if event_type:
            score += 1
        return score
    
    def create_excerpt(self, body_text: str, max_length: int = 200) -> str:
        """Create a short excerpt from body text."""
        if not body_text:
            return ""
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', body_text.strip())
        
        if len(text) <= max_length:
            return text
        
        # Find a good break point
        excerpt = text[:max_length]
        last_space = excerpt.rfind(' ')
        if last_space > max_length * 0.8:  # If we can break at a reasonable point
            excerpt = excerpt[:last_space]
        
        return excerpt + "..."
