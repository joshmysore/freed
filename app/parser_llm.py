"""
LLM-based event parser with gating, caching, and configurable behavior.

This module handles:
- Event-likeness gating before LLM calls
- Response caching to minimize API usage
- Configurable prompt injection
- Integration with learning store
"""
import os
import json
import logging
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from config import get_config
from store import EventStore
from schema import ParsedEvent
from utils import norm_text

logger = logging.getLogger(__name__)

class LLMParser:
    """LLM parser with gating, caching, and learning capabilities."""
    
    def __init__(self, api_key: Optional[str] = None, store: EventStore = None):
        """Initialize LLM parser with Harvard OpenAI API key."""
        self.config = get_config()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Configure for Harvard's OpenAI API gateway
        harvard_api_base = 'https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1'
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=harvard_api_base
        )
        
        self.store = store or EventStore()
        self.prompt_template = self._load_prompt_template()
        self.llm_calls_made = 0
        self.max_calls = self.config["max_llm_calls_per_run"]
        
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'event_parser_prompt.txt')
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template not found at {prompt_path}")
            raise

    def _is_event_like(self, email_content: str, subject: str) -> bool:
        """
        Gate emails before LLM processing using generic patterns.
        
        Args:
            email_content: Email body content
            subject: Email subject
            
        Returns:
            True if email appears to contain an event
        """
        if not email_content:
            return False
        
        content_normalized = norm_text(email_content)
        if len(content_normalized) < 100:
            return False
        
        content_lower = norm_text(email_content)
        subject_lower = norm_text(subject or "")
        
        # Check for event keywords in subject first (more reliable for mailing lists)
        has_event_keywords_in_subject = any(keyword in subject_lower 
                                           for keyword in self.config["event_keyword_patterns"])
        has_event_keywords_in_content = any(keyword in content_lower 
                                           for keyword in self.config["event_keyword_patterns"])
        
        # If subject has event keywords, be more lenient about body content
        if has_event_keywords_in_subject:
            # Skip the mailing list footer check for event-like subjects
            has_event_keywords = True
        else:
            # Check for mailing list footers (common non-event content)
            if len(content_normalized) < 200 and "mailing list" in content_normalized:
                return False
            has_event_keywords = has_event_keywords_in_content
        
        # Check for time/date patterns
        has_time_patterns = any(re.search(pattern, content_normalized, re.IGNORECASE) 
                              for pattern in self.config["event_time_patterns"])
        
        # Check for location indicators
        has_location = any(keyword in content_lower for keyword in self.config["location_keyword_patterns"])
        
        # Must have at least event keywords OR (time patterns AND location)
        return has_event_keywords or (has_time_patterns and has_location)

    def _inject_prompt_variables(self, prompt: str, email_data: Dict[str, Any]) -> str:
        """Inject configuration variables into the prompt template."""
        # Replace template variables
        prompt = prompt.replace('{{CATEGORIES}}', json.dumps(self.config["categories"]))
        prompt = prompt.replace('{{CUISINES}}', json.dumps(self.config["cuisines"]))
        prompt = prompt.replace('{{EMAIL_PLAIN_TEXT}}', email_data.get('body', ''))
        prompt = prompt.replace('{{EMAIL_SUBJECT}}', email_data.get('subject', ''))
        prompt = prompt.replace('{{EMAIL_DATE}}', email_data.get('date', ''))
        prompt = prompt.replace('{{EMAIL_MESSAGE_ID}}', email_data.get('message_id', ''))
        
        return prompt

    def parse_email(self, email_content: str, message_id: str, subject: str, received_at: str = None) -> Optional[ParsedEvent]:
        """
        Parse email content using LLM with gating and caching.
        
        Args:
            email_content: Plain text email content
            message_id: Gmail message ID
            subject: Email subject
            received_at: Email received timestamp (ISO format)
            
        Returns:
            ParsedEvent object if parsing successful, None otherwise
        """
        try:
            # Check call budget
            if self.llm_calls_made >= self.max_calls:
                logger.warning(f"Max LLM calls ({self.max_calls}) reached, skipping email: {subject}")
                return None
            
            # Gate: Check if email looks like an event
            if not self._is_event_like(email_content, subject):
                logger.debug(f"Email gated out (not event-like): {subject}")
                return None
            
            # Check cache
            cache_key = self.store.generate_cache_key(message_id, email_content)
            cached_response = self.store.get_cached_response(cache_key)
            
            if cached_response:
                logger.debug(f"Using cached response for: {subject}")
                return self._process_llm_response(cached_response, message_id, subject)
            
            # Prepare email data for prompt
            email_data = {
                'body': email_content,
                'subject': subject,
                'date': received_at or '',
                'message_id': message_id
            }
            
            # Prepare prompt with injected variables
            prompt = self._inject_prompt_variables(self.prompt_template, email_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=1500
            )
            
            self.llm_calls_made += 1
            
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
            
            # Cache the response
            self.store.cache_response(cache_key, parsed_data)
            
            # Process the response
            return self._process_llm_response(parsed_data, message_id, subject)
                
        except Exception as e:
            logger.error(f"Error parsing email with LLM: {e}")
            return None

    def _process_llm_response(self, parsed_data: Dict[str, Any], message_id: str, subject: str) -> Optional[ParsedEvent]:
        """Process LLM response into ParsedEvent."""
        try:
            # Add source information
            parsed_data['source_message_id'] = message_id
            parsed_data['source_subject'] = subject
            
            # Extract mailing list from subject
            mailing_list = self._extract_mailing_list_from_subject(subject)
            if mailing_list:
                parsed_data['mailing_list'] = mailing_list
            
            # Clean up None values - convert string "None" to actual None
            parsed_data = self._clean_none_values(parsed_data)
            
            # Validate with Pydantic
            try:
                event = ParsedEvent(**parsed_data)
                return event
            except Exception as e:
                logger.error(f"Pydantic validation failed: {e}")
                logger.error(f"Parsed data: {parsed_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            return None

    def _clean_none_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert string 'None' values to actual None and clean up URLs."""
        cleaned = {}
        for key, value in data.items():
            if value == "None" or value == "null":
                cleaned[key] = None
            elif key == "urls" and isinstance(value, list):
                # Clean up URLs - add protocol if missing
                cleaned_urls = []
                for url in value:
                    if url and url not in ["None", "null"]:
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        cleaned_urls.append(url)
                cleaned[key] = cleaned_urls
            elif isinstance(value, dict):
                cleaned[key] = self._clean_none_values(value)
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(self._clean_none_values(item))
                    elif item in ["None", "null"]:
                        cleaned_list.append(None)
                    else:
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
        return cleaned

    def _extract_mailing_list_from_subject(self, subject: str) -> Optional[str]:
        """Extract mailing list name from [XXXXX] pattern in subject."""
        match = re.search(r'\[([^\]]+)\]', subject)
        return match.group(1) if match else None

    def parse_emails_batch(self, emails: List[Dict[str, Any]]) -> List[ParsedEvent]:
        """
        Parse multiple emails in batch with gating and caching.
        
        Args:
            emails: List of email dictionaries with 'body', 'message_id', 'subject'
            
        Returns:
            List of successfully parsed ParsedEvent objects
        """
        parsed_events = []
        self.llm_calls_made = 0  # Reset call counter
        
        logger.info(f"Starting batch parse of {len(emails)} emails (max {self.max_calls} LLM calls)")
        
        for email in emails:
            # Check if we've hit the call limit
            if self.llm_calls_made >= self.max_calls:
                logger.warning(f"Stopping batch parse: max LLM calls ({self.max_calls}) reached")
                break
            
            event = self.parse_email(
                email_content=email['body'],
                message_id=email['message_id'],
                subject=email['subject'],
                received_at=email.get('date')
            )
            
            if event:
                parsed_events.append(event)
        
        logger.info(f"Batch parse complete: {len(parsed_events)} events parsed, {self.llm_calls_made} LLM calls made")
        return parsed_events

    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        store_stats = self.store.get_stats()
        return {
            **store_stats,
            "llm_calls_made": self.llm_calls_made,
            "max_llm_calls": self.max_calls,
            "calls_remaining": max(0, self.max_calls - self.llm_calls_made)
        }

    def reset_call_counter(self):
        """Reset the LLM call counter."""
        self.llm_calls_made = 0
