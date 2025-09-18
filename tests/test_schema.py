import pytest
from pydantic import ValidationError
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from schema import ParsedEvent, Contact


class TestContact:
    def test_contact_creation(self):
        contact = Contact(name="John Doe", email="john@example.com")
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
    
    def test_contact_optional_fields(self):
        contact = Contact()
        assert contact.name is None
        assert contact.email is None


class TestParsedEvent:
    def test_valid_event_creation(self):
        event_data = {
            "title": "Test Event",
            "date_start": "2024-12-19",
            "time_start": "14:00",
            "time_end": "15:00",
            "timezone": "America/New_York",
            "location": "Test Location",
            "organizer": "Test Organizer",
            "description": "Test description",
            "urls": ["https://example.com"],
            "food_type": "Pizza",
            "food_quantity_hint": "Dinner provided",
            "source_message_id": "test123",
            "source_subject": "Test Subject"
        }
        
        event = ParsedEvent(**event_data)
        assert event.title == "Test Event"
        assert event.date_start == "2024-12-19"
        assert event.time_start == "14:00"
        assert event.time_end == "15:00"
        assert event.timezone == "America/New_York"
        assert event.location == "Test Location"
        assert event.organizer == "Test Organizer"
        assert event.description == "Test description"
        assert len(event.urls) == 1
        assert str(event.urls[0]) == "https://example.com/"
        assert event.food_type == "Pizza"
        assert event.food_quantity_hint == "Dinner provided"
        assert event.source_message_id == "test123"
        assert event.source_subject == "Test Subject"
    
    def test_minimal_event_creation(self):
        event_data = {
            "title": "Minimal Event",
            "date_start": "2024-12-19"
        }
        
        event = ParsedEvent(**event_data)
        assert event.title == "Minimal Event"
        assert event.date_start == "2024-12-19"
        assert event.time_start is None
        assert event.time_end is None
        assert event.timezone == "America/New_York"  # default
        assert event.location is None
        assert event.organizer is None
        assert event.description is None
        assert event.urls == []
        assert event.food_type is None
        assert event.food_quantity_hint is None
        assert event.source_message_id is None
        assert event.source_subject is None
    
    def test_invalid_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            ParsedEvent(title="Test", date_start="12/19/2024")
        
        assert "date_start must be YYYY-MM-DD" in str(exc_info.value)
    
    def test_invalid_time_format(self):
        with pytest.raises(ValidationError) as exc_info:
            ParsedEvent(title="Test", date_start="2024-12-19", time_start="2:00 PM")
        
        assert "time must be HH:MM 24h" in str(exc_info.value)
    
    def test_valid_time_formats(self):
        # Valid 24-hour format
        event = ParsedEvent(title="Test", date_start="2024-12-19", time_start="14:00")
        assert event.time_start == "14:00"
        
        # Valid with end time
        event = ParsedEvent(
            title="Test", 
            date_start="2024-12-19", 
            time_start="14:00",
            time_end="15:00"
        )
        assert event.time_start == "14:00"
        assert event.time_end == "15:00"
    
    def test_contacts_list(self):
        contacts_data = [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"}
        ]
        
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            contacts=contacts_data
        )
        
        assert len(event.contacts) == 2
        assert event.contacts[0].name == "John Doe"
        assert event.contacts[0].email == "john@example.com"
        assert event.contacts[1].name == "Jane Smith"
        assert event.contacts[1].email == "jane@example.com"
    
    def test_urls_validation(self):
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            urls=["https://example.com", "http://test.org"]
        )
        
        assert len(event.urls) == 2
        assert str(event.urls[0]) == "https://example.com/"
        assert str(event.urls[1]) == "http://test.org/"
    
    def test_invalid_urls(self):
        with pytest.raises(ValidationError):
            ParsedEvent(
                title="Test Event",
                date_start="2024-12-19",
                urls=["not-a-url"]
            )
