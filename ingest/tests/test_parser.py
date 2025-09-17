"""Tests for event parser."""

import pytest
from datetime import datetime
from models import GmailMessage, Config
from parser import EventParser


@pytest.fixture
def config():
    """Test configuration."""
    return Config(
        label_name="GG.Events",
        gmail_query="newer_than:60d",
        timezone="America/New_York",
        save_body_text=False,
        body_max_chars=20000
    )


@pytest.fixture
def parser(config):
    """Test parser instance."""
    return EventParser(config)


@pytest.fixture
def sample_message():
    """Sample Gmail message for testing."""
    return GmailMessage(
        id="test123",
        thread_id="thread123",
        subject="[hcs-discuss] Comp Harvard Alternative Investment! [9/18 Kickoff]",
        from_email="test@harvard.edu",
        to_email="hcs-discuss@lists.harvard.edu",
        date="2024-09-15T10:00:00Z",
        list_id="hcs-discuss.lists.harvard.edu",
        message_id="<test123@harvard.edu>",
        body_text="Join us for the Harvard Alternative Investment kickoff event!\n\n🗓️ When: September 18th, 7:00 PM\n📍 Where: Sever 202\n\nPizza and refreshments will be provided. Free for all Harvard students!",
        body_html=None
    )


def test_extract_list_from_subject(parser):
    """Test list tag extraction from subject."""
    # Test with bracket format
    list_tag, title = parser.extract_list_from_subject("[hcs-discuss] Comp Harvard Alternative Investment!")
    assert list_tag == "hcs-discuss"
    assert title == "Comp Harvard Alternative Investment!"
    
    # Test with no brackets
    list_tag, title = parser.extract_list_from_subject("Regular subject line")
    assert list_tag == "Regular"
    assert title == "Regular subject line"
    
    # Test empty subject
    list_tag, title = parser.extract_list_from_subject("")
    assert list_tag == "unknown"
    assert title == ""


def test_parse_location(parser):
    """Test location parsing."""
    # Test explicit location markers
    body = "📍 Where: Sever 202\nJoin us for the event!"
    location = parser.parse_location(body)
    assert location == "Sever 202"
    
    # Test "Where:" marker
    body = "Where: Science Center 101\nEvent details..."
    location = parser.parse_location(body)
    assert location == "Science Center 101"
    
    # Test building pattern matching
    body = "The event will be held in Maxwell-Dworkin 119."
    location = parser.parse_location(body)
    assert "Maxwell-Dworkin" in location
    
    # Test no location found
    body = "Just some regular text with no location info."
    location = parser.parse_location(body)
    assert location is None


def test_parse_type(parser):
    """Test event type parsing."""
    # Test info session
    subject = "Info session about careers in tech"
    body = "Join us for an information session about tech careers."
    event_type = parser.parse_type(subject, body)
    assert event_type == "info session"
    
    # Test workshop
    subject = "Python Workshop"
    body = "Hands-on workshop to learn Python programming."
    event_type = parser.parse_type(subject, body)
    assert event_type == "workshop"
    
    # Test tech talk
    subject = "Tech Talk: Machine Learning"
    body = "Technical presentation on machine learning algorithms."
    event_type = parser.parse_type(subject, body)
    assert event_type == "tech talk"
    
    # Test application deadline
    subject = "DUE WEDNESDAY, SEPTEMBER 17th, 11:59PM EST"
    body = "Application deadline for the program."
    event_type = parser.parse_type(subject, body)
    assert event_type == "application deadline"
    
    # Test no type found
    subject = "Random email"
    body = "Just some random content."
    event_type = parser.parse_type(subject, body)
    assert event_type is None


def test_has_food(parser):
    """Test food detection."""
    # Test with food keywords
    text = "Pizza and boba will be provided at the event!"
    assert parser.has_food(text) == True
    
    # Test with refreshments
    text = "Refreshments and snacks will be available."
    assert parser.has_food(text) == True
    
    # Test without food
    text = "Just a regular meeting with no food mentioned."
    assert parser.has_food(text) == False


