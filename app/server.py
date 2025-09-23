"""
FastAPI server for the Email Event Parser with configurable behavior.

This module provides:
- Config-driven API endpoints
- Generic filtering by category and cuisine
- Learning and caching integration
- Backward compatibility
"""
import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from gmail_client import GmailClient
from parser_llm import LLMParser
from postprocess import PostProcessor
from store import EventStore
from schema import ParsedEvent
from calendar_ics import ICSGenerator
from utils import norm_text

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Email Event Parser",
    description="Parse events from Gmail emails using LLM with configurable behavior",
    version="2.0.0"
)

# Initialize components
gmail_client = None
llm_parser = None
post_processor = None
event_store = None
config = None

def get_components():
    """Get or initialize all components."""
    global gmail_client, llm_parser, post_processor, event_store, config
    
    if config is None:
        config = get_config()
    
    if event_store is None:
        try:
            event_store = EventStore()
        except Exception as e:
            logger.error(f"Failed to initialize event store: {e}")
            event_store = None
    
    if gmail_client is None:
        try:
            gmail_client = GmailClient()
        except Exception as e:
            logger.error(f"Failed to initialize Gmail client: {e}")
            gmail_client = None
    
    if llm_parser is None:
        try:
            llm_parser = LLMParser(store=event_store)
        except Exception as e:
            logger.error(f"Failed to initialize LLM parser: {e}")
            llm_parser = None
    
    if post_processor is None:
        try:
            post_processor = PostProcessor(store=event_store)
        except Exception as e:
            logger.error(f"Failed to initialize post-processor: {e}")
            post_processor = None
    
    return gmail_client, llm_parser, post_processor, event_store, config

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Email Event Parser v2.0 is running"}

@app.get("/config")
async def get_configuration():
    """Get current configuration."""
    gmail, llm, post, store, config = get_components()
    
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not available")
    
    return {
        "categories": config["categories"],
        "cuisines": config["cuisines"],
        "event_window_days": config["event_window_days"],
        "max_llm_calls_per_run": config["max_llm_calls_per_run"],
        "min_confidence": config["min_confidence"]
    }

@app.get("/events/scan")
async def scan_events(
    query: Optional[str] = None,
    max_results: int = 10,
    category: Optional[str] = None,
    cuisine: Optional[str] = None
):
    """
    Scan Gmail for events and return parsed results with filtering.
    
    Args:
        query: Gmail search query (uses config default if not provided)
        max_results: Maximum number of emails to process
        category: Filter by event category
        cuisine: Filter by food cuisine
        
    Returns:
        List of parsed events
    """
    gmail, llm, post, store, config = get_components()
    
    if not gmail or not llm or not post:
        raise HTTPException(
            status_code=500, 
            detail="Required components not available. Check configuration."
        )
    
    # Use default query if not provided
    if not query:
        query = config["gmail_query"]
    
    try:
        # Fetch emails
        emails = gmail.get_emails_for_parsing(query, max_results)
        
        if not emails:
            return {"events": [], "message": "No emails found matching the query"}
        
        # Parse emails
        parsed_events = llm.parse_emails_batch(emails)
        
        # Events are already parsed and validated, no need for post-processing
        processed_events = parsed_events
        
        # Apply filters
        filtered_events = []
        for event in processed_events:
            # Category filter
            if category and event.category != category:
                continue
            
            # Cuisine filter
            if cuisine:
                want_cuisine = norm_text(cuisine)
                event_cuisines = [norm_text(item.cuisine) for item in event.food if item.cuisine]
                if want_cuisine not in event_cuisines:
                    continue
            
            filtered_events.append(event)
        
        # Convert to dict for JSON response
        events_data = [event.model_dump() for event in filtered_events]
        
        return {
            "events": events_data,
            "count": len(events_data),
            "query": query,
            "filters": {
                "category": category,
                "cuisine": cuisine
            },
            "stats": llm.get_parsing_stats()
        }
        
    except Exception as e:
        logger.error(f"Error scanning events: {e}")
        raise HTTPException(status_code=500, detail=f"Error scanning events: {str(e)}")

