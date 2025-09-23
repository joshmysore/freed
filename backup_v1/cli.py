#!/usr/bin/env python3
"""
CLI interface for email event parser.
"""
import os
import sys
import argparse
import json
from typing import List, Optional
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gmail_client import GmailClient
from parser_llm import LLMParser
from postprocess import PostProcessor
from calendar_ics import ICSGenerator
from utils import setup_logging, format_event_summary
from schema import ParsedEvent


def load_environment():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print("Warning: .env file not found. Using system environment variables.")


def scan_emails(query: str, max_results: int = 10, output_ics: bool = False) -> List[ParsedEvent]:
    """
    Scan emails and parse events.
    
    Args:
        query: Gmail search query
        max_results: Maximum number of emails to process
        output_ics: Whether to generate ICS files
        
    Returns:
        List of parsed events
    """
    try:
        # Initialize components
        gmail_client = GmailClient()
        llm_parser = LLMParser()
        
        print(f"Searching Gmail with query: {query}")
        print(f"Max results: {max_results}")
        print()
        
        # Fetch emails
        emails = gmail_client.get_emails_for_parsing(query, max_results)
        print(f"Found {len(emails)} emails to process")
        
        if not emails:
            print("No emails found matching the query.")
            return []
        
        # Parse emails
        print("Parsing emails with LLM...")
        parsed_events = llm_parser.parse_emails_batch(emails)
        print(f"Successfully parsed {len(parsed_events)} events")
        
        # Post-process events
        print("Applying post-processing heuristics...")
        processed_events = []
        for event in parsed_events:
            processed_event = PostProcessor.process_event(event)
            processed_events.append(processed_event)
        
        # Generate ICS files if requested
        if output_ics and processed_events:
            print("Generating ICS files...")
            for i, event in enumerate(processed_events):
                ics_content = ICSGenerator.generate_ics([event])
                filename = f"event_{i+1}_{event.title.replace(' ', '_')}.ics"
                with open(filename, 'w') as f:
                    f.write(ics_content)
                print(f"Generated: {filename}")
        
        return processed_events
        
    except Exception as e:
        print(f"Error during email scanning: {e}")
        return []


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Email Event Parser CLI")
    parser.add_argument(
        "--query", 
        default=os.getenv('GMAIL_QUERY', 'newer_than:14d (subject:invite OR subject:event OR subject:seminar OR subject:talk OR subject:workshop OR subject:session)'),
        help="Gmail search query"
    )
    parser.add_argument(
        "--max-results", 
        type=int, 
        default=10,
        help="Maximum number of emails to process"
    )
    parser.add_argument(
        "--ics", 
        action="store_true",
        help="Generate ICS calendar files"
    )
    parser.add_argument(
        "--json", 
        action="store_true",
        help="Output raw JSON instead of formatted text"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load environment
    load_environment()
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        sys.exit(1)
    
    # Scan emails
    events = scan_emails(args.query, args.max_results, args.ics)
    
    if not events:
        print("No events found.")
        sys.exit(0)
    
    # Output results
    if args.json:
        # Output as JSON
        events_data = [event.model_dump() for event in events]
        print(json.dumps(events_data, indent=2, default=str))
    else:
        # Output formatted summary
        events_data = [event.model_dump() for event in events]
        print(format_event_summary(events_data))


if __name__ == "__main__":
    main()
