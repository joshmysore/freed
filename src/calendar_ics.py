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
            "PRODID:-//Email Event Parser//NONSGML v1.0//EN",
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
        
        # Add description
        if event.description:
            description = event.description
            if event.food_type:
                description += f"\n\nFood: {event.food_type}"
                if event.food_quantity_hint:
                    description += f" ({event.food_quantity_hint})"
            if event.urls:
                description += f"\n\nLinks: {', '.join(str(url) for url in event.urls)}"
            
            lines.append(f"DESCRIPTION:{ICSGenerator._escape_text(description)}")
        
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
        
        # Add source information
        if event.source_subject:
            lines.append(f"X-SOURCE-SUBJECT:{ICSGenerator._escape_text(event.source_subject)}")
        
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
