#!/usr/bin/env python3
"""
PyTaskAI CLI Setup Script
Automatically configures and tests the CLI interface.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def print_status(message, status="info"):
    """Print colored status messages."""
    colors = {
        "info": "\033[94m",  # Blue
        "success": "\033[92m",  # Green
        "warning": "\033[93m",  # Yellow
        "error": "\033[91m",  # Red
        "reset": "\033[0m",  # Reset
    }

    symbols = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}

    color = colors.get(status, colors["info"])
    symbol = symbols.get(status, "•")
    reset = colors["reset"]

    print(f"{color}{symbol} {message}{reset}")


def check_python_version():
    """Check if Python version is compatible."""
    print_status("Checking Python version...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_status(
            f"Python {version.major}.{version.minor} detected. Python 3.9+ required.",
            "error",
        )
        return False

    print_status(f"Python {version.major}.{version.minor}.{version.micro} ✓", "success")
    return True


def check_project_structure():
    """Verify project structure is correct."""
    print_status("Checking project structure...")

    required_files = [
        "tasks/tasks.json",
        "mcp_server/task_manager.py",
        "mcp_server/utils.py",
        "pytaskai_minimal.py",
    ]

    required_dirs = ["mcp_server", "tasks", "frontend", "shared"]

    missing_items = []

    # Check directories
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_items.append(f"Directory: {dir_path}")

    # Check files
    for file_path in required_files:
        if not os.path.isfile(file_path):
            missing_items.append(f"File: {file_path}")

    if missing_items:
        print_status("Missing required items:", "error")
        for item in missing_items:
            print(f"  - {item}")
        return False

    print_status("Project structure ✓", "success")
    return True


def create_cli_config():
    """Create default CLI configuration."""
    print_status("Creating CLI configuration...")

    config = {
        "version": "1.0.0",
        "project_name": "PyTaskAI",
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
            "auto_save": True,
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
            "backup_on_change": True,
        },
        "ui_preferences": {
            "theme": "default",
            "task_display_limit": 50,
            "show_subtasks": True,
            "group_by_status": False,
        },
    }

    config_file = ".pytaskai.config.json"

    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print_status(f"Configuration created: {config_file}", "success")
        return True

    except Exception as e:
        print_status(f"Failed to create configuration: {e}", "error")
        return False


def create_shell_aliases():
    """Create convenient shell aliases."""
    print_status("Setting up shell aliases...")

    aliases = [
        'alias ptai="python3 pytaskai_minimal.py"',
        'alias ptai-list="python3 pytaskai_minimal.py list"',
        'alias ptai-next="python3 pytaskai_minimal.py next"',
        'alias ptai-stats="python3 pytaskai_minimal.py stats"',
    ]

    alias_file = ".pytaskai_aliases"

    try:
        with open(alias_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# PyTaskAI CLI Aliases\n")
            f.write("# Source this file: source .pytaskai_aliases\n\n")

            for alias in aliases:
                f.write(f"{alias}\n")

        print_status(f"Aliases created: {alias_file}", "success")
        print_status("To use aliases, run: source .pytaskai_aliases", "info")
        return True

    except Exception as e:
        print_status(f"Failed to create aliases: {e}", "error")
        return False


def test_cli_functionality():
    """Test basic CLI functionality."""
    print_status("Testing CLI functionality...")

    cli_script_name = "pytaskai_cli.py"
    # Use the same Python interpreter that's running setup_cli.py
    python_executable = sys.executable

    commands_to_test = [
        (f"{python_executable} {cli_script_name} --help", "Test 1: --help"),
        (
            f"{python_executable} {cli_script_name} --json usage-stats",
            "Test 2: --json stats",
        ),
    ]

    all_tests_passed = True
    for command, test_name in commands_to_test:
        print_status(test_name, "info")
        try:
            # Use os.environ.copy() to ensure PYTHONPATH is inherited if set externally
            # Run with shell=False for better security and argument handling with sys.executable
            process = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                check=False,
            )

            if process.returncode == 0:
                print_status(f"{test_name} ✓", "success")
            else:
                print_status(
                    f"{test_name} failed (return code: {process.returncode}):", "error"
                )
                if process.stdout:
                    print_status(
                        f"Subprocess STDOUT:\n{process.stdout.strip()}", "warning"
                    )
                if process.stderr:
                    print_status(
                        f"Subprocess STDERR:\n{process.stderr.strip()}", "error"
                    )
                all_tests_passed = False
                break  # Stop on first failure
        except Exception as e:
            print_status(f"{test_name} failed with exception: {e}", "error")
            all_tests_passed = False
            break  # Stop on first failure

    return all_tests_passed


def create_usage_guide():
    """Create a usage guide file."""
    print_status("Creating usage guide...")

    guide_content = """# PyTaskAI CLI Usage Guide

