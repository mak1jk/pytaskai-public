"""
PyTaskAI - LTS Research Prompt Templates

Centralized prompts for AI-powered research on LTS versions, best practices, 
and technology recommendations with a focus on long-term stability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


def create_lts_research_prompt(
    technology_stack: List[str],
    project_type: str = "web application",
    target_environment: str = "production",
    current_versions: Optional[Dict[str, str]] = None,
    constraints: Optional[List[str]] = None,
) -> str:
    """
    Generate a research prompt for LTS version recommendations.

    Args:
        technology_stack: List of technologies to research (e.g., ["Python", "FastAPI", "PostgreSQL"])
        project_type: Type of project (e.g., "web application", "API service", "desktop app")
        target_environment: Target deployment environment (e.g., "production", "enterprise", "cloud")
        current_versions: Current versions being used, if any
        constraints: Any specific constraints or requirements

    Returns:
        Formatted research prompt for LTS version analysis
    """

    current_versions = current_versions or {}
    constraints = constraints or []

    prompt_parts = [
        "# LTS Technology Research Request",
        "",
        "You are a senior DevOps engineer and technology consultant specializing in long-term software maintenance and stability.",
        "",
        "## Research Objective",
        f"Research and recommend LTS (Long Term Support) versions for a {project_type} targeting {target_environment} deployment.",
        "",
        "## Technology Stack to Research",
        "",
    ]

    # Add technology stack details
    for i, tech in enumerate(technology_stack, 1):
        current_version = current_versions.get(tech, "Unknown")
        prompt_parts.append(f"{i}. **{tech}** (current: {current_version})")

    prompt_parts.append("")

    # Add current state context
    if current_versions:
        prompt_parts.extend(
            ["## Current State", "The project currently uses these versions:", ""]
        )

        for tech, version in current_versions.items():
            prompt_parts.append(f"- {tech}: {version}")

        prompt_parts.append("")

    # Add constraints if provided
    if constraints:
        prompt_parts.extend(["## Constraints and Requirements", ""])

        for constraint in constraints:
            prompt_parts.append(f"- {constraint}")

        prompt_parts.append("")

    # Add research requirements
    prompt_parts.extend(
        [
            "## Research Requirements",
            "",
            "For each technology, provide:",
            "",
            "### 1. LTS Version Analysis",
            "- Current LTS version and release date",
            "- Support timeline and end-of-life dates",
            "- Key features and improvements in LTS version",
            "- Known stability issues or considerations",
            "",
            "### 2. Compatibility Assessment",
            "- Compatibility with other technologies in the stack",
            "- Breaking changes from current version (if applicable)",
            "- Migration complexity and effort estimation",
            "- Dependency chain considerations",
            "",
            "### 3. Security and Maintenance",
            "- Security update frequency and track record",
            "- Community support and enterprise backing",
            "- Critical security patches available",
            "- Maintenance burden and operational considerations",
            "",
            "### 4. Performance and Features",
            "- Performance characteristics vs. newer versions",
            "- Feature completeness for project requirements",
            "- Known performance optimizations or regressions",
            "- Resource usage considerations",
            "",
            "### 5. Ecosystem Maturity",
            "- Third-party library support for LTS version",
            "- Documentation quality and completeness",
            "- Tooling and development environment support",
            "- Cloud provider and hosting platform support",
            "",
        ]
    )

    # Add specific guidance for enterprise/production environments
    if target_environment in ["production", "enterprise"]:
        prompt_parts.extend(
            [
                "## Enterprise/Production Considerations",
                "",
                "Pay special attention to:",
                "- Vendor support availability and cost",
                "- Compliance and certification requirements",
                "- High availability and disaster recovery features",
                "- Monitoring and observability capabilities",
                "- Scalability characteristics and limitations",
                "- Integration with enterprise infrastructure",
                "",
            ]
        )

    # Add research methodology
    prompt_parts.extend(
        [
            "## Research Methodology",
            "",
            "Base your analysis on:",
            "- Official project documentation and roadmaps",
            "- Version release notes and changelogs",
            "- Security advisory databases",
            "- Community feedback and production usage reports",
            "- Enterprise adoption patterns",
            "- Benchmark data and performance studies",
            "",
            "## Output Format",
            "",
            "Provide your research findings as a structured analysis:",
            "",
            "```json",
            "{",
            '  "research_summary": "Executive summary of findings and recommendations",',
            '  "technologies": [',
            "    {",
            '      "name": "Technology Name",',
            '      "current_lts_version": "x.x.x",',
            '      "recommended_version": "x.x.x",',
            '      "support_until": "YYYY-MM-DD",',
            '      "migration_complexity": "Low|Medium|High",',
            '      "recommendation": "Upgrade|Stay|Evaluate",',
            '      "key_benefits": ["benefit1", "benefit2"],',
            '      "risks": ["risk1", "risk2"],',
            '      "migration_notes": "Specific migration considerations"',
            "    }",
            "  ],",
            '  "stack_compatibility": {',
            '    "overall_rating": "Excellent|Good|Fair|Poor",',
            '    "compatibility_issues": ["issue1", "issue2"],',
            '    "integration_considerations": ["consideration1", "consideration2"]',
            "  },",
            '  "implementation_timeline": {',
            '    "estimated_effort_days": 10,',
            '    "phases": ["phase1", "phase2", "phase3"],',
            '    "critical_dependencies": ["dep1", "dep2"]',
            "  },",
            '  "maintenance_plan": {',
            '    "update_frequency": "Monthly|Quarterly|Biannual",',
            '    "monitoring_requirements": ["req1", "req2"],',
            '    "backup_strategy": "Recommended backup approach"',
            "  }",
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
            "Ensure your research is:",
            "- Based on current and authoritative sources",
            "- Balanced between stability and functionality",
            "- Practical for the specified project type and environment",
            "- Considers long-term maintenance and support",
            "- Includes concrete next steps and recommendations",
            "",
            f"**Research conducted on:** {datetime.now().isoformat()}",
            f"**Target environment:** {target_environment}",
            f"**Project type:** {project_type}",
        ]
    )

    return "\\n".join(prompt_parts)


def create_dependency_research_prompt(
    primary_technology: str,
    required_features: List[str],
    compatibility_constraints: Optional[List[str]] = None,
) -> str:
    """
    Generate a research prompt for dependency and library recommendations.

    Args:
        primary_technology: Main technology (e.g., "Python", "Node.js")
        required_features: List of required features or capabilities
        compatibility_constraints: Version or compatibility constraints

    Returns:
        Formatted research prompt for dependency analysis
    """

    compatibility_constraints = compatibility_constraints or []

    prompt = f"""# Dependency Research for {primary_technology}

