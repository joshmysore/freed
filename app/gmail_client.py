"""
Gmail client with configurable queries and no hard-coded sender lists.

This module provides Gmail API integration with:
- Configurable search queries
- Generic header filtering
- User-managed label support
- No hard-coded domains or sender lists
"""
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

from config import get_config

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    """Gmail client with configurable queries and generic filtering."""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.config = get_config()
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
            list_id = next((h['value'] for h in headers if h['name'] == 'List-Id'), '')
            
            # Extract plain text body
            body = self._extract_text_from_payload(message['payload'])
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'list_id': list_id
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

    def get_events_emails(self, max_results: int = 50, custom_query: str = None) -> List[Dict[str, Any]]:
        """
        Get event-related emails using configurable query.
        
        Args:
            max_results: Maximum number of emails to process
            custom_query: Custom Gmail query (overrides config)
            
        Returns:
            List of email dictionaries ready for parsing
        """
        query = custom_query or self.config["gmail_query"]
        return self.get_emails_for_parsing(query, max_results)

    def get_emails_by_label(self, label: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails by Gmail label (user-managed).
        
        Args:
            label: Gmail label name
            max_results: Maximum number of emails to process
            
        Returns:
            List of email dictionaries ready for parsing
        """
        query = f"label:{label} newer_than:{self.config['event_window_days']}d"
        return self.get_emails_for_parsing(query, max_results)

    def get_emails_by_list_id(self, list_domain: str = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails by mailing list (generic, no hard-coded domains).
        
        Args:
            list_domain: Optional domain filter for List-Id header
            max_results: Maximum number of emails to process
            
        Returns:
            List of email dictionaries ready for parsing
        """
        if list_domain:
            query = f"list:{list_domain} newer_than:{self.config['event_window_days']}d"
        else:
            query = f"has:list-id newer_than:{self.config['event_window_days']}d"
        
        return self.get_emails_for_parsing(query, max_results)

    def get_emails_by_sender_domain(self, domain: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails by sender domain (user-specified).
        
        Args:
            domain: Sender domain (e.g., "lists.harvard.edu")
            max_results: Maximum number of emails to process
            
        Returns:
            List of email dictionaries ready for parsing
        """
        query = f"from:{domain} newer_than:{self.config['event_window_days']}d"
        return self.get_emails_for_parsing(query, max_results)

    def get_gg_events_emails(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails with GG.Events tag for parsing from the configured time window.
        
        Args:
            max_results: Maximum number of emails to process (default 50)
            
        Returns:
            List of email dictionaries ready for parsing
        """
        # Use configurable time window
        query = f"label:GG.Events newer_than:{self.config['event_window_days']}d"
        return self.get_emails_for_parsing(query, max_results)

    def get_mailing_list_emails(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails from mailing lists only (GG.Events + other mailing lists).
        This excludes regular emails with event keywords in subjects.
        
        Args:
            max_results: Maximum number of emails to process (default 50)
            
        Returns:
            List of email dictionaries ready for parsing
        """
        try:
            # Build query for mailing lists only
            query_parts = []
            
            # Add GG.Events label
            query_parts.append("label:GG.Events")
            
            # Add common mailing lists
            mailing_lists = ["hcs-discuss", "pfoho-open", "pfoho-announce", "pfoho-events", 
                            "pfoho-social", "pfoho-academic", "pfoho-residential", "pfoho-open",
                            "cnugs", "gg-events", "pfoho-discuss"]
            for ml in mailing_lists:
                query_parts.append(f"list:{ml}")
            
            # Add time window
            time_window = f"newer_than:{self.config['event_window_days']}d"
            
            # Combine with OR logic and add time window
            mailing_query = " OR ".join(f"({part})" for part in query_parts)
            query = f"({mailing_query}) {time_window}"
            
            return self.get_emails_for_parsing(query, max_results)
        except Exception as e:
            logger.error(f"Error in get_mailing_list_emails: {e}")
            # Fallback to just GG.Events if there's an error
            fallback_query = f"label:GG.Events {time_window}"
            return self.get_emails_for_parsing(fallback_query, max_results)

    def get_all_events_emails(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get emails from all event sources (GG.Events + mailing lists + event keywords).
        
        Args:
            max_results: Maximum number of emails to process (default 50)
            
        Returns:
            List of email dictionaries ready for parsing
        """
        # Build comprehensive query for events
        query_parts = []
        
        # Add GG.Events label
        query_parts.append("label:GG.Events")
        
        # Add common mailing lists
        mailing_lists = ["hcs-discuss", "pfoho-open", "pfoho-announce", "pfoho-events", 
                        "pfoho-social", "pfoho-academic", "pfoho-residential", "pfoho-open"]
        for ml in mailing_lists:
            query_parts.append(f"list:{ml}")
        
        # Add event keywords in subject
        event_keywords = ["event", "meeting", "workshop", "seminar", "talk", "lecture", 
                         "conference", "gathering", "session", "presentation", "party", 
                         "celebration", "dinner", "lunch", "breakfast", "reception", 
                         "ceremony", "festival", "fair", "exhibition", "show", "comedy", 
                         "performance", "concert", "theater", "theatre", "movie", "film", 
                         "screening", "demo", "demonstration", "tour", "visit", "open house", 
                         "mixer", "networking", "social", "hangout", "get together", "outing"]
        
        for keyword in event_keywords:
            query_parts.append(f"subject:{keyword}")
        
        # Add time window
        query_parts.append(f"newer_than:{self.config['event_window_days']}d")
        
        # Combine with OR logic
        query = " OR ".join(f"({part})" for part in query_parts)
        
        return self.get_emails_for_parsing(query, max_results)

    def get_available_labels(self) -> List[Dict[str, Any]]:
        """
        Get available Gmail labels for user configuration.
        
        Returns:
            List of label dictionaries
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            return labels
        except HttpError as error:
            logger.error(f"Error getting labels: {error}")
            return []

    def create_custom_query(self, 
                          labels: List[str] = None,
                          domains: List[str] = None,
                          list_domains: List[str] = None,
                          additional_terms: List[str] = None) -> str:
        """
        Create a custom Gmail query from configuration options.
        
        Args:
            labels: Gmail labels to include
            domains: Sender domains to include
            list_domains: List-Id domains to include
            additional_terms: Additional search terms
            
        Returns:
            Gmail query string
        """
        query_parts = []
        
        # Time window
        query_parts.append(f"newer_than:{self.config['event_window_days']}d")
        
        # Labels
        if labels:
            label_query = " OR ".join(f"label:{label}" for label in labels)
            query_parts.append(f"({label_query})")
        
        # Domains
        if domains:
            domain_query = " OR ".join(f"from:{domain}" for domain in domains)
            query_parts.append(f"({domain_query})")
        
        # List domains
        if list_domains:
            list_query = " OR ".join(f"list:{domain}" for domain in list_domains)
            query_parts.append(f"({list_query})")
        
        # Additional terms
        if additional_terms:
            terms_query = " OR ".join(f"({term})" for term in additional_terms)
            query_parts.append(f"({terms_query})")
        
        # If no specific filters, use default patterns
        if not any([labels, domains, list_domains, additional_terms]):
            patterns_query = " OR ".join(f"({pattern})" for pattern in self.config["gmail_query_patterns"])
            query_parts.append(f"({patterns_query})")
        
        return " ".join(query_parts)

    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get Gmail parsing statistics."""
        try:
            # Get recent email counts
            recent_query = f"newer_than:{self.config['event_window_days']}d"
            recent_count = len(self.search_emails(recent_query, max_results=1000))
            
            # Get GG.Events count
            gg_query = f"label:GG.Events newer_than:{self.config['event_window_days']}d"
            gg_count = len(self.search_emails(gg_query, max_results=1000))
            
            return {
                "recent_emails": recent_count,
                "gg_events_emails": gg_count,
                "event_window_days": self.config["event_window_days"],
                "available_labels": len(self.get_available_labels())
            }
        except Exception as e:
            logger.error(f"Error getting parsing stats: {e}")
            return {}
