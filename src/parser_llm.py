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

    def parse_email(self, email_content: str, message_id: str, subject: str) -> Optional[ParsedEvent]:
        """
        Parse email content using LLM and return validated ParsedEvent.
        
        Args:
            email_content: Plain text email content
            message_id: Gmail message ID
            subject: Email subject
            
        Returns:
            ParsedEvent object if parsing successful, None otherwise
        """
        try:
            # Prepare prompt with email content
            prompt = self.prompt_template.replace('{{EMAIL_PLAIN_TEXT}}', email_content)
            
            # Call OpenAI API with JSON mode
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=1000
            )
            
            # Extract JSON from response
            json_str = response.choices[0].message.content.strip()
            
            # Parse JSON
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.error(f"Raw response: {json_str}")
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

    def parse_emails_batch(self, emails: list) -> list[ParsedEvent]:
        """
        Parse multiple emails in batch.
        
        Args:
            emails: List of email dictionaries with 'body', 'message_id', 'subject'
            
        Returns:
            List of successfully parsed ParsedEvent objects
        """
        parsed_events = []
        
        for email in emails:
            event = self.parse_email(
                email_content=email['body'],
                message_id=email['message_id'],
                subject=email['subject']
            )
            if event:
                parsed_events.append(event)
            else:
                logger.warning(f"Failed to parse email: {email.get('subject', 'Unknown')}")
        
        return parsed_events