Research and recommend stable, well-maintained dependencies for:

## Required Features
{chr(10).join(f"- {feature}" for feature in required_features)}

## Compatibility Constraints
{chr(10).join(f"- {constraint}" for constraint in compatibility_constraints) if compatibility_constraints else "None specified"}

## Research Focus
For each recommended dependency:
- Current stable version and LTS status
- Maintenance activity and community health
- Security track record
- Performance characteristics
- Integration complexity
- Alternative options and trade-offs

Prioritize libraries with:
- Active maintenance and regular updates
- Good documentation and community support
- Proven track record in production environments
- Minimal dependency chain complexity
- Strong security practices

Provide recommendations in order of preference with rationale."""

    return prompt


def create_migration_research_prompt(
    from_version: str, to_version: str, technology: str, project_size: str = "medium"
) -> str:
    """
    Generate a research prompt for version migration planning.

    Args:
        from_version: Current version
        to_version: Target version
        technology: Technology being migrated
        project_size: Size of project (small, medium, large, enterprise)

    Returns:
        Formatted research prompt for migration analysis
    """

    return f"""# Migration Research: {technology} {from_version} → {to_version}

## Migration Analysis Request

Research the migration path from {technology} {from_version} to {to_version} for a {project_size} project.

## Required Analysis

### Breaking Changes
- List all breaking changes between versions
- Impact assessment for each change
- Required code modifications

