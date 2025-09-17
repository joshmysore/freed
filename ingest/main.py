"""Main script for Gmail event ingestion."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from models import Config
from gmail_client import GmailClient
from llm_parser import LLMEventParser as EventParser
from db import Database


def load_config(config_path: str = "config.json") -> Config:
    """Load configuration from file."""
    if not Path(config_path).exists():
        if Path("config.example.json").exists():
            print(f"Config file not found. Please copy config.example.json to {config_path} and configure it.")
            sys.exit(1)
        else:
            print("No config file found. Using default configuration.")
            return Config()
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    return Config(**config_data)


def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(description="Ingest Harvard events from Gmail")
    parser.add_argument("--since", type=int, default=60, help="Days to look back (default: 60)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum messages to process (default: 100)")
    parser.add_argument("--label", type=str, help="Gmail label name (overrides config)")
    parser.add_argument("--save-body", action="store_true", help="Save full message body")
    parser.add_argument("--dump-json", type=str, help="Dump raw messages to JSONL file")
    parser.add_argument("--config", type=str, default="config.json", help="Config file path")
    parser.add_argument("--db", type=str, default="events.db", help="Database file path")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line args
    if args.label:
        config.label_name = args.label
    if args.save_body:
        config.save_body_text = True
    
    print(f"Starting Gmail ingestion...")
    print(f"Label: {config.label_name}")
    print(f"Query: {config.gmail_query}")
    print(f"Since: {args.since} days")
    print(f"Limit: {args.limit} messages")
    print(f"Database: {args.db}")
    
    try:
        # Initialize components
        gmail_client = GmailClient(config)
        parser = EventParser(config)
        db = Database(args.db)
        
        # Fetch messages
        print("\nFetching messages from Gmail...")
        messages = gmail_client.fetch_labeled_messages(since_days=args.since, limit=args.limit)
        
        if not messages:
            print("No messages found.")
            return
        
        print(f"Fetched {len(messages)} messages")
        
        # Dump raw messages if requested
        if args.dump_json:
            print(f"Dumping raw messages to {args.dump_json}")
            with open(args.dump_json, 'w') as f:
                for message in messages:
                    # Convert GmailMessage to dict
                    message_dict = {
                        'id': message.id,
                        'thread_id': message.thread_id,
                        'subject': message.subject,
                        'from_email': message.from_email,
                        'to_email': message.to_email,
                        'date': message.date,
                        'list_id': message.list_id,
                        'message_id': message.message_id,
                        'body_text': message.body_text,
                        'body_html': message.body_html
                    }
                    f.write(json.dumps(message_dict) + '\n')
        
        # Parse and store events
        print("\nParsing and storing events...")
        processed = 0
        errors = 0
        
        for i, message in enumerate(messages):
            try:
                print(f"Processing message {i+1}/{len(messages)}: {message.subject[:50]}...")
                
                # Parse event
                event = parser.parse_message(message)
                
                # Store in database
                db.upsert_event(event)
                processed += 1
                
                print(f"  ✓ Parsed: {event.title[:50]}...")
                print(f"    List: {event.source_list_tag}")
                print(f"    Type: {event.etype}")
                print(f"    Start: {event.start}")
                print(f"    Location: {event.location}")
                print(f"    Food: {bool(event.food)}, Free: {bool(event.free)}")
                print(f"    Confidence: {event.confidence}/3")
                
            except Exception as e:
                print(f"  ✗ Error processing message: {e}")
                errors += 1
                continue
        
        print(f"\nIngestion complete!")
        print(f"Processed: {processed}")
        print(f"Errors: {errors}")
        
        # Show database stats
        stats = db.get_stats()
        print(f"\nDatabase stats:")
        print(f"Total events: {stats['total_events']}")
        print(f"Events with food: {stats['events_with_food']}")
        print(f"Free events: {stats['free_events']}")
        print(f"Events by type: {stats['events_by_type']}")
        print(f"Events by list: {stats['events_by_list']}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