@app.get("/events/all")
async def scan_all_events(
    max_results: int = Query(50, ge=1, le=100, description="Maximum number of emails to process"),
    sort: str = Query("desc", description="Sort order - 'desc' for newest first, 'asc' for oldest first"),
    category: Optional[str] = Query(None, description="Filter by event category"),
    cuisine: Optional[str] = Query(None, description="Filter by food cuisine")
):
    """
    Scan Gmail for events from mailing lists only (GG.Events + other mailing lists).
    
    Args:
        max_results: Maximum number of emails to process
        sort: Sort order - "desc" for newest first, "asc" for oldest first
        category: Filter by event category
        cuisine: Filter by food cuisine
        
    Returns:
        List of parsed events from mailing lists only
    """
    gmail, llm, post, store, config = get_components()
    
    if not gmail or not llm or not post:
        raise HTTPException(
            status_code=500, 
            detail="Required components not available. Check configuration."
        )
    
    try:
        # Fetch emails from mailing lists only (GG.Events + other mailing lists)
        emails = gmail.get_mailing_list_emails(max_results)
        
        if not emails:
            return {"events": [], "message": "No mailing list emails found"}
        
        # Parse emails
        parsed_events = llm.parse_emails_batch(emails)
        
        # Events are already parsed and validated, no need for post-processing
        processed_events = parsed_events
        
        # Apply filters
        filtered_events = []
        for event in processed_events:
            # Category filter
            if category and event.category != category:
                continue
            
            # Cuisine filter
            if cuisine:
                want_cuisine = norm_text(cuisine)
                event_cuisines = [norm_text(item.cuisine) for item in event.food if item.cuisine]
                if want_cuisine not in event_cuisines:
                    continue
            
            # Add original email body for display
            event.original_email_body = next(
                (email['body'] for email in emails if email['message_id'] == event.source_message_id), 
                'Email content not available'
            )
            
            filtered_events.append(event)
        
        # Convert to dict for JSON response
        events_data = [event.model_dump() for event in filtered_events]
        
        # Sort events by date_start, then by time_start
        def sort_key(event):
            date = event.get('date_start') or ''  # Handle None values
            time = event.get('time_start') or '23:59'  # Handle None values, put null times at end
            return (date, time)
        
        if sort == "desc":
            events_data.sort(key=sort_key, reverse=True)
        else:
            events_data.sort(key=sort_key)
        
        return {
            "events": events_data,
            "count": len(events_data),
            "source": "Mailing Lists",
            "filters": {
                "category": category,
                "cuisine": cuisine
            },
            "stats": llm.get_parsing_stats()
        }
        
    except Exception as e:
        logger.error(f"Error scanning all events: {e}")
        raise HTTPException(status_code=500, detail=f"Error scanning all events: {str(e)}")

