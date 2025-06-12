#!/usr/bin/env python3
"""
PyTaskAI - Minimal CLI Interface
Basic task management functionality without external dependencies.
"""

import argparse
import json
import os
import sys
import subprocess
from typing import Dict, Any, Optional, List


class MinimalCLI:
    """Minimal CLI interface using MCP tools directly."""

    def __init__(self):
        self.project_root = os.getcwd()

    def run_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Run MCP tool using mcp__taskmaster-ai__ prefix."""
        try:
            # Construct the tool call
            tool_call = f"mcp__taskmaster-ai__{tool_name}"

            # For now, return a placeholder since we can't call MCP directly
            # In a real implementation, this would use the MCP protocol
            return {"error": "Direct MCP calls not implemented in minimal CLI"}

        except Exception as e:
            return {"error": f"MCP tool call failed: {e}"}

    def load_tasks_direct(self) -> Dict[str, Any]:
        """Load tasks directly from tasks.json file."""
        tasks_file = os.path.join(self.project_root, "tasks", "tasks.json")

        try:
            with open(tasks_file, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to load tasks: {e}"}

    def save_tasks_direct(self, data: Dict[str, Any]) -> bool:
        """Save tasks directly to tasks.json file."""
        tasks_file = os.path.join(self.project_root, "tasks", "tasks.json")

        try:
            with open(tasks_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False

    def format_task_list(self, tasks: List[Dict], title: str = "Tasks"):
        """Format tasks as a simple table."""
        if not tasks:
            print("No tasks found.")
            return

        print(f"\n{title}")
        print("=" * len(title))
        print(f"{'ID':<4} {'Title':<35} {'Status':<12} {'Priority':<8} {'Deps':<4}")
        print("-" * 70)

        for task in tasks:
            deps_count = len(task.get("dependencies", []))
            print(
                f"{task.get('id', 'N/A'):<4} "
                f"{task.get('title', 'Untitled')[:35]:<35} "
                f"{task.get('status', 'unknown'):<12} "
                f"{task.get('priority', 'medium'):<8} "
                f"{deps_count:<4}"
            )

    def cmd_list(self, args):
        """List tasks with basic filtering."""
        data = self.load_tasks_direct()

        if "error" in data:
            print(f"Error: {data['error']}")
            return 1

        tasks = data.get("tasks", [])

        # Apply filters
        if args.status:
            tasks = [t for t in tasks if t.get("status") == args.status]

        if args.priority:
            tasks = [t for t in tasks if t.get("priority") == args.priority]

        if args.limit:
            tasks = tasks[: args.limit]

        # Output
        if args.json:
            output = {
                "tasks": tasks,
                "total_count": len(tasks),
                "filters": {"status": args.status, "priority": args.priority},
            }
            print(json.dumps(output, indent=2))
        else:
            title = f"Tasks ({len(tasks)} total"
            if args.status:
                title += f", status: {args.status}"
            if args.priority:
                title += f", priority: {args.priority}"
            title += ")"

            self.format_task_list(tasks, title)

        return 0

    def cmd_get(self, args):
        """Get specific task details."""
        data = self.load_tasks_direct()

        if "error" in data:
            print(f"Error: {data['error']}")
            return 1

        tasks = data.get("tasks", [])
        task = next((t for t in tasks if t.get("id") == args.task_id), None)

        if not task:
            print(f"Task {args.task_id} not found.")
            return 1

        if args.json:
            print(json.dumps(task, indent=2))
        else:
            print(f"\nTask {task['id']}: {task.get('title', 'Untitled')}")
            print("=" * 50)
            print(f"Description: {task.get('description', 'N/A')}")
            print(f"Status: {task.get('status', 'unknown')}")
            print(f"Priority: {task.get('priority', 'medium')}")
            print(f"Dependencies: {task.get('dependencies', [])}")

            if task.get("details"):
                print(f"\nDetails:\n{task['details']}")

            if task.get("test_strategy"):
                print(f"\nTest Strategy:\n{task['test_strategy']}")

        return 0

    def cmd_next(self, args):
        """Find next available task."""
        data = self.load_tasks_direct()

        if "error" in data:
            print(f"Error: {data['error']}")
            return 1

        tasks = data.get("tasks", [])

        # Find pending tasks
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]

        if not pending_tasks:
            print("No pending tasks found.")
            return 0

        # Simple next task logic (without dependency checking for minimal version)
        if args.ignore_deps:
            # Just return first pending task by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            pending_tasks.sort(
                key=lambda x: (
                    priority_order.get(x.get("priority", "medium"), 2),
                    x.get("id", 0),
                ),
                reverse=True,
            )
            next_task = pending_tasks[0]
        else:
            # Simple dependency checking
            done_task_ids = {t.get("id") for t in tasks if t.get("status") == "done"}

            available_tasks = []
            for task in pending_tasks:
                dependencies = task.get("dependencies", [])
                if not dependencies or all(
                    dep_id in done_task_ids for dep_id in dependencies
                ):
                    available_tasks.append(task)

            if not available_tasks:
                print(
                    "No tasks available (pending tasks have unfulfilled dependencies)."
                )
                return 0

            # Sort by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            available_tasks.sort(
                key=lambda x: (
                    priority_order.get(x.get("priority", "medium"), 2),
                    x.get("id", 0),
                ),
                reverse=True,
            )
            next_task = available_tasks[0]

        if args.json:
            print(json.dumps(next_task, indent=2))
        else:
            print(
                f"🎯 Next Task: {next_task['id']} - {next_task.get('title', 'Untitled')}"
            )
            print(f"Priority: {next_task.get('priority', 'medium')}")
            print(f"Description: {next_task.get('description', 'N/A')}")

            if next_task.get("dependencies"):
                print(f"Dependencies: {next_task['dependencies']}")

        return 0

    def cmd_status(self, args):
        """Set task status."""
        data = self.load_tasks_direct()

        if "error" in data:
            print(f"Error: {data['error']}")
            return 1

        tasks = data.get("tasks", [])
        task_index = None

        for i, task in enumerate(tasks):
            if task.get("id") == args.task_id:
                task_index = i
                break

        if task_index is None:
            print(f"Task {args.task_id} not found.")
            return 1

        old_status = tasks[task_index].get("status", "unknown")
        tasks[task_index]["status"] = args.new_status
        tasks[task_index]["updated_at"] = "2025-01-06T00:00:00"  # Simplified timestamp

        if self.save_tasks_direct(data):
            print(
                f"✅ Task {args.task_id} status updated: {old_status} → {args.new_status}"
            )
            return 0
        else:
            print(f"❌ Failed to save task status update.")
            return 1

    def cmd_stats(self, args):
        """Show project statistics."""
        data = self.load_tasks_direct()

        if "error" in data:
            print(f"Error: {data['error']}")
            return 1

        tasks = data.get("tasks", [])

        # Calculate statistics
        stats = {
            "total_tasks": len(tasks),
            "by_status": {},
            "by_priority": {},
            "with_dependencies": 0,
        }

        for task in tasks:
            status = task.get("status", "unknown")
            priority = task.get("priority", "medium")

            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

            if task.get("dependencies"):
                stats["with_dependencies"] += 1

        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n📊 Project Statistics")
            print("=" * 20)
            print(f"Total tasks: {stats['total_tasks']}")
            print(f"Tasks with dependencies: {stats['with_dependencies']}")

            print("\n📋 By Status:")
            for status, count in stats["by_status"].items():
                print(f"  {status}: {count}")

            print("\n🎯 By Priority:")
            for priority, count in stats["by_priority"].items():
                print(f"  {priority}: {count}")

        return 0


def create_parser():
    """Create argument parser for minimal CLI."""
    parser = argparse.ArgumentParser(
        prog="pytaskai-minimal",
        description="PyTaskAI Minimal CLI - Basic task management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytaskai-minimal list --status pending
  pytaskai-minimal next
  pytaskai-minimal get 5
  pytaskai-minimal status 5 done
  pytaskai-minimal stats
        """,
    )

    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        choices=["pending", "in-progress", "done", "cancelled", "review", "deferred"],
        help="Filter by status",
    )
    list_parser.add_argument(
        "--priority", choices=["high", "medium", "low"], help="Filter by priority"
    )
    list_parser.add_argument("--limit", type=int, help="Limit number of results")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get task details")
    get_parser.add_argument("task_id", type=int, help="Task ID")

    # Next command
    next_parser = subparsers.add_parser("next", help="Get next task")
    next_parser.add_argument(
        "--ignore-deps", action="store_true", help="Ignore dependencies"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Set task status")
    status_parser.add_argument("task_id", type=int, help="Task ID")
    status_parser.add_argument(
        "new_status",
        choices=["pending", "in-progress", "done", "cancelled", "review", "deferred"],
        help="New status",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show project statistics")

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    cli = MinimalCLI()

    try:
        if args.command == "list":
            return cli.cmd_list(args)
        elif args.command == "get":
            return cli.cmd_get(args)
        elif args.command == "next":
            return cli.cmd_next(args)
        elif args.command == "status":
            return cli.cmd_status(args)
        elif args.command == "stats":
            return cli.cmd_stats(args)
        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
