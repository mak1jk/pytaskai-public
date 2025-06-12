"""
PyTaskAI - Claude Code Integration Setup

Generates .cursor/rules/*.mdc and .windsurfrules files with MCP tool instructions
for seamless Claude Code integration with PyTaskAI MCP server.
"""

import os
import json
import inspect
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import argparse
import logging

# Configure logging
logger = logging.getLogger(__name__)


def generate_mcp_tool_instructions(mcp_instance) -> str:
    """
    Analizza tutti i tool registrati e genera istruzioni dettagliate per Claude Code.

    Args:
        mcp_instance: Istanza FastMCP con tool registrati

    Returns:
        Stringa contenente istruzioni formattate per Claude Code
    """
    try:
        # Get registered tools from FastMCP instance
        tools = []

        # Try to access _registered_tools attribute or similar
        if hasattr(mcp_instance, "_tools"):
            tools = mcp_instance._tools
        elif hasattr(mcp_instance, "_registered_tools"):
            tools = mcp_instance._registered_tools
        elif hasattr(mcp_instance, "tools"):
            tools = mcp_instance.tools

        if not tools:
            logger.warning("No tools found in MCP instance")
            return "# No MCP tools registered\n"

        instructions = []
        instructions.append("# PyTaskAI MCP Tools Reference\n")
        instructions.append(
            "The following MCP tools are available for task management:\n"
        )

        for tool_name, tool_func in tools.items():
            instructions.append(f"## {tool_name}\n")

            # Get function docstring
            doc = inspect.getdoc(tool_func) or "No description available"
            instructions.append(f"**Description:** {doc.split('.')[0]}.\n")

            # Get function signature
            sig = inspect.signature(tool_func)

            instructions.append("**Parameters:**")
            for param_name, param in sig.parameters.items():
                param_type = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else "Any"
                )
                default = (
                    param.default
                    if param.default != inspect.Parameter.empty
                    else "Required"
                )
                instructions.append(f"- `{param_name}` ({param_type}): {default}")

            instructions.append("")

            # Add usage example
            instructions.append("**Example Usage:**")
            instructions.append(f"```python")
            instructions.append(f"# {tool_name} example")
            param_examples = []
            for param_name, param in sig.parameters.items():
                if param_name == "project_root":
                    param_examples.append('project_root="/workspace"')
                elif "id" in param_name.lower():
                    param_examples.append(f'{param_name}="1"')
                elif "status" in param_name.lower():
                    param_examples.append(f'{param_name}="in-progress"')
                else:
                    param_examples.append(f'{param_name}="value"')

            example_call = f"{tool_name}({', '.join(param_examples)})"
            instructions.append(example_call)
            instructions.append("```\n")

        return "\n".join(instructions)

    except Exception as e:
        logger.error(f"Error generating MCP tool instructions: {e}")
        return f"# Error generating MCP tool instructions\n# {str(e)}\n"


def create_dev_workflow_template() -> str:
    """Template per dev_workflow.mdc"""
    return """---
description: "PyTaskAI Development Workflow Guidelines"
globs: ["**/*.py", "**/pyproject.toml", "**/README.md"]
alwaysApply: true
---

# PyTaskAI Development Workflow

## Code Style and Standards
- Follow PEP 8 for Python code formatting
- Use type hints for all function parameters and returns
- Write comprehensive docstrings for all functions and classes
- Use Pydantic models for data validation and serialization
- Prefer async/await patterns for I/O operations where applicable

## FastMCP Integration
- All MCP tools should be decorated with @mcp.tool()
- Tool functions must include comprehensive type hints
- Tool docstrings should explain parameters and return values clearly
- Error handling should return structured error responses
- Always validate project_root parameter existence

## Task Management Workflow
1. Use `list_tasks_tool` to view available tasks
2. Use `get_next_task_tool` to find the next recommended task
3. Set task status to "in-progress" before starting work
4. Update task progress with `update_task_tool` as needed
5. Set task status to "done" when completed
6. Use dependency validation before marking tasks complete

## Testing Strategy
- Create simple validation tests for each major feature
- Test both successful and error cases
- Use temporary directories for file operation tests
- Clean up test files and directories after tests
- Validate JSON schema compliance for task files

## Architecture Principles
- Modular design with clear separation of concerns
- Utility functions in dedicated modules
- MCP tools in task_manager.py
- Pydantic models in shared/models.py
- Claude Code integration in claude_code_setup.py
"""


