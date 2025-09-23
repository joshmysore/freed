"""
Lightweight key-value store for learned aliases, caches, and deduplication.

This module provides persistent storage for:
- Learned food name → cuisine mappings
- LLM response caching
- Event deduplication tracking
"""
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from config import get_config
from utils import norm_text, event_dedupe_key

logger = logging.getLogger(__name__)

class EventStore:
    """Persistent store for learned data and caches."""
    
    def __init__(self, store_file: str = None):
        self.config = get_config()
        self.store_file = Path(store_file or self.config["store_file"])
        self.data = self._load_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """Load data from persistent store."""
        if not self.store_file.exists():
            return {
                "learned_aliases": {},
                "llm_cache": {},
                "event_dedup": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
        
        try:
            with open(self.store_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load store from {self.store_file}: {e}")
            return {
                "learned_aliases": {},
                "llm_cache": {},
                "event_dedup": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
    
    def _save_data(self):
        """Save data to persistent store."""
        try:
            self.store_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save store to {self.store_file}: {e}")
    
    def get_learned_cuisine(self, food_name: str) -> Optional[Tuple[str, float]]:
        """
        Get learned cuisine for a food name.
        
        Returns:
            Tuple of (cuisine, confidence) or None if not learned
        """
        normalized_name = norm_text(food_name)
        alias_data = self.data["learned_aliases"].get(normalized_name)
        
        if not alias_data:
            return None
            
        confidence = alias_data.get("rolling_confidence", 0.0)
        threshold = self.config["learning_config"]["alias_confidence_threshold"]
        
        if confidence >= threshold:
            return (alias_data["last_cuisine"], confidence)
        
        return None
    
    def learn_cuisine(self, food_name: str, cuisine: str, confidence: float):
        """
        Learn cuisine mapping for a food name.
        
        Args:
            food_name: Normalized food name
            cuisine: Detected cuisine type
            confidence: Confidence score from LLM
        """
        normalized_name = norm_text(food_name)
        threshold = self.config["learning_config"]["alias_confidence_threshold"]
        
        if confidence < threshold:
            return  # Don't learn low-confidence mappings
        
        alias_data = self.data["learned_aliases"].get(normalized_name, {
            "last_cuisine": cuisine,
            "rolling_confidence": 0.0,
            "sample_count": 0
        })
        
        # Update rolling average
        alpha = self.config["learning_config"]["rolling_average_alpha"]
        old_confidence = alias_data["rolling_confidence"]
        new_confidence = alpha * confidence + (1 - alpha) * old_confidence
        
        alias_data.update({
            "last_cuisine": cuisine,
            "rolling_confidence": new_confidence,
            "sample_count": alias_data["sample_count"] + 1,
            "last_updated": datetime.now().isoformat()
        })
        
        self.data["learned_aliases"][normalized_name] = alias_data
        self._save_data()
        
        logger.debug(f"Learned cuisine: {normalized_name} -> {cuisine} (conf: {new_confidence:.3f})")
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached LLM response."""
        cache_entry = self.data["llm_cache"].get(cache_key)
        
        if not cache_entry:
            return None
            
        # Check if cache is still valid (24 hours)
        try:
            cached_time = datetime.fromisoformat(cache_entry["timestamp"])
            if datetime.now() - cached_time > timedelta(hours=24):
                del self.data["llm_cache"][cache_key]
                self._save_data()
                return None
        except (ValueError, KeyError):
            return None
            
        return cache_entry["response"]
    
    def cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache LLM response."""
        self.data["llm_cache"][cache_key] = {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        self._save_data()
    
    def generate_cache_key(self, message_id: str, email_body: str) -> str:
        """Generate cache key for email content."""
        # Create deterministic hash of email content
        content_hash = hashlib.sha256(email_body.encode('utf-8')).hexdigest()[:16]
        return f"{message_id}_{content_hash}"
    
    def is_duplicate_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Check if event is a duplicate.
        
        Returns:
            Duplicate event ID if found, None otherwise
        """
        # Generate deterministic key using safe normalization
        primary_key = event_dedupe_key(
            event_data.get("title"),
            event_data.get("date_start"),
            event_data.get("time_start"),
            event_data.get("location")
        )
        
        # Check exact match first
        if primary_key in self.data["event_dedup"]:
            return self.data["event_dedup"][primary_key]
        
        # Fuzzy matching for similar events
        for stored_key, event_id in self.data["event_dedup"].items():
            stored_title = stored_key.split("|")[0]
            
            # Check if titles are similar and dates are close
            if self._is_similar_event(event_data, stored_key):
                return event_id
        
        return None
    
    def _is_similar_event(self, event_data: Dict[str, Any], stored_key: str) -> bool:
        """Check if two events are similar enough to be duplicates."""
        try:
            stored_parts = stored_key.split("|")
            if len(stored_parts) < 4:
                return False
                
            stored_title, stored_date, stored_time, stored_location = stored_parts[:4]
            
            # Title similarity (token sort ratio)
            title_similarity = SequenceMatcher(
                None, 
                norm_text(event_data.get("title")),
                stored_title
            ).ratio()
            
            if title_similarity < 0.9:
                return False
            
            # Date proximity (within 1 day)
            try:
                event_date = datetime.strptime(event_data.get("date_start", ""), "%Y-%m-%d")
                stored_date = datetime.strptime(stored_date, "%Y-%m-%d")
                date_diff = abs((event_date - stored_date).days)
                
                if date_diff > 1:
                    return False
            except ValueError:
                return False
            
            # Location similarity (if both have locations)
            event_location = norm_text(event_data.get("location"))
            if event_location and stored_location:
                location_similarity = SequenceMatcher(
                    None, event_location, stored_location
                ).ratio()
                if location_similarity < 0.8:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error in similarity check: {e}")
            return False
    
    def register_event(self, event_id: str, event_data: Dict[str, Any]):
        """Register event for deduplication tracking."""
        primary_key = event_dedupe_key(
            event_data.get("title"),
            event_data.get("date_start"),
            event_data.get("time_start"),
            event_data.get("location")
        )
        self.data["event_dedup"][primary_key] = event_id
        self._save_data()
    
    def merge_event_data(self, base_event: Dict[str, Any], new_event: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two event data dictionaries."""
        merged = base_event.copy()
        
        # Merge URLs
        base_urls = set(base_event.get("urls", []))
        new_urls = set(new_event.get("urls", []))
        merged["urls"] = list(base_urls.union(new_urls))
        
        # Merge mailing lists
        base_lists = set(base_event.get("mailing_list", []))
        new_lists = set(new_event.get("mailing_list", []))
        merged["mailing_list"] = list(base_lists.union(new_lists))
        
        # Use higher confidence scores
        if "confidence" in new_event and "confidence" in base_event:
            merged["confidence"] = {}
            for key in ["category", "cuisine"]:
                if key in new_event["confidence"] and key in base_event["confidence"]:
                    merged["confidence"][key] = max(
                        new_event["confidence"][key],
                        base_event["confidence"][key]
                    )
                elif key in new_event["confidence"]:
                    merged["confidence"][key] = new_event["confidence"][key]
                elif key in base_event["confidence"]:
                    merged["confidence"][key] = base_event["confidence"][key]
        
        return merged
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old cache and dedup data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old cache entries
        old_cache_keys = []
        for key, entry in self.data["llm_cache"].items():
            try:
                cached_time = datetime.fromisoformat(entry["timestamp"])
                if cached_time < cutoff_date:
                    old_cache_keys.append(key)
            except (ValueError, KeyError):
                old_cache_keys.append(key)
        
        for key in old_cache_keys:
            del self.data["llm_cache"][key]
        
        # Clean up old dedup entries (keep last 30 days)
        old_dedup_keys = []
        for key, event_id in self.data["event_dedup"].items():
            try:
                # Extract date from key
                date_part = key.split("|")[1]
                event_date = datetime.strptime(date_part, "%Y-%m-%d")
                if event_date < cutoff_date:
                    old_dedup_keys.append(key)
            except (ValueError, IndexError):
                old_dedup_keys.append(key)
        
        for key in old_dedup_keys:
            del self.data["event_dedup"][key]
        
        if old_cache_keys or old_dedup_keys:
            self._save_data()
            logger.info(f"Cleaned up {len(old_cache_keys)} cache entries and {len(old_dedup_keys)} dedup entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "learned_aliases_count": len(self.data["learned_aliases"]),
            "cache_entries_count": len(self.data["llm_cache"]),
            "dedup_entries_count": len(self.data["event_dedup"]),
            "store_size_mb": self.store_file.stat().st_size / (1024 * 1024) if self.store_file.exists() else 0
        }
