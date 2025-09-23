"""
Regression tests for None-safe text normalization.
"""
import pytest
from app.utils import norm_text, event_dedupe_key, safe_lower, normalize_food_name


def test_norm_text_none_ok():
    """Test that norm_text handles None values safely."""
    assert norm_text(None) == ""
    assert norm_text("") == ""
    assert norm_text("  ") == ""
    assert norm_text("Hello World") == "hello world"
    assert norm_text("  Hello   World  ") == "hello world"


def test_norm_text_non_string_ok():
    """Test that norm_text handles non-string values safely."""
    assert norm_text(123) == ""
    assert norm_text([]) == ""
    assert norm_text({}) == ""
    assert norm_text(True) == ""


def test_event_dedupe_key_all_none_ok():
    """Test that event_dedupe_key handles all None values safely."""
    key = event_dedupe_key(None, None, None, None)
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length


def test_event_dedupe_key_mixed_none_ok():
    """Test that event_dedupe_key handles mixed None values safely."""
    key1 = event_dedupe_key("Test Event", None, "14:00", None)
    key2 = event_dedupe_key("Test Event", "2025-01-15", None, "Room 101")
    
    assert isinstance(key1, str)
    assert isinstance(key2, str)
    assert len(key1) == 32
    assert len(key2) == 32
    assert key1 != key2  # Different inputs should produce different keys


def test_safe_lower_none_ok():
    """Test that safe_lower handles None values safely."""
    assert safe_lower(None) == ""
    assert safe_lower("") == ""
    assert safe_lower("Hello") == "hello"
    assert safe_lower("  WORLD  ") == "world"


def test_normalize_food_name_none_ok():
    """Test that normalize_food_name handles None values safely."""
    assert normalize_food_name(None) == ""
    assert normalize_food_name("") == ""
    assert normalize_food_name("Pizza") == "pizza"
    assert normalize_food_name("  SUSHI  ") == "sushi"


def test_norm_text_unicode_normalization():
    """Test that norm_text properly normalizes unicode."""
    # Test case folding
    assert norm_text("Café") == "café"
    assert norm_text("CAFÉ") == "café"
    
    # Test whitespace normalization
    assert norm_text("Hello\t\nWorld") == "hello world"
    assert norm_text("Hello   World") == "hello world"


def test_event_dedupe_key_consistency():
    """Test that event_dedupe_key produces consistent results."""
    key1 = event_dedupe_key("Test Event", "2025-01-15", "14:00", "Room 101")
    key2 = event_dedupe_key("Test Event", "2025-01-15", "14:00", "Room 101")
    
    assert key1 == key2  # Same inputs should produce same key
    
    # Test with different whitespace
    key3 = event_dedupe_key("  Test Event  ", "2025-01-15", "14:00", "  Room 101  ")
    assert key1 == key3  # Normalized whitespace should produce same key


def test_norm_text_edge_cases():
    """Test edge cases for norm_text."""
    # Empty string
    assert norm_text("") == ""
    
    # Only whitespace
    assert norm_text("   ") == ""
    assert norm_text("\t\n") == ""
    
    # Special characters
    assert norm_text("Hello-World") == "hello-world"
    assert norm_text("Hello_World") == "hello_world"
    
    # Numbers
    assert norm_text("123") == "123"
    assert norm_text("123.45") == "123.45"

