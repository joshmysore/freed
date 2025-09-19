"""
Unit tests for URL normalization utilities.
"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from url_utils import normalize_url, normalize_urls


class TestNormalizeUrl:
    """Test cases for normalize_url function."""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are returned as-is."""
        assert normalize_url("https://example.com") == "https://example.com"
        assert normalize_url("https://example.com/path") == "https://example.com/path"
    
    def test_valid_http_url(self):
        """Test that valid HTTP URLs are returned as-is."""
        assert normalize_url("http://example.com") == "http://example.com"
    
    def test_domain_without_scheme(self):
        """Test that domains without schemes get https:// prefix."""
        assert normalize_url("example.com") == "https://example.com"
        assert normalize_url("subdomain.example.com") == "https://subdomain.example.com"
        assert normalize_url("example.com/path") == "https://example.com/path"
    
    def test_invalid_urls(self):
        """Test that invalid URLs return None."""
        assert normalize_url("") is None
        assert normalize_url("   ") is None
        assert normalize_url("not-a-url") is None
        assert normalize_url("just-text") is None
        assert normalize_url("123") is None
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        assert normalize_url("  https://example.com  ") == "https://example.com"
        assert normalize_url("  example.com  ") == "https://example.com"


class TestNormalizeUrls:
    """Test cases for normalize_urls function."""
    
    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert normalize_urls([]) == []
        assert normalize_urls(None) == []
    
    def test_valid_urls(self):
        """Test that valid URLs are normalized and returned."""
        urls = [
            "https://example.com",
            "http://test.com",
            "domain.com",
            "sub.domain.org/path"
        ]
        expected = [
            "https://example.com",
            "http://test.com",
            "https://domain.com",
            "https://sub.domain.org/path"
        ]
        assert normalize_urls(urls) == expected
    
    def test_duplicate_removal(self):
        """Test that duplicates are removed."""
        urls = [
            "https://example.com",
            "https://example.com",
            "example.com",
            "https://example.com/path"
        ]
        expected = [
            "https://example.com",
            "https://example.com/path"
        ]
        assert normalize_urls(urls) == expected
    
    def test_invalid_url_filtering(self):
        """Test that invalid URLs are filtered out."""
        urls = [
            "https://example.com",
            "",
            "not-a-url",
            "domain.com",
            "   "
        ]
        expected = [
            "https://example.com",
            "https://domain.com"
        ]
        assert normalize_urls(urls) == expected
    
    def test_mixed_valid_invalid(self):
        """Test handling of mixed valid and invalid URLs."""
        urls = [
            "https://valid.com",
            "invalid",
            "also-valid.com",
            "",
            "https://another-valid.com"
        ]
        expected = [
            "https://valid.com",
            "https://also-valid.com",
            "https://another-valid.com"
        ]
        assert normalize_urls(urls) == expected


if __name__ == "__main__":
    pytest.main([__file__])

