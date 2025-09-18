#!/usr/bin/env python3
"""
Analyze GG.Events parsing to understand why some events aren't being parsed.
"""

import sys
import os
import json
sys.path.append('src')

from gmail_client import GmailClient
from parser_llm import LLMParser
from postprocess import PostProcessor
from utils import extract_mailing_list_from_subject
from schema import ParsedEvent

def analyze_parsing():
    """Analyze parsing issues in detail."""
    print("🔍 GG.Events Parsing Analysis")
    print("=" * 60)
    print()
    
    try:
        # Initialize components
        gmail = GmailClient()
        llm = LLMParser()
        
        # Fetch emails from last 14 days
        print("📧 Fetching GG.Events emails from last 14 days...")
        emails = gmail.get_gg_events_emails(max_results=50)
        print(f"✅ Found {len(emails)} emails")
        print()
        
        if not emails:
            print("❌ No emails found")
            return
        
        # Analyze each email
        print("📊 Email Analysis:")
        print("-" * 40)
        
        parsed_count = 0
        failed_count = 0
        non_event_count = 0
        
        for i, email in enumerate(emails, 1):
            subject = email['subject']
            mailing_list = extract_mailing_list_from_subject(subject)
            
            print(f"\n📧 Email {i}: {subject}")
            print(f"   Mailing List: {mailing_list}")
            print(f"   Sender: {email['sender']}")
            print(f"   Date: {email['date']}")
            
            # Try to parse this email
            try:
                parsed_event = llm.parse_email(
                    email_content=email['body'],
                    message_id=email['message_id'],
                    subject=subject
                )
                
                if parsed_event:
                    parsed_count += 1
                    print(f"   ✅ PARSED: {parsed_event.title}")
                    print(f"      Date: {parsed_event.date_start}")
                    print(f"      Location: {parsed_event.location}")
                    print(f"      Organizer: {parsed_event.organizer}")
                else:
                    failed_count += 1
                    print(f"   ❌ FAILED TO PARSE")
                    
                    # Analyze why it failed
                    print(f"   📝 Body preview: {email['body'][:200]}...")
                    
                    # Check if it looks like an event
                    event_keywords = ['event', 'meeting', 'workshop', 'seminar', 'talk', 'lecture', 'conference', 
                                    'gathering', 'session', 'presentation', 'party', 'celebration', 'dinner', 
                                    'lunch', 'breakfast', 'reception', 'ceremony', 'festival', 'fair', 'exhibition']
                    
                    body_lower = email['body'].lower()
                    has_event_keywords = any(keyword in body_lower for keyword in event_keywords)
                    
                    if has_event_keywords:
                        print(f"   ⚠️  Contains event keywords but failed to parse")
                        non_event_count += 1
                    else:
                        print(f"   ℹ️  No event keywords detected - likely not an event")
                        
            except Exception as e:
                failed_count += 1
                print(f"   ❌ ERROR: {str(e)}")
        
        # Summary
        print(f"\n📊 Parsing Summary:")
        print("-" * 40)
        print(f"Total emails: {len(emails)}")
        print(f"Successfully parsed: {parsed_count}")
        print(f"Failed to parse: {failed_count}")
        print(f"Non-event emails: {non_event_count}")
        print(f"Success rate: {parsed_count/len(emails)*100:.1f}%")
        
        # Detailed analysis of failed emails
        print(f"\n🔍 Detailed Analysis of Failed Emails:")
        print("-" * 40)
        
        for i, email in enumerate(emails, 1):
            subject = email['subject']
            
            try:
                parsed_event = llm.parse_email(
                    email_content=email['body'],
                    message_id=email['message_id'],
                    subject=subject
                )
                
                if not parsed_event:
                    print(f"\n❌ Failed Email {i}: {subject}")
                    print(f"   Body length: {len(email['body'])} characters")
                    
                    # Check for common issues
                    body = email['body']
                    
                    # Check if it's a forwarded email
                    if 'fwd:' in subject.lower() or 'forwarded' in body.lower():
                        print(f"   🔄 This is a forwarded email")
                    
                    # Check if it's a reply
                    if subject.lower().startswith('re:'):
                        print(f"   ↩️  This is a reply email")
                    
                    # Check for event indicators
                    event_indicators = ['when:', 'where:', 'time:', 'date:', 'location:', 'rsvp:', 'register:']
                    found_indicators = [ind for ind in event_indicators if ind in body.lower()]
                    if found_indicators:
                        print(f"   📅 Contains event indicators: {found_indicators}")
                    
                    # Check for time/date patterns
                    import re
                    time_patterns = [
                        r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)\b',
                        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
                        r'\b(mon|tue|wed|thu|fri|sat|sun)day\b',
                        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b'
                    ]
                    
                    found_patterns = []
                    for pattern in time_patterns:
                        if re.search(pattern, body, re.IGNORECASE):
                            found_patterns.append(pattern)
                    
                    if found_patterns:
                        print(f"   🕐 Contains time/date patterns: {len(found_patterns)} found")
                    
                    # Show a sample of the body
                    print(f"   📝 Body sample: {body[:300]}...")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing email {i}: {str(e)}")
        
        print(f"\n💡 Recommendations:")
        print("-" * 40)
        print("1. Check if failed emails are actually events or just announcements")
        print("2. Consider improving the LLM prompt for better event detection")
        print("3. Add more robust date/time parsing")
        print("4. Handle forwarded emails better")
        print("5. Consider filtering out replies and non-event content")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_parsing()