def test_is_free(parser):
    """Test free event detection."""
    # Test free event
    text = "Free event for all Harvard students!"
    assert parser.is_free(text) == True
    
    # Test paid event
    text = "Tickets cost $10 for non-HUID holders."
    assert parser.is_free(text) == False
    
    # Test with fee mention
    text = "Registration fee required for this workshop."
    assert parser.is_free(text) == False


def test_extract_links(parser):
    """Test link extraction."""
    text = "Register at https://eventbrite.com/event123 and fill out https://google.com/forms/abc"
    links = parser.extract_links(text)
    
    assert len(links) == 2
    assert "eventbrite.com" in links[0]  # Should be prioritized
    assert "google.com/forms" in links[1]


def test_calculate_confidence(parser):
    """Test confidence score calculation."""
    # Test full confidence
    confidence = parser.calculate_confidence("2024-09-18T19:00:00-04:00", "Sever 202", "info session")
    assert confidence == 3
    
    # Test partial confidence
    confidence = parser.calculate_confidence("2024-09-18T19:00:00-04:00", None, "workshop")
    assert confidence == 2
    
    # Test no confidence
    confidence = parser.calculate_confidence(None, None, None)
    assert confidence == 0


def test_parse_message_integration(parser, sample_message):
    """Test full message parsing integration."""
    event = parser.parse_message(sample_message)
    
    # Check basic fields
    assert event.id == "test123"
    assert event.thread_id == "thread123"
    assert event.source_list_tag == "hcs-discuss"
    assert event.title == "Comp Harvard Alternative Investment! [9/18 Kickoff]"
    assert event.subject == sample_message.subject
    
    # Check parsed fields
    assert event.location == "Sever 202"
    assert event.etype == "info session"
    assert event.food == 1  # Has "refreshments"
    assert event.free == 1  # Has "Free for all"
    assert event.confidence >= 2  # Should have location and type
    
    # Check links
    links = event.links
    assert isinstance(links, str)  # JSON string


def test_application_deadline_parsing(parser):
    """Test application deadline parsing."""
    message = GmailMessage(
        id="deadline123",
        thread_id="thread123",
        subject="[WECode] DUE WEDNESDAY, SEPTEMBER 17th, 11:59PM EST",
        from_email="wecode@harvard.edu",
        to_email="wecode@lists.harvard.edu",
        date="2024-09-15T10:00:00Z",
        list_id="wecode.lists.harvard.edu",
        message_id="<deadline123@harvard.edu>",
        body_text="Application deadline for WECode program. Submit by 11:59PM EST on September 17th.",
        body_html=None
    )
    
    event = parser.parse_message(message)
    
    assert event.etype == "application deadline"
    assert event.source_list_tag == "WECode"
    # Should have parsed the deadline time
    assert event.start is not None
    assert event.end is not None
    # End should be 1 minute after start for deadlines
    if event.start and event.end:
        from datetime import datetime
        start_dt = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(event.end.replace('Z', '+00:00'))
        assert (end_dt - start_dt).total_seconds() == 60  # 1 minute duration


def test_create_excerpt(parser):
    """Test excerpt creation."""
    # Test short text
    short_text = "This is a short message."
    excerpt = parser.create_excerpt(short_text)
    assert excerpt == short_text
    
    # Test long text
    long_text = "This is a very long message that should be truncated because it exceeds the maximum length allowed for excerpts and needs to be cut off at an appropriate point to maintain readability while providing a good summary of the content."
    excerpt = parser.create_excerpt(long_text, max_length=50)
    assert len(excerpt) <= 53  # 50 + "..."
    assert excerpt.endswith("...")
    
    # Test empty text
    excerpt = parser.create_excerpt("")
    assert excerpt == ""
