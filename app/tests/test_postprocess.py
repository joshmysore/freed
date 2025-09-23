"""
Tests for the post-processing functionality with learning and confidence thresholds.
"""
import pytest
from unittest.mock import Mock
from ..postprocess import PostProcessor
from ..store import EventStore
from ..schema import ParsedEvent, FoodItem, ConfidenceScores

@pytest.fixture
def mock_store():
    """Create a mock store for testing."""
    store = Mock(spec=EventStore)
    store.get_learned_cuisine.return_value = None
    store.learn_cuisine.return_value = None
    return store

@pytest.fixture
def post_processor(mock_store):
    """Create a PostProcessor with mock store."""
    return PostProcessor(store=mock_store)

def test_confidence_filtering_category(post_processor):
    """Test category filtering based on confidence."""
    # High confidence category should pass
    event_data = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "category": "workshop",
        "confidence": {"category": 0.8}
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    assert result.category == "workshop"
    
    # Low confidence category should be filtered out
    event_data_low = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "category": "workshop",
        "confidence": {"category": 0.4}
    }
    
    result_low = post_processor.process_event(event_data_low)
    assert result_low is not None
    assert result_low.category is None

def test_confidence_filtering_cuisine(post_processor):
    """Test cuisine filtering based on confidence."""
    event_data = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "food": [
            {
                "name": "pizza",
                "cuisine": "Italian",
                "confidence": {"cuisine": 0.8}
            },
            {
                "name": "sushi",
                "cuisine": "Japanese", 
                "confidence": {"cuisine": 0.3}
            }
        ]
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    assert len(result.food) == 2
    
    # High confidence cuisine should remain
    pizza_item = next(item for item in result.food if item.name == "pizza")
    assert pizza_item.cuisine == "Italian"
    
    # Low confidence cuisine should be filtered out
    sushi_item = next(item for item in result.food if item.name == "sushi")
    assert sushi_item.cuisine is None

def test_learned_cuisine_usage(post_processor, mock_store):
    """Test usage of learned cuisine mappings."""
    # Mock learned cuisine
    mock_store.get_learned_cuisine.return_value = ("Italian", 0.9)
    
    event_data = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "food": [
            {
                "name": "pizza",
                "cuisine": None,  # No cuisine detected
                "confidence": {"cuisine": 0.0}
            }
        ]
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    
    # Should use learned cuisine
    pizza_item = result.food[0]
    assert pizza_item.cuisine == "Italian"
    
    # Should have called get_learned_cuisine
    mock_store.get_learned_cuisine.assert_called_with("pizza")

def test_cuisine_learning(post_processor, mock_store):
    """Test learning of new cuisine mappings."""
    event_data = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "food": [
            {
                "name": "sushi",
                "cuisine": "Japanese",
                "confidence": {"cuisine": 0.8}
            }
        ]
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    
    # Should have learned the cuisine mapping
    mock_store.learn_cuisine.assert_called_with("sushi", "Japanese", 0.8)

def test_batch_processing_with_deduplication(post_processor, mock_store):
    """Test batch processing with deduplication."""
    # Mock no duplicates
    mock_store.is_duplicate_event.return_value = None
    
    events_data = [
        {
            "title": "Event 1",
            "date_start": "2025-09-20",
            "time_start": "14:00",
            "location": "Room 1"
        },
        {
            "title": "Event 2", 
            "date_start": "2025-09-21",
            "time_start": "15:00",
            "location": "Room 2"
        }
    ]
    
    results = post_processor.process_events_batch(events_data)
    
    # Should process both events
    assert len(results) == 2
    assert results[0].title == "Event 1"
    assert results[1].title == "Event 2"
    
    # Should have registered both events
    assert mock_store.register_event.call_count == 2

def test_batch_processing_with_duplicates(post_processor, mock_store):
    """Test batch processing with duplicate detection."""
    # Mock duplicate for second event
    mock_store.is_duplicate_event.side_effect = [None, "event1"]
    
    events_data = [
        {
            "title": "Event 1",
            "date_start": "2025-09-20",
            "time_start": "14:00",
            "location": "Room 1"
        },
        {
            "title": "Event 1 Duplicate",
            "date_start": "2025-09-20",
            "time_start": "14:00",
            "location": "Room 1"
        }
    ]
    
    results = post_processor.process_events_batch(events_data)
    
    # Should only process first event (second is duplicate)
    assert len(results) == 1
    assert results[0].title == "Event 1"

def test_url_normalization(post_processor):
    """Test URL normalization."""
    event_data = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "urls": [
            "https://example.com",
            "http://test.com?utm_source=test&utm_campaign=test",
            "invalid-url"
        ]
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    
    # Should normalize URLs
    urls = [str(url) for url in result.urls]
    assert "https://example.com" in urls
    assert "http://test.com" in urls  # Should be cleaned
    assert "https://invalid-url" in urls  # Should be prefixed

def test_data_normalization(post_processor):
    """Test data normalization."""
    event_data = {
        "title": "  Test   Event  ",
        "date_start": "2025-09-20",
        "description": "Event with – fancy dashes and   multiple   spaces",
        "organizer": "TBD",
        "location": "Room 101"
    }
    
    result = post_processor.process_event(event_data)
    assert result is not None
    
    # Should normalize whitespace and dashes
    assert result.title == "Test Event"
    assert result.description == "Event with - fancy dashes and multiple spaces"
    assert result.organizer is None  # TBD should be None

def test_learning_stats(post_processor, mock_store):
    """Test learning statistics generation."""
    # Mock store stats
    mock_store.get_stats.return_value = {
        "learned_aliases_count": 10,
        "cache_entries_count": 5,
        "dedup_entries_count": 3
    }
    
    # Mock learned aliases data
    mock_store.data = {
        "learned_aliases": {
            "pizza": {"rolling_confidence": 0.9},
            "sushi": {"rolling_confidence": 0.7},
            "burger": {"rolling_confidence": 0.5}
        }
    }
    
    stats = post_processor.get_learning_stats()
    
    assert stats["learned_aliases_count"] == 10
    assert stats["learned_cuisines"]["high_confidence"] == 1  # 0.9
    assert stats["learned_cuisines"]["medium_confidence"] == 1  # 0.7
    assert stats["learned_cuisines"]["low_confidence"] == 1  # 0.5

def test_cleanup_functionality(post_processor, mock_store):
    """Test cleanup functionality."""
    post_processor.cleanup_old_data(days=30)
    
    # Should call store cleanup
    mock_store.cleanup_old_data.assert_called_with(30)

