"""
Post-processing heuristics for event parsing with learning and confidence thresholds.

This module handles:
- Confidence-based filtering and abstention
- Learned alias management for food items
- Data normalization and validation
- Integration with the learning store
"""
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_config
from store import EventStore
from schema import ParsedEvent, FoodItem, ConfidenceScores
from utils import norm_text

logger = logging.getLogger(__name__)

class PostProcessor:
    """Post-processes parsed events with learning and confidence handling."""
    
    def __init__(self, store: EventStore = None):
        self.config = get_config()
        self.store = store or EventStore()
        self.min_confidence = self.config["min_confidence"]
        
    def process_event(self, event_data: Dict[str, Any]) -> Optional[ParsedEvent]:
        """
        Process a parsed event with confidence filtering and learning.
        
        Args:
            event_data: Raw parsed data from LLM
            
        Returns:
            Processed ParsedEvent or None if filtered out
        """
        try:
            # Normalize the data first
            normalized_data = self._normalize_parsed_data(event_data)
            
            # Apply confidence filtering
            filtered_data = self._apply_confidence_filtering(normalized_data)
            
            # Process food items with learning
            filtered_data = self._process_food_items(filtered_data)
            
            # Validate and create ParsedEvent
            try:
                event = ParsedEvent(**filtered_data)
                return event
            except Exception as e:
                logger.error(f"Pydantic validation failed: {e}")
                logger.error(f"Filtered data: {filtered_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
            return None
    
    def _normalize_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed data before validation."""
        # Normalize URLs
        if 'urls' in parsed_data:
            parsed_data['urls'] = self._normalize_urls(parsed_data.get('urls', []))
        
        # Map placeholders to None
        placeholders = {"", "TBD", "N/A", "-", "null", "NULL"}
        
        for key in ['organizer', 'location', 'description']:
            if key in parsed_data and parsed_data[key] in placeholders:
                parsed_data[key] = None
        
        # Clean up contact information
        if 'contacts' in parsed_data:
            for contact in parsed_data.get('contacts', []):
                if isinstance(contact, dict):
                    for field in ['name', 'email']:
                        if field in contact and contact[field] in placeholders:
                            contact[field] = None
        
        # Strip exotic dashes and collapse whitespace
        for key in ['title', 'description', 'location']:
            if key in parsed_data and parsed_data[key]:
                text = str(parsed_data[key])
                # Replace fancy dashes
                text = re.sub(r'[–—]', '-', text)
                # Collapse repeated spaces
                text = re.sub(r'\s+', ' ', text).strip()
                parsed_data[key] = text
        
        return parsed_data
    
    def _apply_confidence_filtering(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply confidence-based filtering and abstention."""
        confidence = data.get('confidence', {})
        
        # Filter category based on confidence
        if 'category' in data and data['category']:
            category_conf = confidence.get('category', 1.0)
            if category_conf < self.min_confidence['category']:
                logger.debug(f"Category '{data['category']}' filtered out (conf: {category_conf:.3f})")
                data['category'] = None
        
        # Filter food items based on cuisine confidence
        if 'food' in data and isinstance(data['food'], list):
            filtered_food = []
            for item in data['food']:
                if isinstance(item, dict):
                    cuisine_conf = item.get('confidence', {}).get('cuisine', 1.0)
                    if cuisine_conf < self.min_confidence['cuisine']:
                        logger.debug(f"Cuisine '{item.get('cuisine')}' filtered out (conf: {cuisine_conf:.3f})")
                        item['cuisine'] = None
                    filtered_food.append(item)
            data['food'] = filtered_food
        
        return data
    
    def _process_food_items(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process food items with learning and alias management."""
        if 'food' not in data or not isinstance(data['food'], list):
            return data
        
        processed_food = []
        for item_data in data['food']:
            if not isinstance(item_data, dict):
                continue
                
            # Create FoodItem with safe normalization
            name = norm_text(item_data.get('name'))
            if not name:
                continue
            food_item = FoodItem(
                name=name,
                quantity_hint=item_data.get('quantity_hint'),
                cuisine=item_data.get('cuisine')
            )
            
            # Check for learned cuisine
            learned_cuisine = self.store.get_learned_cuisine(food_item.name)
            if learned_cuisine and not food_item.cuisine:
                # Use learned cuisine if no cuisine was detected
                food_item.cuisine = learned_cuisine[0]
                logger.debug(f"Using learned cuisine for '{food_item.name}': {learned_cuisine[0]}")
            elif food_item.cuisine:
                # Learn this mapping if confidence is high enough
                confidence = item_data.get('confidence', {}).get('cuisine', 1.0)
                if confidence >= self.min_confidence['cuisine']:
                    self.store.learn_cuisine(food_item.name, food_item.cuisine, confidence)
            
            processed_food.append(food_item)
        
        data['food'] = processed_food
        return data
    
    def _normalize_urls(self, urls: List[str]) -> List[str]:
        """Normalize URLs for consistency."""
        normalized = []
        for url in urls:
            if not url or not isinstance(url, str):
                continue
            
            # Basic URL cleaning
            url = url.strip()
            if not url:
                continue
                
            # Only add protocol if it doesn't have one
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Basic validation - just check if it looks like a URL
            if '.' in url and len(url) > 3:
                # Remove common tracking parameters
                url = re.sub(r'[?&](utm_[^&]*|fbclid|gclid|ref)=[^&]*', '', url)
                url = re.sub(r'[?&]$', '', url)  # Remove trailing ? or &
                normalized.append(url)
        
        return normalized

    def normalize_food_items(self, food_items: List[Dict[str, Any]]) -> List[FoodItem]:
        """Normalize food items with safe string handling."""
        normalized_items = []
        for item in (food_items or []):
            name = norm_text(item.get("name"))
            if not name:
                continue
            quantity_hint = item.get("quantity_hint")
            cuisine = item.get("cuisine")
            normalized_items.append(FoodItem(
                name=name,
                quantity_hint=quantity_hint,
                cuisine=cuisine
            ))
        return normalized_items

    def process_events_batch(self, events_data: List[Dict[str, Any]]) -> List[ParsedEvent]:
        """Process a batch of events with deduplication."""
        processed_events = []
        seen_events = set()
        
        for event_data in events_data:
            # Check for duplicates
            event_id = f"{event_data.get('title', '')}_{event_data.get('date_start', '')}_{event_data.get('time_start', '')}"
            if event_id in seen_events:
                continue
            
            # Process the event
            event = self.process_event(event_data)
            if event:
                # Check for duplicate in store
                duplicate_id = self.store.is_duplicate_event(event.model_dump())
                if duplicate_id:
                    logger.debug(f"Duplicate event detected: {event.title}")
                    # Could merge with existing event here
                    continue
                
                # Register event for future deduplication
                self.store.register_event(event_id, event.model_dump())
                processed_events.append(event)
                seen_events.add(event_id)
        
        return processed_events
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learned aliases and processing."""
        store_stats = self.store.get_stats()
        
        # Count learned cuisines by confidence level
        high_conf_count = 0
        medium_conf_count = 0
        low_conf_count = 0
        
        for alias_data in self.store.data["learned_aliases"].values():
            conf = alias_data.get("rolling_confidence", 0.0)
            if conf >= 0.8:
                high_conf_count += 1
            elif conf >= 0.6:
                medium_conf_count += 1
            else:
                low_conf_count += 1
        
        return {
            **store_stats,
            "learned_cuisines": {
                "high_confidence": high_conf_count,
                "medium_confidence": medium_conf_count,
                "low_confidence": low_conf_count
            },
            "confidence_thresholds": self.min_confidence
        }
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old learned data and caches."""
        self.store.cleanup_old_data(days)
        logger.info(f"Cleaned up data older than {days} days")

# Backward compatibility
def process_event(event_data: Dict[str, Any]) -> Optional[ParsedEvent]:
    """Backward compatibility function."""
    processor = PostProcessor()
    return processor.process_event(event_data)
