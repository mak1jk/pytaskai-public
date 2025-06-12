#!/usr/bin/env python3
"""
Test script to check working directory context between MCP server and direct calls
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

async def test_mcp_context():
    """Test MCP context vs direct context"""
    
    print("=== TESTING WORKING DIRECTORY CONTEXT ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"sys.path[0]: {sys.path[0]}")
    
    # Test 1: Direct call with absolute path
    print("\n=== TEST 1: Direct call with absolute path ===")
    from mcp_server.task_manager import _list_tasks_internal
    
    result1 = _list_tasks_internal(
        project_root=project_root,
        include_subtasks=True,
        include_stats=False
    )
    print(f"Direct call with absolute path: {len(result1.get('tasks', []))} tasks")
    
    # Test 2: Direct call with relative path
    print("\n=== TEST 2: Direct call with relative path ===")
    old_cwd = os.getcwd()
    os.chdir(project_root)
    
    result2 = _list_tasks_internal(
        project_root=".",
        include_subtasks=True,
        include_stats=False
    )
    print(f"Direct call with relative path: {len(result2.get('tasks', []))} tasks")
    print(f"Current directory during call: {os.getcwd()}")
    
    os.chdir(old_cwd)
    
    # Test 3: Check database path resolution
    print("\n=== TEST 3: Database path resolution ===")
    from mcp_server.database import get_db_manager
    
    db_manager1 = get_db_manager(project_root)
    print(f"DB path (absolute): {db_manager1.db_path}")
    print(f"DB exists: {db_manager1.db_path.exists()}")
    
    os.chdir(project_root)
    db_manager2 = get_db_manager(".")
    print(f"DB path (relative): {db_manager2.db_path}")
    print(f"DB exists: {db_manager2.db_path.exists()}")
    print(f"Paths equal: {db_manager1.db_path == db_manager2.db_path}")
    
    os.chdir(old_cwd)
    
    # Test 4: Test via MCP tool interface
    print("\n=== TEST 4: MCP tool interface ===")
    from mcp_server.task_manager import mcp
    
    tools = await mcp.get_tools()
    list_tool = tools['list_tasks_tool']
    
    # Call with absolute path
    result4a = list_tool.fn(
        project_root=project_root,
        include_subtasks=True,
        include_stats=False
    )
    print(f"MCP tool with absolute path: {len(result4a.get('tasks', []))} tasks")
    
    # Call with relative path from project root
    os.chdir(project_root)
    result4b = list_tool.fn(
        project_root=".",
        include_subtasks=True,
        include_stats=False
    )
    print(f"MCP tool with relative path: {len(result4b.get('tasks', []))} tasks")
    print(f"Current directory during MCP call: {os.getcwd()}")
    
    os.chdir(old_cwd)
    
    # Test 5: Test with various relative paths
    print("\n=== TEST 5: Various path formats ===")
    test_paths = [
        project_root,  # Absolute path
        ".",  # Current directory (when in project root)
        os.path.basename(project_root),  # Just folder name
        f"../{os.path.basename(project_root)}"  # Parent/folder
    ]
    
    for test_path in test_paths:
        try:
            # Change to appropriate directory
            if test_path == ".":
                os.chdir(project_root)
            elif test_path == os.path.basename(project_root):
                parent_dir = os.path.dirname(project_root)
                os.chdir(parent_dir)
            elif test_path.startswith("../"):
                parent_dir = os.path.dirname(project_root)
                os.chdir(parent_dir)
            
            result = _list_tasks_internal(
                project_root=test_path,
                include_subtasks=True,
                include_stats=False
            )
            print(f"Path '{test_path}': {len(result.get('tasks', []))} tasks (cwd: {os.getcwd()})")
            
        except Exception as e:
            print(f"Path '{test_path}': ERROR - {e}")
        finally:
            os.chdir(old_cwd)

if __name__ == "__main__":
    asyncio.run(test_mcp_context())