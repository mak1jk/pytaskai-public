"""
PyTaskAI - Utilities Module

Core utilities for task persistence, file management, and data operations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import logging
from contextlib import contextmanager

from shared.models import Task, SubTask, TaskStatus


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

DEFAULT_DATA_DIR = ".pytaskai"
DEFAULT_TASKS_FILE = "tasks.json"
DEFAULT_TASKS_DIR = "tasks"
DEFAULT_USAGE_DIR = "usage"
DEFAULT_REPORTS_DIR = "reports"

# File backup settings
MAX_BACKUP_FILES = 5
BACKUP_EXTENSION = ".backup"


# =============================================================================
# PATH MANAGEMENT
# =============================================================================


def get_data_directory(project_root: str = ".") -> Path:
    """Get the PyTaskAI data directory path"""
    data_dir = os.getenv("PYTASKAI_DATA_DIR", DEFAULT_DATA_DIR)
    return Path(project_root) / data_dir


def get_tasks_file_path(project_root: str = ".") -> Path:
    """Get the main tasks.json file path"""
    return get_data_directory(project_root) / DEFAULT_TASKS_DIR / DEFAULT_TASKS_FILE


def get_individual_task_file_path(task_id: int, project_root: str = ".") -> Path:
    """Get the individual task file path"""
    return (
        get_data_directory(project_root) / DEFAULT_TASKS_DIR / f"task_{task_id:03d}.txt"
    )


def get_usage_directory(project_root: str = ".") -> Path:
    """Get the usage tracking directory"""
    return get_data_directory(project_root) / DEFAULT_USAGE_DIR


def get_reports_directory(project_root: str = ".") -> Path:
    """Get the reports directory"""
    return get_data_directory(project_root) / DEFAULT_REPORTS_DIR


def ensure_directories_exist(project_root: str = ".") -> None:
    """Ensure all required directories exist"""
    directories = [
        get_data_directory(project_root),
        get_data_directory(project_root) / DEFAULT_TASKS_DIR,
        get_usage_directory(project_root),
        get_reports_directory(project_root),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


# =============================================================================
# BACKUP MANAGEMENT
# =============================================================================


def create_backup(file_path: Path) -> bool:
    """Create a backup of the file before modifying it"""
    if not file_path.exists():
        return True

    try:
        backup_path = file_path.with_suffix(f"{file_path.suffix}{BACKUP_EXTENSION}")

        # If backup already exists, rotate backups
        if backup_path.exists():
            _rotate_backups(backup_path)

        # Create new backup
        import shutil

        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return False


def _rotate_backups(backup_path: Path) -> None:
    """Rotate backup files, keeping only the most recent ones"""
    base_path = backup_path.with_suffix(
        backup_path.suffix.replace(BACKUP_EXTENSION, "")
    )
    backup_pattern = f"{base_path.name}*{BACKUP_EXTENSION}*"

    # Find existing backup files
    backup_files = list(backup_path.parent.glob(backup_pattern))
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Remove old backups
    for old_backup in backup_files[MAX_BACKUP_FILES - 1 :]:
        try:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup}")
        except Exception as e:
            logger.warning(f"Failed to remove old backup {old_backup}: {e}")


@contextmanager
def safe_file_write(file_path: Path, make_backup: bool = True):
    """Context manager for safe file writing with backup"""
    if make_backup:
        create_backup(file_path)

    temp_path = file_path.with_suffix(".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            yield f

        # Atomic move
        temp_path.replace(file_path)
        logger.debug(f"Successfully wrote file: {file_path}")

    except Exception as e:
        # Cleanup temp file on error
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to write file {file_path}: {e}")
        raise


# =============================================================================
# TASK ID MANAGEMENT
# =============================================================================


def get_next_task_id(tasks: List[Task]) -> int:
    """Get the next available task ID"""
    if not tasks:
        return 1

    max_id = max(task.id for task in tasks)
    return max_id + 1


def get_next_subtask_id(parent_task: Task) -> int:
    """Get the next available subtask ID within a parent task"""
    if not parent_task.subtasks:
        return 1

    max_subtask_id = max(subtask.id for subtask in parent_task.subtasks)
    return max_subtask_id + 1


def find_task_by_id(tasks: List[Task], task_id: int) -> Optional[Task]:
    """Find a task by its ID"""
    for task in tasks:
        if task.id == task_id:
            return task
    return None


def find_subtask_by_id(
    tasks: List[Task], parent_task_id: int, subtask_id: int
) -> Optional[Tuple[Task, SubTask]]:
    """Find a subtask by parent task ID and subtask ID"""
    parent_task = find_task_by_id(tasks, parent_task_id)
    if not parent_task:
        return None

    for subtask in parent_task.subtasks:
        if subtask.id == subtask_id:
            return parent_task, subtask

    return None


# =============================================================================
# MAIN PERSISTENCE FUNCTIONS
# =============================================================================


def load_tasks(project_root: str = ".") -> List[Task]:
    """Load tasks from SQLite database"""
    try:
        from .database import get_db_manager

        # Get database manager
        db_manager = get_db_manager(project_root)

        # Get all tasks as dictionaries
        tasks_data = db_manager.get_all_tasks(include_subtasks=True)

        # Convert to Task objects
        tasks = []
        for task_data in tasks_data:
            try:
                task = Task(**task_data)
                tasks.append(task)
            except Exception as e:
                logger.error(
                    f"Failed to parse task {task_data.get('id', 'unknown')}: {e}"
                )
                continue

        logger.info(f"Loaded {len(tasks)} tasks from SQLite database")
        return tasks

    except Exception as e:
        logger.error(f"Failed to load tasks from database: {e}")
        # Fall back to JSON if database fails
        return _load_tasks_from_json_fallback(project_root)


def _load_tasks_from_json_fallback(project_root: str = ".") -> List[Task]:
    """Fallback function to load tasks from JSON file"""
    tasks_file = get_tasks_file_path(project_root)

    if not tasks_file.exists():
        logger.info(f"Tasks file not found: {tasks_file}. Returning empty list.")
        return []

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON formats
        if isinstance(data, dict) and "tasks" in data:
            tasks_data = data["tasks"]
        elif isinstance(data, list):
            tasks_data = data
        else:
            logger.error(f"Invalid tasks file format: {tasks_file}")
            return []

        # Validate and return Task objects
        tasks = []
        for task_data in tasks_data:
            try:
                task = Task(**task_data)
                tasks.append(task)
            except Exception as e:
                logger.error(
                    f"Failed to parse task {task_data.get('id', 'unknown')}: {e}"
                )
                continue

        logger.info(f"Loaded {len(tasks)} tasks from JSON fallback: {tasks_file}")
        return tasks

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in tasks file {tasks_file}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load tasks from {tasks_file}: {e}")
        return []


def save_tasks(tasks: List[Task], project_root: str = ".") -> bool:
    """Save tasks to SQLite database"""
    try:
        from .database import get_db_manager

        # Get database manager
        db_manager = get_db_manager(project_root)

        # This function is mainly used for bulk updates,
        # but for individual operations we'll use the database methods directly
        # For now, we'll handle it as individual updates/creates

        saved_count = 0
        for task in tasks:
            task_dict = task.model_dump()

            # Check if task exists
            existing_task = db_manager.get_task_by_id(task.id)

            if existing_task:
                # Update existing task
                if db_manager.update_task(task.id, task_dict):
                    saved_count += 1
            else:
                # Create new task
                if db_manager.create_task(task_dict):
                    saved_count += 1

        # Also generate individual task files
        generate_individual_task_files(tasks, project_root)

        logger.info(f"Saved {saved_count}/{len(tasks)} tasks to SQLite database")
        return saved_count == len(tasks)

    except Exception as e:
        logger.error(f"Failed to save tasks to database: {e}")
        # Fall back to JSON saving if database fails
        return _save_tasks_to_json_fallback(tasks, project_root)


def _save_tasks_to_json_fallback(tasks: List[Task], project_root: str = ".") -> bool:
    """Fallback function to save tasks to JSON file"""
    ensure_directories_exist(project_root)
    tasks_file = get_tasks_file_path(project_root)

    try:
        # Convert tasks to dictionaries
        tasks_data = []
        for task in tasks:
            task_dict = task.model_dump()
            # Ensure datetime objects are properly serialized
            for key, value in task_dict.items():
                if isinstance(value, datetime):
                    task_dict[key] = value.isoformat()

            # Handle subtasks datetime serialization
            if "subtasks" in task_dict:
                for subtask in task_dict["subtasks"]:
                    for key, value in subtask.items():
                        if isinstance(value, datetime):
                            subtask[key] = value.isoformat()

            tasks_data.append(task_dict)

        # Create the JSON structure
        json_data = {
            "tasks": tasks_data,
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "total_tasks": len(tasks_data),
                "generator": "PyTaskAI",
            },
        }

        # Write file safely
        with safe_file_write(tasks_file, make_backup=True) as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(tasks)} tasks to JSON fallback: {tasks_file}")

        # Also generate individual task files
        generate_individual_task_files(tasks, project_root)

        return True

    except Exception as e:
        logger.error(f"Failed to save tasks to {tasks_file}: {e}")
        return False


def generate_individual_task_files(tasks: List[Task], project_root: str = ".") -> bool:
    """Generate individual markdown files for each task"""
    try:
        tasks_dir = get_data_directory(project_root) / DEFAULT_TASKS_DIR

        # Clean up old task files
        for old_file in tasks_dir.glob("task_*.txt"):
            old_file.unlink()

        # Generate new task files
        for task in tasks:
            task_file = get_individual_task_file_path(task.id, project_root)

            # Generate task content
            content = generate_task_file_content(task)

            with open(task_file, "w", encoding="utf-8") as f:
                f.write(content)

        logger.info(f"Generated {len(tasks)} individual task files")
        return True

    except Exception as e:
        logger.error(f"Failed to generate individual task files: {e}")
        return False


def generate_task_file_content(task: Task) -> str:
    """Generate markdown content for an individual task file"""
    content = f"""# Task ID: {task.id}
