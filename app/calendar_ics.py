"""
ICS calendar generation for ParsedEvent objects.

This module provides ICS file generation with support for the new
schema including food items and confidence scoring.
"""
import datetime
from typing import List
from schema import ParsedEvent


class ICSGenerator:
    """Generate ICS calendar files from ParsedEvent objects."""
    
    @staticmethod
    def generate_ics(events: List[ParsedEvent]) -> str:
        """
        Generate ICS content for a list of events.
        
        Args:
            events: List of ParsedEvent objects
            
        Returns:
            ICS file content as string
        """
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Email Event Parser v2.0//NONSGML v2.0//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        for event in events:
            ics_content.extend(ICSGenerator._event_to_ics(event))
        
        ics_content.append("END:VCALENDAR")
        
        return "\r\n".join(ics_content)
    
    @staticmethod
    def _event_to_ics(event: ParsedEvent) -> List[str]:
        """
        Convert a single ParsedEvent to ICS format.
        
        Args:
            event: ParsedEvent object
            
        Returns:
            List of ICS lines for the event
        """
        lines = ["BEGIN:VEVENT"]
        
        # Generate unique ID
        uid = f"{event.source_message_id or 'unknown'}@email-parser.local"
        lines.append(f"UID:{uid}")
        
        # Add timestamp
        now = datetime.datetime.now(datetime.timezone.utc)
        lines.append(f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}")
        
        # Add event date/time
        start_dt = ICSGenerator._parse_datetime(event.date_start, event.time_start, event.timezone)
        if start_dt:
            lines.append(f"DTSTART:{ICSGenerator._format_datetime(start_dt)}")
            
            # Add end time if available
            if event.time_end:
                end_dt = ICSGenerator._parse_datetime(event.date_start, event.time_end, event.timezone)
                if end_dt:
                    lines.append(f"DTEND:{ICSGenerator._format_datetime(end_dt)}")
            else:
                # Default to 1 hour duration if no end time
                end_dt = start_dt + datetime.timedelta(hours=1)
                lines.append(f"DTEND:{ICSGenerator._format_datetime(end_dt)}")
        
        # Add summary (title)
        lines.append(f"SUMMARY:{ICSGenerator._escape_text(event.title)}")
        
        # Add description with rich food information
        if event.description or event.food:
            description_parts = []
            
            if event.description:
                description_parts.append(event.description)
            
            # Add food information
            if event.food:
                food_info = []
                for item in event.food:
                    item_str = item.name
                    if item.quantity_hint:
                        item_str += f" ({item.quantity_hint})"
                    if item.cuisine:
                        item_str += f" [{item.cuisine}]"
                    food_info.append(item_str)
                
                if food_info:
                    description_parts.append(f"Food: {', '.join(food_info)}")
            
            # Add URLs
            if event.urls:
                description_parts.append(f"Links: {', '.join(str(url) for url in event.urls)}")
            
            # Add confidence information
            if event.confidence:
                conf_parts = []
                if event.confidence.category is not None:
                    conf_parts.append(f"Category confidence: {event.confidence.category:.2f}")
                if event.confidence.cuisine is not None:
                    conf_parts.append(f"Cuisine confidence: {event.confidence.cuisine:.2f}")
                if event.confidence.overall is not None:
                    conf_parts.append(f"Overall confidence: {event.confidence.overall:.2f}")
                
                if conf_parts:
                    description_parts.append(f"Confidence: {', '.join(conf_parts)}")
            
            if description_parts:
                lines.append(f"DESCRIPTION:{ICSGenerator._escape_text('\\n\\n'.join(description_parts))}")
        
        # Add location
        if event.location:
            lines.append(f"LOCATION:{ICSGenerator._escape_text(event.location)}")
        
        # Add organizer
        if event.organizer:
            lines.append(f"ORGANIZER:CN={ICSGenerator._escape_text(event.organizer)}")
        
        # Add contacts
        for contact in event.contacts:
            if contact.email:
                contact_line = f"ATTENDEE:CN={ICSGenerator._escape_text(contact.name or '')}"
                if contact.email:
                    contact_line += f";EMAIL={contact.email}"
                lines.append(contact_line)
        
        # Add category information
        if event.category:
            lines.append(f"CATEGORIES:{ICSGenerator._escape_text(event.category)}")
        
        # Add source information
        if event.source_subject:
            lines.append(f"X-SOURCE-SUBJECT:{ICSGenerator._escape_text(event.source_subject)}")
        
        if event.mailing_list:
            lines.append(f"X-MAILING-LIST:{ICSGenerator._escape_text(event.mailing_list)}")
        
        lines.append("END:VEVENT")
        
        return lines
    
    @staticmethod
    def _parse_datetime(date_str: str, time_str: str, timezone: str) -> datetime.datetime:
        """
        Parse date and time strings into a datetime object.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format
            timezone: IANA timezone string
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Parse date
            date_parts = date_str.split('-')
            year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
            
            # Parse time
            if time_str:
                time_parts = time_str.split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
            else:
                hour, minute = 0, 0
            
            # Create datetime
            dt = datetime.datetime(year, month, day, hour, minute)
            
            # Apply timezone
            import pytz
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
            
            return dt
            
        except Exception:
            return None
    
    @staticmethod
    def _format_datetime(dt: datetime.datetime) -> str:
        """
        Format datetime for ICS format.
        
        Args:
            dt: Datetime object
            
        Returns:
            Formatted datetime string
        """
        return dt.strftime('%Y%m%dT%H%M%S')
    
    @staticmethod
    def _escape_text(text: str) -> str:
        """
        Escape text for ICS format.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        if not text:
            return ""
        
        # Replace problematic characters
        text = text.replace('\\', '\\\\')
        text = text.replace(';', '\\;')
        text = text.replace(',', '\\,')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '')
        
        return text