## Quick Start

### Basic Commands
```bash
# List all tasks
python3 pytaskai_minimal.py list

# List pending tasks only
python3 pytaskai_minimal.py list --status pending

# Get next task to work on
python3 pytaskai_minimal.py next

# Get details for task 5
python3 pytaskai_minimal.py get 5

# Update task status
python3 pytaskai_minimal.py status 5 done

# Show project statistics
python3 pytaskai_minimal.py stats
```

### Filtering and Output

```bash
# Filter by priority
python3 pytaskai_minimal.py list --priority high

# Limit results
python3 pytaskai_minimal.py list --limit 10

# JSON output
python3 pytaskai_minimal.py list --json
python3 pytaskai_minimal.py stats --json
```

### Shell Aliases

Source the aliases file for shortcuts:
```bash
source .pytaskai_aliases

# Then use short commands:
ptai list
ptai-next
ptai-stats
```

## Task Status Values

- `pending`: Not started
- `in-progress`: Currently working on
- `done`: Completed
- `cancelled`: Cancelled/abandoned
- `review`: Waiting for review
- `deferred`: Postponed

## Priority Values

- `high`: Urgent/important
- `medium`: Normal priority
- `low`: Nice to have

## Tips

1. Use `ptai next` to find your next task
2. Always update status when starting/finishing work
3. Use `--json` for scripting and automation
4. Check `ptai stats` for project overview

## Advanced Features

For full MCP integration and AI features, install dependencies:
```bash
pip install fastmcp rich litellm
python3 pytaskai_cli.py --help
```
"""

    try:
        with open("CLI_USAGE_GUIDE.md", "w") as f:
            f.write(guide_content)

        print_status("Usage guide created: CLI_USAGE_GUIDE.md", "success")
        return True

    except Exception as e:
        print_status(f"Failed to create usage guide: {e}", "error")
        return False


def main():
    """Main setup function."""
    print("🚀 PyTaskAI CLI Setup")
    print("=" * 25)

    # Change to workspace if needed
    if not os.getcwd().endswith("workspace"):
        if os.path.exists("/workspace"):
            os.chdir("/workspace")

    print_status(f"Working directory: {os.getcwd()}", "info")

    # Run setup steps
    setup_steps = [
        ("Python Version Check", check_python_version),
        ("Project Structure Check", check_project_structure),
        ("CLI Configuration", create_cli_config),
        ("Shell Aliases", create_shell_aliases),
        ("CLI Functionality Test", test_cli_functionality),
        ("Usage Guide", create_usage_guide),
    ]

    passed_steps = 0
    total_steps = len(setup_steps)

    for step_name, step_func in setup_steps:
        print(f"\n📋 {step_name}")
        print("-" * (len(step_name) + 4))

        if step_func():
            passed_steps += 1
        else:
            print_status(f"Setup step failed: {step_name}", "error")
            break

    # Summary
    print(f"\n📊 Setup Results: {passed_steps}/{total_steps} steps completed")

    if passed_steps == total_steps:
        print_status("🎉 PyTaskAI CLI setup completed successfully!", "success")

        print("\n🎯 Next Steps:")
        print("1. Start using the CLI: python3 pytaskai_minimal.py list")
        print("2. Source aliases: source .pytaskai_aliases")
        print("3. Read the guide: cat CLI_USAGE_GUIDE.md")
        print("4. For advanced features: pip install fastmcp rich")

        return 0
    else:
        print_status("⚠️ Setup incomplete. Check errors above.", "warning")
        return 1


if __name__ == "__main__":
    sys.exit(main())
