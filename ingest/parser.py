"""Event parsing logic for Harvard mailing list messages."""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import dateparser

from models import GmailMessage, Event, Config


class EventParser:
    """Parser for extracting event information from Gmail messages."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
        
        # Common Harvard building patterns
        self.building_patterns = [
            r'\b(Sever|Science Center|SEC|Maxwell-Dworkin|MD|Pierce Hall|Smith Campus Center|Sanders|Boylston|Cabot|Winthrop)\b',
            r'\b(Sever \d+|Science Center \d+|SEC \d+|Maxwell-Dworkin \d+|MD \d+|Pierce Hall \d+)\b',
            r'\b(Smith Campus Center|Sanders Theatre|Boylston Hall|Cabot Science Library|Winthrop House)\b'
        ]
        
        # Event type patterns
        self.type_patterns = {
            'info session': [
                r'\b(info session|information session|kickoff|comp)\b',
                r'\b(recruiting|recruitment)\b',
                r'\b(company presentation|corporate presentation)\b'
            ],
            'workshop': [
                r'\b(workshop|tutorial|training)\b',
                r'\b(hands-on|practical session)\b'
            ],
            'tech talk': [
                r'\b(tech talk|technical talk|lecture)\b',
                r'\b(presentation|talk)\b'
            ],
            'career': [
                r'\b(career|careers|job fair|networking)\b',
                r'\b(interview|resume|CV)\b'
            ],
            'social': [
                r'\b(social|mixer|party|gathering)\b',
                r'\b(food|pizza|boba|dumpling)\b'
            ],
            'application deadline': [
                r'\b(DUE|DEADLINE|deadline)\b',
                r'\b(application|apply)\b.*\b(deadline|due)\b'
            ]
        }
        
        # Food keywords
        self.food_keywords = [
            'pizza', 'boba', 'dumpling', 'snack', 'refreshment', 'cater',
            'lunch', 'dinner', 'food', 'meal', 'treat', 'drink'
        ]
        
        # Free keywords (negative indicators)
        self.cost_keywords = [
            '$', 'ticket', 'fee', 'cost', 'price', 'charge', 'non-huid',
            'payment', 'register', 'buy', 'purchase'
        ]
    
    def parse_message(self, message: GmailMessage) -> Event:
        """Parse a Gmail message into an Event."""
        # Extract list tag from subject
        list_tag, title = self.extract_list_from_subject(message.subject)
        
        # Parse event times
        start, end, event_type = self.parse_event_times(message.subject, message.body_text, message.date)
        
        # Parse location
        location = self.parse_location(message.body_text)
        
        # Parse event type if not already determined
        if not event_type:
            event_type = self.parse_type(message.subject, message.body_text)
        
        # Check for food and free status
        food = self.has_food(message.subject + " " + message.body_text)
        free = self.is_free(message.subject + " " + message.body_text)
        
        # Extract links
        links = self.extract_links(message.body_text)
        
        # Calculate confidence score
        confidence = self.calculate_confidence(start, location, event_type)
        
        # Create raw excerpt
        raw_excerpt = self.create_excerpt(message.body_text)
        
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
        """Extract list tag from subject line."""
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
    
    def parse_event_times(self, subject: str, body_text: str, received_dt: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse event start and end times from subject and body."""
        text = f"{subject} {body_text}"
        
        # Check for deadline pattern first
        deadline_match = re.search(r'\b(DUE|DEADLINE)\s+.*?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', text, re.IGNORECASE)
        if deadline_match:
            # This is an application deadline
            time_str = deadline_match.group(2)
            try:
                # Parse the time
                parsed_time = dateparser.parse(
                    time_str,
                    settings={
                        'PREFER_DATES_FROM': 'future',
                        'TIMEZONE': self.timezone,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                if parsed_time:
                    # For deadlines, set end time to 1 minute after start
                    start = parsed_time.isoformat()
                    end = (parsed_time + timedelta(minutes=1)).isoformat()
                    return start, end, "application deadline"
            except Exception:
                pass
        
        # Look for time patterns in subject
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
            r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?)'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                time_text = match.group(1) if match.groups() else match.group(0)
                parsed_time = self._parse_time_string(time_text)
                if parsed_time:
                    times.append(parsed_time)
                    if len(times) >= 2:  # We only need start and end
                        break
            if times:
                break
        
        return times
    
    def _parse_time_string(self, time_str: str) -> Optional[str]:
        """Parse a time string to ISO format."""
        try:
            parsed = dateparser.parse(
                time_str,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'TIMEZONE': self.timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
            if parsed:
                return parsed.isoformat()
        except Exception:
            pass
        return None
    
    def parse_location(self, body_text: str) -> Optional[str]:
        """Parse event location from body text."""
        # Look for explicit location markers
        location_patterns = [
            r'📍\s*(.*?)(?:\n|$)',
            r'Where:\s*(.*?)(?:\n|$)',
            r'Location:\s*(.*?)(?:\n|$)',
            r'Venue:\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, body_text, re.IGNORECASE | re.MULTILINE)
            if match:
                location = match.group(1).strip()
                if location:
                    return location
        
        # Look for common Harvard buildings
        for pattern in self.building_patterns:
            match = re.search(pattern, body_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
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
        
        # Prioritize Eventbrite and Google Forms
        prioritized_links = []
        other_links = []
        
        for link in links:
            if 'eventbrite' in link.lower() or 'google.com/forms' in link.lower():
                prioritized_links.append(link)
            else:
                other_links.append(link)
        
        # Return up to 5 links, prioritizing Eventbrite/Google Forms
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
