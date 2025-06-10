"""
PyTaskAI - Best Practices Prompt Templates

Centralized prompts for AI-powered best practices research and recommendations
across different domains like security, performance, testing, and code quality.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


def create_best_practices_prompt(
    domain: str,
    technology_stack: List[str],
    project_context: str,
    specific_challenges: Optional[List[str]] = None,
    compliance_requirements: Optional[List[str]] = None,
    team_experience: str = "intermediate",
) -> str:
    """
    Generate a best practices research prompt.

    Args:
        domain: Domain area (e.g., "security", "performance", "testing", "code-quality")
        technology_stack: Technologies being used
        project_context: Description of the project and its goals
        specific_challenges: Specific challenges or pain points to address
        compliance_requirements: Any compliance standards to consider
        team_experience: Team experience level (beginner, intermediate, advanced)

    Returns:
        Formatted best practices research prompt
    """

    specific_challenges = specific_challenges or []
    compliance_requirements = compliance_requirements or []

    prompt_parts = [
        f"# {domain.title()} Best Practices Research",
        "",
        f"You are a senior {domain} consultant with extensive experience in enterprise software development and industry best practices.",
        "",
        "## Research Context",
        f"**Domain Focus:** {domain}",
        f"**Team Experience Level:** {team_experience}",
        f"**Project Context:** {project_context}",
        "",
        "## Technology Stack",
        "",
    ]

    # Add technology stack
    for tech in technology_stack:
        prompt_parts.append(f"- {tech}")

    prompt_parts.append("")

    # Add specific challenges if provided
    if specific_challenges:
        prompt_parts.extend(["## Specific Challenges to Address", ""])

        for challenge in specific_challenges:
            prompt_parts.append(f"- {challenge}")

        prompt_parts.append("")

    # Add compliance requirements if provided
    if compliance_requirements:
        prompt_parts.extend(["## Compliance Requirements", ""])

        for requirement in compliance_requirements:
            prompt_parts.append(f"- {requirement}")

        prompt_parts.append("")

    # Domain-specific research requirements
    if domain.lower() == "security":
        prompt_parts.extend(
            [
                "## Security Best Practices Research",
                "",
                "Focus on these security areas:",
                "",
                "### 1. Application Security",
                "- Input validation and sanitization strategies",
                "- Authentication and authorization patterns",
                "- Session management and security",
                "- API security and rate limiting",
                "- Secure coding practices for the technology stack",
                "",
                "### 2. Infrastructure Security",
                "- Secure deployment configurations",
                "- Network security and firewalling",
                "- Secrets management and encryption",
                "- Container and cloud security",
                "- Monitoring and intrusion detection",
                "",
                "### 3. Data Protection",
                "- Data encryption at rest and in transit",
                "- Personal data handling and privacy",
                "- Backup and recovery security",
                "- Database security hardening",
                "- Data access controls and auditing",
                "",
            ]
        )

    elif domain.lower() == "performance":
        prompt_parts.extend(
            [
                "## Performance Best Practices Research",
                "",
                "Focus on these performance areas:",
                "",
                "### 1. Application Performance",
                "- Code optimization techniques",
                "- Memory management and garbage collection",
                "- Asynchronous programming patterns",
                "- Database query optimization",
                "- Caching strategies and implementation",
                "",
                "### 2. Scalability Patterns",
                "- Horizontal vs. vertical scaling approaches",
                "- Load balancing and distribution",
                "- Microservices architecture considerations",
                "- State management in distributed systems",
                "- Auto-scaling strategies",
                "",
                "### 3. Monitoring and Optimization",
                "- Performance monitoring and profiling",
                "- Bottleneck identification techniques",
                "- Resource utilization optimization",
                "- Performance testing strategies",
                "- Alerting and response procedures",
                "",
            ]
        )

    elif domain.lower() == "testing":
        prompt_parts.extend(
            [
                "## Testing Best Practices Research",
                "",
                "Focus on these testing areas:",
                "",
                "### 1. Test Strategy and Planning",
                "- Test pyramid and testing levels",
                "- Test-driven development (TDD) approaches",
                "- Behavior-driven development (BDD) practices",
                "- Risk-based testing strategies",
                "- Test environment management",
                "",
                "### 2. Automated Testing",
                "- Unit testing frameworks and patterns",
                "- Integration testing strategies",
                "- End-to-end testing automation",
                "- API testing and contract testing",
                "- Performance and load testing",
                "",
                "### 3. Quality Assurance",
                "- Code coverage and quality metrics",
                "- Continuous testing in CI/CD pipelines",
                "- Test data management",
                "- Defect tracking and analysis",
                "- Quality gates and release criteria",
                "",
            ]
        )

    elif domain.lower() == "code-quality":
        prompt_parts.extend(
            [
                "## Code Quality Best Practices Research",
                "",
                "Focus on these code quality areas:",
                "",
                "### 1. Code Structure and Design",
                "- Clean code principles and patterns",
                "- SOLID principles application",
                "- Design patterns and architectural patterns",
                "- Code organization and modularity",
                "- Dependency management strategies",
                "",
                "### 2. Code Standards and Review",
                "- Coding standards and style guides",
                "- Code review processes and checklists",
                "- Static analysis and linting tools",
                "- Documentation standards",
                "- Refactoring strategies and techniques",
                "",
                "### 3. Maintainability",
                "- Technical debt management",
                "- Legacy code modernization",
                "- Versioning and change management",
                "- Error handling and logging",
                "- Configuration management",
                "",
            ]
        )

    else:
        # Generic best practices structure
        prompt_parts.extend(
            [
                f"## {domain.title()} Best Practices Research",
                "",
                "Provide comprehensive best practices covering:",
                "",
                "### 1. Foundation Principles",
                f"- Core principles specific to {domain}",
                "- Industry standards and frameworks",
                "- Common patterns and approaches",
                "",
                "### 2. Implementation Strategies",
                "- Practical implementation techniques",
                "- Tool recommendations and usage",
                "- Integration with existing workflows",
                "",
                "### 3. Monitoring and Improvement",
                "- Measurement and metrics",
                "- Continuous improvement processes",
                "- Common pitfalls and how to avoid them",
                "",
            ]
        )

    # Add team experience considerations
    experience_guidance = {
        "beginner": "- Focus on fundamental concepts and step-by-step guidance\\n- Provide concrete examples and avoid complex patterns\\n- Include learning resources and training recommendations",
        "intermediate": "- Balance theory with practical implementation\\n- Include intermediate patterns and techniques\\n- Provide decision-making frameworks",
        "advanced": "- Focus on advanced patterns and optimization\\n- Include cutting-edge practices and emerging trends\\n- Emphasize architectural and strategic considerations",
    }

    prompt_parts.extend(
        [
            f"### Team Experience Considerations ({team_experience})",
            "",
            experience_guidance.get(
                team_experience, experience_guidance["intermediate"]
            ),
            "",
        ]
    )

    # Add output format requirements
    prompt_parts.extend(
        [
            "## Research Output Format",
            "",
            "Provide your research as a comprehensive guide:",
            "",
            "```json",
            "{",
            f'  "domain": "{domain}",',
            '  "executive_summary": "High-level overview of key recommendations",',
            '  "best_practices": [',
            "    {",
            '      "category": "Category name",',
            '      "practice": "Specific best practice",',
            '      "implementation": "How to implement this practice",',
            '      "benefits": ["benefit1", "benefit2"],',
            '      "tools": ["tool1", "tool2"],',
            '      "priority": "High|Medium|Low",',
            '      "effort_level": "Low|Medium|High"',
            "    }",
            "  ],",
            '  "quick_wins": [',
            '    "Practices that can be implemented quickly with high impact"',
            "  ],",
            '  "long_term_initiatives": [',
            '    "Strategic practices requiring longer-term commitment"',
            "  ],",
            '  "technology_specific_notes": {',
            '    "technology_name": "Specific considerations for this technology"',
            "  },",
            '  "implementation_roadmap": {',
            '    "phase_1": ["immediate actions"],',
            '    "phase_2": ["short-term goals"],',
            '    "phase_3": ["long-term objectives"]',
            "  },",
            '  "metrics_and_monitoring": [',
            '    "Key metrics to track success and improvement"',
            "  ],",
            '  "resources": [',
            '    "Additional learning resources and references"',
            "  ]",
            "}",
            "```",
            "",
        ]
    )

    # Add quality guidelines
    prompt_parts.extend(
        [
            "## Research Quality Guidelines",
            "",
            "Ensure your recommendations are:",
            "- Based on current industry standards and proven practices",
            "- Practical and implementable for the specified team experience level",
            "- Tailored to the specific technology stack and project context",
            "- Balanced between immediate improvements and long-term benefits",
            "- Supported by concrete examples and implementation guidance",
            "",
            "Include specific tool recommendations, code examples (where appropriate), and measurable success criteria.",
            "",
            f"**Research conducted on:** {datetime.now().isoformat()}",
            f"**Domain focus:** {domain}",
            f"**Team experience:** {team_experience}",
        ]
    )

    return "\\n".join(prompt_parts)


def create_code_review_prompt(
    code_snippet: str, language: str, focus_areas: List[str] = None
) -> str:
    """
    Generate a prompt for AI-powered code review.

    Args:
        code_snippet: The code to review
        language: Programming language
        focus_areas: Specific areas to focus on (e.g., ["security", "performance"])

    Returns:
        Formatted code review prompt
    """

    focus_areas = focus_areas or ["code-quality", "security", "performance"]

    return f"""# Code Review Request

