"""
FastAPI application for email event parser.
"""
import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gmail_client import GmailClient
from parser_llm import LLMParser
from postprocess import PostProcessor
from calendar_ics import ICSGenerator
from schema import ParsedEvent
from utils import setup_logging

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Email Event Parser",
    description="Parse events from Gmail emails using LLM",
    version="1.0.0"
)

# Initialize components
gmail_client = None
llm_parser = None

def get_components():
    """Get or initialize Gmail client and LLM parser."""
    global gmail_client, llm_parser
    
    if gmail_client is None:
        try:
            gmail_client = GmailClient()
        except Exception as e:
            logging.error(f"Failed to initialize Gmail client: {e}")
            gmail_client = None
    
    if llm_parser is None:
        try:
            llm_parser = LLMParser()
        except Exception as e:
            logging.error(f"Failed to initialize LLM parser: {e}")
            llm_parser = None
    
    return gmail_client, llm_parser


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Email Event Parser is running"}


@app.get("/events/scan")
async def scan_events(
    query: Optional[str] = None,
    max_results: int = 10
):
    """
    Scan Gmail for events and return parsed results.
    
    Args:
        query: Gmail search query (uses default if not provided)
        max_results: Maximum number of emails to process
        
    Returns:
        List of parsed events
    """
    gmail, llm = get_components()
    
    if not gmail or not llm:
        raise HTTPException(
            status_code=500, 
            detail="Gmail client or LLM parser not available. Check configuration."
        )
    
    # Use default query if not provided
    if not query:
        query = os.getenv('GMAIL_QUERY', 'newer_than:14d (subject:invite OR subject:event OR subject:seminar OR subject:talk OR subject:workshop OR subject:session)')
    
    try:
        # Fetch emails
        emails = gmail.get_emails_for_parsing(query, max_results)
        
        if not emails:
            return {"events": [], "message": "No emails found matching the query"}
        
        # Parse emails
        parsed_events = llm.parse_emails_batch(emails)
        
        # Post-process events
        processed_events = []
        for event in parsed_events:
            processed_event = PostProcessor.process_event(event)
            processed_events.append(processed_event)
        
        # Convert to dict for JSON response
        events_data = [event.model_dump() for event in processed_events]
        
        return {
            "events": events_data,
            "count": len(events_data),
            "query": query
        }
        
    except Exception as e:
        logging.error(f"Error scanning events: {e}")
        raise HTTPException(status_code=500, detail=f"Error scanning events: {str(e)}")


@app.get("/events/gg-events")
async def scan_gg_events(max_results: int = 50, sort: str = "desc"):
    """
    Scan GG.Events emails and return parsed results.
    
    Args:
        max_results: Maximum number of emails to process (default 50)
        sort: Sort order - "desc" for newest first, "asc" for oldest first
        
    Returns:
        List of parsed events from GG.Events
    """
    gmail, llm = get_components()
    
    if not gmail or not llm:
        raise HTTPException(
            status_code=500, 
            detail="Gmail client or LLM parser not available. Check configuration."
        )
    
    try:
        # Fetch GG.Events emails
        emails = gmail.get_gg_events_emails(max_results)
        
        if not emails:
            return {"events": [], "message": "No GG.Events emails found"}
        
        # Parse emails
        parsed_events = llm.parse_emails_batch(emails)
        
        # Post-process events
        processed_events = []
        for event in parsed_events:
            processed_event = PostProcessor.process_event(event)
            # Add original email body for display
            processed_event.original_email_body = next(
                (email['body'] for email in emails if email['message_id'] == event.source_message_id), 
                'Email content not available'
            )
            processed_events.append(processed_event)
        
        # Convert to dict for JSON response
        events_data = [event.model_dump() for event in processed_events]
        
        # Sort events by date_start, then by time_start
        def sort_key(event):
            date = event.get('date_start', '')
            time = event.get('time_start', '')
            return (date, time or '23:59')  # Put null times at end
        
        if sort == "desc":
            events_data.sort(key=sort_key, reverse=True)
        else:
            events_data.sort(key=sort_key)
        
        return {
            "events": events_data,
            "count": len(events_data),
            "source": "GG.Events"
        }
        
    except Exception as e:
        logging.error(f"Error scanning GG.Events: {e}")
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
        # Validate event data
        event = ParsedEvent(**event_data)
        
        # Generate ICS content
        ics_content = ICSGenerator.generate_ics([event])
        
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={"Content-Disposition": "attachment; filename=event.ics"}
        )
        
    except Exception as e:
        logging.error(f"Error generating ICS: {e}")
        raise HTTPException(status_code=400, detail=f"Error generating ICS: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main HTML page."""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'views', 'index.html'), 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Email Event Parser</h1><p>HTML template not found.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
