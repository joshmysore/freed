"""
Tests for the new schema with configurable categories and confidence scoring.
"""
import pytest
from datetime import datetime
from ..schema import ParsedEvent, FoodItem, ConfidenceScores, Category, Cuisine
from ..config import get_config

def test_food_item_creation():
    """Test FoodItem creation and validation."""
    # Valid food item
    food = FoodItem(
        name="pizza",
        quantity_hint="first 50 people",
        cuisine="Italian"
    )
    assert food.name == "pizza"
    assert food.quantity_hint == "first 50 people"
    assert food.cuisine == "Italian"
    
    # Invalid cuisine should be set to None
    food_invalid = FoodItem(
        name="sushi",
        cuisine="InvalidCuisine"
    )
    assert food_invalid.cuisine is None

def test_confidence_scores():
    """Test ConfidenceScores validation."""
    conf = ConfidenceScores(
        category=0.8,
        cuisine=0.6,
        overall=0.7
    )
    assert conf.category == 0.8
    assert conf.cuisine == 0.6
    assert conf.overall == 0.7
    
    # Test bounds validation
    with pytest.raises(ValueError):
        ConfidenceScores(category=1.5)  # > 1.0
    
    with pytest.raises(ValueError):
        ConfidenceScores(category=-0.1)  # < 0.0

def test_parsed_event_creation():
    """Test ParsedEvent creation with new schema."""
    config = get_config()
    
    event = ParsedEvent(
        title="Test Event",
        date_start="2025-09-20",
        time_start="14:00",
        location="Test Location",
        category="workshop",
        food=[
            FoodItem(name="pizza", cuisine="Italian", quantity_hint="dinner provided"),
            FoodItem(name="soda", quantity_hint="unlimited")
        ],
        confidence=ConfidenceScores(category=0.8, cuisine=0.7)
    )
    
    assert event.title == "Test Event"
    assert event.category == "workshop"
    assert len(event.food) == 2
    assert event.food[0].cuisine == "Italian"
    assert event.confidence.category == 0.8

def test_category_validation():
    """Test category validation against config."""
    config = get_config()
    
    # Valid category
    event = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        category="workshop"
    )
    assert event.category == "workshop"
    
    # Invalid category should be set to None
    event_invalid = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        category="invalid_category"
    )
    assert event_invalid.category is None

def test_food_summary():
    """Test food summary generation."""
    event = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        food=[
            FoodItem(name="pizza", cuisine="Italian", quantity_hint="dinner"),
            FoodItem(name="soda", quantity_hint="unlimited")
        ]
    )
    
    summary = event.get_food_summary()
    assert "pizza (dinner) [Italian]" in summary
    assert "soda (unlimited)" in summary

def test_primary_cuisine():
    """Test primary cuisine detection."""
    event = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        food=[
            FoodItem(name="pizza", cuisine="Italian"),
            FoodItem(name="pasta", cuisine="Italian"),
            FoodItem(name="soda")  # No cuisine
        ]
    )
    
    assert event.get_primary_cuisine() == "Italian"
    
    # Test with no cuisines
    event_no_cuisine = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        food=[FoodItem(name="soda")]
    )
    assert event_no_cuisine.get_primary_cuisine() is None

def test_confidence_check():
    """Test high confidence checking."""
    # High confidence event
    event_high = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        confidence=ConfidenceScores(category=0.8, cuisine=0.7, overall=0.9)
    )
    assert event_high.is_high_confidence(0.6) is True
    
    # Low confidence event
    event_low = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        confidence=ConfidenceScores(category=0.4, cuisine=0.5)
    )
    assert event_low.is_high_confidence(0.6) is False
    
    # No confidence scores
    event_no_conf = ParsedEvent(
        title="Test",
        date_start="2025-09-20"
    )
    assert event_no_conf.is_high_confidence(0.6) is False

def test_legacy_format_conversion():
    """Test conversion to/from legacy format."""
    # Test to_legacy_format
    event = ParsedEvent(
        title="Test Event",
        date_start="2025-09-20",
        time_start="14:00",
        food=[FoodItem(name="pizza", quantity_hint="dinner")]
    )
    
    legacy = event.to_legacy_format()
    assert legacy["title"] == "Test Event"
    assert legacy["food_type"] == "pizza"
    assert legacy["food_quantity_hint"] == "dinner"
    
    # Test from_legacy_format
    legacy_data = {
        "title": "Legacy Event",
        "date_start": "2025-09-20",
        "food_type": "sushi",
        "food_quantity_hint": "lunch"
    }
    
    event_from_legacy = ParsedEvent.from_legacy_format(legacy_data)
    assert event_from_legacy.title == "Legacy Event"
    assert len(event_from_legacy.food) == 1
    assert event_from_legacy.food[0].name == "sushi"
    assert event_from_legacy.food[0].quantity_hint == "lunch"

def test_date_validation():
    """Test date format validation."""
    # Valid date
    event = ParsedEvent(
        title="Test",
        date_start="2025-09-20"
    )
    assert event.date_start == "2025-09-20"
    
    # Invalid date format
    with pytest.raises(ValueError):
        ParsedEvent(
            title="Test",
            date_start="2025/09/20"  # Wrong format
        )

def test_time_validation():
    """Test time format validation."""
    # Valid times
    event = ParsedEvent(
        title="Test",
        date_start="2025-09-20",
        time_start="14:00",
        time_end="16:00"
    )
    assert event.time_start == "14:00"
    assert event.time_end == "16:00"
    
    # Invalid time format
    with pytest.raises(ValueError):
        ParsedEvent(
            title="Test",
            date_start="2025-09-20",
            time_start="2:00 PM"  # Wrong format
        )

