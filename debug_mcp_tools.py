#!/usr/bin/env python3
"""
Debug script to identify the issue between MCP tools and database access
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

def test_direct_database_access():
    """Test direct database access"""
    print("=== TEST 1: Direct Database Access ===")
    
    from mcp_server.database import get_db_manager
    
    db_manager = get_db_manager(project_root)
    tasks = db_manager.get_all_tasks(include_subtasks=True)
    
    print(f"Database manager tasks: {len(tasks)}")
    if tasks:
        print(f"First task: {tasks[0]['id']} - {tasks[0]['title']}")
        print(f"Last task: {tasks[-1]['id']} - {tasks[-1]['title']}")
    return len(tasks)

def test_internal_mcp_function():
    """Test internal MCP function"""
    print("\n=== TEST 2: Internal MCP Function ===")
    
    from mcp_server.task_manager import _list_tasks_internal
    
    result = _list_tasks_internal(
        project_root=project_root,
        include_subtasks=True,
        include_stats=False
    )
    
    tasks = result.get("tasks", [])
    print(f"Internal MCP function tasks: {len(tasks)}")
    print(f"Message: {result.get('message', 'No message')}")
    if tasks:
        print(f"First task: {tasks[0]['id']} - {tasks[0]['title']}")
        print(f"Last task: {tasks[-1]['id']} - {tasks[-1]['title']}")
    return len(tasks)

async def test_mcp_tool_direct():
    """Test MCP tool directly"""
    print("\n=== TEST 3: MCP Tool Direct Call ===")
    
    try:
        from mcp_server.task_manager import list_tasks_tool
        
        # Check if it's wrapped
        print(f"Tool type: {type(list_tasks_tool)}")
        print(f"Tool attributes: {dir(list_tasks_tool)}")
        
        # Try to get the underlying function
        if hasattr(list_tasks_tool, 'func'):
            actual_function = list_tasks_tool.func
            print(f"Underlying function: {actual_function}")
        elif hasattr(list_tasks_tool, '__wrapped__'):
            actual_function = list_tasks_tool.__wrapped__
            print(f"Wrapped function: {actual_function}")
        else:
            actual_function = list_tasks_tool
            print(f"Direct function: {actual_function}")
        
        # Try calling it - check if it's a FunctionTool wrapper
        if hasattr(actual_function, 'fn'):
            print("Found FunctionTool wrapper, accessing .fn")
            actual_function = actual_function.fn
        
        # Try calling it
        if asyncio.iscoroutinefunction(actual_function):
            print("Function is async, calling with await...")
            result = await actual_function(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
        else:
            print("Function is sync, calling directly...")
            result = actual_function(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
        
        tasks = result.get("tasks", []) if isinstance(result, dict) else []
        print(f"MCP Tool tasks: {len(tasks)}")
        print(f"Full result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"Message: {result.get('message', 'No message') if isinstance(result, dict) else result}")
        
        return len(tasks) if isinstance(result, dict) else 0
        
    except Exception as e:
        print(f"Error calling MCP tool: {e}")
        import traceback
        traceback.print_exc()
        return 0

def test_utils_functions():
    """Test utility functions used by MCP"""
    print("\n=== TEST 4: Utility Functions ===")
    
    from mcp_server.utils import load_tasks, ensure_directories_exist
    
    # Test directory creation
    ensure_directories_exist(project_root)
    print("Directories ensured")
    
    # Test load_tasks function
    tasks_data = load_tasks(project_root)
    print(f"Utils load_tasks result: {type(tasks_data)}")
    if tasks_data:
        if isinstance(tasks_data, list):
            print(f"Tasks from utils (direct list): {len(tasks_data)}")
            return len(tasks_data)
        elif isinstance(tasks_data, dict):
            tasks = tasks_data.get("tasks", [])
            print(f"Tasks from utils (dict): {len(tasks)}")
            return len(tasks)
        else:
            print(f"Unexpected tasks_data type: {type(tasks_data)}")
            return 0
    else:
        print("No tasks data from utils")
        return 0

async def test_mcp_with_pytaskai_tool():
    """Test using the actual PyTaskAI MCP tool"""
    print("\n=== TEST 5: PyTaskAI MCP Tool ===")
    
    try:
        # Import the actual MCP tool as if we're calling it externally
        sys.path.append('/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public')
        
        from mcp_server.task_manager import mcp
        
        # Get the registered tools
        tools = mcp._tools if hasattr(mcp, '_tools') else {}
        print(f"Available MCP tools: {list(tools.keys())}")
        
        if 'list_tasks_tool' in tools:
            tool = tools['list_tasks_tool']
            print(f"Found list_tasks_tool: {type(tool)}")
            
            # Try to call it
            result = await tool.fn(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
            
            tasks = result.get("tasks", []) if isinstance(result, dict) else []
            print(f"PyTaskAI MCP Tool tasks: {len(tasks)}")
            print(f"Message: {result.get('message', 'No message') if isinstance(result, dict) else result}")
            
            return len(tasks)
        else:
            print("list_tasks_tool not found in MCP tools")
            return 0
            
    except Exception as e:
        print(f"Error with PyTaskAI MCP tool: {e}")
        import traceback
        traceback.print_exc()
        return 0

def check_database_file_details():
    """Check database file details"""
    print("\n=== TEST 6: Database File Analysis ===")
    
    db_path = os.path.join(project_root, '.pytaskai', 'tasks.db')
    
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        print(f"Database file size: {stat.st_size} bytes")
        print(f"Database file modified: {stat.st_mtime}")
        
        # Try to open with sqlite3 directly
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Database tables: {[t[0] for t in tables]}")
            
            # Count tasks
            cursor.execute("SELECT COUNT(*) FROM tasks;")
            count = cursor.fetchone()[0]
            print(f"Direct SQLite task count: {count}")
            
            # Get sample task
            cursor.execute("SELECT id, title, status FROM tasks LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                print(f"Sample task: ID={sample[0]}, Title={sample[1]}, Status={sample[2]}")
            
            conn.close()
            return count
        except Exception as e:
            print(f"SQLite direct access error: {e}")
            return 0
    else:
        print("Database file does not exist!")
        return 0

async def main():
    """Run all debug tests"""
    print("Starting systematic debug of MCP tools vs database disconnect\n")
    
    results = {}
    
    # Run all tests
    results['direct_db'] = test_direct_database_access()
    results['internal_mcp'] = test_internal_mcp_function()
    results['mcp_tool'] = await test_mcp_tool_direct()
    results['utils'] = test_utils_functions()
    results['pytaskai_mcp'] = await test_mcp_with_pytaskai_tool()
    results['sqlite_direct'] = check_database_file_details()
    
    # Summary
    print("\n" + "="*50)
    print("DEBUG SUMMARY")
    print("="*50)
    for test_name, task_count in results.items():
        status = "✅ PASS" if task_count > 0 else "❌ FAIL"
        print(f"{test_name:20} {task_count:3d} tasks {status}")
    
    # Analysis
    print("\nANALYSIS:")
    if results['direct_db'] > 0 and results['internal_mcp'] > 0:
        print("✅ Database and internal MCP function work correctly")
    
    if results['mcp_tool'] == 0:
        print("❌ MCP tool wrapper has issues")
    
    if results['pytaskai_mcp'] == 0:
        print("❌ PyTaskAI MCP integration has issues")
    
    if results['sqlite_direct'] != results['direct_db']:
        print("⚠️  SQLite count differs from ORM count")

if __name__ == "__main__":
    asyncio.run(main())