def create_self_improve_template() -> str:
    """Template per self_improve.mdc"""
    return """---
description: "PyTaskAI Self-Improvement and Learning Guidelines"
globs: ["**/*.py", "**/*.md"]
alwaysApply: true
---

# PyTaskAI Self-Improvement Guidelines

## Learning from Code Patterns
When examining existing code:
- Analyze current naming conventions and follow them
- Study existing error handling patterns and replicate them
- Review how dependencies are managed throughout the codebase
- Understand the project's architectural decisions and maintain consistency

## Code Quality Improvements
- Identify repetitive code patterns and suggest refactoring
- Look for opportunities to improve error messages and user feedback
- Suggest performance optimizations for file I/O operations
- Recommend additional validation and safety checks

## Feature Enhancement Opportunities
- Identify missing error cases that should be handled
- Suggest additional tool parameters that would be useful
- Recommend logging improvements for better debugging
- Propose additional validation for data integrity

## Documentation Improvements
- Ensure all functions have clear, comprehensive docstrings
- Add inline comments for complex logic
- Maintain up-to-date README.md with current features
- Create usage examples for new MCP tools

## Testing and Validation
- Suggest edge cases that should be tested
- Recommend integration tests for MCP tool interactions
- Identify areas where additional validation would prevent errors
- Propose performance benchmarks for critical operations
"""


def create_project_specific_template(mcp_tools_instructions: str) -> str:
    """Template per project_specific_rules.mdc con istruzioni MCP"""
    return f"""---
description: "PyTaskAI Project-Specific Rules and MCP Tool Integration"
globs: ["**/*.py", "**/*.json", "**/*.md"]
alwaysApply: true
---

# PyTaskAI Project-Specific Rules

## Project Structure
```
/workspace/
├── mcp_server/          # FastMCP server implementation
│   ├── task_manager.py  # MCP tools for task management
│   ├── utils.py         # Persistence and utility functions
│   └── claude_code_setup.py  # Claude Code integration
├── shared/              # Shared models and schemas
│   ├── models.py        # Pydantic models for tasks and requests
│   └── schemas.py       # Extended UI and analytics models
├── tasks/               # Task management files
│   └── tasks.json       # Main task database
└── tests/               # Test files and validation
```

## Key Files and Their Purpose
- `mcp_server/task_manager.py`: Contains all MCP tools (@mcp.tool decorated functions)
- `mcp_server/utils.py`: File persistence, validation, and utility functions
- `shared/models.py`: Pydantic models for Task, SubTask, and AI integration
- `tasks/tasks.json`: Central task database with metadata
- `pyproject.toml`: Package configuration with PyTaskAI branding

## Task Management Data Model
Tasks use the following structure:
```json
{{
  "id": 1,
  "title": "Task Title",
  "description": "Task description",
  "status": "pending|in-progress|done|cancelled",
  "priority": "high|medium|low",
  "dependencies": [2, 3],
  "subtasks": [...]
}}
```

## MCP Tool Integration
This project provides MCP tools for task management. Always use the project_root parameter with absolute path "/workspace".

{mcp_tools_instructions}

## Development Guidelines
- Always use absolute paths starting with "/workspace"
- Validate task dependencies before marking tasks complete
- Create backups before modifying tasks.json
- Use structured error responses for all MCP tools
- Follow the existing naming convention (snake_case for functions, PascalCase for classes)

## Testing Requirements
- Test all MCP tools with valid and invalid inputs
- Validate JSON schema compliance
- Test file operations with temporary directories
- Ensure proper error handling and logging
"""


