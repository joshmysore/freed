"""
Migration script for Email Event Parser v2.0.

This script helps migrate from the old hard-coded system to the new
configurable system with learning and confidence scoring.
"""
import os
import sys
import json
import shutil
from pathlib import Path

def migrate_from_old_system():
    """Migrate from the old src/ structure to the new app/ structure."""
    print("🔄 Migrating Email Event Parser to v2.0...")
    
    # Check if old system exists
    old_src = Path("../src")
    if not old_src.exists():
        print("❌ Old src/ directory not found. Nothing to migrate.")
        return
    
    # Create backup
    backup_dir = Path("../backup_v1")
    if not backup_dir.exists():
        print("📦 Creating backup of old system...")
        shutil.copytree(old_src, backup_dir)
        print(f"✅ Backup created at {backup_dir}")
    
    # Copy credentials and token files
    print("🔑 Copying credentials and tokens...")
    for file in ["credentials.json", "token.json", ".env"]:
        old_file = Path(f"../{file}")
        if old_file.exists():
            shutil.copy2(old_file, ".")
            print(f"✅ Copied {file}")
    
    # Create custom config if needed
    custom_config = Path("custom_config.json")
    if not custom_config.exists():
        print("⚙️ Creating custom configuration...")
        config_data = {
            "categories": [
                "workshop", "lecture", "meeting", "concert", "social",
                "seminar", "talk", "presentation", "conference", "gathering"
            ],
            "cuisines": [
                "American", "Chinese", "Indian", "Italian", "Japanese",
                "Korean", "Mexican", "Thai", "Taiwanese", "Mediterranean"
            ],
            "event_window_days": 14,
            "max_llm_calls_per_run": 10,
            "min_confidence": {
                "category": 0.6,
                "cuisine": 0.6
            }
        }
        
        with open(custom_config, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print("✅ Created custom_config.json")
    
    print("🎉 Migration completed!")
    print("\nNext steps:")
    print("1. Review custom_config.json and adjust settings as needed")
    print("2. Run: python -m uvicorn app.server:app --host 0.0.0.0 --port 8080 --reload")
    print("3. Visit http://localhost:8080 to test the new system")
    print("4. The old system is backed up in backup_v1/")

def create_sample_config():
    """Create a sample configuration file."""
    config_data = {
        "categories": [
            "workshop", "lecture", "meeting", "concert", "social",
            "seminar", "talk", "presentation", "conference", "gathering",
            "session", "party", "celebration", "dinner", "lunch",
            "breakfast", "reception", "ceremony", "festival", "fair"
        ],
        "cuisines": [
            "American", "Chinese", "Indian", "Italian", "Japanese",
            "Korean", "Mexican", "Thai", "Taiwanese", "Mediterranean",
            "Middle Eastern", "African", "Latin American", "European", "Other"
        ],
        "event_window_days": 14,
        "max_llm_calls_per_run": 10,
        "min_confidence": {
            "category": 0.6,
            "cuisine": 0.6
        },
        "gmail_query_patterns": [
            "subject:invite", "subject:event", "subject:seminar",
            "subject:talk", "subject:workshop", "subject:session"
        ]
    }
    
    with open("custom_config.json", 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print("✅ Created sample custom_config.json")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        create_sample_config()
    else:
        migrate_from_old_system()

