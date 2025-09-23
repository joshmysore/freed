"""
Tests for the EventStore learning and caching functionality.
"""
import pytest
import tempfile
import os
from ..store import EventStore

@pytest.fixture
def temp_store():
    """Create a temporary store for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    store = EventStore(temp_file)
    yield store
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)

def test_learned_cuisine_retrieval(temp_store):
    """Test learned cuisine retrieval."""
    # Initially no learned cuisines
    assert temp_store.get_learned_cuisine("pizza") is None
    
    # Learn a cuisine
    temp_store.learn_cuisine("pizza", "Italian", 0.8)
    
    # Should now return learned cuisine
    result = temp_store.get_learned_cuisine("pizza")
    assert result is not None
    assert result[0] == "Italian"
    assert result[1] >= 0.8

def test_cuisine_learning_threshold(temp_store):
    """Test that low confidence cuisines are not learned."""
    # Low confidence should not be learned
    temp_store.learn_cuisine("sushi", "Japanese", 0.3)
    assert temp_store.get_learned_cuisine("sushi") is None
    
    # High confidence should be learned
    temp_store.learn_cuisine("sushi", "Japanese", 0.8)
    result = temp_store.get_learned_cuisine("sushi")
    assert result is not None
    assert result[0] == "Japanese"

def test_rolling_average_learning(temp_store):
    """Test rolling average learning."""
    # First learning
    temp_store.learn_cuisine("pizza", "Italian", 0.8)
    result1 = temp_store.get_learned_cuisine("pizza")
    assert result1[1] == 0.8
    
    # Second learning with different confidence
    temp_store.learn_cuisine("pizza", "Italian", 0.6)
    result2 = temp_store.get_learned_cuisine("pizza")
    
    # Rolling average should be between 0.6 and 0.8
    assert 0.6 <= result2[1] <= 0.8
    assert result2[1] != 0.8  # Should have changed

def test_cache_functionality(temp_store):
    """Test LLM response caching."""
    cache_key = "test_message_123"
    response = {"title": "Test Event", "date_start": "2025-09-20"}
    
    # Initially no cached response
    assert temp_store.get_cached_response(cache_key) is None
    
    # Cache response
    temp_store.cache_response(cache_key, response)
    
    # Should now return cached response
    cached = temp_store.get_cached_response(cache_key)
    assert cached == response

def test_cache_key_generation(temp_store):
    """Test cache key generation."""
    key1 = temp_store.generate_cache_key("msg123", "email body content")
    key2 = temp_store.generate_cache_key("msg123", "email body content")
    key3 = temp_store.generate_cache_key("msg123", "different content")
    
    # Same content should generate same key
    assert key1 == key2
    
    # Different content should generate different key
    assert key1 != key3

def test_duplicate_detection(temp_store):
    """Test event duplicate detection."""
    event1 = {
        "title": "Test Event",
        "date_start": "2025-09-20",
        "time_start": "14:00",
        "location": "Room 101"
    }
    
    event2 = {
        "title": "Test Event",
        "date_start": "2025-09-20", 
        "time_start": "14:00",
        "location": "Room 101"
    }
    
    event3 = {
        "title": "Different Event",
        "date_start": "2025-09-20",
        "time_start": "14:00",
        "location": "Room 101"
    }
    
    # Register first event
    temp_store.register_event("event1", event1)
    
    # Check for duplicates
    assert temp_store.is_duplicate_event(event2) == "event1"  # Duplicate
    assert temp_store.is_duplicate_event(event3) is None  # Not duplicate

def test_similar_event_detection(temp_store):
    """Test fuzzy duplicate detection for similar events."""
    event1 = {
        "title": "Workshop on Machine Learning",
        "date_start": "2025-09-20",
        "time_start": "14:00",
        "location": "Room 101"
    }
    
    event2 = {
        "title": "Machine Learning Workshop",
        "date_start": "2025-09-20",
        "time_start": "14:00", 
        "location": "Room 101"
    }
    
    # Register first event
    temp_store.register_event("event1", event1)
    
    # Should detect as similar (high title similarity, same date)
    duplicate_id = temp_store.is_duplicate_event(event2)
    assert duplicate_id == "event1"

def test_event_merging(temp_store):
    """Test event data merging."""
    base_event = {
        "title": "Test Event",
        "urls": ["https://example.com"],
        "mailing_list": ["list1"],
        "confidence": {"category": 0.7}
    }
    
    new_event = {
        "title": "Test Event",
        "urls": ["https://example2.com"],
        "mailing_list": ["list2"],
        "confidence": {"category": 0.9}
    }
    
    merged = temp_store.merge_event_data(base_event, new_event)
    
    # URLs should be merged
    assert len(merged["urls"]) == 2
    assert "https://example.com" in merged["urls"]
    assert "https://example2.com" in merged["urls"]
    
    # Mailing lists should be merged
    assert len(merged["mailing_list"]) == 2
    assert "list1" in merged["mailing_list"]
    assert "list2" in merged["mailing_list"]
    
    # Confidence should use higher value
    assert merged["confidence"]["category"] == 0.9

def test_stats_generation(temp_store):
    """Test statistics generation."""
    # Add some test data
    temp_store.learn_cuisine("pizza", "Italian", 0.8)
    temp_store.cache_response("test_key", {"test": "data"})
    temp_store.register_event("event1", {"title": "Test"})
    
    stats = temp_store.get_stats()
    
    assert stats["learned_aliases_count"] >= 1
    assert stats["cache_entries_count"] >= 1
    assert stats["dedup_entries_count"] >= 1
    assert "store_size_mb" in stats

def test_cleanup_functionality(temp_store):
    """Test cleanup of old data."""
    # Add some test data
    temp_store.learn_cuisine("pizza", "Italian", 0.8)
    temp_store.cache_response("test_key", {"test": "data"})
    temp_store.register_event("event1", {"title": "Test"})
    
    initial_stats = temp_store.get_stats()
    
    # Cleanup (should not remove recent data)
    temp_store.cleanup_old_data(days=0)  # Remove everything older than today
    
    # Data should still be there (created today)
    stats_after = temp_store.get_stats()
    assert stats_after["learned_aliases_count"] == initial_stats["learned_aliases_count"]