# Title: {task.title}
# Status: {task.status}
# Dependencies: {', '.join(map(str, task.dependencies)) if task.dependencies else 'None'}
# Priority: {task.priority}
# Description: {task.description}

## Details:
{task.details if task.details else 'No additional details provided.'}

## Test Strategy:
{task.test_strategy if task.test_strategy else 'No test strategy defined.'}
"""

    # Add AI metadata if present
    if task.generated_by_ai:
        content += f"""
## AI Generation Info:
- Generated by AI: Yes
- Model used: {task.ai_model_used or 'Unknown'}
- Research mode: {'Yes' if task.research_used else 'No'}
- Complexity score: {task.complexity_score or 'Not assessed'}
"""

    # Add subtasks if present
    if task.subtasks:
        content += f"""
## Subtasks ({len(task.subtasks)} total):
"""
        for subtask in task.subtasks:
            status_emoji = (
                "✅"
                if subtask.status == TaskStatus.DONE
                else "⏳" if subtask.status == TaskStatus.IN_PROGRESS else "📋"
            )
            content += f"""
### {subtask.id}. {subtask.title} {status_emoji}
**Status:** {subtask.status}
**Description:** {subtask.description}
**Details:** {subtask.details if subtask.details else 'No details'}
**Test Strategy:** {subtask.test_strategy if subtask.test_strategy else 'No test strategy'}
"""

    # Add timestamps
    content += f"""
