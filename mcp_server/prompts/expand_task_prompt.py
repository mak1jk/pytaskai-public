"""
PyTaskAI - Expand Task Prompt Templates

Centralized prompts for AI-powered task expansion into detailed subtasks.
These prompts help break down complex tasks into manageable, actionable subtasks.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


def create_expand_task_prompt(
    task_data: Dict[str, Any],
    num_subtasks: Optional[int] = None,
    use_research: bool = False,
    use_lts_deps: bool = True,
    additional_context: Optional[str] = None,
    research_findings: Optional[str] = None,
    existing_subtasks: Optional[List[Dict[str, Any]]] = None,
    project_context: Optional[str] = None,
) -> str:
    """
    Generate a comprehensive prompt for AI task expansion.

    Args:
        task_data: The task to be expanded (must include id, title, description)
        num_subtasks: Target number of subtasks (if not specified, AI will determine)
        use_research: Whether to incorporate research findings
        use_lts_deps: Whether to prefer LTS versions of dependencies
        additional_context: Additional context for subtask generation
        research_findings: Research findings to incorporate (when use_research=True)
        existing_subtasks: Any existing subtasks to avoid duplication
        project_context: Overall project context and goals

    Returns:
        Formatted prompt string for AI task expansion
    """

    existing_subtasks = existing_subtasks or []

    # Validate required task data
    if not task_data or "title" not in task_data:
        raise ValueError("task_data must include at least 'title' field")

    task_id = task_data.get("id", "Unknown")
    task_title = task_data.get("title", "Unknown Task")
    task_description = task_data.get("description", "No description provided")
    task_details = task_data.get("details", "")
    task_priority = task_data.get("priority", "medium")
    task_dependencies = task_data.get("dependencies", [])

    prompt_parts = [
        "# PyTaskAI Task Expansion Request",
        "",
        "You are an expert project manager and software architect specializing in breaking down complex tasks into manageable, actionable subtasks.",
        "",
        "## Task to Expand",
        f"**Task ID:** {task_id}",
        f"**Title:** {task_title}",
        f"**Description:** {task_description}",
        f"**Priority:** {task_priority}",
        f"**Dependencies:** {task_dependencies if task_dependencies else 'None'}",
        "",
    ]

    # Add task details if available
    if task_details:
        prompt_parts.extend(["**Implementation Details:**", task_details, ""])

    # Add expansion parameters
    prompt_parts.extend(
        [
            "## Expansion Parameters",
            f"**Target Number of Subtasks:** {num_subtasks if num_subtasks else 'Determine automatically based on complexity'}",
            f"**LTS Preference:** {'Prefer LTS/stable versions' if use_lts_deps else 'Use latest versions'}",
            f"**Research Mode:** {'Enabled' if use_research else 'Disabled'}",
            "",
        ]
    )

    # Add additional context if provided
    if additional_context:
        prompt_parts.extend(["## Additional Context", additional_context, ""])

    # Add project context if available
    if project_context:
        prompt_parts.extend(["## Project Context", project_context, ""])

    # Add existing subtasks context if available
    if existing_subtasks:
        prompt_parts.extend(["## Existing Subtasks (to avoid duplication)", ""])

        for i, subtask in enumerate(
            existing_subtasks[:10], 1
        ):  # Limit to 10 for context
            subtask_title = subtask.get("title", f"Subtask {i}")
            subtask_status = subtask.get("status", "unknown")
            prompt_parts.append(f"{i}. **{subtask_title}** ({subtask_status})")

        if len(existing_subtasks) > 10:
            prompt_parts.append(
                f"... and {len(existing_subtasks) - 10} more existing subtasks"
            )

        prompt_parts.extend(
            [
                "",
                "**Important:** Do not duplicate these existing subtasks. Build upon or complement them.",
                "",
            ]
        )

    # Add research findings if available
    if use_research and research_findings:
        prompt_parts.extend(
            [
                "## Research Findings",
                "Incorporate these research findings into your subtask planning:",
                "",
                research_findings,
                "",
                "**Important:** Use the research findings to:",
                "- Identify specific technologies and approaches to use",
                "- Anticipate potential challenges and include mitigation subtasks",
                "- Follow current best practices and industry standards",
                "- Consider security, performance, and maintainability aspects",
                "",
            ]
        )

    # Add detailed expansion instructions
    prompt_parts.extend(
        [
            "## Subtask Expansion Requirements",
            "",
            "Break down the main task into logical, sequential subtasks that:",
            "",
            "### 1. Logical Flow and Dependencies",
            "- Follow a logical implementation sequence",
            "- Consider inter-subtask dependencies",
            "- Build from foundation to completion",
            "- Allow for parallel work where possible",
            "",
            "### 2. Granularity and Scope",
            "- Each subtask should be completable in 2-8 hours",
            "- Focus on single, well-defined objectives",
            "- Avoid overly granular micro-tasks",
            "- Balance detail with practicality",
            "",
            "### 3. Actionability and Clarity",
            "- Use clear, action-oriented titles",
            "- Include specific deliverables and outcomes",
            "- Provide sufficient detail for implementation",
            "- Define clear completion criteria",
            "",
        ]
    )

    # Add technology-specific guidance
    if use_lts_deps:
        prompt_parts.extend(
            [
                "### 4. Technology and Dependency Choices",
                "- Prefer stable, LTS (Long Term Support) versions",
                "- Choose well-established libraries and frameworks",
                "- Avoid experimental or bleeding-edge technologies",
                "- Document version constraints and compatibility requirements",
                "",
            ]
        )
    else:
        prompt_parts.extend(
            [
                "### 4. Technology and Dependency Choices",
                "- Consider latest stable versions and modern approaches",
                "- Balance innovation with project stability",
                "- Evaluate new features and capabilities",
                "- Document any compatibility considerations",
                "",
            ]
        )

    # Add research-specific guidance
    if use_research:
        prompt_parts.extend(
            [
                "### 5. Research-Informed Planning",
                "- Apply insights from the research findings above",
                "- Include best practices and industry standards",
                "- Consider security implications and performance requirements",
                "- Plan for testing and validation subtasks",
                "- Include documentation and maintenance considerations",
                "",
            ]
        )

    # Add output format requirements
    prompt_parts.extend(
        [
            "## Output Format",
            "",
            "Provide your response as a JSON array of subtasks:",
            "",
            "```json",
            "{",
            '  "expansion_summary": "Brief explanation of the expansion approach and rationale",',
            '  "total_subtasks": 6,',
            '  "estimated_total_hours": 24.5,',
            '  "subtasks": [',
            "    {",
            '      "id": 1,',
            '      "title": "Clear, action-oriented subtask title",',
            '      "description": "Detailed description of what needs to be done",',
            '      "implementation_notes": "Specific implementation guidance and considerations",',
            '      "dependencies": [2, 3],',
            '      "estimated_hours": 4.0,',
            '      "complexity_score": 3,',
            '      "deliverables": ["deliverable1", "deliverable2"],',
            '      "acceptance_criteria": ["criteria1", "criteria2"],',
            '      "potential_challenges": ["challenge1", "challenge2"],',
            '      "required_skills": ["skill1", "skill2"]',
            "    }",
            "  ],",
            '  "dependencies_overview": "Explanation of how subtasks depend on each other",',
            '  "parallel_work_opportunities": ["Groups of subtasks that can be done in parallel"],',
            '  "critical_path": [1, 3, 5],',
            '  "risk_factors": ["risk1", "risk2"],',
            '  "testing_strategy": "How to validate the completed task"',
            "}",
            "```",
            "",
        ]
    )

    # Add quality guidelines
    prompt_parts.extend(
        [
            "## Quality Guidelines",
            "",
            "Ensure your subtask breakdown:",
            "- Covers all aspects of the main task completely",
            "- Follows logical implementation order",
            "- Considers testing, documentation, and maintenance",
            "- Balances detail with practicality",
            "- Allows for measurable progress tracking",
            f"- Aligns with the {task_priority} priority level of the main task",
            "",
            "**Subtask Numbering:** Use sequential IDs starting from 1",
            "**Dependencies:** Reference subtask IDs, not external task IDs",
            "**Estimation:** Be realistic about time requirements",
            "**Scope:** Each subtask should have clear boundaries and outcomes",
            "",
        ]
    )

    # Add specific considerations based on task characteristics
    if "security" in task_title.lower() or "auth" in task_title.lower():
        prompt_parts.extend(
            [
                "## Security-Specific Considerations",
                "- Include security review and validation subtasks",
                "- Consider threat modeling and vulnerability assessment",
                "- Plan for security testing and penetration testing",
                "- Include compliance verification if applicable",
                "",
            ]
        )

    if "api" in task_title.lower() or "service" in task_title.lower():
        prompt_parts.extend(
            [
                "## API/Service-Specific Considerations",
                "- Include API design and documentation subtasks",
                "- Plan for API testing and contract validation",
                "- Consider rate limiting and error handling",
                "- Include monitoring and observability setup",
                "",
            ]
        )

    if "database" in task_title.lower() or "data" in task_title.lower():
        prompt_parts.extend(
            [
                "## Data/Database-Specific Considerations",
                "- Include data modeling and schema design",
                "- Plan for data migration and validation",
                "- Consider backup and recovery procedures",
                "- Include performance optimization subtasks",
                "",
            ]
        )

    # Add final metadata
    prompt_parts.extend(
        [
            f"**Generated on:** {datetime.now().isoformat()}",
            f"**Main Task Priority:** {task_priority}",
            f"**Research Mode:** {'Enabled' if use_research else 'Disabled'}",
            f"**LTS Preference:** {'Enabled' if use_lts_deps else 'Disabled'}",
        ]
    )

    return "\\n".join(prompt_parts)


def create_simple_expand_task_prompt(
    task_title: str, task_description: str, num_subtasks: int = 5
) -> str:
    """
    Generate a simplified prompt for basic task expansion.

    Args:
        task_title: Title of the task to expand
        task_description: Description of the task
        num_subtasks: Number of subtasks to generate

    Returns:
        Simple formatted prompt for task expansion
    """

    return f"""# Simple Task Expansion

