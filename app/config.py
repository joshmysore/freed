"""
Configuration for the Email Event Parser.

This module contains all configurable settings that can be modified
without changing code. All hard-coded lists and thresholds are centralized here.
"""
from typing import Dict, List, Any
import os
from pathlib import Path

# Event Categories (user-editable)
CATEGORIES = [
    "workshop",
    "lecture", 
    "meeting",
    "concert",
    "social",
    "seminar",
    "talk",
    "presentation",
    "conference",
    "gathering",
    "session",
    "party",
    "celebration",
    "dinner",
    "lunch",
    "breakfast",
    "reception",
    "ceremony",
    "festival",
    "fair",
    "exhibition",
    "audition",
    "tryout",
    "info_session",
    "kickoff",
    "launch",
    "orientation"
]

# Cuisine Types (user-editable)
CUISINES = [
    "American",
    "Chinese", 
    "Indian",
    "Italian",
    "Japanese",
    "Korean",
    "Mexican",
    "Thai",
    "Taiwanese",
    "Mediterranean",
    "Middle Eastern",
    "African",
    "Latin American",
    "European",
    "Other"
]

# System Configuration
EVENT_WINDOW_DAYS = 14
MAX_LLM_CALLS_PER_RUN = 10

# Confidence Thresholds
MIN_CONF = {
    "category": 0.6,
    "cuisine": 0.6
}

# Gmail Configuration
GMAIL_QUERY_BASE = "newer_than:{days}d"
GMAIL_QUERY_PATTERNS = [
    "subject:invite",
    "subject:event", 
    "subject:seminar",
    "subject:talk",
    "subject:workshop",
    "subject:session",
    "subject:meeting",
    "subject:lecture"
]

# Event Detection Patterns (generic, language-agnostic)
EVENT_TIME_PATTERNS = [
    r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b\d{4}-\d{2}-\d{2}\b',
    r'\b(mon|tue|wed|thu|fri|sat|sun)day\b',
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b',
    r'\b(today|tomorrow|tonight|this week|next week)\b',
    r'\b(morning|afternoon|evening|night)\b'
]

EVENT_KEYWORD_PATTERNS = [
    'event', 'meeting', 'workshop', 'seminar', 'talk', 'lecture',
    'conference', 'gathering', 'session', 'presentation', 'party',
    'celebration', 'dinner', 'lunch', 'breakfast', 'reception',
    'ceremony', 'festival', 'fair', 'exhibition', 'audition', 'tryout',
    'info session', 'kickoff', 'launch', 'orientation', 'show', 'comedy',
    'performance', 'concert', 'theater', 'theatre', 'movie', 'film',
    'screening', 'demo', 'demonstration', 'tour', 'visit', 'open house',
    'mixer', 'networking', 'social', 'hangout', 'get together',
    # Food-related events
    'bread', 'food', 'snack', 'treat', 'refreshments', 'catering',
    'pizza', 'cookies', 'cake', 'coffee', 'tea', 'drinks',
    'community', 'join', 'please join', 'come', 'everyone'
]

LOCATION_KEYWORD_PATTERNS = [
    'location', 'where', 'room', 'hall', 'building', 'address',
    'venue', 'place', 'site', 'campus', 'center', 'centre'
]

# File Paths
CONFIG_DIR = Path(__file__).parent
PROMPTS_DIR = CONFIG_DIR / "prompts"
STORE_FILE = CONFIG_DIR / "store.json"

# Learning Configuration
LEARNING_CONFIG = {
    "alias_confidence_threshold": 0.7,
    "rolling_average_alpha": 0.3,  # Exponential moving average factor
    "min_samples_for_confidence": 3
}

def get_gmail_query() -> str:
    """Generate Gmail query from configuration."""
    base_query = GMAIL_QUERY_BASE.format(days=EVENT_WINDOW_DAYS)
    pattern_query = " OR ".join(f"({pattern})" for pattern in GMAIL_QUERY_PATTERNS)
    return f"{base_query} ({pattern_query})"

def load_custom_config(config_file: str = None) -> Dict[str, Any]:
    """Load custom configuration from file if it exists."""
    if config_file is None:
        config_file = os.getenv('EVENT_PARSER_CONFIG', str(CONFIG_DIR / "custom_config.json"))
    
    if not os.path.exists(config_file):
        return {}
    
    import json
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load custom config from {config_file}: {e}")
        return {}

def get_config() -> Dict[str, Any]:
    """Get complete configuration with custom overrides."""
    config = {
        "categories": CATEGORIES,
        "cuisines": CUISINES,
        "event_window_days": EVENT_WINDOW_DAYS,
        "max_llm_calls_per_run": MAX_LLM_CALLS_PER_RUN,
        "min_confidence": MIN_CONF,
        "gmail_query": get_gmail_query(),
        "event_time_patterns": EVENT_TIME_PATTERNS,
        "event_keyword_patterns": EVENT_KEYWORD_PATTERNS,
        "location_keyword_patterns": LOCATION_KEYWORD_PATTERNS,
        "learning_config": LEARNING_CONFIG,
        "store_file": str(STORE_FILE)
    }
    
    # Apply custom overrides
    custom = load_custom_config()
    config.update(custom)
    
    return config
