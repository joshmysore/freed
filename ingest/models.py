"""Data models for Harvard events."""

from datetime import datetime
from typing import List, Optional, Dict, Any


class Event:
    """Event model for Harvard mailing list events."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '')
        self.thread_id = kwargs.get('thread_id', '')
        self.source_list_tag = kwargs.get('source_list_tag', '')
        self.source_list_id = kwargs.get('source_list_id')
        self.message_id = kwargs.get('message_id')
        self.subject = kwargs.get('subject', '')
        self.received_utc = kwargs.get('received_utc', '')
        self.title = kwargs.get('title', '')
        self.start = kwargs.get('start')
        self.end = kwargs.get('end')
        self.timezone = kwargs.get('timezone', 'America/New_York')
        self.location = kwargs.get('location')
        self.etype = kwargs.get('etype')
        self.food = kwargs.get('food', 0)
        self.free = kwargs.get('free', 1)
        self.links = kwargs.get('links', '[]')
        self.raw_excerpt = kwargs.get('raw_excerpt')
        self.confidence = kwargs.get('confidence', 0)
        self.created_at = kwargs.get('created_at', '')
        self.updated_at = kwargs.get('updated_at', '')


class GmailMessage:
    """Gmail message model for parsing."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '')
        self.thread_id = kwargs.get('thread_id', '')
        self.subject = kwargs.get('subject', '')
        self.from_email = kwargs.get('from_email', '')
        self.to_email = kwargs.get('to_email', '')
        self.date = kwargs.get('date', '')
        self.list_id = kwargs.get('list_id')
        self.message_id = kwargs.get('message_id')
        self.body_text = kwargs.get('body_text', '')
        self.body_html = kwargs.get('body_html')


class Config:
    """Configuration model."""
    
    def __init__(self, **kwargs):
        self.label_name = kwargs.get('label_name', 'GG.Events')
        self.gmail_query = kwargs.get('gmail_query', 'newer_than:60d')
        self.timezone = kwargs.get('timezone', 'America/New_York')
        self.save_body_text = kwargs.get('save_body_text', False)
        self.body_max_chars = kwargs.get('body_max_chars', 20000)