Break down this task into {num_subtasks} actionable subtasks:

**Task:** {task_title}
**Description:** {task_description}

For each subtask, provide:
- Clear, actionable title
- Brief description
- Estimated hours
- Dependencies (reference other subtask numbers)

Format as JSON array with subtasks that:
- Follow logical implementation order
- Are completable in 2-6 hours each
- Have clear deliverables
- Build toward completing the main task

Focus on practical, sequential steps that a developer can follow."""


def create_complexity_based_expansion_prompt(
    task_data: Dict[str, Any],
    complexity_score: int,
    complexity_analysis: Optional[str] = None,
) -> str:
    """
    Generate an expansion prompt based on complexity analysis.

    Args:
        task_data: The task to be expanded
        complexity_score: Complexity score (1-10)
        complexity_analysis: Detailed complexity analysis

    Returns:
        Formatted expansion prompt based on complexity
    """

    task_title = task_data.get("title", "Unknown Task")
    task_description = task_data.get("description", "")

    # Determine subtask count and approach based on complexity
    if complexity_score <= 3:
        num_subtasks = "3-5"
        approach = "straightforward implementation"
    elif complexity_score <= 6:
        num_subtasks = "5-8"
        approach = "structured breakdown with clear phases"
    elif complexity_score <= 8:
        num_subtasks = "8-12"
        approach = "detailed planning with risk mitigation"
    else:
        num_subtasks = "12-20"
        approach = "comprehensive breakdown with extensive planning"

    prompt = f"""# Complexity-Based Task Expansion

