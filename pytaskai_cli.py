#!/usr/bin/env python3
"""
PyTaskAI - Advanced CLI Interface
Complete PyTaskAI functionality with rich formatting and configuration management.
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Rich formatting imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.panel import Panel
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Try to import MCP tools with fallback
# Assumes project root is in PYTHONPATH, so mcp_server is a top-level package.
try:
    from mcp_server.task_manager import (
        list_tasks_tool,
        get_task_tool,
        get_next_task_tool,
        set_task_status_tool,
        add_dependency_tool,
        remove_dependency_tool,
        validate_dependencies_tool,
        parse_prd_tool,
        init_claude_support_tool,
        get_cache_metrics_tool,
        clear_cache_tool,
        check_rate_limits_tool,
        get_usage_stats_tool,
        check_budget_status_tool,
    )

    MCP_AVAILABLE = True
except ImportError as e:
    import traceback

    print(
        f"Detailed Import Error for MCP tools:\nType: {type(e)}\nError: {e}\nTraceback:\n{traceback.format_exc()}"
    )
    print(f"Warning: MCP tools not available: {e}")
    print(
        "Some functionality will be limited. Install dependencies with: pip install fastmcp rich"
    )
    MCP_AVAILABLE = False

    # Define dummy objects with .fn attribute for graceful failure if imports fail
    pytaskai_mcp_instance = None  # Not used for tool calls

    class _DummyMCPToolWithFn:
        def __init__(self, tool_name_str_for_dummy):
            self.name = tool_name_str_for_dummy
            # The fn attribute holds the callable dummy function
            self.fn = self._create_dummy_callable(tool_name_str_for_dummy)

        def _create_dummy_callable(self, tool_name_str_for_dummy_callable):
            def dummy_callable_fn(*args, **kwargs):
                # Try to get project_root from kwargs, similar to how real tools might receive it
                project_root_val = kwargs.get(
                    "project_root", "unknown_project_root_in_dummy"
                )
                error_message = f"Error: MCP Tool '{tool_name_str_for_dummy_callable}' (called via .fn) is not available due to import errors."
                if RICH_AVAILABLE:
                    # Assuming 'self' here refers to an instance of PyTaskAICLI if this were integrated
                    # For now, just print to stdout as PyTaskAICLI instance isn't available here.
                    print(f"[bold red]{error_message}[/bold red]")
                else:
                    print(error_message)

                # Return a dictionary structure similar to what a real tool might return on error
                return {
                    "error": error_message,
                    "details": "MCP tool dependencies are missing. Please ensure 'fastmcp' and other required packages are installed correctly.",
                    "project_root": project_root_val,
                    "status_code": 503,  # HTTP 503 Service Unavailable
                    "data": None,
                }

            return dummy_callable_fn

    _tool_names_for_dummies = [
        "list_tasks_tool",
        "get_task_tool",
        "get_next_task_tool",
        "set_task_status_tool",
        "add_dependency_tool",
        "remove_dependency_tool",
        "validate_dependencies_tool",
        "parse_prd_tool",
        "init_claude_support_tool",
        "get_cache_metrics_tool",
        "clear_cache_tool",
        "check_rate_limits_tool",
        "get_usage_stats_tool",
        "check_budget_status_tool",
    ]
    for _tool_name_val in _tool_names_for_dummies:
        globals()[_tool_name_val] = _DummyMCPToolWithFn(_tool_name_val)


class PyTaskAIConfig:
    """Configuration manager for PyTaskAI CLI."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.config_file = os.path.join(project_root, ".pytaskai.config.json")
        self.default_config = {
            "ai_service": {
                "use_research": False,
                "use_lts_deps": True,
                "default_model": "gpt-4o-mini",
                "fallback_model": "claude-3-haiku-20240307",
            },
            "cli": {
                "output_format": "table",
                "show_colors": True,
                "verbose": False,
                "page_size": 20,
            },
            "rate_limits": {
                "daily_budget": 10.0,
                "monthly_budget": 100.0,
                "warn_threshold": 0.8,
            },
            "task_management": {
                "auto_validate_dependencies": True,
                "default_priority": "medium",
                "auto_timestamp": True,
            },
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load config file: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config file: {e}")

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update nested dictionary."""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get(self, key_path: str, default=None):
        """Get config value using dot notation (e.g., 'ai_service.use_research')."""
        keys = key_path.split(".")
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """Set config value using dot notation."""
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


class PyTaskAICLI:
    """Advanced CLI interface for PyTaskAI."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.project_root = os.getcwd()
        self.config = PyTaskAIConfig(self.project_root)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Configure logging based on verbosity settings."""
        level = logging.DEBUG if self.config.get("cli.verbose") else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger("PyTaskAI")

    def print_rich(self, content, style=None):
        """Print content with rich formatting if available."""
        if RICH_AVAILABLE and self.console:
            if style:
                self.console.print(content, style=style)
            else:
                self.console.print(content)
        else:
            print(content)

    def print_error(self, message: str):
        """Print error message with appropriate formatting."""
        if RICH_AVAILABLE:
            self.print_rich(f"❌ Error: {message}", style="red")
        else:
            print(f"ERROR: {message}")

    def print_success(self, message: str):
        """Print success message with appropriate formatting."""
        if RICH_AVAILABLE:
            self.print_rich(f"✅ {message}", style="green")
        else:
            print(f"SUCCESS: {message}")

    def print_warning(self, message: str):
        """Print warning message with appropriate formatting."""
        if RICH_AVAILABLE:
            self.print_rich(f"⚠️  {message}", style="yellow")
        else:
            print(f"WARNING: {message}")

    def format_task_table(self, tasks: List[Dict], title: str = "Tasks") -> None:
        """Format tasks as a rich table or plain text."""
        if not tasks:
            self.print_warning("No tasks found")
            return

        if RICH_AVAILABLE and self.console:
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("ID", style="cyan", width=4)
            table.add_column("Title", style="white", width=30)
            table.add_column("Status", width=12)
            table.add_column("Priority", width=8)
            table.add_column("Dependencies", width=12)

            for task in tasks:
                status = task.get("status", "unknown")
                priority = task.get("priority", "medium")
                deps = str(len(task.get("dependencies", [])))

                # Color coding for status
                status_style = {
                    "pending": "yellow",
                    "in-progress": "blue",
                    "done": "green",
                    "cancelled": "red",
                    "review": "magenta",
                    "deferred": "dim",
                }.get(status, "white")

                # Priority styling
                priority_style = {
                    "high": "red bold",
                    "medium": "yellow",
                    "low": "dim",
                }.get(priority, "white")

                table.add_row(
                    str(task.get("id", "N/A")),
                    task.get("title", "Untitled")[:30],
                    Text(status, style=status_style),
                    Text(priority, style=priority_style),
                    deps,
                )

            self.console.print(table)
        else:
            # Plain text fallback
            print(f"\n{title}")
            print("=" * len(title))
            print(f"{'ID':<4} {'Title':<30} {'Status':<12} {'Priority':<8} {'Deps':<4}")
            print("-" * 60)

            for task in tasks:
                print(
                    f"{task.get('id', 'N/A'):<4} "
                    f"{task.get('title', 'Untitled')[:30]:<30} "
                    f"{task.get('status', 'unknown'):<12} "
                    f"{task.get('priority', 'medium'):<8} "
                    f"{len(task.get('dependencies', [])):<4}"
                )

    def cmd_list(self, args):
        """List tasks with filtering options."""
        if not MCP_AVAILABLE:
            self.print_error("MCP tools not available. Cannot list tasks.")
            return 1

        try:
            result = list_tasks_tool.fn(
                project_root=self.project_root,
                status_filter=args.status,
                priority_filter=args.priority,
                include_subtasks=not args.no_subtasks,
                include_stats=args.stats,
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            tasks = result.get("tasks", [])

            # Apply limit
            if args.limit:
                tasks = tasks[: args.limit]

            # Format output
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                title = f"Tasks ({result.get('total_count', len(tasks))} total"
                if args.status:
                    title += f", status: {args.status}"
                if args.priority:
                    title += f", priority: {args.priority}"
                title += ")"

                self.format_task_table(tasks, title)

                if args.stats and "statistics" in result:
                    stats = result["statistics"]
                    self.print_rich(f"\nStatistics: {stats}", style="dim")

            return 0

        except Exception as e:
            self.print_error(f"Failed to list tasks: {e}")
            return 1

    def cmd_next(self, args):
        """Get next task to work on."""
        try:
            result = get_next_task_tool.fn(
                project_root=self.project_root, exclude_dependencies=args.ignore_deps
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                next_task = result.get("next_task")
                if next_task:
                    self.print_success(
                        f"Next task: {next_task['id']} - {next_task['title']}"
                    )

                    if RICH_AVAILABLE:
                        panel = Panel(
                            f"[bold]{next_task['title']}[/bold]\n\n"
                            f"Description: {next_task.get('description', 'N/A')}\n"
                            f"Priority: {next_task.get('priority', 'medium')}\n"
                            f"Dependencies: {next_task.get('dependencies', [])}",
                            title=f"Task {next_task['id']}",
                            border_style="green",
                        )
                        self.console.print(panel)
                    else:
                        print(f"Description: {next_task.get('description', 'N/A')}")
                        print(f"Priority: {next_task.get('priority', 'medium')}")
                        print(f"Dependencies: {next_task.get('dependencies', [])}")
                else:
                    self.print_warning("No next task available")

            return 0

        except Exception as e:
            self.print_error(f"Failed to get next task: {e}")
            return 1

    def cmd_status(self, args):
        """Set task status."""
        try:
            result = set_task_status_tool.fn(
                project_root=self.project_root,
                task_id=args.task_id,
                new_status=args.status,
                subtask_id=args.subtask_id,
                update_timestamp=not args.no_timestamp,
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                self.print_success(result.get("message", "Status updated"))

                if "status_progression" in result:
                    for progression in result["status_progression"]:
                        self.print_rich(progression, style="blue")

            return 0

        except Exception as e:
            self.print_error(f"Failed to set status: {e}")
            return 1

    def cmd_add_dep(self, args):
        """Add dependency between tasks."""
        try:
            result = add_dependency_tool.fn(
                project_root=self.project_root,
                task_id=args.task_id,
                dependency_id=args.dependency_id,
                validate_circular=not args.no_circular_check,
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                self.print_success(result.get("message", "Dependency added"))

            return 0

        except Exception as e:
            self.print_error(f"Failed to add dependency: {e}")
            return 1

    def cmd_remove_dep(self, args):
        """Remove dependency between tasks."""
        try:
            result = remove_dependency_tool.fn(
                project_root=self.project_root,
                task_id=args.task_id,
                dependency_id=args.dependency_id,
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                self.print_success(result.get("message", "Dependency removed"))

            return 0

        except Exception as e:
            self.print_error(f"Failed to remove dependency: {e}")
            return 1

    def cmd_validate_deps(self, args):
        """Validate task dependencies."""
        try:
            result = validate_dependencies_tool.fn(
                project_root=self.project_root, fix_issues=args.fix
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                validation = result.get("validation_results", {})

                if validation.get("is_valid"):
                    self.print_success("✅ Dependencies validation passed")
                else:
                    self.print_error("❌ Dependencies validation failed")

                issues = validation.get("issues_found", [])
                if issues:
                    self.print_rich(f"\nIssues found ({len(issues)}):", style="red")
                    for issue in issues:
                        self.print_rich(
                            f"  • {issue.get('description', 'Unknown issue')}",
                            style="red",
                        )

                warnings = validation.get("warnings", [])
                if warnings:
                    self.print_rich(f"\nWarnings ({len(warnings)}):", style="yellow")
                    for warning in warnings:
                        self.print_rich(
                            f"  • {warning.get('description', 'Unknown warning')}",
                            style="yellow",
                        )

                fixes = validation.get("fixes_applied", [])
                if fixes and args.fix:
                    self.print_rich(f"\nFixes applied ({len(fixes)}):", style="green")
                    for fix in fixes:
                        self.print_rich(
                            f"  • {fix.get('type', 'Unknown fix')}", style="green"
                        )

            return 0

        except Exception as e:
            self.print_error(f"Failed to validate dependencies: {e}")
            return 1

    def cmd_parse_prd(self, args):
        """Parse PRD and generate tasks."""
        try:
            # Read PRD content
            if not os.path.exists(args.prd_file):
                self.print_error(f"PRD file not found: {args.prd_file}")
                return 1

            with open(args.prd_file, "r", encoding="utf-8") as f:
                prd_content = f.read()

            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task(
                        "Parsing PRD and generating tasks...", total=None
                    )

                    result = parse_prd_tool.fn(
                        project_root=self.project_root,
                        prd_content=prd_content,
                        target_tasks_count=args.count,
                        use_research=args.research,
                        use_lts_deps=not args.latest,
                        overwrite_existing=args.overwrite,
                    )
            else:
                print("Parsing PRD and generating tasks...")
                result = parse_prd_tool.fn(
                    project_root=self.project_root,
                    prd_content=prd_content,
                    target_tasks_count=args.count,
                    use_research=args.research,
                    use_lts_deps=not args.latest,
                    overwrite_existing=args.overwrite,
                )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                generated_count = result.get("generated_tasks_count", 0)
                self.print_success(
                    f"Successfully generated {generated_count} tasks from PRD"
                )

                if "ai_metadata" in result:
                    metadata = result["ai_metadata"]
                    self.print_rich(
                        f"Research used: {metadata.get('research_used', False)}",
                        style="dim",
                    )
                    self.print_rich(
                        f"Model used: {metadata.get('model_used', 'unknown')}",
                        style="dim",
                    )

            return 0

        except Exception as e:
            self.print_error(f"Failed to parse PRD: {e}")
            return 1

    def cmd_cache_metrics(self, args):
        """Get cache performance metrics."""
        try:
            result = get_cache_metrics_tool.fn(
                project_root=self.project_root, include_detailed_stats=args.detailed
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                metrics = result.get("metrics", {})
                cache_metrics = metrics.get("cache", {})

                self.print_rich("Cache Performance Metrics", style="bold blue")
                self.print_rich(
                    f"Hit Rate: {cache_metrics.get('hit_rate', 0):.1f}%", style="green"
                )
                self.print_rich(f"Total Calls: {cache_metrics.get('total_calls', 0)}")
                self.print_rich(f"Cache Hits: {cache_metrics.get('cache_hits', 0)}")
                self.print_rich(f"Cache Size: {cache_metrics.get('cache_size', 0)}")
                self.print_rich(
                    f"Total Saved Cost: ${cache_metrics.get('total_saved_cost', 0):.4f}"
                )

                insights = result.get("insights", [])
                if insights:
                    self.print_rich("\nInsights:", style="yellow")
                    for insight in insights:
                        self.print_rich(f"  • {insight}")

            return 0

        except Exception as e:
            self.print_error(f"Failed to get cache metrics: {e}")
            return 1

    def cmd_usage_stats(self, args):
        """Get AI usage statistics."""
        try:
            result = get_usage_stats_tool.fn(
                project_root=self.project_root,
                start_date=args.start_date,
                end_date=args.end_date,
                provider=args.provider,
                operation_type=args.operation_type,
            )

            if "error" in result:
                self.print_error(result["error"])
                return 1

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                stats = result.get("usage_stats", {})

                self.print_rich("AI Usage Statistics", style="bold blue")
                self.print_rich(f"Total Calls: {stats.get('total_calls', 0)}")
                self.print_rich(f"Total Cost: ${stats.get('total_cost', 0):.4f}")
                self.print_rich(
                    f"Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1f}%"
                )

                if stats.get("most_used_model"):
                    self.print_rich(f"Most Used Model: {stats['most_used_model']}")

                insights = result.get("insights", [])
                if insights:
                    self.print_rich("\nInsights:", style="yellow")
                    for insight in insights:
                        self.print_rich(f"  • {insight}")

            return 0

        except Exception as e:
            self.print_error(f"Failed to get usage stats: {e}")
            return 1

    def cmd_config(self, args):
        """Manage configuration."""
        try:
            if args.action == "show":
                if args.json:
                    print(json.dumps(self.config.config, indent=2))
                else:
                    self.print_rich("Current Configuration:", style="bold blue")
                    self._print_config_tree(self.config.config)

            elif args.action == "get":
                if not args.key:
                    self.print_error("Key is required for 'get' action")
                    return 1

                value = self.config.get(args.key)
                if args.json:
                    print(json.dumps({args.key: value}, indent=2))
                else:
                    self.print_rich(f"{args.key}: {value}")

            elif args.action == "set":
                if not args.key or args.value is None:
                    self.print_error("Both key and value are required for 'set' action")
                    return 1

                # Try to parse value as JSON first, then as string
                try:
                    parsed_value = json.loads(args.value)
                except json.JSONDecodeError:
                    parsed_value = args.value

                self.config.set(args.key, parsed_value)
                self.config.save_config()
                self.print_success(f"Set {args.key} = {parsed_value}")

            elif args.action == "reset":
                self.config.config = self.config.default_config.copy()
                self.config.save_config()
                self.print_success("Configuration reset to defaults")

            return 0

        except Exception as e:
            self.print_error(f"Configuration error: {e}")
            return 1

    def _print_config_tree(self, config: Dict, indent: str = ""):
        """Recursively print configuration tree."""
        for key, value in config.items():
            if isinstance(value, dict):
                self.print_rich(f"{indent}{key}:", style="bold")
                self._print_config_tree(value, indent + "  ")
            else:
                self.print_rich(f"{indent}{key}: {value}")


def create_parser():
    """Create the argument parser with all commands and options."""
    parser = argparse.ArgumentParser(
        prog="pytaskai",
        description="PyTaskAI - Advanced Task Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytaskai list --status pending --priority high
  pytaskai next --ignore-deps
  pytaskai status 5 done
  pytaskai add-dep 5 3
  pytaskai parse-prd docs/prd.txt --count 15 --research
  pytaskai config set ai_service.use_research true
        """,
    )

    # Global options
    parser.add_argument(
        "--project-root",
        "-p",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Subcommands
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
    list_parser.add_argument(
        "--no-subtasks", action="store_true", help="Exclude subtasks from output"
    )
    list_parser.add_argument(
        "--stats", action="store_true", help="Include project statistics"
    )

    # Next command
    next_parser = subparsers.add_parser("next", help="Get next task to work on")
    next_parser.add_argument(
        "--ignore-deps",
        action="store_true",
        help="Ignore dependencies when selecting next task",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Set task status")
    status_parser.add_argument("task_id", type=int, help="Task ID")
    status_parser.add_argument(
        "status",
        choices=["pending", "in-progress", "done", "cancelled", "review", "deferred"],
        help="New status",
    )
    status_parser.add_argument(
        "--subtask-id", type=int, help="Subtask ID (if updating a subtask)"
    )
    status_parser.add_argument(
        "--no-timestamp", action="store_true", help="Do not update timestamp"
    )

    # Dependency management
    add_dep_parser = subparsers.add_parser("add-dep", help="Add task dependency")
    add_dep_parser.add_argument(
        "task_id", type=int, help="Task ID that depends on another"
    )
    add_dep_parser.add_argument("dependency_id", type=int, help="Task ID to depend on")
    add_dep_parser.add_argument(
        "--no-circular-check",
        action="store_true",
        help="Skip circular dependency validation",
    )

    remove_dep_parser = subparsers.add_parser(
        "remove-dep", help="Remove task dependency"
    )
    remove_dep_parser.add_argument("task_id", type=int, help="Task ID")
    remove_dep_parser.add_argument(
        "dependency_id", type=int, help="Dependency ID to remove"
    )

    validate_deps_parser = subparsers.add_parser(
        "validate-deps", help="Validate task dependencies"
    )
    validate_deps_parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues found"
    )

    # PRD parsing
    prd_parser = subparsers.add_parser("parse-prd", help="Parse PRD and generate tasks")
    prd_parser.add_argument("prd_file", help="Path to PRD file")
    prd_parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of tasks to generate (default: 10)",
    )
    prd_parser.add_argument(
        "--research", action="store_true", help="Use research capabilities"
    )
    prd_parser.add_argument(
        "--latest", action="store_true", help="Prefer latest versions over LTS"
    )
    prd_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing tasks"
    )

    # Cache and metrics
    cache_parser = subparsers.add_parser(
        "cache-metrics", help="Show cache performance metrics"
    )
    cache_parser.add_argument(
        "--detailed", action="store_true", help="Include detailed statistics"
    )

    usage_parser = subparsers.add_parser("usage-stats", help="Show AI usage statistics")
    usage_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    usage_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    usage_parser.add_argument("--provider", help="AI provider filter")
    usage_parser.add_argument("--operation-type", help="Operation type filter")

    # Configuration
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "action", choices=["show", "get", "set", "reset"], help="Configuration action"
    )
    config_parser.add_argument(
        "key", nargs="?", help="Configuration key (dot notation)"
    )
    config_parser.add_argument("value", nargs="?", help="Configuration value")

    # MCP Server
    serve_parser = subparsers.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument("--host", default="localhost", help="Server host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Server port")

    # Claude Code setup
    init_parser = subparsers.add_parser(
        "init-claude", help="Initialize Claude Code support"
    )
    init_parser.add_argument(
        "--no-windsurfrules",
        action="store_true",
        help="Skip creating .windsurfrules file",
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Initialize CLI
    cli = PyTaskAICLI()

    # Override project root if specified
    if args.project_root:
        cli.project_root = os.path.abspath(args.project_root)
        cli.config = PyTaskAIConfig(cli.project_root)

    # Override verbosity if specified
    if args.verbose:
        cli.config.set("cli.verbose", True)
        cli.setup_logging()

    # Check if Rich is available and warn if not
    if not RICH_AVAILABLE and not args.json:
        print("Warning: Rich library not available. Output will be plain text.")
        print("Install rich for better formatting: pip install rich")

    # Command routing
    try:
        if args.command == "list":
            return cli.cmd_list(args)
        elif args.command == "next":
            return cli.cmd_next(args)
        elif args.command == "status":
            return cli.cmd_status(args)
        elif args.command == "add-dep":
            return cli.cmd_add_dep(args)
        elif args.command == "remove-dep":
            return cli.cmd_remove_dep(args)
        elif args.command == "validate-deps":
            return cli.cmd_validate_deps(args)
        elif args.command == "parse-prd":
            return cli.cmd_parse_prd(args)
        elif args.command == "cache-metrics":
            return cli.cmd_cache_metrics(args)
        elif args.command == "usage-stats":
            return cli.cmd_usage_stats(args)
        elif args.command == "config":
            return cli.cmd_config(args)
        elif args.command == "serve":
            cli.print_error("MCP server functionality not yet implemented")
            return 1
        elif args.command == "init-claude":
            cli.print_error("Claude Code initialization not yet implemented")
            return 1
        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        cli.print_warning("Operation cancelled by user")
        return 130
    except Exception as e:
        cli.print_error(f"Unexpected error: {e}")
        if cli.config.get("cli.verbose"):
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
