import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from schema import ParsedEvent
from utils import extract_mailing_list_from_subject

logger = logging.getLogger(__name__)


class LLMParser:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM parser with Harvard OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Configure for Harvard's OpenAI API gateway
        harvard_api_base = 'https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1'
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=harvard_api_base
        )
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'event_parser_prompt.txt')
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template not found at {prompt_path}")
            raise

    def parse_email(self, email_content: str, message_id: str, subject: str, received_at: str = None) -> Optional[ParsedEvent]:
        """
        Parse email content using LLM and return validated ParsedEvent.
        
        Args:
            email_content: Plain text email content
            message_id: Gmail message ID
            subject: Email subject
            received_at: Email received timestamp (ISO format)
            
        Returns:
            ParsedEvent object if parsing successful, None otherwise
        """
        try:
            # Prepare prompt with email content and timestamp
            prompt = self.prompt_template.replace('{{EMAIL_PLAIN_TEXT}}', email_content)
            if received_at:
                # Replace the example timestamp with actual received_at
                prompt = prompt.replace("RECEIVED_AT: 2025-09-18 16:48 America/New_York", f"RECEIVED_AT: {received_at}")
                prompt = prompt.replace("RECEIVED_AT: 2025-09-18", f"RECEIVED_AT: {received_at}")
            
            # Call OpenAI API (removed JSON mode to allow "DROP" responses)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=1000
            )
            
            # Extract response
            response_text = response.choices[0].message.content.strip()
            
            # Check for DROP response
            if response_text.strip() == '"DROP"' or response_text.strip() == 'DROP':
                logger.info(f"Email dropped (no event): {subject}")
                return None
            
            # Parse JSON
            try:
                parsed_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.error(f"Raw response: {response_text}")
                return None
            
            # Add source information
            parsed_data['source_message_id'] = message_id
            parsed_data['source_subject'] = subject
            
            # Extract mailing list from subject
            mailing_list = extract_mailing_list_from_subject(subject)
            if mailing_list:
                parsed_data['mailing_list'] = mailing_list
            
            # Validate with Pydantic
            try:
                event = ParsedEvent(**parsed_data)
                return event
            except Exception as e:
                logger.error(f"Pydantic validation failed: {e}")
                logger.error(f"Parsed data: {parsed_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing email with LLM: {e}")
            return None

    def quick_event_detection(self, email_content: str, subject: str) -> bool:
        """
        Quick check if an email likely contains an event.
        This is much faster than full LLM parsing.
        
        Args:
            email_content: Email body content
            subject: Email subject
            
        Returns:
            True if likely an event, False otherwise
        """
        if not email_content or len(email_content.strip()) < 100:
            return False
        
        # Check for mailing list footers (common non-event content)
        if len(email_content) < 200 and "mailing list" in email_content.lower():
            return False
        
        # Event indicators
        event_keywords = [
            'event', 'meeting', 'workshop', 'seminar', 'talk', 'lecture', 
            'conference', 'gathering', 'session', 'presentation', 'party', 
            'celebration', 'dinner', 'lunch', 'breakfast', 'reception', 
            'ceremony', 'festival', 'fair', 'exhibition', 'audition', 'tryout',
            'info session', 'kickoff', 'launch', 'orientation'
        ]
        
        # Time/date indicators
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b(mon|tue|wed|thu|fri|sat|sun)day\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b',
            r'\b(today|tomorrow|tonight|this week|next week)\b'
        ]
        
        content_lower = email_content.lower()
        subject_lower = subject.lower()
        
        # Check for event keywords
        has_event_keywords = any(keyword in content_lower or keyword in subject_lower 
                               for keyword in event_keywords)
        
        # Check for time/date patterns
        import re
        has_time_patterns = any(re.search(pattern, email_content, re.IGNORECASE) 
                              for pattern in time_patterns)
        
        # Check for location indicators
        location_keywords = ['location', 'where', 'room', 'hall', 'building', 'address']
        has_location = any(keyword in content_lower for keyword in location_keywords)
        
        # Must have at least event keywords OR (time patterns AND location)
        return has_event_keywords or (has_time_patterns and has_location)

    def parse_emails_batch(self, emails: list) -> list[ParsedEvent]:
        """
        Parse multiple emails in batch with two-stage optimization.
        
        Args:
            emails: List of email dictionaries with 'body', 'message_id', 'subject'
            
        Returns:
            List of successfully parsed ParsedEvent objects
        """
        parsed_events = []
        
        # Stage 1: Quick filtering to identify likely events
        likely_events = []
        for email in emails:
            if self.quick_event_detection(email['body'], email['subject']):
                likely_events.append(email)
        
        logger.info(f"Quick scan: {len(likely_events)} of {len(emails)} emails appear to be events")
        
        # Stage 2: Full LLM parsing only for likely events
        for email in likely_events:
            event = self.parse_email(
                email_content=email['body'],
                message_id=email['message_id'],
                subject=email['subject'],
                received_at=email.get('date')  # Pass the email date as received_at
            )
            if event:
                parsed_events.append(event)
            else:
                logger.warning(f"Failed to parse email: {email.get('subject', 'Unknown')}")
        
        return parsed_events
