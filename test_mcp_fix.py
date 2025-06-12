#!/usr/bin/env python3
"""
Test the fix for MCP tool calling
"""

import sys
import os

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

def test_correct_mcp_calling():
    """Test calling MCP tools the correct way"""
    print("=== Testing Correct MCP Tool Calling ===")
    
    try:
        from mcp_server.task_manager import list_tasks_tool
        
        print(f"Tool type: {type(list_tasks_tool)}")
        print(f"Tool has .fn attribute: {hasattr(list_tasks_tool, 'fn')}")
        
        # Call the tool correctly using .fn
        result = list_tasks_tool.fn(
            project_root=project_root,
            include_subtasks=True,
            include_stats=False
        )
        
        print(f"✅ Correct MCP call successful!")
        print(f"Tasks found: {len(result.get('tasks', []))}")
        print(f"Total count: {result.get('total_count', 0)}")
        print(f"Message: {result.get('message', 'No message')}")
        
        # Show a few task titles
        tasks = result.get('tasks', [])
        if tasks:
            print(f"\nFirst 3 tasks:")
            for i, task in enumerate(tasks[:3]):
                print(f"  {i+1}. [{task['id']}] {task['title']} (Priority: {task['priority']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in correct MCP calling: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_tool_run_method():
    """Test if the tool has a run method"""
    print("\n=== Testing MCP Tool .run() Method ===")
    
    try:
        from mcp_server.task_manager import list_tasks_tool
        
        print(f"Tool has .run attribute: {hasattr(list_tasks_tool, 'run')}")
        
        if hasattr(list_tasks_tool, 'run'):
            # Try the run method
            result = list_tasks_tool.run(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
            
            print(f"✅ MCP .run() call successful!")
            print(f"Tasks found: {len(result.get('tasks', []))}")
            return True
        else:
            print("No .run() method available")
            return False
        
    except Exception as e:
        print(f"❌ Error in MCP .run() calling: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing MCP tool calling fixes...\n")
    
    results = {
        'fn_method': test_correct_mcp_calling(),
        'run_method': test_mcp_tool_run_method()
    }
    
    print("\n" + "="*50)
    print("MCP TOOL CALLING FIX TEST SUMMARY")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    if any(results.values()):
        print("\n🎉 Found working method for calling MCP tools!")
        print("The issue is that external callers need to use .fn or .run method")
    else:
        print("\n⚠️  Neither .fn nor .run methods worked.")
        print("Need to investigate further.")