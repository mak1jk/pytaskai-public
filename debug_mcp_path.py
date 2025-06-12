#!/usr/bin/env python3
"""
Add debugging to MCP tools to understand what's happening in external calls
"""

import os
import sys

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

# Patch the _list_tasks_internal function to add debugging
def patch_mcp_tools():
    from mcp_server import task_manager
    
    # Save original function
    original_list_tasks = task_manager._list_tasks_internal
    
    def debug_list_tasks_internal(*args, **kwargs):
        print(f"DEBUG: _list_tasks_internal called with args={args}, kwargs={kwargs}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: sys.path[0]: {sys.path[0]}")
        print(f"DEBUG: __file__: {__file__}")
        
        try:
            result = original_list_tasks(*args, **kwargs)
            print(f"DEBUG: _list_tasks_internal returned {len(result.get('tasks', []))} tasks")
            print(f"DEBUG: Result keys: {list(result.keys())}")
            if 'error' in result:
                print(f"DEBUG: Error in result: {result['error']}")
            if 'message' in result:
                print(f"DEBUG: Message in result: {result['message']}")
            return result
        except Exception as e:
            print(f"DEBUG: Exception in _list_tasks_internal: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # Replace the function
    task_manager._list_tasks_internal = debug_list_tasks_internal
    
    # Also patch the database manager
    from mcp_server import database
    
    original_get_db_manager = database.get_db_manager
    
    def debug_get_db_manager(*args, **kwargs):
        print(f"DEBUG: get_db_manager called with args={args}, kwargs={kwargs}")
        try:
            result = original_get_db_manager(*args, **kwargs)
            print(f"DEBUG: Database path: {result.db_path}")
            print(f"DEBUG: Database exists: {result.db_path.exists()}")
            return result
        except Exception as e:
            print(f"DEBUG: Exception in get_db_manager: {e}")
            raise
    
    database.get_db_manager = debug_get_db_manager

if __name__ == "__main__":
    patch_mcp_tools()
    
    # Now test both internal and external calls
    print("=== Testing after patching ===")
    
    # Test internal call
    from mcp_server.task_manager import _list_tasks_internal
    result = _list_tasks_internal(
        project_root=project_root,
        include_subtasks=True,
        include_stats=False
    )
    print(f"Internal call: {len(result.get('tasks', []))} tasks")