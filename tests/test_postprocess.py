import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from postprocess import PostProcessor
from schema import ParsedEvent


class TestPostProcessor:
    
    def test_normalize_time_12_hour_format(self):
        # Test 12-hour format conversion
        assert PostProcessor.normalize_time("2:00 PM") == "14:00"
        assert PostProcessor.normalize_time("10:30 AM") == "10:30"
        assert PostProcessor.normalize_time("12:00 PM") == "12:00"
        assert PostProcessor.normalize_time("12:00 AM") == "00:00"
        assert PostProcessor.normalize_time("11:59 PM") == "23:59"
    
    def test_normalize_time_24_hour_format(self):
        # Test 24-hour format (should pass through)
        assert PostProcessor.normalize_time("14:00") == "14:00"
        assert PostProcessor.normalize_time("09:30") == "09:30"
        assert PostProcessor.normalize_time("00:00") == "00:00"
        assert PostProcessor.normalize_time("23:59") == "23:59"
    
    def test_normalize_time_hour_only(self):
        # Test hour only with AM/PM
        assert PostProcessor.normalize_time("2 PM") == "14:00"
        assert PostProcessor.normalize_time("10 AM") == "10:00"
        assert PostProcessor.normalize_time("12 PM") == "12:00"
        assert PostProcessor.normalize_time("12 AM") == "00:00"
    
    def test_normalize_time_invalid_formats(self):
        # Test invalid formats
        assert PostProcessor.normalize_time("invalid") is None
        assert PostProcessor.normalize_time("25:00") is None
        assert PostProcessor.normalize_time("14:60") is None
        assert PostProcessor.normalize_time("") is None
        assert PostProcessor.normalize_time(None) is None
    
    def test_infer_end_time_from_duration(self):
        # Test duration inference
        assert PostProcessor.infer_end_time("14:00", "2 hours") == "16:00"
        assert PostProcessor.infer_end_time("14:00", "1 hour") == "15:00"
        assert PostProcessor.infer_end_time("14:00", "30 minutes") == "14:30"
        assert PostProcessor.infer_end_time("14:00", "90 minutes") == "15:30"
    
    def test_infer_end_time_from_range(self):
        # Test time range inference
        assert PostProcessor.infer_end_time("14:00", "5-6 PM") == "18:00"
        assert PostProcessor.infer_end_time("14:00", "2-3 PM") == "15:00"
    
    def test_infer_end_time_no_match(self):
        # Test when no duration/range found
        assert PostProcessor.infer_end_time("14:00", "Some other text") is None
        assert PostProcessor.infer_end_time("14:00", None) is None
        assert PostProcessor.infer_end_time(None, "2 hours") is None
    
    def test_normalize_location(self):
        # Test location normalization
        assert PostProcessor.normalize_location("  Test Location  ") == "Test Location"
        assert PostProcessor.normalize_location("Location: Test Hall") == "Test Hall"
        assert PostProcessor.normalize_location("Where: Room 101 (Building A)") == "Where: Room 101"
        assert PostProcessor.normalize_location("") is None
        assert PostProcessor.normalize_location(None) is None
    
    def test_extract_food_info_specific_vendors(self):
        # Test specific vendor detection
        food_type, quantity = PostProcessor.extract_food_info("Bonchon chicken will be provided")
        assert food_type == "Bonchon"
        assert quantity is None
        
        food_type, quantity = PostProcessor.extract_food_info("Pizza from Domino's")
        assert food_type == "Pizza"
        assert quantity is None
        
        food_type, quantity = PostProcessor.extract_food_info("Sushi dinner")
        assert food_type == "Sushi"
        assert quantity is None
    
    def test_extract_food_info_generic(self):
        # Test generic food detection
        food_type, quantity = PostProcessor.extract_food_info("Dinner provided")
        assert food_type == "Catered"
        assert quantity == "dinner provided"
        
        food_type, quantity = PostProcessor.extract_food_info("Light snacks will be available")
        assert food_type == "Catered"
        assert quantity == "light snacks"
        
        food_type, quantity = PostProcessor.extract_food_info("Refreshments provided")
        assert food_type == "Catered"
        assert quantity == "refreshments provided"
    
    def test_extract_food_info_quantity_hints(self):
        # Test quantity hint extraction
        food_type, quantity = PostProcessor.extract_food_info("Pizza provided while supplies last")
        assert food_type == "Pizza"
        assert quantity == "while supplies last"
        
        food_type, quantity = PostProcessor.extract_food_info("Limited snacks available")
        assert food_type == "Catered"
        assert quantity == "limited snacks"
    
    def test_extract_food_info_no_food(self):
        # Test when no food mentioned
        food_type, quantity = PostProcessor.extract_food_info("Regular meeting")
        assert food_type is None
        assert quantity is None
        
        food_type, quantity = PostProcessor.extract_food_info("")
        assert food_type is None
        assert quantity is None
        
        food_type, quantity = PostProcessor.extract_food_info(None)
        assert food_type is None
        assert quantity is None
    
    def test_extract_urls(self):
        # Test URL extraction
        text = "Visit https://example.com for more info and http://test.org"
        urls = PostProcessor.extract_urls(text)
        assert "https://example.com" in urls
        assert "http://test.org" in urls
        assert len(urls) == 2
        
        # Test with no URLs
        urls = PostProcessor.extract_urls("No URLs here")
        assert urls == []
        
        # Test with duplicate URLs
        text = "Check https://example.com and also https://example.com"
        urls = PostProcessor.extract_urls(text)
        assert len(urls) == 1  # duplicates removed
        assert "https://example.com" in urls
    
    def test_process_event_comprehensive(self):
        # Test comprehensive event processing
        event = ParsedEvent(
            title="Test Event",
            date_start="2024-12-19",
            time_start="14:00",  # Use 24-hour format for initial creation
            location="  Test Hall  ",
            description="Dinner provided by Bonchon. Visit https://example.com for details. Duration: 2 hours."
        )
        
        processed = PostProcessor.process_event(event)
        
        # Check time normalization (should remain the same)
        assert processed.time_start == "14:00"
        
        # Check end time inference
        assert processed.time_end == "16:00"
        
        # Check location normalization
        assert processed.location == "Test Hall"
        
        # Check food extraction
        assert processed.food_type == "Bonchon"
        assert processed.food_quantity_hint == "dinner provided"
        
        # Check URL extraction
        assert len(processed.urls) == 1
        assert str(processed.urls[0]) == "https://example.com/"
    
    def test_process_event_minimal(self):
        # Test processing with minimal data
        event = ParsedEvent(
            title="Minimal Event",
            date_start="2024-12-19"
        )
        
        processed = PostProcessor.process_event(event)
        
        # Should not change anything
        assert processed.title == "Minimal Event"
        assert processed.date_start == "2024-12-19"
        assert processed.time_start is None
        assert processed.time_end is None
        assert processed.location is None
        assert processed.food_type is None
        assert processed.food_quantity_hint is None
        assert processed.urls == []
