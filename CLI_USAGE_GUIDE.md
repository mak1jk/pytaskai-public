# PyTaskAI CLI Usage Guide

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
