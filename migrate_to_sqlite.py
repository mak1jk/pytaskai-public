#!/usr/bin/env python3
"""
Script to migrate PyTaskAI from JSON to SQLite database
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main migration function"""
    try:
        from mcp_server.database import migrate_json_to_sqlite, get_db_manager
        
        project_root = "."
        
        print("🚀 PyTaskAI Migration: JSON to SQLite")
        print("=" * 50)
        
        # Check if database already exists
        db_manager = get_db_manager(project_root)
        existing_tasks = db_manager.get_all_tasks()
        
        if existing_tasks:
            print(f"⚠️  Database already exists with {len(existing_tasks)} tasks")
            response = input("Do you want to proceed anyway? This may duplicate tasks. (y/N): ")
            if response.lower() != 'y':
                print("❌ Migration cancelled")
                return
        
        print("\n📦 Starting migration...")
        
        # Perform migration
        success = migrate_json_to_sqlite(project_root)
        
        if success:
            print("✅ Migration completed successfully!")
            
            # Verify migration
            migrated_tasks = db_manager.get_all_tasks()
            print(f"📊 Total tasks in database: {len(migrated_tasks)}")
            
            # Show summary
            if migrated_tasks:
                print("\n📋 Task Summary:")
                for task in migrated_tasks[:5]:  # Show first 5 tasks
                    print(f"  - Task {task['id']}: {task['title']}")
                if len(migrated_tasks) > 5:
                    print(f"  ... and {len(migrated_tasks) - 5} more tasks")
            
        else:
            print("❌ Migration failed!")
            
    except Exception as e:
        print(f"💥 Migration error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()