Review the following {language} code for best practices:

## Code to Review
```{language}
{code_snippet}
```

## Review Focus Areas
{chr(10).join(f"- {area}" for area in focus_areas)}

## Review Requirements
Provide feedback on:
- Code quality and readability
- Security vulnerabilities
- Performance considerations
- Best practices adherence
- Potential improvements

Format your review with:
- Issue severity (Critical, High, Medium, Low)
- Specific line references
- Concrete improvement suggestions
- Positive observations

Be constructive and educational in your feedback."""


def create_architecture_review_prompt(
    architecture_description: str,
    system_requirements: List[str],
    constraints: List[str] = None,
) -> str:
    """
    Generate a prompt for architecture review and recommendations.

    Args:
        architecture_description: Description of the current architecture
        system_requirements: Functional and non-functional requirements
        constraints: Technical or business constraints

    Returns:
        Formatted architecture review prompt
    """

    constraints = constraints or []

    return f"""# Architecture Review Request

## Current Architecture
{architecture_description}

## System Requirements
{chr(10).join(f"- {req}" for req in system_requirements)}

## Constraints
{chr(10).join(f"- {constraint}" for constraint in constraints) if constraints else "None specified"}

## Review Focus
Evaluate the architecture for:
- Scalability and performance
- Security and compliance
- Maintainability and extensibility
- Technology choices and integration
- Risk assessment and mitigation