@app.get("/events/gg-events")
async def scan_gg_events(
    max_results: int = 50, 
    sort: str = "desc",
    category: Optional[str] = None,
    cuisine: Optional[str] = None
):
    """
    Scan GG.Events emails and return parsed results with filtering.
    
    Args:
        max_results: Maximum number of emails to process
        sort: Sort order - "desc" for newest first, "asc" for oldest first
        category: Filter by event category
        cuisine: Filter by food cuisine
        
    Returns:
        List of parsed events from GG.Events
    """
    gmail, llm, post, store, config = get_components()
    
    if not gmail or not llm or not post:
        raise HTTPException(
            status_code=500, 
            detail="Required components not available. Check configuration."
        )
    
    try:
        # Fetch GG.Events emails
        emails = gmail.get_gg_events_emails(max_results)
        
        if not emails:
            return {"events": [], "message": "No GG.Events emails found"}
        
        # Parse emails
        parsed_events = llm.parse_emails_batch(emails)
        
        # Events are already parsed and validated, no need for post-processing
        processed_events = parsed_events
        
        # Apply filters
        filtered_events = []
        for event in processed_events:
            # Category filter
            if category and event.category != category:
                continue
            
            # Cuisine filter
            if cuisine:
                want_cuisine = norm_text(cuisine)
                event_cuisines = [norm_text(item.cuisine) for item in event.food if item.cuisine]
                if want_cuisine not in event_cuisines:
                    continue
            
            # Add original email body for display
            event.original_email_body = next(
                (email['body'] for email in emails if email['message_id'] == event.source_message_id), 
                'Email content not available'
            )
            
            filtered_events.append(event)
        
        # Convert to dict for JSON response
        events_data = [event.model_dump() for event in filtered_events]
        
        # Sort events by date_start, then by time_start
        def sort_key(event):
            date = event.get('date_start') or ''  # Handle None values
            time = event.get('time_start') or '23:59'  # Handle None values, put null times at end
            return (date, time)
        
        if sort == "desc":
            events_data.sort(key=sort_key, reverse=True)
        else:
            events_data.sort(key=sort_key)
        
        return {
            "events": events_data,
            "count": len(events_data),
            "source": "GG.Events",
            "filters": {
                "category": category,
                "cuisine": cuisine
            },
            "stats": llm.get_parsing_stats()
        }
        
    except Exception as e:
        logger.error(f"Error scanning GG.Events: {e}")
        raise HTTPException(status_code=500, detail=f"Error scanning GG.Events: {str(e)}")

@app.post("/ics")
async def generate_ics(event_data: dict):
    """
    Generate ICS calendar file from event data.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        ICS file content
    """
    try:
        # Convert to ParsedEvent
        if "food" in event_data and isinstance(event_data["food"], list):
            # New format
            event = ParsedEvent(**event_data)
        else:
            # Legacy format
            event = ParsedEvent.from_legacy_format(event_data)
        
        # Generate ICS content
        ics_content = ICSGenerator.generate_ics([event])
        
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={"Content-Disposition": "attachment; filename=event.ics"}
        )
        
    except Exception as e:
        logger.error(f"Error generating ICS: {e}")
        raise HTTPException(status_code=400, detail=f"Error generating ICS: {str(e)}")

@app.get("/events/sample")
async def get_sample_events():
    """Get sample events for testing the UI."""
    sample_events = [
        {
            "title": "AI Workshop: Machine Learning Fundamentals",
            "description": "Learn the basics of machine learning with hands-on exercises and real-world examples.",
            "date_start": "2025-01-15",
            "time_start": "14:00",
            "time_end": "16:00",
            "location": "Science Center 101",
            "organizer": "Harvard AI Society",
            "category": "workshop",
            "food": [
                {
                    "name": "Pizza",
                    "quantity_hint": "dinner for first 30 attendees",
                    "cuisine": "Italian"
                },
                {
                    "name": "Coffee",
                    "quantity_hint": "unlimited",
                    "cuisine": "Other"
                }
            ],
            "confidence": {
                "category": 0.9,
                "cuisine": 0.8,
                "overall": 0.85
            },
            "urls": ["https://harvard.edu/ai-workshop"],
            "mailing_list": "GG.Events",
            "source_subject": "[GG.Events] AI Workshop: Machine Learning Fundamentals"
        },
        {
            "title": "Sushi Night Social",
            "description": "Join us for a fun evening of networking over delicious sushi and drinks.",
            "date_start": "2025-01-16",
            "time_start": "18:00",
            "time_end": "21:00",
            "location": "Student Center Dining Hall",
            "organizer": "International Students Association",
            "category": "social",
            "food": [
                {
                    "name": "Sushi Platter",
                    "quantity_hint": "dinner for ~50 people",
                    "cuisine": "Japanese"
                },
                {
                    "name": "Sake",
                    "quantity_hint": "wine and beer available",
                    "cuisine": "Japanese"
                }
            ],
            "confidence": {
                "category": 0.95,
                "cuisine": 0.9,
                "overall": 0.92
            },
            "urls": ["https://forms.gle/sushi-night"],
            "mailing_list": "GG.Events",
            "source_subject": "[GG.Events] Sushi Night Social - RSVP Required"
        },
        {
            "title": "Research Seminar: Climate Change Solutions",
            "description": "Dr. Smith presents latest research on renewable energy and climate adaptation strategies.",
            "date_start": "2025-01-17",
            "time_start": "15:30",
            "time_end": "17:00",
            "location": "Environmental Science Building, Room 200",
            "organizer": "Environmental Studies Department",
            "category": "seminar",
            "food": [
                {
                    "name": "Light Refreshments",
                    "quantity_hint": "coffee and pastries",
                    "cuisine": "Other"
                }
            ],
            "confidence": {
                "category": 0.85,
                "cuisine": 0.6,
                "overall": 0.75
            },
            "urls": ["https://harvard.edu/climate-seminar"],
            "mailing_list": "GG.Events",
            "source_subject": "[GG.Events] Climate Change Research Seminar"
        }
    ]
    
    return {
        "events": sample_events,
        "count": len(sample_events),
        "source": "Sample Data",
        "message": "These are sample events to demonstrate the enhanced UI features"
    }

