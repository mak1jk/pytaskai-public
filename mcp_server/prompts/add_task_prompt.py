"""
PyTaskAI - Add Task Prompt Templates

Centralized prompts for AI-powered task generation with research integration.
These prompts are used by the AI service to generate comprehensive, actionable tasks.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


def create_add_task_prompt(
    user_prompt: str,
    dependencies: List[int] = None,
    priority: str = "medium",
    use_research: bool = False,
    use_lts_deps: bool = True,
    research_findings: Optional[str] = None,
    existing_tasks_context: Optional[List[Dict[str, Any]]] = None,
    project_context: Optional[str] = None,
) -> str:
    """
    Generate a comprehensive prompt for AI task creation.

    Args:
        user_prompt: The user's description of what they want to accomplish
        dependencies: List of task IDs this task depends on
        priority: Priority level (high, medium, low)
        use_research: Whether to incorporate research findings
        use_lts_deps: Whether to prefer LTS versions of dependencies
        research_findings: Research findings to incorporate (when use_research=True)
        existing_tasks_context: Context about existing tasks in the project
        project_context: Overall project context and goals

    Returns:
        Formatted prompt string for AI task generation
    """

    dependencies = dependencies or []

    # Base prompt structure
    prompt_parts = [
        "# PyTaskAI Task Generation Request",
        "",
        "You are an expert project manager and software architect helping to create a detailed, actionable task.",
        "",
        "## User Request",
        f"**User wants to accomplish:** {user_prompt}",
        f"**Priority Level:** {priority}",
        f"**Dependencies:** {dependencies if dependencies else 'None'}",
        f"**LTS Preference:** {'Prefer LTS/stable versions' if use_lts_deps else 'Use latest versions'}",
        "",
    ]

    # Add project context if available
    if project_context:
        prompt_parts.extend(["## Project Context", project_context, ""])

    # Add existing tasks context if available
    if existing_tasks_context:
        prompt_parts.extend(
            [
                "## Existing Tasks Context",
                "Consider these existing tasks to avoid duplication and ensure proper integration:",
                "",
            ]
        )

        for task in existing_tasks_context[:5]:  # Limit to 5 most relevant tasks
            prompt_parts.append(
                f"- **Task {task.get('id', '?')}:** {task.get('title', 'Unknown')} ({task.get('status', 'unknown')})"
            )

        if len(existing_tasks_context) > 5:
            prompt_parts.append(f"... and {len(existing_tasks_context) - 5} more tasks")

        prompt_parts.append("")

    # Add research findings if available
    if use_research and research_findings:
        prompt_parts.extend(
            [
                "## Research Findings",
                "Incorporate these research findings into your task planning:",
                "",
                research_findings,
                "",
                "**Important:** Use the research findings to inform best practices, identify potential challenges, and suggest specific technologies or approaches.",
                "",
            ]
        )

    # Add detailed generation instructions
    prompt_parts.extend(
        [
            "## Task Generation Requirements",
            "",
            "Generate a comprehensive task with the following structure:",
            "",
            "### 1. Title",
            "- Clear, action-oriented title (max 80 characters)",
            "- Should clearly indicate what will be accomplished",
            "",
            "### 2. Description",
            "- Concise but comprehensive description (100-300 characters)",
            "- Explain the purpose and expected outcome",
            "",
            "### 3. Implementation Details",
            "- Specific, actionable steps to complete the task",
            "- Include technical considerations and requirements",
            "- Reference specific files, directories, or components when relevant",
            "- Consider integration with existing project structure",
            "",
        ]
    )

    # Add dependency-specific guidance
    if use_lts_deps:
        prompt_parts.extend(
            [
                "### 4. Technology Choices",
                "- Prefer stable, LTS (Long Term Support) versions of dependencies",
                "- Choose well-established libraries and frameworks",
                "- Avoid bleeding-edge or experimental technologies unless specifically required",
                "- Document version constraints and compatibility requirements",
                "",
            ]
        )
    else:
        prompt_parts.extend(
            [
                "### 4. Technology Choices",
                "- Use latest stable versions of dependencies when possible",
                "- Consider modern approaches and newest features",
                "- Balance innovation with project stability",
                "- Document any compatibility considerations",
                "",
            ]
        )

    # Add research-specific guidance
    if use_research:
        prompt_parts.extend(
            [
                "### 5. Research-Informed Decisions",
                "- Apply insights from the research findings above",
                "- Reference current best practices and industry standards",
                "- Consider security implications and performance requirements",
                "- Identify potential pitfalls and mitigation strategies",
                "",
            ]
        )

    # Add output format requirements
    prompt_parts.extend(
        [
            "### 6. Testing Strategy",
            "- Define how the task completion will be verified",
            "- Specify what tests or validation steps are needed",
            "- Include both functional and integration testing considerations",
            "",
            "## Output Format",
            "",
            "Provide your response as a JSON object with exactly these fields:",
            "",
            "```json",
            "{",
            '  "title": "Clear, action-oriented task title",',
            '  "description": "Comprehensive description of what needs to be done",',
            '  "details": "Detailed implementation steps and technical requirements",',
            '  "test_strategy": "How to verify the task is completed correctly",',
            '  "estimated_hours": 8.5,',
            '  "complexity_score": 6,',
            '  "key_technologies": ["technology1", "technology2"],',
            '  "risk_factors": ["potential risk 1", "potential risk 2"]',
            "}",
            "```",
            "",
            "**Important Guidelines:**",
            "- Make the task specific and actionable",
            "- Ensure it can be completed by a skilled developer",
            "- Consider the broader project context and goals",
            "- Balance thoroughness with practicality",
            f"- Align with the {priority} priority level",
            "",
        ]
    )

    # Add final considerations
    prompt_parts.extend(
        [
            "## Final Considerations",
            "",
            "- Ensure the task is atomic and focused on a single major objective",
            "- Consider how this task fits into the overall project workflow",
            "- Think about what the developer will need to succeed",
            "- Balance detail with flexibility for implementation approaches",
            "",
        ]
    )

    if dependencies:
        prompt_parts.append(
            f"- Remember this task depends on completion of tasks: {dependencies}"
        )

    prompt_parts.extend(
        [
            "",
            f"**Generated on:** {datetime.now().isoformat()}",
            f"**Research Mode:** {'Enabled' if use_research else 'Disabled'}",
            f"**LTS Preference:** {'Enabled' if use_lts_deps else 'Disabled'}",
        ]
    )

    return "\\n".join(prompt_parts)


def create_simple_add_task_prompt(user_prompt: str, priority: str = "medium") -> str:
    """
    Generate a simplified prompt for basic task creation without research.

    Args:
        user_prompt: The user's description of what they want to accomplish
        priority: Priority level (high, medium, low)

    Returns:
        Simple formatted prompt for basic task generation
    """

    return f"""# Simple Task Generation

