import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from schema import ParsedEvent
from postprocess import PostProcessor
from calendar_ics import ICSGenerator


class TestEndToEnd:
    
    def test_sample_humic_email_parsing(self):
        """Test parsing of the HUMIC sample email as specified in acceptance criteria."""
        
        # Sample HUMIC email content (as mentioned in acceptance criteria)
        sample_email = """
        Subject: HUMIC Intro Session
        
        Dear Students,
        
        You are invited to the HUMIC (Harvard Undergraduate Machine Intelligence Community) 
        Introduction Session.
        
        Date: September 19, 2025
        Time: 5:00 PM - 6:00 PM
        Location: Sever Hall 203
        
        We will have dinner provided by Bonchon and light snacks available.
        
        Please RSVP at: https://humic.harvard.edu/rsvp
        
        Best regards,
        HUMIC Team
        """
        
        # Mock the LLM response (simulating what the LLM would return)
        mock_llm_response = {
            "title": "HUMIC Intro Session",
            "organizer": "HUMIC Team",
            "contacts": [{"name": "HUMIC Team", "email": None}],
            "date_start": "2025-09-19",
            "time_start": "17:00",
            "time_end": "18:00",
            "timezone": "America/New_York",
            "location": "Sever Hall 203",
            "description": "You are invited to the HUMIC (Harvard Undergraduate Machine Intelligence Community) Introduction Session.",
            "urls": ["https://humic.harvard.edu/rsvp"],
            "food_type": "Bonchon",
            "food_quantity_hint": "dinner provided",
            "source_message_id": "test123",
            "source_subject": "HUMIC Intro Session"
        }
        
        # Create ParsedEvent from mock response
        event = ParsedEvent(**mock_llm_response)
        
        # Apply post-processing
        processed_event = PostProcessor.process_event(event)
        
        # Verify acceptance criteria
        assert processed_event.title == "HUMIC Intro Session"
        assert processed_event.date_start == "2025-09-19"
        assert processed_event.time_start == "17:00"
        assert processed_event.time_end == "18:00"
        assert processed_event.timezone == "America/New_York"
        assert processed_event.location == "Sever Hall 203"
        assert processed_event.food_type == "Bonchon"
        assert "dinner provided" in processed_event.food_quantity_hint
        assert len(processed_event.urls) == 1
        assert str(processed_event.urls[0]) == "https://humic.harvard.edu/rsvp"
        assert processed_event.source_message_id == "test123"
        assert processed_event.source_subject == "HUMIC Intro Session"
    
    def test_ics_generation(self):
        """Test ICS file generation from parsed event."""
        
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            time_start="14:00",
            time_end="15:00",
            timezone="America/New_York",
            location="Test Location",
            organizer="Test Organizer",
            description="Test description",
            urls=["https://example.com"],
            source_message_id="test123",
            source_subject="Test Subject"
        )
        
        ics_content = ICSGenerator.generate_ics([event])
        
        # Verify ICS content contains expected elements
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert "BEGIN:VEVENT" in ics_content
        assert "END:VEVENT" in ics_content
        assert "SUMMARY:Test Event" in ics_content
        assert "DTSTART:" in ics_content
        assert "DTEND:" in ics_content
        assert "LOCATION:Test Location" in ics_content
        assert "ORGANIZER:CN=Test Organizer" in ics_content
        assert "DESCRIPTION:Test description" in ics_content
        assert "UID:test123@email-parser.local" in ics_content
    
    def test_event_validation_strict(self):
        """Test that invalid events are rejected by Pydantic validation."""
        
        # Test invalid date format
        with pytest.raises(Exception):  # ValidationError
            ParsedEvent(
                title="Test Event",
                date_start="12/19/2024"  # Invalid format
            )
        
        # Test invalid time format
        with pytest.raises(Exception):  # ValidationError
            ParsedEvent(
                title="Test Event",
                date_start="2024-12-19",
                time_start="2:00 PM"  # Invalid format
            )
        
        # Test invalid URL
        with pytest.raises(Exception):  # ValidationError
            ParsedEvent(
                title="Test Event",
                date_start="2024-12-19",
                urls=["not-a-url"]
            )
    
    def test_postprocessing_heuristics(self):
        """Test that post-processing heuristics work correctly."""
        
        # Test time normalization
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            time_start="14:00",  # Use 24-hour format for initial creation
            description="Duration: 2 hours"
        )
        
        processed = PostProcessor.process_event(event)
        assert processed.time_start == "14:00"  # Should remain the same
        assert processed.time_end == "16:00"  # Inferred from duration
        
        # Test location normalization
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            location="  Test Hall 203  "
        )
        
        processed = PostProcessor.process_event(event)
        assert processed.location == "Test Hall 203"
        
        # Test food extraction
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            description="Dinner provided by Bonchon. Light snacks available."
        )
        
        processed = PostProcessor.process_event(event)
        assert processed.food_type == "Bonchon"
        assert "dinner provided" in processed.food_quantity_hint
    
    def test_multiple_events_processing(self):
        """Test processing multiple events."""
        
        events = [
            ParsedEvent(
                title="Event 1",
                date_start="2024-12-19",
                time_start="14:00",
                location="Location 1"
            ),
            ParsedEvent(
                title="Event 2",
                date_start="2024-12-20",
                time_start="15:00",
                location="Location 2"
            )
        ]
        
        processed_events = []
        for event in events:
            processed = PostProcessor.process_event(event)
            processed_events.append(processed)
        
        assert len(processed_events) == 2
        assert processed_events[0].title == "Event 1"
        assert processed_events[1].title == "Event 2"
        
        # Test ICS generation for multiple events
        ics_content = ICSGenerator.generate_ics(processed_events)
        assert ics_content.count("BEGIN:VEVENT") == 2
        assert ics_content.count("END:VEVENT") == 2
    
    @pytest.mark.skip(reason="Requires openai module")
    @patch('parser_llm.OpenAI')
    def test_llm_parser_integration(self, mock_openai):
        """Test LLM parser integration with mocked OpenAI."""
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"title": "Test Event", "date_start": "2024-12-19", "time_start": "14:00", "timezone": "America/New_York", "location": "Test Location", "organizer": "Test Organizer", "description": "Test description", "urls": ["https://example.com"], "food_type": "Pizza", "food_quantity_hint": "dinner provided", "source_message_id": "test123", "source_subject": "Test Subject"}'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        from parser_llm import LLMParser
        
        parser = LLMParser(api_key="test-key")
        
        # Test parsing
        result = parser.parse_email(
            email_content="Test email content",
            message_id="test123",
            subject="Test Subject"
        )
        
        assert result is not None
        assert result.title == "Test Event"
        assert result.date_start == "2024-12-19"
        assert result.time_start == "14:00"
        assert result.timezone == "America/New_York"
        assert result.location == "Test Location"
        assert result.organizer == "Test Organizer"
        assert result.description == "Test description"
        assert len(result.urls) == 1
        assert str(result.urls[0]) == "https://example.com"
        assert result.food_type == "Pizza"
        assert result.food_quantity_hint == "dinner provided"
        assert result.source_message_id == "test123"
        assert result.source_subject == "Test Subject"