### Migration Strategy
- Recommended migration approach (big bang vs. incremental)
- Testing strategy for migration validation
- Rollback plan and risk mitigation

### Effort Estimation
- Estimated migration effort by component
- Required team expertise and skills
- Timeline recommendations

### Dependencies Impact
- Third-party library compatibility
- Required dependency updates
- Potential cascade effects

## Output Requirements
Provide a comprehensive migration plan with:
- Step-by-step migration checklist
- Risk assessment and mitigation strategies
- Resource requirements and timeline
- Testing and validation approach

Focus on practical, actionable guidance for a {project_size} development team."""


def validate_lts_research_response(
    response_data: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Validate the AI response for LTS research prompt.

    Args:
        response_data: The AI's JSON response

    Returns:
        Tuple of (is_valid, list_of_errors)
    """

    errors = []
    required_fields = ["research_summary", "technologies", "stack_compatibility"]

    # Check required top-level fields
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")

    # Validate technologies array
    if "technologies" in response_data:
        if not isinstance(response_data["technologies"], list):
            errors.append("Technologies field must be an array")
        else:
            for i, tech in enumerate(response_data["technologies"]):
                if not isinstance(tech, dict):
                    errors.append(f"Technology {i} must be an object")
                    continue

                required_tech_fields = [
                    "name",
                    "current_lts_version",
                    "recommended_version",
                    "recommendation",
                ]
                for tech_field in required_tech_fields:
                    if tech_field not in tech:
                        errors.append(
                            f"Technology {i} missing required field: {tech_field}"
                        )

    # Validate stack compatibility
    if "stack_compatibility" in response_data:
        compat = response_data["stack_compatibility"]
        if not isinstance(compat, dict):
            errors.append("Stack compatibility must be an object")
        elif "overall_rating" not in compat:
            errors.append("Stack compatibility missing overall_rating")

    return len(errors) == 0, errors


def get_lts_research_system_prompt() -> str:
    """
    Get the system prompt for LTS research operations.

    Returns:
        System prompt for LTS version research
    """
    return """You are an expert DevOps engineer and technology consultant specializing in Long Term Support (LTS) versions and enterprise software stability.

Your expertise includes:
- Deep knowledge of LTS release cycles for major technologies
- Understanding of enterprise deployment requirements and constraints
- Experience with version compatibility and migration planning
- Knowledge of security update patterns and maintenance timelines
- Expertise in dependency management and ecosystem stability

When conducting LTS research:
1. Prioritize stability and long-term maintenance over cutting-edge features
2. Consider enterprise requirements like support timelines and vendor backing
3. Evaluate security update frequency and critical patch availability
4. Assess ecosystem maturity and third-party library compatibility
5. Provide concrete recommendations with clear rationale
6. Include migration effort estimates and compatibility considerations

Always provide structured, actionable recommendations based on current industry standards and proven practices."""


def get_lts_research_user_prompt(
    technologies: List[str], additional_context: str = ""
) -> str:
    """
    Generate user prompt for LTS research on specific technologies.

    Args:
        technologies: List of technologies to research
        additional_context: Additional context or constraints

    Returns:
        Formatted user prompt for LTS research
    """

    prompt_parts = [
        "# LTS Version Research Request",
        "",
        "Please research the current LTS (Long Term Support) versions for the following technologies:",
        "",
    ]

    # Add technologies list
    for i, tech in enumerate(technologies, 1):
        prompt_parts.append(f"{i}. **{tech}**")

    prompt_parts.append("")

    # Add additional context if provided
    if additional_context:
        prompt_parts.extend(["## Additional Context", additional_context, ""])

    # Add research requirements
    prompt_parts.extend(
        [
            "## Research Requirements",
            "",
            "For each technology, provide:",
            "",
            "### Current LTS Status",
            "- Current LTS version number and release date",
            "- Support timeline and end-of-life dates",
            "- Maintenance and security update schedule",
            "",
            "### Stability Assessment",
            "- Known stability issues or considerations",
            "- Production readiness and enterprise adoption",
            "- Performance characteristics vs newer versions",
            "",
            "### Ecosystem Compatibility",
            "- Compatibility with other technologies in the list",
            "- Third-party library and tool support",
            "- Cloud provider and hosting platform support",
            "",
            "### Recommendation",
            "- Whether to use LTS version or consider alternatives",
            "- Migration strategy if upgrade is needed",
            "- Risk assessment and mitigation strategies",
            "",
            "## Output Format",
            "Provide your research as a structured JSON response with detailed analysis for each technology.",
            f"**Research timestamp:** {datetime.now().isoformat()}",
        ]
    )

    return "\\n".join(prompt_parts)