## Metadata:
- Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else 'Unknown'}
- Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else 'Unknown'}
"""
    if task.completed_at:
        content += f"- Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    return content


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def validate_tasks_file(project_root: str = ".") -> Dict[str, Any]:
    """Validate the tasks.json file and return validation report"""
    tasks_file = get_tasks_file_path(project_root)
    report = {
        "is_valid": False,
        "file_exists": False,
        "is_readable": False,
        "json_valid": False,
        "tasks_count": 0,
        "issues": [],
        "warnings": [],
    }

    # Check if file exists
    if not tasks_file.exists():
        report["issues"].append(f"Tasks file not found: {tasks_file}")
        return report

    report["file_exists"] = True

    # Check if file is readable
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        report["is_readable"] = True
        report["json_valid"] = True
    except json.JSONDecodeError as e:
        report["issues"].append(f"Invalid JSON: {e}")
        return report
    except Exception as e:
        report["issues"].append(f"File read error: {e}")
        return report

    # Validate structure
    if isinstance(data, dict) and "tasks" in data:
        tasks_data = data["tasks"]
    elif isinstance(data, list):
        tasks_data = data
    else:
        report["issues"].append(
            "Invalid file structure: expected tasks array or object with tasks property"
        )
        return report

    report["tasks_count"] = len(tasks_data)

    # Validate individual tasks
    task_ids = set()
    for i, task_data in enumerate(tasks_data):
        try:
            task = Task(**task_data)

            # Check for duplicate IDs
            if task.id in task_ids:
                report["issues"].append(f"Duplicate task ID: {task.id}")
            task_ids.add(task.id)

            # Validate dependencies
            for dep_id in task.dependencies:
                if dep_id not in task_ids and dep_id > task.id:
                    report["warnings"].append(
                        f"Task {task.id} depends on future task {dep_id}"
                    )

        except Exception as e:
            report["issues"].append(f"Invalid task at index {i}: {e}")

    report["is_valid"] = len(report["issues"]) == 0
    return report


def get_tasks_statistics(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about the tasks list"""
    if not tasks:
        return {"total": 0}

    stats = {
        "total": len(tasks),
        "by_status": {},
        "by_priority": {},
        "with_subtasks": 0,
        "total_subtasks": 0,
        "with_dependencies": 0,
        "ai_generated": 0,
        "avg_complexity": 0.0,
        "completion_percentage": 0.0,
    }

    # Count by status and priority
    for task in tasks:
        # Status counts
        status = task.get("status", "pending")
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # Priority counts
        priority = task.get("priority", "medium")
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

        # Other statistics
        subtasks = task.get("subtasks", [])
        if subtasks:
            stats["with_subtasks"] += 1
            stats["total_subtasks"] += len(subtasks)

        dependencies = task.get("dependencies", [])
        if dependencies:
            stats["with_dependencies"] += 1

        if task.get("generated_by_ai", False):
            stats["ai_generated"] += 1

    # Calculate averages
    complexity_scores = [
        task.get("complexity_score")
        for task in tasks
        if task.get("complexity_score") is not None
    ]
    if complexity_scores:
        stats["avg_complexity"] = sum(complexity_scores) / len(complexity_scores)

    # Calculate completion percentage
    done_tasks = stats["by_status"].get("done", 0)
    stats["completion_percentage"] = (done_tasks / len(tasks)) * 100 if tasks else 0

    return stats


