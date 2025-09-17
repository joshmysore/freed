"""LLM-based event parsing using local models via Ollama."""

import json
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import dateparser

from models import GmailMessage, Event, Config


class LLMEventParser:
    """LLM-based parser for extracting event information from Gmail messages."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Check if Ollama is available
        self.ollama_available = self._check_ollama()
        
        if not self.ollama_available:
            print("⚠️  Ollama not available. Falling back to rule-based parsing.")
            from improved_parser import ImprovedEventParser
            self.fallback_parser = ImprovedEventParser(config)
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _call_llm(self, prompt: str, model: str = "llama3.2:3b") -> str:
        """Call local LLM via Ollama."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            print(f"LLM call failed: {e}")
            return ""
    
    def parse_message(self, message: GmailMessage) -> Event:
        """Parse a Gmail message into an Event using LLM."""
        if not self.ollama_available:
            print("⚠️  Using fallback parser (Ollama not available)")
            return self.fallback_parser.parse_message(message)
        
        # Using LLM parser
        
        # Extract actual email content
        actual_content = self._extract_actual_content(message.body_text, message.subject)
        
        # Create a comprehensive prompt for the LLM
        prompt = self._create_parsing_prompt(message.subject, actual_content, message.date)
        
        # Get LLM response
        llm_response = self._call_llm(prompt)
        
        # Parse the LLM response
        parsed_data = self._parse_llm_response(llm_response)
        
        # Extract list tag from subject
        list_tag, title = self._extract_list_from_subject(message.subject)
        
        # Create event
        now = datetime.now().isoformat()
        
        return Event(
            id=message.id,
            thread_id=message.thread_id,
            source_list_tag=list_tag,
            source_list_id=message.list_id,
            message_id=message.message_id,
            subject=message.subject,
            received_utc=message.date,
            title=parsed_data.get('title', title),
            start=parsed_data.get('start'),
            end=parsed_data.get('end'),
            timezone=self.timezone,
            location=parsed_data.get('location'),
            etype=parsed_data.get('type'),
            food=1 if parsed_data.get('food', False) else 0,
            free=1 if parsed_data.get('free', True) else 0,
            links=json.dumps(parsed_data.get('links', [])),
            raw_excerpt=parsed_data.get('excerpt', actual_content[:200] + "..." if len(actual_content) > 200 else actual_content),
            confidence=parsed_data.get('confidence', 0),
            created_at=now,
            updated_at=now
        )
    
    def _extract_actual_content(self, body_text: str, subject: str) -> str:
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
    
    def _extract_list_from_subject(self, subject: str) -> Tuple[str, str]:
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
    
    def _create_parsing_prompt(self, subject: str, content: str, received_date: str) -> str:
        """Create a comprehensive prompt for the LLM to parse event information."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are an expert at parsing Harvard University event emails. Extract event information from this email and return ONLY a valid JSON object.

EMAIL SUBJECT: {subject}

EMAIL CONTENT:
{content}

CURRENT DATE: {current_date}
RECEIVED DATE: {received_date}

Extract the following information and return as JSON:
{{
  "title": "Clean event title (remove list tags, prefixes)",
  "start": "ISO datetime string if event has a specific start time, null otherwise",
  "end": "ISO datetime string if event has a specific end time, null otherwise", 
  "location": "Event location/venue if mentioned, null otherwise",
  "type": "Event type: info_session, workshop, tech_talk, career, social, meeting, application_deadline, or null",
  "food": true/false if food/refreshments mentioned,
  "free": true/false if event is free (default true unless cost mentioned),
  "links": ["array of URLs found in email"],
  "excerpt": "2-3 sentence summary of the event",
  "confidence": 0-3 based on how much information was extracted
}}

IMPORTANT RULES:
1. For dates: Use current year (2025) unless explicitly stated otherwise
2. For times: If only date given, assume 7:00 PM. If "tonight" use current date 7:00 PM
3. For "today/tomorrow": Use current date or next day
4. For locations: Look for building names, rooms, addresses
5. For types: Be specific - "info session" for recruiting, "social" for food/parties, "meeting" for house meetings
6. For links: Include registration forms, eventbrite, google forms, etc.
7. For excerpt: Summarize what the event is about in 1-2 sentences

Return ONLY the JSON object, no other text."""

        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response and extract event data."""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            # Find JSON object in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Validate and clean the data
                return self._validate_parsed_data(data)
            else:
                print(f"Could not find JSON in LLM response: {response[:200]}...")
                return {}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response: {response[:200]}...")
            return {}
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _validate_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the parsed data."""
        # Ensure required fields exist
        result = {
            'title': data.get('title', ''),
            'start': data.get('start'),
            'end': data.get('end'),
            'location': data.get('location'),
            'type': data.get('type'),
            'food': bool(data.get('food', False)),
            'free': bool(data.get('free', True)),
            'links': data.get('links', []),
            'excerpt': data.get('excerpt', ''),
            "confidence": max(0, min(3, int(data.get("confidence", 0))))  # Clamp between 0-3
        }
        
        # Clean up title
        if result['title']:
            result['title'] = result['title'].strip()
        
        # Clean up location
        if result['location']:
            result['location'] = result['location'].strip()
        
        # Clean up excerpt
        if result['excerpt']:
            result['excerpt'] = result['excerpt'].strip()
        
        # Ensure links is a list
        if not isinstance(result['links'], list):
            result['links'] = []
        
        # Ensure confidence is an integer
        try:
            result['confidence'] = int(result['confidence'])
        except (ValueError, TypeError):
            result['confidence'] = 0
        
        return result