Provide:
- Strengths of current approach
- Areas for improvement
- Alternative architectural patterns
- Migration strategy (if changes recommended)
- Risk assessment and timeline"""


def validate_best_practices_response(
    response_data: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Validate the AI response for best practices prompt.

    Args:
        response_data: The AI's JSON response

    Returns:
        Tuple of (is_valid, list_of_errors)
    """

    errors = []
    required_fields = ["domain", "executive_summary", "best_practices"]

    # Check required fields
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")

    # Validate best_practices array
    if "best_practices" in response_data:
        if not isinstance(response_data["best_practices"], list):
            errors.append("Best practices field must be an array")
        else:
            for i, practice in enumerate(response_data["best_practices"]):
                if not isinstance(practice, dict):
                    errors.append(f"Best practice {i} must be an object")
                    continue

                required_practice_fields = [
                    "category",
                    "practice",
                    "implementation",
                    "priority",
                ]
                for practice_field in required_practice_fields:
                    if practice_field not in practice:
                        errors.append(
                            f"Best practice {i} missing required field: {practice_field}"
                        )

    return len(errors) == 0, errors


def get_best_practices_system_prompt() -> str:
    """
    Get the system prompt for best practices research operations.

    Returns:
        System prompt for best practices research
    """
    return """You are a senior software engineering consultant and architect with extensive experience across multiple domains including security, performance, testing, code quality, and operational excellence.

Your expertise spans:
- Software engineering best practices across all major domains
- Industry standards and compliance frameworks (SOC2, PCI-DSS, ISO 27001, etc.)
- Modern development methodologies (Agile, DevOps, CI/CD)
- Code quality and maintainability principles (SOLID, Clean Code, etc.)
- Security engineering and threat modeling
- Performance optimization and scalability patterns
- Testing strategies and quality assurance
- Operational excellence and monitoring

When providing best practices guidance:
1. Base recommendations on proven industry standards and patterns
2. Consider the specific technology stack and project context
3. Balance theoretical ideals with practical implementation constraints
4. Provide actionable, measurable recommendations
5. Include both immediate improvements and long-term strategic initiatives
6. Consider team experience level and organizational maturity
7. Address security, performance, and maintainability concerns
8. Include relevant tools, frameworks, and implementation approaches

Always provide structured, prioritized recommendations with clear implementation guidance and expected outcomes."""


