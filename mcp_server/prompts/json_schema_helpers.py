"""
PyTaskAI - JSON Schema Helpers

Helper functions for generating explicit JSON schema instructions in prompts.
Ensures all AI responses follow structured formats for reliable parsing.
"""

from typing import Dict, List, Any, Optional


def get_json_output_instructions(
    schema_name: str,
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
    example_values: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate explicit JSON output format instructions.

    Args:
        schema_name: Name of the JSON schema/object
        required_fields: List of required field names
        optional_fields: List of optional field names
        example_values: Example values for fields

    Returns:
        Formatted JSON output instructions
    """

    optional_fields = optional_fields or []
    example_values = example_values or {}

    instructions = [
        "## JSON Output Format Requirements",
        "",
        f"**CRITICAL:** Your response must be valid JSON only. No additional text before or after the JSON.",
        "",
        f"### {schema_name} Schema",
        "",
        "```json",
        "{",
    ]

    # Add required fields
    for field in required_fields:
        field_type = get_field_type_hint(field, example_values.get(field))
        example_val = get_example_value(field, example_values.get(field), field_type)
        instructions.append(
            f'  "{field}": {example_val},  // REQUIRED: {get_field_description(field)}'
        )

    # Add optional fields
    for field in optional_fields:
        field_type = get_field_type_hint(field, example_values.get(field))
        example_val = get_example_value(field, example_values.get(field), field_type)
        instructions.append(
            f'  "{field}": {example_val},  // OPTIONAL: {get_field_description(field)}'
        )

    # Remove trailing comma from last field
    if instructions[-1].endswith(","):
        instructions[-1] = instructions[-1][:-1]

    instructions.extend(
        [
            "}",
            "```",
            "",
            "### Validation Rules",
            "- All required fields must be present and non-null",
            "- String fields must not be empty unless explicitly allowed",
            "- Numeric fields must be valid numbers within specified ranges",
            "- Array fields must contain valid elements of the specified type",
            "- Enum fields must use exactly one of the allowed values",
            "",
            "### Response Format",
            "- Return ONLY the JSON object, no markdown formatting",
            "- Ensure all JSON syntax is correct (proper quotes, commas, brackets)",
            "- Validate your JSON before responding",
            "- Do not include comments in the actual JSON response",
        ]
    )

    return "\\n".join(instructions)


def get_field_type_hint(field_name: str, example_value: Any = None) -> str:
    """Get type hint for a field based on name and example."""
    if example_value is not None:
        if isinstance(example_value, str):
            return "string"
        elif isinstance(example_value, int):
            return "integer"
        elif isinstance(example_value, float):
            return "number"
        elif isinstance(example_value, bool):
            return "boolean"
        elif isinstance(example_value, list):
            return "array"
        elif isinstance(example_value, dict):
            return "object"

    # Infer from field name
    if "count" in field_name or "score" in field_name or "hours" in field_name:
        return "number"
    elif "is_" in field_name or field_name.endswith("_enabled"):
        return "boolean"
    elif field_name.endswith("s") or "list" in field_name:
        return "array"
    else:
        return "string"


def get_example_value(
    field_name: str, provided_example: Any = None, field_type: str = "string"
) -> str:
    """Get formatted example value for JSON output."""
    if provided_example is not None:
        if isinstance(provided_example, str):
            return f'"{provided_example}"'
        elif isinstance(provided_example, (int, float, bool)):
            return (
                str(provided_example).lower()
                if isinstance(provided_example, bool)
                else str(provided_example)
            )
        elif isinstance(provided_example, list):
            return str(provided_example).replace("'", '"')
        elif isinstance(provided_example, dict):
            import json

            return json.dumps(provided_example)

    # Generate reasonable defaults based on field name and type
    if field_type == "boolean":
        return "true"
    elif field_type == "integer":
        if "score" in field_name:
            return "7"
        elif "count" in field_name:
            return "5"
        else:
            return "1"
    elif field_type == "number":
        if "hours" in field_name:
            return "4.5"
        else:
            return "2.5"
    elif field_type == "array":
        if "technologies" in field_name:
            return '["Python", "FastAPI"]'
        elif "risks" in field_name or "factors" in field_name:
            return '["risk1", "risk2"]'
        else:
            return '["item1", "item2"]'
    elif field_type == "object":
        return '{"key": "value"}'
    else:
        # String type
        if "title" in field_name:
            return '"Clear, descriptive title"'
        elif "description" in field_name:
            return '"Detailed description of the item"'
        elif "summary" in field_name:
            return '"Brief summary of key points"'
        elif "version" in field_name:
            return '"1.0.0"'
        elif "status" in field_name:
            return '"pending"'
        else:
            return f'"Example {field_name.replace("_", " ")}"'


def get_field_description(field_name: str) -> str:
    """Get description for a field based on its name."""
    descriptions = {
        "title": "Clear, concise title describing the item",
        "description": "Detailed explanation of what needs to be done",
        "details": "Implementation details and technical requirements",
        "summary": "Executive summary of key findings and recommendations",
        "status": "Current status (pending, in-progress, done, etc.)",
        "priority": "Priority level (high, medium, low)",
        "estimated_hours": "Estimated time in hours to complete",
        "complexity_score": "Complexity rating from 1 (simple) to 10 (very complex)",
        "dependencies": "List of dependency IDs or requirements",
        "technologies": "List of technologies involved",
        "recommendations": "List of recommended actions or approaches",
        "risks": "List of potential risks or challenges",
        "benefits": "List of benefits or positive outcomes",
        "requirements": "List of requirements or prerequisites",
        "test_strategy": "Approach for testing and validation",
        "acceptance_criteria": "Criteria that must be met for completion",
        "deliverables": "Expected outputs or artifacts",
        "timeline": "Expected timeline or schedule",
        "resources": "Required resources or references",
    }

    # Try exact match first
    if field_name in descriptions:
        return descriptions[field_name]

    # Try partial matches
    for key, desc in descriptions.items():
        if key in field_name or field_name in key:
            return desc

    # Default description
    return f"Value for {field_name.replace('_', ' ')}"


def get_task_json_schema() -> str:
    """Get JSON schema instructions for task objects."""
    return get_json_output_instructions(
        schema_name="Task Object",
        required_fields=["title", "description", "details", "test_strategy"],
        optional_fields=[
            "estimated_hours",
            "complexity_score",
            "dependencies",
            "priority",
        ],
        example_values={
            "title": "Implement User Authentication",
            "description": "Create secure user authentication system",
            "details": "Implement OAuth2 with JWT tokens, session management, and password policies",
            "test_strategy": "Unit tests for auth logic, integration tests for endpoints, security testing",
            "estimated_hours": 16.0,
            "complexity_score": 7,
            "dependencies": [1, 2],
            "priority": "high",
        },
    )


def get_subtasks_json_schema() -> str:
    """Get JSON schema instructions for subtask arrays."""
    return get_json_output_instructions(
        schema_name="Subtasks Array",
        required_fields=["expansion_summary", "total_subtasks", "subtasks"],
        optional_fields=[
            "estimated_total_hours",
            "critical_path",
            "parallel_opportunities",
        ],
        example_values={
            "expansion_summary": "Breaking down authentication into 6 logical implementation steps",
            "total_subtasks": 6,
            "subtasks": [
                {
                    "id": 1,
                    "title": "Setup OAuth2 Configuration",
                    "description": "Configure OAuth2 provider and client settings",
                    "estimated_hours": 3.0,
                }
            ],
            "estimated_total_hours": 18.0,
            "critical_path": [1, 3, 5],
            "parallel_opportunities": ["Subtasks 2 and 4 can be done in parallel"],
        },
    )


def get_research_json_schema() -> str:
    """Get JSON schema instructions for research responses."""
    return get_json_output_instructions(
        schema_name="Research Results",
        required_fields=["research_summary", "findings", "recommendations"],
        optional_fields=["technologies_analyzed", "confidence_level", "sources"],
        example_values={
            "research_summary": "Comprehensive analysis of LTS versions and best practices",
            "findings": [
                {
                    "category": "LTS Versions",
                    "details": "Python 3.11 is current LTS with support until 2027",
                    "impact": "High stability for production use",
                }
            ],
            "recommendations": [
                {
                    "action": "Upgrade to Python 3.11",
                    "priority": "High",
                    "timeline": "2-3 weeks",
                    "effort": "Medium",
                }
            ],
            "technologies_analyzed": ["Python", "FastAPI", "PostgreSQL"],
            "confidence_level": "High",
            "sources": ["Official Python documentation", "Industry surveys"],
        },
    )


# Export functions for use in prompt templates
__all__ = [
    "get_json_output_instructions",
    "get_field_type_hint",
    "get_example_value",
    "get_field_description",
    "get_task_json_schema",
    "get_subtasks_json_schema",
    "get_research_json_schema",
]