## Task Details
**Title:** {task_title}
**Description:** {task_description}
**Complexity Score:** {complexity_score}/10

## Complexity Analysis
{complexity_analysis or "High complexity task requiring detailed breakdown"}

## Expansion Strategy
Based on the complexity score of {complexity_score}, create {num_subtasks} subtasks using a {approach}.

## Requirements
- Break down into logical implementation phases
- Include risk mitigation and validation steps
- Consider testing and quality assurance
- Plan for documentation and maintenance
- Account for integration and deployment

Focus on reducing complexity through proper decomposition and clear dependencies."""

    return prompt


def validate_expand_task_response(
    response_data: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Validate the AI response for expand task prompt.

    Args:
        response_data: The AI's JSON response

    Returns:
        Tuple of (is_valid, list_of_errors)
    """

    errors = []
    required_fields = ["expansion_summary", "subtasks", "total_subtasks"]

    # Check required top-level fields
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")

    # Validate subtasks array
    if "subtasks" in response_data:
        subtasks = response_data["subtasks"]
        if not isinstance(subtasks, list):
            errors.append("Subtasks field must be an array")
        else:
            # Check total count matches
            if "total_subtasks" in response_data:
                expected_count = response_data["total_subtasks"]
                if len(subtasks) != expected_count:
                    errors.append(
                        f"Subtasks count ({len(subtasks)}) doesn't match total_subtasks ({expected_count})"
                    )

            # Validate each subtask
            for i, subtask in enumerate(subtasks):
                if not isinstance(subtask, dict):
                    errors.append(f"Subtask {i} must be an object")
                    continue

                required_subtask_fields = [
                    "id",
                    "title",
                    "description",
                    "estimated_hours",
                ]
                for subtask_field in required_subtask_fields:
                    if subtask_field not in subtask:
                        errors.append(
                            f"Subtask {i} missing required field: {subtask_field}"
                        )

                # Validate numeric fields
                if "estimated_hours" in subtask:
                    try:
                        hours = float(subtask["estimated_hours"])
                        if hours <= 0:
                            errors.append(
                                f"Subtask {i} estimated_hours must be positive"
                            )
                    except (ValueError, TypeError):
                        errors.append(
                            f"Subtask {i} estimated_hours must be a valid number"
                        )

                if "complexity_score" in subtask:
                    try:
                        score = int(subtask["complexity_score"])
                        if not (1 <= score <= 10):
                            errors.append(
                                f"Subtask {i} complexity_score must be between 1 and 10"
                            )
                    except (ValueError, TypeError):
                        errors.append(
                            f"Subtask {i} complexity_score must be a valid integer"
                        )

    return len(errors) == 0, errors


# Export functions for use in AI service
__all__ = [
    "create_expand_task_prompt",
    "create_simple_expand_task_prompt",
    "create_complexity_based_expansion_prompt",
    "validate_expand_task_response",
]