def get_best_practices_user_prompt(topic: str, additional_context: str = "") -> str:
    """
    Generate user prompt for best practices research on a specific topic.

    Args:
        topic: Specific topic or domain for best practices research
        additional_context: Additional context about the project or requirements

    Returns:
        Formatted user prompt for best practices research
    """

    prompt_parts = [
        f"# {topic.title()} Best Practices Research",
        "",
        f"Please provide comprehensive best practices guidance for: **{topic}**",
        "",
    ]

    # Add additional context if provided
    if additional_context:
        prompt_parts.extend(["## Project Context", additional_context, ""])

    # Add research requirements
    prompt_parts.extend(
        [
            "## Research Requirements",
            "",
            f"Provide detailed best practices guidance for {topic} covering:",
            "",
            "### 1. Core Principles",
            f"- Fundamental principles and concepts for {topic}",
            "- Industry standards and frameworks to follow",
            "- Key success metrics and measurement approaches",
            "",
            "### 2. Implementation Strategies",
            "- Practical implementation approaches and patterns",
            "- Recommended tools and technologies",
            "- Step-by-step implementation guidelines",
            "- Common pitfalls and how to avoid them",
            "",
            "### 3. Advanced Practices",
            "- Advanced techniques for mature implementations",
            "- Optimization strategies and performance considerations",
            "- Integration with broader system architecture",
            "- Continuous improvement approaches",
            "",
            "### 4. Organizational Considerations",
            "- Team training and skill development requirements",
            "- Process integration and workflow considerations",
            "- Change management and adoption strategies",
            "- Compliance and governance requirements",
            "",
            "## Output Requirements",
            "",
            "Structure your response to include:",
            "- Executive summary with key recommendations",
            "- Prioritized list of practices (High/Medium/Low priority)",
            "- Quick wins that can be implemented immediately",
            "- Long-term strategic initiatives",
            "- Implementation roadmap with timelines",
            "- Success metrics and monitoring approaches",
            "- Recommended tools and resources",
            "",
            "Focus on actionable, measurable practices that can be implemented by development teams.",
            f"**Research timestamp:** {datetime.now().isoformat()}",
        ]
    )

    return "\\n".join(prompt_parts)


def get_domain_specific_best_practices_prompt(
    domain: str, technology_stack: List[str], team_level: str = "intermediate"
) -> str:
    """
    Generate prompt for domain-specific best practices (security, performance, etc.).

    Args:
        domain: Specific domain (security, performance, testing, etc.)
        technology_stack: List of technologies in use
        team_level: Team experience level (beginner, intermediate, advanced)

    Returns:
        Formatted domain-specific best practices prompt
    """

    return f"""# {domain.title()} Best Practices for Technology Stack

## Domain Focus
**{domain.title()}** best practices and recommendations

## Technology Stack
{chr(10).join(f"- {tech}" for tech in technology_stack)}

## Team Experience Level
**{team_level.title()}** - tailor recommendations accordingly

## Research Requirements

### Technology-Specific Guidance
For each technology in the stack, provide:
- {domain.title()}-specific configuration and setup recommendations
- Common {domain} issues and prevention strategies
- Recommended libraries, tools, and frameworks
- Integration patterns and best practices

### Implementation Roadmap
- Phase 1: Essential {domain} measures (immediate implementation)
- Phase 2: Enhanced {domain} practices (short-term goals)
- Phase 3: Advanced {domain} optimization (long-term objectives)

### Practical Guidelines
- Concrete implementation steps
- Code examples and configuration samples
- Testing and validation approaches
- Monitoring and alerting recommendations

### Team Considerations
- Training and skill development needs for {team_level} team
- Tool adoption and workflow integration
- Review processes and quality gates
- Documentation and knowledge sharing

Provide specific, actionable guidance that can be implemented immediately while building toward comprehensive {domain} excellence."""


def get_compliance_best_practices_prompt(
    compliance_standards: List[str], industry: str = "general"
) -> str:
    """
    Generate prompt for compliance-focused best practices.

    Args:
        compliance_standards: List of compliance standards (SOC2, PCI-DSS, etc.)
        industry: Industry context (healthcare, finance, etc.)

    Returns:
        Formatted compliance best practices prompt
    """

    return f"""# Compliance Best Practices Research

## Compliance Standards
{chr(10).join(f"- {standard}" for standard in compliance_standards)}

## Industry Context
**{industry.title()}** industry requirements and considerations

## Research Requirements

### Compliance Framework Analysis
For each compliance standard:
- Key requirements and control objectives
- Technical implementation requirements
- Audit and documentation needs
- Ongoing monitoring and maintenance

### Implementation Strategy
- Risk assessment and gap analysis approach
- Prioritized implementation roadmap
- Resource requirements and timeline
- Integration with existing systems and processes

### Technical Controls
- Security controls and configurations
- Access management and authentication
- Data protection and encryption requirements
- Logging, monitoring, and incident response

### Operational Procedures
- Policy and procedure development
- Staff training and awareness programs
- Regular assessment and testing procedures
- Continuous improvement processes

### Industry-Specific Considerations
- Additional requirements for {industry} industry
- Common challenges and proven solutions
- Integration with industry-standard practices
- Vendor and third-party management

Provide a comprehensive compliance implementation guide with specific technical and procedural recommendations."""


# Export functions for use in AI service
__all__ = [
    "create_best_practices_prompt",
    "create_code_review_prompt",
    "create_architecture_review_prompt",
    "validate_best_practices_response",
    "get_best_practices_system_prompt",
    "get_best_practices_user_prompt",
    "get_domain_specific_best_practices_prompt",
    "get_compliance_best_practices_prompt",
]
