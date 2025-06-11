"""
PyTaskAI - Centralized Prompt Templates

This package contains AI prompt templates for task generation, research,
best practices, and task expansion with research integration support.
"""

from .add_task_prompt import (
    create_add_task_prompt,
    create_simple_add_task_prompt,
    validate_add_task_response,
)

from .lts_research_prompt import (
    create_lts_research_prompt,
    create_dependency_research_prompt,
    create_migration_research_prompt,
    validate_lts_research_response,
    RESEARCH_SYSTEM_PROMPT,
    RESEARCH_LTS_VERSIONS_PROMPT,
)

from .best_practices_prompt import (
    create_best_practices_prompt,
    create_code_review_prompt,
    create_architecture_review_prompt,
    validate_best_practices_response,
)

from .expand_task_prompt import (
    create_expand_task_prompt,
    create_simple_expand_task_prompt,
    create_complexity_based_expansion_prompt,
    validate_expand_task_response,
)

from .json_schema_helpers import (
    get_json_output_instructions,
    get_task_json_schema,
    get_subtasks_json_schema,
    get_research_json_schema,
)

__version__ = "0.1.0"
__author__ = "PyTaskAI Team"

# Import advanced functions
from .lts_research_prompt import (
    get_lts_research_system_prompt,
    get_lts_research_user_prompt,
    get_lts_compatibility_prompt,
)

from .best_practices_prompt import (
    get_best_practices_system_prompt,
    get_best_practices_user_prompt,
    get_domain_specific_best_practices_prompt,
    get_compliance_best_practices_prompt,
)

# Prompt template registry for easy access
PROMPT_TEMPLATES = {
    "add_task": {
        "comprehensive": create_add_task_prompt,
        "simple": create_simple_add_task_prompt,
        "validator": validate_add_task_response,
    },
    "lts_research": {
        "comprehensive": create_lts_research_prompt,
        "dependency": create_dependency_research_prompt,
        "migration": create_migration_research_prompt,
        "system_prompt": get_lts_research_system_prompt,
        "user_prompt": get_lts_research_user_prompt,
        "compatibility": get_lts_compatibility_prompt,
        "validator": validate_lts_research_response,
    },
    "best_practices": {
        "comprehensive": create_best_practices_prompt,
        "code_review": create_code_review_prompt,
        "architecture": create_architecture_review_prompt,
        "system_prompt": get_best_practices_system_prompt,
        "user_prompt": get_best_practices_user_prompt,
        "domain_specific": get_domain_specific_best_practices_prompt,
        "compliance": get_compliance_best_practices_prompt,
        "validator": validate_best_practices_response,
    },
    "expand_task": {
        "comprehensive": create_expand_task_prompt,
        "simple": create_simple_expand_task_prompt,
        "complexity_based": create_complexity_based_expansion_prompt,
        "validator": validate_expand_task_response,
    },
    "json_schema": {
        "task": get_task_json_schema,
        "subtasks": get_subtasks_json_schema,
        "research": get_research_json_schema,
        "custom": get_json_output_instructions,
    },
}


def get_prompt_template(category: str, template_type: str = "comprehensive"):
    """
    Get a prompt template function by category and type.

    Args:
        category: Prompt category ('add_task', 'lts_research', 'best_practices', 'expand_task')
        template_type: Template type ('comprehensive', 'simple', etc.)

    Returns:
        Prompt template function or None if not found
    """
    return PROMPT_TEMPLATES.get(category, {}).get(template_type)


def get_validator(category: str):
    """
    Get a response validator function by category.

    Args:
        category: Prompt category

    Returns:
        Validator function or None if not found
    """
    return PROMPT_TEMPLATES.get(category, {}).get("validator")


def list_available_templates():
    """
    List all available prompt templates.

    Returns:
        Dictionary of available templates by category
    """
    return {
        category: list(templates.keys())
        for category, templates in PROMPT_TEMPLATES.items()
    }


__all__ = [
    # Add task prompts
    "create_add_task_prompt",
    "create_simple_add_task_prompt",
    "validate_add_task_response",
    # LTS research prompts
    "create_lts_research_prompt",
    "create_dependency_research_prompt",
    "create_migration_research_prompt",
    "validate_lts_research_response",
    "get_lts_research_system_prompt",
    "get_lts_research_user_prompt",
    "get_lts_compatibility_prompt",
    # Best practices prompts
    "create_best_practices_prompt",
    "create_code_review_prompt",
    "create_architecture_review_prompt",
    "validate_best_practices_response",
    "get_best_practices_system_prompt",
    "get_best_practices_user_prompt",
    "get_domain_specific_best_practices_prompt",
    "get_compliance_best_practices_prompt",
    # Expand task prompts
    "create_expand_task_prompt",
    "create_simple_expand_task_prompt",
    "create_complexity_based_expansion_prompt",
    "validate_expand_task_response",
    # JSON schema helpers
    "get_json_output_instructions",
    "get_task_json_schema",
    "get_subtasks_json_schema",
    "get_research_json_schema",
    # Utility functions
    "get_prompt_template",
    "get_validator",
    "list_available_templates",
    "PROMPT_TEMPLATES",
]