def get_lts_compatibility_prompt(primary_tech: str, dependencies: List[str]) -> str:
    """
    Generate prompt for LTS compatibility analysis between technologies.

    Args:
        primary_tech: Primary technology to focus on
        dependencies: List of dependent technologies

    Returns:
        Formatted compatibility analysis prompt
    """

    return f"""# LTS Compatibility Analysis

## Primary Technology
**{primary_tech}** (LTS version)

## Dependencies to Analyze
{chr(10).join(f"- {dep}" for dep in dependencies)}

## Analysis Requirements

Research the compatibility between the LTS version of {primary_tech} and the latest stable/LTS versions of its dependencies.

### Compatibility Matrix
For each dependency, determine:
- Supported version ranges with {primary_tech} LTS
- Known compatibility issues or limitations
- Recommended versions for optimal stability
- Required configuration or setup considerations

### Integration Assessment
- Overall compatibility rating (Excellent/Good/Fair/Poor)
- Critical issues that must be addressed
- Performance implications of version combinations
- Security considerations and update strategies

### Recommendations
- Optimal version combination for production use
- Alternative options if compatibility issues exist
- Migration path if current versions are incompatible
- Monitoring and maintenance recommendations

Provide structured recommendations prioritizing stability and long-term maintenance."""


# =============================================================================
# PROMPT CONSTANTS FOR AI SERVICE
# =============================================================================

RESEARCH_SYSTEM_PROMPT = """You are an expert technology researcher specializing in Long Term Support (LTS) versions and best practices for software development.

Your expertise includes:
- LTS version recommendations for all major technologies
- Compatibility analysis between different technology versions
- Production deployment best practices
- Security and maintenance considerations
- Performance optimization recommendations

Always prioritize stability, security, and long-term maintainability in your recommendations.
Provide specific version numbers when available and explain the rationale behind recommendations."""

RESEARCH_LTS_VERSIONS_PROMPT = """Research and provide the latest LTS (Long Term Support) versions and recommendations for the following technologies: {technologies}

For each technology, provide:

1. **Current LTS Version**: The latest stable LTS release
2. **Release Date**: When this LTS version was released  
3. **Support Timeline**: How long this LTS version will be supported
4. **Key Features**: Major improvements in this LTS version
5. **Production Readiness**: Assessment for production deployment
6. **Known Issues**: Any critical bugs or limitations to be aware of
7. **Upgrade Path**: Recommended migration strategy from previous versions

**Output Format**: Provide a structured response with clear sections for each technology.

**Focus Areas**:
- Prioritize stability and long-term support over cutting-edge features
- Include security considerations and update policies
- Mention compatibility with major deployment platforms (Docker, cloud providers)
- Consider enterprise/production environment requirements"""


# Export functions and constants for use in AI service
__all__ = [
    "create_lts_research_prompt",
    "create_dependency_research_prompt", 
    "create_migration_research_prompt",
    "validate_lts_research_response",
    "get_lts_research_system_prompt",
    "get_lts_research_user_prompt",
    "get_lts_compatibility_prompt",
    "RESEARCH_SYSTEM_PROMPT",
    "RESEARCH_LTS_VERSIONS_PROMPT",
]