Create a task based on this request: {user_prompt}

Priority: {priority}

Provide a JSON response with:
- title: Clear task title
- description: What needs to be done
- details: Implementation steps
- test_strategy: How to verify completion
- estimated_hours: Estimated time
- complexity_score: 1-10 complexity rating

Keep it focused and actionable."""


def validate_add_task_response(response_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate the AI response for add_task prompt.

    Args:
        response_data: The AI's JSON response

    Returns:
        Tuple of (is_valid, list_of_errors)
    """

    errors = []
    required_fields = ["title", "description", "details", "test_strategy"]

    # Check required fields
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")
        elif not response_data[field] or not str(response_data[field]).strip():
            errors.append(f"Empty value for required field: {field}")

    # Validate field lengths
    if "title" in response_data and len(response_data["title"]) > 80:
        errors.append("Title too long (max 80 characters)")

    if "description" in response_data and len(response_data["description"]) > 300:
        errors.append("Description too long (max 300 characters)")

    # Validate numeric fields
    if "estimated_hours" in response_data:
        try:
            hours = float(response_data["estimated_hours"])
            if hours < 0:
                errors.append("Estimated hours cannot be negative")
        except (ValueError, TypeError):
            errors.append("Estimated hours must be a valid number")

    if "complexity_score" in response_data:
        try:
            score = int(response_data["complexity_score"])
            if not (1 <= score <= 10):
                errors.append("Complexity score must be between 1 and 10")
        except (ValueError, TypeError):
            errors.append("Complexity score must be a valid integer")

    return len(errors) == 0, errors


# Export functions for use in AI service
__all__ = [
    "create_add_task_prompt",
    "create_simple_add_task_prompt",
    "validate_add_task_response",
]
