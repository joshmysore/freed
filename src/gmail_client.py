import os
import base64
import json
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file {self.credentials_file} not found. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)

    def search_emails(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search for emails matching the query and return message IDs.
        
        Args:
            query: Gmail search query string
            max_results: Maximum number of emails to return
            
        Returns:
            List of message IDs
        """
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return [msg['id'] for msg in messages]
            
        except HttpError as error:
            logger.error(f"Error searching emails: {error}")
            return []

    def get_email_content(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get email content for a specific message ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with email metadata and content
        """
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract plain text body
            body = self._extract_text_from_payload(message['payload'])
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body
            }
            
        except HttpError as error:
            logger.error(f"Error getting email content: {error}")
            return None

    def _extract_text_from_payload(self, payload: Dict[str, Any]) -> str:
        """Extract plain text from email payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'multipart/alternative':
                    # Recursively extract from multipart
                    body += self._extract_text_from_payload(part)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body.strip()

    def get_emails_for_parsing(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get emails matching query with full content for parsing.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of emails to process
            
        Returns:
            List of email dictionaries ready for parsing
        """
        message_ids = self.search_emails(query, max_results)
        emails = []
        
        for msg_id in message_ids:
            email_data = self.get_email_content(msg_id)
            if email_data and email_data['body']:
                emails.append(email_data)
        
        return emails
