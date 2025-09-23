"""
Pydantic models for event parsing with configurable categories and confidence scoring.

This module defines the strict JSON schema for parsed events, including
configurable categories, rich food parsing, and confidence tracking.
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
import re

from config import get_config

# Get configuration
config = get_config()

# Note: Categories and cuisines are now validated against config lists
# instead of using dynamic enums to avoid import issues

class Contact(BaseModel):
    """Contact information for an event."""
    name: Optional[str] = None
    email: Optional[str] = None

class FoodItem(BaseModel):
    """Rich food information with cuisine and quantity details."""
    name: str = Field(..., description="Food item name")
    quantity_hint: Optional[str] = Field(None, description="Quantity description (e.g., 'first 50', 'light snacks')")
    cuisine: Optional[str] = Field(None, description="Cuisine type from config")
    
    @field_validator("cuisine")
    @classmethod
    def validate_cuisine(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Check if cuisine is in configured list
        if v not in config["cuisines"]:
            return None  # Invalid cuisine, set to None
        return v

class ConfidenceScores(BaseModel):
    """Confidence scores for different aspects of parsing."""
    category: Optional[float] = Field(None, ge=0.0, le=1.0, description="Category confidence score")
    cuisine: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cuisine confidence score")
    overall: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall parsing confidence")

class ParsedEvent(BaseModel):
    """Main event model with configurable categories and rich food parsing."""
    
    # Core event information
    title: str = Field(..., description="Event name")
    description: Optional[str] = Field(None, description="Event description")
    organizer: Optional[str] = None
    contacts: List[Contact] = []
    
    # Date and time
    date_start: Optional[str] = Field(None, description="YYYY-MM-DD")
    time_start: Optional[str] = Field(None, description="HH:MM 24h")
    time_end: Optional[str] = None
    timezone: str = "America/New_York"
    
    # Location and logistics
    location: Optional[str] = None
    urls: List[str] = []  # Changed to List[str] for more flexibility
    
    # Rich food information
    food: List[FoodItem] = Field(default=[], description="List of food items with cuisine and quantity")
    
    # Categorization (configurable)
    category: Optional[str] = Field(None, description="Event category from config")
    
    # Confidence tracking
    confidence: Optional[ConfidenceScores] = None
    
    # Source tracking
    source_message_id: Optional[str] = None
    source_subject: Optional[str] = None
    mailing_list: Optional[str] = None
    original_email_body: Optional[str] = None

    @field_validator("date_start")
    @classmethod
    def validate_date_start(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format."""
        if v is None:
            return v
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("date_start must be YYYY-MM-DD")
        return v

    @field_validator("time_start", "time_end")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format."""
        if v is None:
            return v
        if not re.fullmatch(r"\d{2}:\d{2}", v):
            raise ValueError("time must be HH:MM 24h")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category against configuration."""
        if v is None:
            return v
        if v not in config["categories"]:
            return None  # Invalid category, set to None
        return v

    def get_primary_cuisine(self) -> Optional[str]:
        """Get the most common cuisine from food items."""
        if not self.food:
            return None
        
        cuisine_counts = {}
        for item in self.food:
            if item.cuisine:
                cuisine_counts[item.cuisine] = cuisine_counts.get(item.cuisine, 0) + 1
        
        if not cuisine_counts:
            return None
        
        return max(cuisine_counts, key=cuisine_counts.get)

    def get_food_summary(self) -> str:
        """Get a human-readable summary of food information."""
        if not self.food:
            return ""
        
        items = []
        for item in self.food:
            item_str = item.name
            if item.quantity_hint:
                item_str += f" ({item.quantity_hint})"
            if item.cuisine:
                item_str += f" [{item.cuisine}]"
            items.append(item_str)
        
        return "; ".join(items)

    def is_high_confidence(self, threshold: float = 0.6) -> bool:
        """Check if event has high confidence scores."""
        if not self.confidence:
            return False
        
        scores = []
        if self.confidence.category is not None:
            scores.append(self.confidence.category)
        if self.confidence.cuisine is not None:
            scores.append(self.confidence.cuisine)
        if self.confidence.overall is not None:
            scores.append(self.confidence.overall)
        
        if not scores:
            return False
        
        return min(scores) >= threshold

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        legacy = {
            "title": self.title,
            "description": self.description,
            "organizer": self.organizer,
            "contacts": [{"name": c.name, "email": c.email} for c in self.contacts],
            "date_start": self.date_start,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "timezone": self.timezone,
            "location": self.location,
            "urls": [str(url) for url in self.urls],
            "source_message_id": self.source_message_id,
            "source_subject": self.source_subject,
            "mailing_list": self.mailing_list,
            "original_email_body": self.original_email_body
        }
        
        # Convert food items to legacy format
        if self.food:
            # Use first food item for legacy compatibility
            first_food = self.food[0]
            legacy["food_type"] = first_food.name
            legacy["food_quantity_hint"] = first_food.quantity_hint
        
        return legacy

    @classmethod
    def from_legacy_format(cls, data: Dict[str, Any]) -> "ParsedEvent":
        """Create from legacy format for backward compatibility."""
        # Convert legacy food format
        food_items = []
        if data.get("food_type"):
            food_items.append(FoodItem(
                name=data["food_type"],
                quantity_hint=data.get("food_quantity_hint"),
                cuisine=None  # Will be learned later
            ))
        
        # Remove legacy fields
        legacy_data = data.copy()
        legacy_data.pop("food_type", None)
        legacy_data.pop("food_quantity_hint", None)
        
        # Add new fields
        legacy_data["food"] = food_items
        
        return cls(**legacy_data)

# Backward compatibility aliases
Event = ParsedEvent  # For existing code
