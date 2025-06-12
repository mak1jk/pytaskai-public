"""
PyTaskAI - Hot Reload Module

Provides hot reload functionality for MCP server development.
Allows reloading of Python modules without restarting the entire server.
"""

import importlib
import sys
import os
import signal
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class HotReloader:
    """Hot reload manager for MCP server modules"""

    def __init__(self, modules_to_watch: List[str] = None, excluded_paths: List[str] = None):
        """
        Initialize hot reloader.
        
        Args:
            modules_to_watch: List of module names to watch for reloading
            excluded_paths: List of paths to exclude from watching (security feature)
        """
        self.modules_to_watch = modules_to_watch or [
            'mcp_server.task_manager',
            'mcp_server.ai_service', 
            'mcp_server.cache_manager',
            'mcp_server.database',
            'mcp_server.utils',
            'mcp_server.usage_tracker',
            'shared.models'
        ]
        
        # Security: Exclude sensitive paths from hot reload
        self.excluded_paths = excluded_paths or [
            'prompts_secure',  # Secure prompt templates
            'mcp_server/security',  # Security modules
            '.env',  # Environment files
            'config',  # Configuration files
            'credentials',  # Credential files
        ]
        
        self.last_reload_time = datetime.now()
    
    def reload_modules(self) -> Dict[str, Any]:
        """
        Reload specified modules.
        
        Returns:
            Dict with reload results and statistics
        """
        reloaded = []
        failed = []
        excluded = []
        
        logger.info("Starting hot reload of modules...")
        
        for module_name in self.modules_to_watch:
            if module_name in sys.modules:
                try:
                    # Get module file path for validation
                    module = sys.modules[module_name]
                    if hasattr(module, '__file__') and module.__file__:
                        module_path = Path(module.__file__)
                        
                        # Security check: verify module path is not in excluded paths
                        if self._is_path_excluded(str(module_path)):
                            excluded.append({
                                "name": module_name,
                                "path": str(module_path),
                                "reason": "Path excluded for security"
                            })
                            logger.warning(f"🔒 Module {module_name} excluded from reload for security")
                            continue
                        
                        if module_path.exists():
                            importlib.reload(module)
                            reloaded.append({
                                "name": module_name,
                                "path": str(module_path),
                                "reloaded_at": datetime.now().isoformat()
                            })
                            logger.info(f"✅ Reloaded module: {module_name}")
                        else:
                            failed.append({
                                "name": module_name,
                                "error": f"Module file not found: {module_path}",
                                "path": str(module_path) if module_path else "Unknown"
                            })
                    else:
                        failed.append({
                            "name": module_name,
                            "error": "Module has no __file__ attribute",
                            "path": "Built-in module"
                        })
                except Exception as e:
                    error_msg = f"Failed to reload {module_name}: {str(e)}"
                    logger.error(error_msg)
                    failed.append({
                        "name": module_name,
                        "error": error_msg,
                        "path": getattr(sys.modules[module_name], '__file__', 'Unknown')
                    })
            else:
                logger.warning(f"Module {module_name} not loaded, skipping reload")
        
        self.last_reload_time = datetime.now()
        
        return {
            "status": "completed",
            "timestamp": self.last_reload_time.isoformat(),
            "reloaded_modules": reloaded,
            "failed_modules": failed,
            "excluded_modules": excluded,
            "summary": {
                "total_requested": len(self.modules_to_watch),
                "successfully_reloaded": len(reloaded),
                "failed": len(failed),
                "excluded": len(excluded),
                "not_loaded": len(self.modules_to_watch) - len(reloaded) - len(failed) - len(excluded)
            }
        }
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Check if a path should be excluded from hot reload for security.
        
        Args:
            path: File path to check
            
        Returns:
            True if path should be excluded
        """
        path_str = str(path).replace('\\', '/')  # Normalize path separators
        
        for excluded_pattern in self.excluded_paths:
            if excluded_pattern in path_str:
                return True
        
        return False
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        Get information about modules being watched.
        
        Returns:
            Dict with module information
        """
        modules_info = []
        
        for module_name in self.modules_to_watch:
            info = {"name": module_name, "loaded": module_name in sys.modules}
            
            if info["loaded"]:
                module = sys.modules[module_name]
                info.update({
                    "file_path": getattr(module, '__file__', 'Built-in'),
                    "package": getattr(module, '__package__', None),
                    "version": getattr(module, '__version__', None)
                })
                
                # Check if file exists and get modification time
                if hasattr(module, '__file__') and module.__file__:
                    file_path = Path(module.__file__)
                    if file_path.exists():
                        info["file_exists"] = True
                        info["last_modified"] = datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    else:
                        info["file_exists"] = False
            
            modules_info.append(info)
        
        return {
            "modules": modules_info,
            "last_reload_time": self.last_reload_time.isoformat(),
            "python_version": sys.version,
            "total_loaded_modules": len(sys.modules)
        }


def restart_server_process(graceful: bool = True) -> Dict[str, Any]:
    """
    Restart the MCP server process.
    
    Args:
        graceful: If True, attempt graceful shutdown before restart
        
    Returns:
        Dict with restart operation results
    """
    try:
        logger.info(f"Initiating server restart (graceful={graceful})...")
        
        # Get current process info
        pid = os.getpid()
        
        if graceful:
            # Try graceful shutdown first
            logger.info("Attempting graceful shutdown...")
            os.kill(pid, signal.SIGTERM)
        else:
            # Force restart
            logger.info("Forcing server restart...")
            os.kill(pid, signal.SIGKILL)
        
        return {
            "status": "restart_initiated",
            "method": "graceful" if graceful else "forced",
            "pid": pid,
            "timestamp": datetime.now().isoformat(),
            "message": "Server restart signal sent"
        }
        
    except Exception as e:
        error_msg = f"Failed to restart server: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


def clear_module_cache(module_pattern: str = None) -> Dict[str, Any]:
    """
    Clear Python module cache for specific modules.
    
    Args:
        module_pattern: Pattern to match module names (default: 'mcp_server')
        
    Returns:
        Dict with cache clearing results
    """
    pattern = module_pattern or "mcp_server"
    cleared_modules = []
    
    try:
        # Find modules matching pattern
        modules_to_clear = [
            name for name in list(sys.modules.keys()) 
            if pattern in name
        ]
        
        # Remove from sys.modules
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
                cleared_modules.append(module_name)
                logger.info(f"Cleared module cache: {module_name}")
        
        # Also clear importlib cache
        if hasattr(importlib, 'invalidate_caches'):
            importlib.invalidate_caches()
        
        return {
            "status": "success",
            "pattern": pattern,
            "cleared_modules": cleared_modules,
            "total_cleared": len(cleared_modules),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Failed to clear module cache: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "pattern": pattern,
            "timestamp": datetime.now().isoformat()
        }


# Global reloader instance
_global_reloader = None

def get_reloader() -> HotReloader:
    """Get or create global reloader instance"""
    global _global_reloader
    if _global_reloader is None:
        _global_reloader = HotReloader()
    return _global_reloader