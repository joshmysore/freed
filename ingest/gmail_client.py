"""Gmail API client for fetching labeled messages."""

import os
import json
import base64
import email
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.header import decode_header

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from models import GmailMessage, Config


class GmailClient:
    """Gmail API client for fetching and parsing messages."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, config: Config, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.config = config
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_label_id(self, label_name: str) -> Optional[str]:
        """Get label ID by name."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            return None
        except HttpError as error:
            print(f"Error getting labels: {error}")
            return None
    
    def search_messages(self, query: str, max_results: int = 100) -> List[str]:
        """Search for messages matching query."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return [msg['id'] for msg in messages]
        
        except HttpError as error:
            print(f"Error searching messages: {error}")
            return []
    
    def get_message(self, message_id: str) -> Optional[GmailMessage]:
        """Get full message details."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
        
        except HttpError as error:
            print(f"Error getting message {message_id}: {error}")
            return None
    
    def _parse_message(self, message: Dict[str, Any]) -> Optional[GmailMessage]:
        """Parse Gmail message into our model."""
        try:
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extract headers
            header_map = {}
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                header_map[name] = value
            
            # Parse subject (decode RFC2047)
            subject = self._decode_header(header_map.get('subject', ''))
            
            # Parse from/to
            from_email = header_map.get('from', '')
            to_email = header_map.get('to', '')
            
            # Parse date
            date_str = header_map.get('date', '')
            date_utc = self._parse_date(date_str)
            
            # Extract body
            body_text, body_html = self._extract_body(payload)
            
            # Limit body text if configured
            if self.config.save_body_text and len(body_text) > self.config.body_max_chars:
                body_text = body_text[:self.config.body_max_chars] + "..."
            
            return GmailMessage(
                id=message['id'],
                thread_id=message['threadId'],
                subject=subject,
                from_email=from_email,
                to_email=to_email,
                date=date_utc,
                list_id=header_map.get('list-id'),
                message_id=header_map.get('message-id'),
                body_text=body_text,
                body_html=body_html if self.config.save_body_text else None
            )
        
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode RFC2047 encoded header."""
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string
        except Exception:
            return header_value
    
    def _parse_date(self, date_str: str) -> str:
        """Parse email date to UTC ISO string."""
        try:
            # Parse email date format
            dt = email.utils.parsedate_to_datetime(date_str)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()
    
    def _extract_body(self, payload: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """Extract text and HTML body from message payload."""
        body_text = ""
        body_html = None
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Convert HTML to text if no plain text
        if not body_text and body_html:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(body_html, 'html.parser')
                body_text = soup.get_text()
            except ImportError:
                body_text = body_html
        
        return body_text, body_html
    
    def fetch_labeled_messages(self, since_days: int = 60, limit: int = 100) -> List[GmailMessage]:
        """Fetch messages with the configured label."""
        # Get label ID
        label_id = self.get_label_id(self.config.label_name)
        if not label_id:
            print(f"Label '{self.config.label_name}' not found")
            return []
        
        # Build query
        query = f"label:{self.config.label_name} {self.config.gmail_query}"
        if since_days:
            query += f" newer_than:{since_days}d"
        
        # Search for messages
        message_ids = self.search_messages(query, limit)
        print(f"Found {len(message_ids)} messages with label '{self.config.label_name}'")
        
        # Fetch full message details
        messages = []
        for i, msg_id in enumerate(message_ids):
            print(f"Fetching message {i+1}/{len(message_ids)}: {msg_id}")
            message = self.get_message(msg_id)
            if message:
                messages.append(message)
        
        return messages