@app.get("/debug/query")
async def debug_query():
    """Debug what emails are found by different queries."""
    try:
        gmail, llm, post, store, config = get_components()
        
        if not gmail:
            return {"error": "Gmail client not available"}
        
        # Test different queries
        queries = {
            "gg_events": "label:GG.Events newer_than:14d",
            "hcs_discuss": "list:hcs-discuss newer_than:14d", 
            "pfoho_open": "list:pfoho-open newer_than:14d",
            "event_keywords": "subject:event OR subject:meeting OR subject:workshop newer_than:14d",
            "broad_inbox": "in:inbox newer_than:7d"
        }
        
        results = {}
        for name, query in queries.items():
            try:
                emails = gmail.get_emails_for_parsing(query, 5)
                results[name] = {
                    "query": query,
                    "count": len(emails),
                    "emails": [{"subject": e.get("subject", ""), "sender": e.get("sender", ""), "mailing_list": e.get("mailing_list", "")} for e in emails[:3]]
                }
            except Exception as e:
                results[name] = {"query": query, "error": str(e)}
        
        return results
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/debug/gating")
async def debug_gating():
    """Debug gating logic on specific emails."""
    try:
        gmail, llm, post, store, config = get_components()
        
        if not gmail:
            return {"error": "Gmail client not available"}
        
        # Get a few emails from different sources
        emails = gmail.get_emails_for_parsing("in:inbox newer_than:7d", 5)
        
        results = []
        for email in emails:
            subject = email.get("subject", "")
            body = email.get("body", "")
            
            # Test gating logic
            is_event_like = llm._is_event_like(body, subject)
            
            # Test parsing
            parsed = llm.parse_email(body, email.get("message_id", ""), subject, email.get("date", ""))
            
            results.append({
                "subject": subject,
                "body_length": len(body),
                "body_preview": body[:100] + "..." if len(body) > 100 else body,
                "gating_passed": is_event_like,
                "parsing_successful": parsed is not None,
                "parsed_title": parsed.title if parsed else None
            })
        
        return {"emails_tested": len(results), "results": results}
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/debug/emails")
async def debug_emails():
    """Debug actual email content from GG.Events."""
    try:
        gmail, llm, post, store, config = get_components()
        
        if not gmail:
            return {"error": "Gmail client not available"}
        
        # Get GG.Events emails
        emails = gmail.get_gg_events_emails(max_results=3)
        
        if not emails:
            return {"error": "No GG.Events emails found"}
        
        # Parse first email
        first_email = emails[0]
        
        # Check gating logic
        is_likely_event = llm._is_event_like(first_email['body'], first_email['subject'])
        
        parsed = llm.parse_email(
            email_content=first_email['body'],
            message_id=first_email['message_id'],
            subject=first_email['subject'],
            received_at=first_email['date']
        )
        
        return {
            "total_emails_found": len(emails),
            "first_email": {
                "message_id": first_email['message_id'],
                "subject": first_email['subject'],
                "sender": first_email['sender'],
                "date": first_email['date'],
                "body_length": len(first_email['body']),
                "body_preview": first_email['body'][:200] + "..." if len(first_email['body']) > 200 else first_email['body']
            },
            "parsed_result": parsed.model_dump() if parsed else None,
            "parsing_successful": parsed is not None,
            "gating_passed": is_likely_event
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/debug/gmail")
async def debug_gmail():
    """Debug Gmail connection and available labels."""
    try:
        gmail, _, _, _, config = get_components()
        
        if not gmail:
            return {"error": "Gmail client not available"}
        
        # Test basic Gmail connection
        try:
            # Get user profile
            profile = gmail.service.users().getProfile(userId='me').execute()
            user_email = profile.get('emailAddress', 'Unknown')
        except Exception as e:
            return {"error": f"Gmail API connection failed: {str(e)}"}
        
        # Get available labels
        try:
            labels_result = gmail.service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])
            label_names = [label['name'] for label in labels]
        except Exception as e:
            return {"error": f"Failed to get labels: {str(e)}"}
        
        # Test GG.Events query
        try:
            gg_events_query = f"label:GG.Events newer_than:{config['event_window_days']}d"
            gg_events_result = gmail.service.users().messages().list(
                userId='me', q=gg_events_query, maxResults=5
            ).execute()
            gg_events_count = len(gg_events_result.get('messages', []))
        except Exception as e:
            gg_events_count = f"Error: {str(e)}"
        
        # Test broader query
        try:
            broad_query = "in:inbox newer_than:7d"
            broad_result = gmail.service.users().messages().list(
                userId='me', q=broad_query, maxResults=5
            ).execute()
            broad_count = len(broad_result.get('messages', []))
        except Exception as e:
            broad_count = f"Error: {str(e)}"
        
        return {
            "gmail_connected": True,
            "user_email": user_email,
            "total_labels": len(labels),
            "label_names": label_names[:20],  # First 20 labels
            "gg_events_label_exists": "GG.Events" in label_names,
            "gg_events_query_count": gg_events_count,
            "broad_query_count": broad_count,
            "event_window_days": config['event_window_days'],
            "gg_events_query": f"label:GG.Events newer_than:{config['event_window_days']}d"
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/stats")
async def get_system_stats():
    """Get system statistics and learning progress."""
    gmail, llm, post, store, config = get_components()
    
    if not all([gmail, llm, post, store]):
        raise HTTPException(status_code=500, detail="Components not available")
    
    try:
        gmail_stats = gmail.get_parsing_stats()
        llm_stats = llm.get_parsing_stats()
        learning_stats = post.get_learning_stats()
        
        return {
            "gmail": gmail_stats,
            "llm": llm_stats,
            "learning": learning_stats,
            "config": {
                "event_window_days": config["event_window_days"],
                "max_llm_calls_per_run": config["max_llm_calls_per_run"],
                "categories_count": len(config["categories"]),
                "cuisines_count": len(config["cuisines"])
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main HTML page with enhanced v2.0 functionality."""
    try:
        # Read the original UI file
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'views', 'index.html')
        with open(ui_path, 'r') as f:
            html_content = f.read()
        
        # Enhance the UI with v2.0 features
        enhanced_html = enhance_ui_with_v2_features(html_content)
        
        return HTMLResponse(content=enhanced_html)
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return HTMLResponse(content="<h1>Email Event Parser v2.0</h1><p>Error loading page.</p>")

def enhance_ui_with_v2_features(html_content):
    """Enhance the original UI with v2.0 features."""
    # Add category and cuisine filters
    enhanced_html = html_content.replace(
        '<div class="form-group">\n                    <label for="mailingListFilter">Filter by Mailing List:</label>\n                    <select id="mailingListFilter">\n                        <option value="">All Mailing Lists</option>\n                    </select>\n                </div>',
        '''<div class="form-group">
                    <label for="mailingListFilter">Filter by Mailing List:</label>
                    <select id="mailingListFilter">
                        <option value="">All Mailing Lists</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="categoryFilter">Filter by Category:</label>
                    <select id="categoryFilter">
                        <option value="">All Categories</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="cuisineFilter">Filter by Cuisine:</label>
                    <select id="cuisineFilter">
                        <option value="">All Cuisines</option>
                    </select>
                </div>'''
    )
    
    # Add confidence and learning indicators
    enhanced_html = enhanced_html.replace(
        '<div class="event-badges">',
        '''<div class="event-badges">
                        ${event.category ? `<span class="badge badge-category">📋 ${event.category}</span>` : ''}
                        ${event.confidence && event.confidence.overall ? `<span class="badge badge-confidence">🎯 ${Math.round(event.confidence.overall * 100)}%</span>` : ''}'''
    )
    
    # Add food breakdown display
    enhanced_html = enhanced_html.replace(
        'if (hasFood(event)) {\n                badges.push(\'<span class="badge badge-food">🍕 Food</span>\');\n            }',
        '''if (hasFood(event)) {
                badges.push('<span class="badge badge-food">🍕 Food</span>');
            }
            
            // Add food breakdown if available
            if (event.food && event.food.length > 0) {
                event.food.forEach(foodItem => {
                    if (foodItem.cuisine) {
                        badges.push(`<span class="badge badge-cuisine">🍽️ ${foodItem.cuisine}</span>`);
                    }
                });
            }'''
    )
    
    # Add CSS for new badges
    enhanced_html = enhanced_html.replace(
        '.badge-url {\n            background: #fef3c7;\n            color: #92400e;\n        }',
        '''.badge-url {
            background: #fef3c7;
            color: #92400e;
        }
        
        .badge-category {
            background: #e0e7ff;
            color: #3730a3;
        }
        
        .badge-cuisine {
            background: #fce7f3;
            color: #be185d;
        }
        
        .badge-confidence {
            background: #f0f9ff;
            color: #0369a1;
        }'''
    )
    
    # Add loading progress indicator
    enhanced_html = enhanced_html.replace(
        'loadBtn.textContent = \'⏳ Loading...\';',
        '''loadBtn.textContent = '⏳ Loading...';
            
            // Show progress indicator
            const progressDiv = document.createElement('div');
            progressDiv.id = 'progressIndicator';
            progressDiv.className = 'status loading';
            progressDiv.innerHTML = '🔄 Processing emails with AI... <div style="margin-top: 10px; background: #e5e7eb; border-radius: 4px; height: 4px; overflow: hidden;"><div style="background: #667eea; height: 100%; width: 0%; animation: progress 2s ease-in-out infinite;"></div></div>';
            document.getElementById('status').parentNode.insertBefore(progressDiv, document.getElementById('status').nextSibling);
            
            // Add progress animation CSS
            if (!document.getElementById('progressCSS')) {
                const style = document.createElement('style');
                style.id = 'progressCSS';
                style.textContent = '@keyframes progress { 0% { width: 0%; } 50% { width: 70%; } 100% { width: 100%; } }';
                document.head.appendChild(style);
            }'''
    )
    
    # Update the loadEvents function to use v2.0 endpoints
    enhanced_html = enhanced_html.replace(
        'const response = await fetch(`/events/all?max_results=${maxResults}&sort=desc`);',
        '''// Get filter values
                const categoryFilter = document.getElementById('categoryFilter').value;
                const cuisineFilter = document.getElementById('cuisineFilter').value;
                
                // Build query parameters
                const params = new URLSearchParams();
                params.append('max_results', maxResults);
                params.append('sort', 'desc');
                if (categoryFilter) params.append('category', categoryFilter);
                if (cuisineFilter) params.append('cuisine', cuisineFilter);
                
                const response = await fetch(`/events/all?${params}`);'''
    )
    
    # Add function to load filter options
    enhanced_html = enhanced_html.replace(
        'document.addEventListener(\'DOMContentLoaded\', function() {\n            loadEvents();\n            setupEventListeners();\n        });',
        '''document.addEventListener('DOMContentLoaded', function() {
            loadFilterOptions();
            loadEvents();
            setupEventListeners();
        });'''
    )
    
    # Add loadFilterOptions function
    enhanced_html = enhanced_html.replace(
        'function setupEventListeners() {',
        '''async function loadFilterOptions() {
            try {
                const response = await fetch('/config');
                const config = await response.json();
                
                // Load categories
                const categoryFilter = document.getElementById('categoryFilter');
                config.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                    categoryFilter.appendChild(option);
                });
                
                // Load cuisines
                const cuisineFilter = document.getElementById('cuisineFilter');
                config.cuisines.forEach(cuisine => {
                    const option = document.createElement('option');
                    option.value = cuisine;
                    option.textContent = cuisine;
                    cuisineFilter.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading filter options:', error);
            }
        }
        
        function setupEventListeners() {'''
    )
    
    # Update event listeners to include new filters
    enhanced_html = enhanced_html.replace(
        'document.getElementById(\'dateFilter\').addEventListener(\'change\', applyFilters);\n            document.getElementById(\'mailingListFilter\').addEventListener(\'change\', applyFilters);',
        '''document.getElementById('dateFilter').addEventListener('change', applyFilters);
            document.getElementById('mailingListFilter').addEventListener('change', applyFilters);
            document.getElementById('categoryFilter').addEventListener('change', applyFilters);
            document.getElementById('cuisineFilter').addEventListener('change', applyFilters);'''
    )
    
    # Update applyFilters to include new filters
    enhanced_html = enhanced_html.replace(
        'function applyFilters() {\n            const dateFilter = document.getElementById(\'dateFilter\').value;\n            const mailingListFilter = document.getElementById(\'mailingListFilter\').value;\n            \n            let filtered = allEvents;',
        '''function applyFilters() {
            const dateFilter = document.getElementById('dateFilter').value;
            const mailingListFilter = document.getElementById('mailingListFilter').value;
            const categoryFilter = document.getElementById('categoryFilter').value;
            const cuisineFilter = document.getElementById('cuisineFilter').value;
            
            let filtered = allEvents;'''
    )
    
    # Add new filter logic
    enhanced_html = enhanced_html.replace(
        '// Filter by food\n            if (foodFilterActive) {\n                filtered = filtered.filter(event => hasFood(event));\n            }',
        '''// Filter by category
            if (categoryFilter) {
                filtered = filtered.filter(event => event.category === categoryFilter);
            }
            
            // Filter by cuisine
            if (cuisineFilter) {
                filtered = filtered.filter(event => {
                    if (event.food && event.food.length > 0) {
                        return event.food.some(foodItem => foodItem.cuisine === cuisineFilter);
                    }
                    return false;
                });
            }
            
            // Filter by food
            if (foodFilterActive) {
                filtered = filtered.filter(event => hasFood(event));
            }'''
    )
    
    # Update hasFood function to work with new food structure
    enhanced_html = enhanced_html.replace(
        'function hasFood(event) {\n            // Check food_type and food_quantity_hint\n            if (event.food_type || event.food_quantity_hint) {\n                return true;\n            }\n            \n            // Check description for food keywords\n            const foodKeywords = /(pizza|snack|snacks|food|lunch|dinner|breakfast|refreshments|cater(ed|ing)|bagels?|coffee|tea|chai|cookies?)/i;\n            return foodKeywords.test(event.description || \'\');\n        }',
        '''function hasFood(event) {
            // Check new food structure
            if (event.food && event.food.length > 0) {
                return true;
            }
            
            // Check legacy food_type and food_quantity_hint
            if (event.food_type || event.food_quantity_hint) {
                return true;
            }
            
            // Check description for food keywords
            const foodKeywords = /(pizza|snack|snacks|food|lunch|dinner|breakfast|refreshments|cater(ed|ing)|bagels?|coffee|tea|chai|cookies?)/i;
            return foodKeywords.test(event.description || '');
        }'''
    )
    
    # Update clearFilters to include new filters
    enhanced_html = enhanced_html.replace(
        'function clearFilters() {\n            document.getElementById(\'dateFilter\').value = \'\';\n            document.getElementById(\'mailingListFilter\').value = \'\';\n            foodFilterActive = false;\n            document.getElementById(\'foodBtn\').classList.remove(\'active\');\n            document.getElementById(\'foodBtn\').textContent = \'🍕 Food Only\';',
        '''function clearFilters() {
            document.getElementById('dateFilter').value = '';
            document.getElementById('mailingListFilter').value = '';
            document.getElementById('categoryFilter').value = '';
            document.getElementById('cuisineFilter').value = '';
            foodFilterActive = false;
            document.getElementById('foodBtn').classList.remove('active');
            document.getElementById('foodBtn').textContent = '🍕 Food Only';'''
    )
    
    # Add food breakdown to event details
    enhanced_html = enhanced_html.replace(
        'if (event.mailing_list) {\n                details += `\n                    <div class="detail-item">\n                        <div class="detail-label">Mailing List:</div>\n                        <div class="detail-value">${event.mailing_list}</div>\n                    </div>\n                `;\n            }',
        '''if (event.food && event.food.length > 0) {
                details += `
                    <div class="detail-item">
                        <div class="detail-label">Food Details:</div>
                        <div class="detail-value">
                            ${event.food.map(foodItem => `
                                <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                                    <strong>${foodItem.name}</strong>
                                    ${foodItem.quantity_hint ? `<br><small>${foodItem.quantity_hint}</small>` : ''}
                                    ${foodItem.cuisine ? `<br><span class="badge badge-cuisine" style="margin-top: 4px; display: inline-block;">${foodItem.cuisine}</span>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (event.mailing_list) {
                details += `
                    <div class="detail-item">
                        <div class="detail-label">Mailing List:</div>
                        <div class="detail-value">${event.mailing_list}</div>
                    </div>
                `;
            }'''
    )
    
    # Add confidence display
    enhanced_html = enhanced_html.replace(
        'if (event.source_subject) {\n                details += `\n                    <div class="detail-item">\n                        <div class="detail-label">Original Subject:</div>\n                        <div class="detail-value">${event.source_subject}</div>\n                    </div>\n                `;\n            }',
        '''if (event.confidence) {
                const confDetails = [];
                if (event.confidence.category !== null) confDetails.push(`Category: ${Math.round(event.confidence.category * 100)}%`);
                if (event.confidence.cuisine !== null) confDetails.push(`Cuisine: ${Math.round(event.confidence.cuisine * 100)}%`);
                if (event.confidence.overall !== null) confDetails.push(`Overall: ${Math.round(event.confidence.overall * 100)}%`);
                
                if (confDetails.length > 0) {
                    details += `
                        <div class="detail-item">
                            <div class="detail-label">Confidence Scores:</div>
                            <div class="detail-value">${confDetails.join(' • ')}</div>
                        </div>
                    `;
                }
            }
            
            if (event.source_subject) {
                details += `
                    <div class="detail-item">
                        <div class="detail-label">Original Subject:</div>
                        <div class="detail-value">${event.source_subject}</div>
                    </div>
                `;
            }'''
    )
    
    # Clean up progress indicator
    enhanced_html = enhanced_html.replace(
        '} finally {\n                loadBtn.disabled = false;\n                loadBtn.textContent = \'🔄 Load Events\';\n            }',
        '''} finally {
                loadBtn.disabled = false;
                loadBtn.textContent = '🔄 Load Events';
                
                // Remove progress indicator
                const progressIndicator = document.getElementById('progressIndicator');
                if (progressIndicator) {
                    progressIndicator.remove();
                }
            }'''
    )
    
    return enhanced_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