def init_claude_support(
    mcp_instance, project_root: str, include_windsurfrules: bool = True
) -> Dict[str, Any]:
    """
    Inizializza il supporto Claude Code creando file .cursor/rules e .windsurfrules.

    Args:
        mcp_instance: Istanza FastMCP con tool registrati
        project_root: Path assoluto alla directory del progetto
        include_windsurfrules: Se generare anche .windsurfrules

    Returns:
        Dict con risultati dell'operazione
    """
    try:
        logger.info(f"Initializing Claude Code support for project: {project_root}")

        # Create .cursor/rules directory
        cursor_rules_dir = os.path.join(project_root, ".cursor", "rules")
        os.makedirs(cursor_rules_dir, exist_ok=True)

        # Generate MCP tool instructions
        mcp_tools_instructions = generate_mcp_tool_instructions(mcp_instance)

        # Create template files
        templates = {
            "dev_workflow.mdc": create_dev_workflow_template(),
            "self_improve.mdc": create_self_improve_template(),
            "project_specific_rules.mdc": create_project_specific_template(
                mcp_tools_instructions
            ),
        }

        created_files = []

        # Write .mdc files
        for filename, content in templates.items():
            file_path = os.path.join(cursor_rules_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(file_path)
            logger.info(f"Created: {file_path}")

        # Include existing CLAUDE.md content if available
        claude_md_path = os.path.join(project_root, "CLAUDE.md")
        if os.path.exists(claude_md_path):
            with open(claude_md_path, "r", encoding="utf-8") as f:
                claude_content = f.read()

            # Append to project_specific_rules.mdc
            project_rules_path = os.path.join(
                cursor_rules_dir, "project_specific_rules.mdc"
            )
            with open(project_rules_path, "a", encoding="utf-8") as f:
                f.write("\\n\\n## Existing CLAUDE.md Content\\n")
                f.write(claude_content)

            logger.info("Incorporated existing CLAUDE.md content")

        # Generate .windsurfrules if requested
        windsurfrules_path = None
        if include_windsurfrules:
            windsurfrules_content = []
            windsurfrules_content.append("# PyTaskAI - Claude Code Integration Rules")
            windsurfrules_content.append(f"# Generated on {datetime.now().isoformat()}")
            windsurfrules_content.append("")

            for filename in [
                "dev_workflow.mdc",
                "self_improve.mdc",
                "project_specific_rules.mdc",
            ]:
                file_path = os.path.join(cursor_rules_dir, filename)
                if os.path.exists(file_path):
                    windsurfrules_content.append(f"## === {filename} ===")
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Remove YAML front matter for .windsurfrules
                        if content.startswith("---"):
                            lines = content.split("\\n")
                            yaml_end = -1
                            for i, line in enumerate(lines[1:], 1):
                                if line.strip() == "---":
                                    yaml_end = i
                                    break
                            if yaml_end > 0:
                                content = "\\n".join(lines[yaml_end + 1 :])
                        windsurfrules_content.append(content)
                    windsurfrules_content.append("")

            windsurfrules_path = os.path.join(project_root, ".windsurfrules")
            with open(windsurfrules_path, "w", encoding="utf-8") as f:
                f.write("\\n".join(windsurfrules_content))
            created_files.append(windsurfrules_path)
            logger.info(f"Created: {windsurfrules_path}")

        result = {
            "success": True,
            "created_files": created_files,
            "cursor_rules_dir": cursor_rules_dir,
            "mcp_tools_count": len(mcp_tools_instructions.split("##")) - 1,
            "project_root": project_root,
        }

        logger.info(f"Claude Code support initialization completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error initializing Claude Code support: {e}")
        return {
            "success": False,
            "error": str(e),
            "created_files": [],
            "project_root": project_root,
        }


def main():
    """CLI command for init-claude functionality"""
    parser = argparse.ArgumentParser(
        description="Initialize Claude Code support for PyTaskAI"
    )
    parser.add_argument(
        "--project-root", default="/workspace", help="Project root directory"
    )
    parser.add_argument(
        "--no-windsurfrules", action="store_true", help="Skip .windsurfrules generation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    try:
        # Import and initialize MCP instance for tool introspection
        from .task_manager import mcp

        result = init_claude_support(
            mcp_instance=mcp,
            project_root=args.project_root,
            include_windsurfrules=not args.no_windsurfrules,
        )

        if result["success"]:
            print("✅ Claude Code support initialized successfully!")
            print(f"📁 Files created in: {result['cursor_rules_dir']}")
            for file_path in result["created_files"]:
                print(f"   - {os.path.basename(file_path)}")
            if result.get("mcp_tools_count", 0) > 0:
                print(f"🔧 {result['mcp_tools_count']} MCP tools documented")
        else:
            print(f"❌ Failed to initialize Claude Code support: {result['error']}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
