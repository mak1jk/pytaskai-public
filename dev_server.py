#!/usr/bin/env python3
"""
PyTaskAI - Development Server with Hot Reload

Development wrapper script that monitors MCP server files and automatically
restarts the server when changes are detected.

Usage:
    python dev_server.py [--watch-dir DIR] [--no-restart] [--verbose]
"""

import subprocess
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, List

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ Warning: watchdog not installed. Auto-reload disabled.")
    print("Install with: pip install watchdog")


class MCPServerReloader(FileSystemEventHandler):
    """File system event handler for MCP server auto-restart"""
    
    def __init__(self, watch_dirs: List[str], auto_restart: bool = True, verbose: bool = False):
        """
        Initialize the reloader.
        
        Args:
            watch_dirs: Directories to watch for changes
            auto_restart: Whether to automatically restart on file changes
            verbose: Enable verbose logging
        """
        self.watch_dirs = watch_dirs
        self.auto_restart = auto_restart
        self.verbose = verbose
        self.process: Optional[subprocess.Popen] = None
        self.last_restart = 0
        self.restart_cooldown = 2  # seconds
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Start server initially
        self.start_server()
    
    def start_server(self):
        """Start or restart the MCP server"""
        current_time = time.time()
        
        # Prevent rapid restarts
        if current_time - self.last_restart < self.restart_cooldown:
            self.logger.debug(f"Restart cooldown active, skipping...")
            return
        
        # Terminate existing process
        if self.process:
            self.logger.info("🔄 Stopping existing MCP server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("⚠️ Force killing MCP server process...")
                self.process.kill()
                self.process.wait()
        
        # Start new process
        self.logger.info("🚀 Starting MCP server...")
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-m", "mcp_server"],
                stdout=subprocess.PIPE if not self.verbose else None,
                stderr=subprocess.PIPE if not self.verbose else None,
                cwd=Path(__file__).parent
            )
            self.last_restart = current_time
            self.logger.info(f"✅ MCP server started (PID: {self.process.pid})")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start MCP server: {e}")
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.logger.info("🛑 Stopping MCP server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                self.logger.info("✅ MCP server stopped")
            except subprocess.TimeoutExpired:
                self.logger.warning("⚠️ Force killing MCP server...")
                self.process.kill()
                self.process.wait()
            self.process = None
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only watch Python files
        if file_path.suffix != '.py':
            return
        
        # Check if file is in watched directories
        for watch_dir in self.watch_dirs:
            try:
                file_path.relative_to(watch_dir)
                break
            except ValueError:
                continue
        else:
            return  # File not in watched directories
        
        self.logger.info(f"📝 File changed: {file_path}")
        
        if self.auto_restart:
            self.start_server()
        else:
            self.logger.info("🔄 Auto-restart disabled. Manual restart required.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PyTaskAI Development Server with Hot Reload')
    parser.add_argument(
        '--watch-dir', 
        action='append',
        default=[],
        help='Additional directories to watch (default: mcp_server, shared)'
    )
    parser.add_argument(
        '--no-restart',
        action='store_true',
        help='Disable automatic restart on file changes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--no-watchdog',
        action='store_true',
        help='Run without file watching (just start server)'
    )
    
    args = parser.parse_args()
    
    # Determine watch directories
    project_root = Path(__file__).parent
    default_watch_dirs = [
        project_root / "mcp_server",
        project_root / "shared"
    ]
    
    watch_dirs = default_watch_dirs + [Path(d) for d in args.watch_dir]
    watch_dirs = [d for d in watch_dirs if d.exists()]
    
    if not watch_dirs:
        print("❌ No valid watch directories found")
        sys.exit(1)
    
    print(f"🎯 PyTaskAI Development Server")
    print(f"📁 Watching directories: {[str(d) for d in watch_dirs]}")
    print(f"🔄 Auto-restart: {'Enabled' if not args.no_restart else 'Disabled'}")
    print(f"📊 Verbose mode: {'Enabled' if args.verbose else 'Disabled'}")
    print()
    
    # Check watchdog availability
    if not WATCHDOG_AVAILABLE or args.no_watchdog:
        print("🐕 File watching disabled - running server only")
        try:
            subprocess.run([sys.executable, "-m", "mcp_server"], cwd=project_root)
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        return
    
    # Setup file watching
    reloader = MCPServerReloader(
        watch_dirs=watch_dirs,
        auto_restart=not args.no_restart,
        verbose=args.verbose
    )
    
    observer = Observer()
    for watch_dir in watch_dirs:
        observer.schedule(reloader, str(watch_dir), recursive=True)
    
    try:
        observer.start()
        print("🐕 File watching started. Press Ctrl+C to stop.")
        print("💡 Tip: Modify any .py file in watched directories to trigger restart")
        print()
        
        while True:
            time.sleep(1)
            
            # Check if server process is still running
            if reloader.process and reloader.process.poll() is not None:
                print(f"⚠️ MCP server process exited with code {reloader.process.returncode}")
                if args.auto_restart:
                    print("🔄 Restarting...")
                    reloader.start_server()
                else:
                    break
                    
    except KeyboardInterrupt:
        print("\n🛑 Stopping development server...")
        observer.stop()
        reloader.stop_server()
        
    observer.join()
    print("👋 Development server stopped")


if __name__ == "__main__":
    main()