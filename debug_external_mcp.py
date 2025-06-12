#!/usr/bin/env python3
"""
Debug script to investigate the external MCP call path resolution issue
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = "/Users/marcomacri/Desktop/cartella progetti github/pytaskai-public"
sys.path.insert(0, project_root)

def debug_path_resolution():
    """Debug path resolution in different contexts"""
    
    print("=== DEBUGGING PATH RESOLUTION ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"__file__: {__file__}")
    print(f"sys.path[0]: {sys.path[0]}")
    
    # Test database path construction
    from mcp_server.database import DatabaseManager
    
    print("\n=== Database Path Construction ===")
    
    # Test 1: Absolute path
    db_manager_abs = DatabaseManager(project_root)
    print(f"Absolute path DB: {db_manager_abs.db_path}")
    print(f"Absolute path exists: {db_manager_abs.db_path.exists()}")
    
    # Test 2: Relative path  
    db_manager_rel = DatabaseManager(".")
    print(f"Relative path DB: {db_manager_rel.db_path}")
    print(f"Relative path exists: {db_manager_rel.db_path.exists()}")
    print(f"Relative path resolved: {db_manager_rel.db_path.resolve()}")
    
    # Test 3: Check if paths point to same file
    print(f"Paths are same file: {db_manager_abs.db_path.samefile(db_manager_rel.db_path.resolve()) if db_manager_rel.db_path.exists() else 'N/A'}")
    
    # Test utils path functions
    print("\n=== Utils Path Functions ===")
    from mcp_server.utils import get_data_directory, get_tasks_file_path
    
    data_dir_abs = get_data_directory(project_root)
    data_dir_rel = get_data_directory(".")
    
    print(f"Data dir (absolute): {data_dir_abs}")
    print(f"Data dir (relative): {data_dir_rel}")
    print(f"Data dir (relative resolved): {data_dir_rel.resolve()}")
    
    tasks_file_abs = get_tasks_file_path(project_root)
    tasks_file_rel = get_tasks_file_path(".")
    
    print(f"Tasks file (absolute): {tasks_file_abs}")
    print(f"Tasks file (relative): {tasks_file_rel}")
    print(f"Tasks file (absolute exists): {tasks_file_abs.exists()}")
    print(f"Tasks file (relative exists): {tasks_file_rel.exists()}")
    
    # Test load_tasks function
    print("\n=== Load Tasks Function ===")
    from mcp_server.utils import load_tasks
    
    try:
        tasks_abs = load_tasks(project_root)
        print(f"Load tasks (absolute): {len(tasks_abs)} tasks")
        if tasks_abs:
            print(f"First task type: {type(tasks_abs[0])}")
    except Exception as e:
        print(f"Load tasks (absolute) error: {e}")
    
    try:
        tasks_rel = load_tasks(".")
        print(f"Load tasks (relative): {len(tasks_rel)} tasks")
    except Exception as e:
        print(f"Load tasks (relative) error: {e}")
    
    # Test direct database manager
    print("\n=== Direct Database Manager ===")
    from mcp_server.database import get_db_manager
    
    try:
        db_mgr_abs = get_db_manager(project_root)
        tasks_db_abs = db_mgr_abs.get_all_tasks()
        print(f"DB manager (absolute): {len(tasks_db_abs)} tasks")
    except Exception as e:
        print(f"DB manager (absolute) error: {e}")
    
    try:
        db_mgr_rel = get_db_manager(".")
        tasks_db_rel = db_mgr_rel.get_all_tasks()
        print(f"DB manager (relative): {len(tasks_db_rel)} tasks")
    except Exception as e:
        print(f"DB manager (relative) error: {e}")

def simulate_external_mcp_context():
    """Simulate how external MCP might be called"""
    
    print("\n=== SIMULATING EXTERNAL MCP CONTEXT ===")
    
    # Try from different working directories
    original_cwd = os.getcwd()
    test_dirs = [
        "/tmp",
        "/Users/marcomacri",
        original_cwd
    ]
    
    for test_dir in test_dirs:
        print(f"\n--- Testing from {test_dir} ---")
        os.chdir(test_dir)
        
        try:
            # Clear module cache to force fresh import
            for module in list(sys.modules.keys()):
                if module.startswith('mcp_server'):
                    del sys.modules[module]
            
            from mcp_server.task_manager import _list_tasks_internal
            
            result = _list_tasks_internal(
                project_root=project_root,
                include_subtasks=True,
                include_stats=False
            )
            
            print(f"Tasks found: {len(result.get('tasks', []))}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            if 'message' in result:
                print(f"Message: {result['message']}")
                
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    debug_path_resolution()
    simulate_external_mcp_context()