# =============================================================================
# MIGRATION AND MAINTENANCE
# =============================================================================


def migrate_tasks_format(project_root: str = ".") -> bool:
    """Migrate tasks from old format to new format if needed"""
    tasks_file = get_tasks_file_path(project_root)

    if not tasks_file.exists():
        return True

    try:
        # Load current data
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if migration is needed
        if isinstance(data, dict) and "metadata" in data:
            logger.info("Tasks file already in current format")
            return True

        # Migrate from old format
        if isinstance(data, list):
            tasks_data = data
        elif isinstance(data, dict) and "tasks" in data:
            tasks_data = data["tasks"]
        else:
            logger.error("Unknown tasks file format")
            return False

        # Load and save to update format
        tasks = []
        for task_data in tasks_data:
            try:
                task = Task(**task_data)
                tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to migrate task: {e}")
                continue

        # Save in new format
        success = save_tasks(tasks, project_root)
        if success:
            logger.info(f"Successfully migrated {len(tasks)} tasks to new format")

        return success

    except Exception as e:
        logger.error(f"Failed to migrate tasks format: {e}")
        return False


def cleanup_orphaned_files(project_root: str = ".") -> int:
    """Clean up orphaned task files that don't have corresponding tasks"""
    tasks = load_tasks(project_root)
    task_ids = {task.id for task in tasks}

    tasks_dir = get_data_directory(project_root) / DEFAULT_TASKS_DIR
    orphaned_count = 0

    # Find orphaned task files
    for task_file in tasks_dir.glob("task_*.txt"):
        try:
            # Extract task ID from filename
            filename = task_file.stem
            if filename.startswith("task_"):
                task_id_str = filename[5:]  # Remove "task_" prefix
                task_id = int(task_id_str)

                if task_id not in task_ids:
                    task_file.unlink()
                    orphaned_count += 1
                    logger.info(f"Removed orphaned task file: {task_file}")

        except (ValueError, OSError) as e:
            logger.warning(f"Error processing task file {task_file}: {e}")

    return orphaned_count
