#!/usr/bin/env python3
"""
Test calling MCP tool exactly as the external interface does
"""

import sys
import os

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

def test_external_import():
    """Test how the external MCP interface imports and calls tools"""
    print("=== Testing External MCP Import Pattern ===")
    
    try:
        # This is how external tools like Claude Code would import
        from mcp_server.task_manager import (
            list_tasks_tool,
            get_task_tool,
            add_task_tool
        )
        
        print("✅ Successfully imported MCP tools")
        print(f"list_tasks_tool type: {type(list_tasks_tool)}")
        
        # Test calling the tool
        result = list_tasks_tool(
            project_root=project_root,
            include_subtasks=True,
            include_stats=False
        )
        
        print(f"✅ Tool call successful!")
        print(f"Result type: {type(result)}")
        print(f"Tasks found: {len(result.get('tasks', []))}")
        print(f"Message: {result.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in external import: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_pytaskai_tools():
    """Test the pytaskai MCP tools pattern"""
    print("\n=== Testing PyTaskAI MCP Tools Pattern ===")
    
    try:
        # This pattern matches what we see in MCP tool registrations
        import mcp_server.task_manager
        
        # Check if the module has the tools
        print(f"Module attributes: {[attr for attr in dir(mcp_server.task_manager) if 'tool' in attr.lower()]}")
        
        # Get the MCP instance
        mcp_instance = mcp_server.task_manager.mcp
        print(f"MCP instance: {mcp_instance}")
        print(f"MCP type: {type(mcp_instance)}")
        
        # Check tools registration
        if hasattr(mcp_instance, '_tools'):
            tools = mcp_instance._tools
            print(f"Registered tools: {list(tools.keys())}")
        elif hasattr(mcp_instance, 'tools'):
            tools = mcp_instance.tools
            print(f"Tools via .tools: {list(tools.keys()) if hasattr(tools, 'keys') else len(tools)}")
        else:
            print("No tools found in MCP instance")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in pytaskai MCP tools: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_claude_code_call():
    """Simulate exactly how Claude Code would call the MCP tool"""
    print("\n=== Simulating Claude Code MCP Call ===")
    
    try:
        # Import as Claude Code would
        sys.path.append(project_root)
        
        # This is likely how the MCP interface imports
        import importlib
        module = importlib.import_module('mcp_server.task_manager')
        
        # Get the list_tasks_tool
        list_tasks_tool = getattr(module, 'list_tasks_tool')
        print(f"Tool found: {list_tasks_tool}")
        print(f"Tool type: {type(list_tasks_tool)}")
        
        # Call it with the same parameters as our previous successful test
        result = list_tasks_tool(
            project_root=project_root,
            status_filter=None,
            priority_filter=None, 
            type_filter=None,
            include_subtasks=True,
            include_stats=False
        )
        
        print(f"✅ Claude Code simulation successful!")
        print(f"Tasks: {len(result.get('tasks', []))}")
        print(f"Total count: {result.get('total_count', 0)}")
        print(f"Message: {result.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in Claude Code simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing external MCP call patterns...\n")
    
    results = {
        'external_import': test_external_import(),
        'pytaskai_tools': test_mcp_pytaskai_tools(), 
        'claude_code_sim': simulate_claude_code_call()
    }
    
    print("\n" + "="*50)
    print("EXTERNAL MCP CALL TEST SUMMARY")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    if all(results.values()):
        print("\n🎉 All external MCP call patterns work!")
        print("The issue must be in the Claude Code integration setup.")
    else:
        print("\n⚠️  Some external MCP call patterns failed.")
        print("This indicates an issue with the MCP tool registration or import.")