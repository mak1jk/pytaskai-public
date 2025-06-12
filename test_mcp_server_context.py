#!/usr/bin/env python3
"""
Test script to simulate MCP server running from different working directories
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

async def test_mcp_server_from_different_dirs():
    """Test MCP server calls from various working directories"""
    
    print("=== TESTING MCP SERVER FROM DIFFERENT WORKING DIRECTORIES ===")
    
    original_cwd = os.getcwd()
    
    test_directories = [
        project_root,  # Same as project root
        "/Users/marcomacri",  # Parent directory
        "/Users/marcomacri/Desktop",  # Another parent
        "/tmp",  # Completely different location
        "/",  # Root directory
    ]
    
    for test_dir in test_directories:
        print(f"\n=== Testing from working directory: {test_dir} ===")
        
        try:
            # Change to test directory
            os.chdir(test_dir)
            print(f"Current working directory: {os.getcwd()}")
            
            # Import and get MCP tools (fresh import)
            if 'mcp_server.task_manager' in sys.modules:
                del sys.modules['mcp_server.task_manager']
            if 'mcp_server.database' in sys.modules:
                del sys.modules['mcp_server.database']
            
            from mcp_server.task_manager import mcp, _list_tasks_internal
            
            # Test 1: Direct internal function call
            result_internal = _list_tasks_internal(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
            tasks_internal = len(result_internal.get('tasks', []))
            
            # Test 2: MCP tool call
            tools = await mcp.get_tools()
            list_tool = tools['list_tasks_tool']
            
            result_mcp = list_tool.fn(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
            tasks_mcp = len(result_mcp.get('tasks', []))
            
            print(f"  Internal function: {tasks_internal} tasks")
            print(f"  MCP tool:          {tasks_mcp} tasks")
            
            if tasks_internal != tasks_mcp:
                print(f"  ⚠️  MISMATCH: Internal ({tasks_internal}) != MCP ({tasks_mcp})")
                
                # Additional debugging
                print(f"  Internal result keys: {list(result_internal.keys())}")
                print(f"  MCP result keys: {list(result_mcp.keys())}")
                
                if 'error' in result_internal:
                    print(f"  Internal error: {result_internal['error']}")
                if 'error' in result_mcp:
                    print(f"  MCP error: {result_mcp['error']}")
                if 'message' in result_internal:
                    print(f"  Internal message: {result_internal['message']}")
                if 'message' in result_mcp:
                    print(f"  MCP message: {result_mcp['message']}")
            else:
                print("  ✅ Results match")
                
        except Exception as e:
            print(f"  ❌ Error from {test_dir}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Always restore original directory
            os.chdir(original_cwd)

    print(f"\n=== Test complete, restored to: {os.getcwd()} ===")

if __name__ == "__main__":
    asyncio.run(test_mcp_server_from_different_dirs())