"""
PyTaskAI - Prompt Validation Module

Advanced validation system for AI prompts using Pydantic models and regex patterns.
Ensures prompt templates and user inputs conform to security requirements.
"""

import re
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

from .input_sanitizer import InputSanitizer, SanitizationLevel

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of prompts that can be validated."""
    TASK_GENERATION = "task_generation"
    RESEARCH = "research"
    SUBTASK_GENERATION = "subtask_generation"
    BEST_PRACTICES = "best_practices"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a prompt."""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    pattern: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of prompt validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    sanitized_data: Optional[Dict[str, Any]] = None
    security_level: str = "unknown"


class SafePromptData(BaseModel):
    """Pydantic model for validating prompt data."""
    
    user_prompt: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="User task description"
    )
    priority: str = Field(
        default="medium",
        pattern=r"^(high|medium|low)$",
        description="Task priority level"
    )
    dependencies: str = Field(
        default="",
        pattern=r"^(\d+(,\s*\d+)*)?$",
        description="Comma-separated task IDs"
    )
    project_context: Optional[str] = Field(
        default="",
        max_length=1000,
        description="Project context"
    )
    research_findings: Optional[str] = Field(
        default="",
        max_length=5000,
        description="Research findings"
    )
    
    @validator('user_prompt')
    def validate_user_prompt(cls, v):
        """Validate user prompt content."""
        if not v or not v.strip():
            raise ValueError("User prompt cannot be empty")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r"(?i)ignore\s+previous",
            r"(?i)system\s+prompt",
            r"\{\{.*?\}\}",
            r"\$\{.*?\}",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v):
                raise ValueError(f"Prompt contains dangerous pattern: {pattern}")
        
        return v.strip()
    
    @validator('project_context', 'research_findings')
    def validate_optional_text(cls, v):
        """Validate optional text fields."""
        if v is None:
            return ""
        
        # Basic security check for optional fields
        if re.search(r"(?i)<script|javascript:|eval\(", v):
            raise ValueError("Text contains dangerous content")
        
        return v.strip()


class ResearchPromptData(BaseModel):
    """Pydantic model for research prompts."""
    
    technologies: str = Field(
        ...,
        min_length=1,
        max_length=500,
        pattern=r"^[a-zA-Z0-9\.,\s\-_]+$",
        description="Technology list"
    )
    research_topic: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\s\-_]+$",
        description="Research topic"
    )
    
    @validator('technologies')
    def validate_technologies(cls, v):
        """Validate technology list."""
        # Check for network command attempts
        dangerous_tech_patterns = [
            r"(?i)curl|wget|fetch|http",
            r"[<>\"'&;|`]",
        ]
        
        for pattern in dangerous_tech_patterns:
            if re.search(pattern, v):
                raise ValueError(f"Technologies contain dangerous pattern: {pattern}")
        
        return v.strip()


class PromptValidator:
    """
    Advanced prompt validator with schema-based validation and security checks.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the prompt validator.
        
        Args:
            schema_path: Path to YAML schema file. Defaults to built-in schemas.
        """
        self.sanitizer = InputSanitizer(SanitizationLevel.STRICT)
        self.schemas = self._load_schemas(schema_path)
        self._init_pydantic_models()
    
    def _load_schemas(self, schema_path: Optional[str]) -> Dict[str, Any]:
        """Load validation schemas from YAML file."""
        if schema_path and Path(schema_path).exists():
            try:
                with open(schema_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load custom schemas: {e}")
        
        # Use default built-in schemas
        return self._get_default_schemas()
    
    def _get_default_schemas(self) -> Dict[str, Any]:
        """Get default validation schemas."""
        return {
            "template_schemas": {
                "add_task_template": {
                    "safe_placeholders": [
                        {
                            "name": "user_prompt",
                            "pattern": r"^[a-zA-Z0-9\s\.,!?\-_()[\]]{1,2000}$",
                            "description": "User task description"
                        },
                        {
                            "name": "priority", 
                            "pattern": r"^(high|medium|low)$",
                            "description": "Task priority level"
                        },
                        {
                            "name": "dependencies",
                            "pattern": r"^(\d+(,\s*\d+)*)?$", 
                            "description": "Task dependencies"
                        }
                    ],
                    "forbidden_patterns": [
                        {
                            "pattern": r"\{\{.*?\}\}",
                            "reason": "Template injection attempt"
                        },
                        {
                            "pattern": r"(?i)ignore\s+previous",
                            "reason": "Prompt override attempt"
                        }
                    ]
                }
            },
            "validation_rules": {
                "max_placeholder_length": 5000,
                "max_total_template_length": 50000
            }
        }
    
    def _init_pydantic_models(self):
        """Initialize Pydantic models for validation."""
        self.prompt_models = {
            PromptType.TASK_GENERATION: SafePromptData,
            PromptType.RESEARCH: ResearchPromptData,
            PromptType.SUBTASK_GENERATION: SafePromptData,
            PromptType.BEST_PRACTICES: ResearchPromptData,
        }
    
    def validate_prompt_data(
        self, 
        prompt_type: PromptType, 
        data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate prompt data using Pydantic models and security checks.
        
        Args:
            prompt_type: Type of prompt being validated
            data: Data to validate
            
        Returns:
            ValidationResult with validation status and issues
        """
        issues = []
        sanitized_data = {}
        
        # Phase 1: Pydantic Model Validation
        try:
            model_class = self.prompt_models.get(prompt_type, SafePromptData)
            validated_model = model_class(**data)
            sanitized_data = validated_model.dict()
            
        except ValidationError as e:
            for error in e.errors():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation error in {error['loc']}: {error['msg']}",
                    field=str(error['loc'][0]) if error['loc'] else None
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Unexpected validation error: {str(e)}"
            ))
        
        # Phase 2: Schema-based Validation
        schema_issues = self._validate_against_schema(prompt_type, data)
        issues.extend(schema_issues)
        
        # Phase 3: Security Validation
        security_issues = self._validate_security(data)
        issues.extend(security_issues)
        
        # Phase 4: Content Sanitization
        if not any(issue.severity == ValidationSeverity.CRITICAL for issue in issues):
            sanitized_data = self._sanitize_prompt_data(data)
        
        # Determine overall validation result
        is_valid = not any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
            for issue in issues
        )
        
        security_level = self._assess_security_level(issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            sanitized_data=sanitized_data if is_valid else None,
            security_level=security_level
        )
    
    def _validate_against_schema(
        self, 
        prompt_type: PromptType, 
        data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate data against loaded schemas."""
        issues = []
        
        # Get schema for prompt type
        schema_key = f"{prompt_type.value}_template"
        schema = self.schemas.get("template_schemas", {}).get(schema_key, {})
        
        if not schema:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"No schema found for prompt type: {prompt_type.value}"
            ))
            return issues
        
        # Validate against safe placeholders
        safe_placeholders = {p["name"]: p for p in schema.get("safe_placeholders", [])}
        
        for field_name, value in data.items():
            if not isinstance(value, str):
                continue
                
            placeholder_config = safe_placeholders.get(field_name)
            if placeholder_config:
                pattern = placeholder_config["pattern"]
                if not re.match(pattern, str(value)):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field_name}' doesn't match safe pattern",
                        field=field_name,
                        pattern=pattern,
                        suggestion=placeholder_config.get("description", "")
                    ))
        
        # Check forbidden patterns
        forbidden_patterns = schema.get("forbidden_patterns", [])
        for field_name, value in data.items():
            if not isinstance(value, str):
                continue
                
            for forbidden in forbidden_patterns:
                pattern = forbidden["pattern"]
                if re.search(pattern, str(value)):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Forbidden pattern detected in '{field_name}': {forbidden['reason']}",
                        field=field_name,
                        pattern=pattern
                    ))
        
        return issues
    
    def _validate_security(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Perform security validation using input sanitizer."""
        issues = []
        
        for field_name, value in data.items():
            if not isinstance(value, str) or not value:
                continue
            
            # Use input sanitizer for threat detection
            sanitization_result = self.sanitizer.sanitize(value, context=field_name)
            
            for threat in sanitization_result.threats_detected:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Security threat detected in '{field_name}': {threat.value}",
                    field=field_name
                ))
            
            if not sanitization_result.safe_to_proceed:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Field '{field_name}' contains dangerous content",
                    field=field_name
                ))
        
        return issues
    
    def _sanitize_prompt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize prompt data for safe usage."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitization_result = self.sanitizer.sanitize(value, context=key)
                sanitized[key] = sanitization_result.sanitized_input
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _assess_security_level(self, issues: List[ValidationIssue]) -> str:
        """Assess overall security level based on issues found."""
        if any(issue.severity == ValidationSeverity.CRITICAL for issue in issues):
            return "critical"
        elif any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return "high"
        elif any(issue.severity == ValidationSeverity.WARNING for issue in issues):
            return "medium"
        else:
            return "low"
    
    def validate_template(self, template: str, template_type: PromptType) -> ValidationResult:
        """
        Validate a prompt template for security and correctness.
        
        Args:
            template: Template string to validate
            template_type: Type of template
            
        Returns:
            ValidationResult with validation status
        """
        issues = []
        
        # Check template length
        max_length = self.schemas.get("validation_rules", {}).get("max_total_template_length", 50000)
        if len(template) > max_length:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Template too long: {len(template)} > {max_length}",
                suggestion="Reduce template size or split into multiple templates"
            ))
        
        # Check for dangerous template syntax
        dangerous_template_patterns = [
            (r"\{\{.*?\}\}", "Jinja2/Django template syntax detected"),
            (r"\{%.*?%\}", "Template control structure detected"),
            (r"\$\{.*?\}", "JavaScript template literal syntax detected"),
            (r"<%.*?%>", "ASP/JSP template syntax detected"),
        ]
        
        for pattern, reason in dangerous_template_patterns:
            if re.search(pattern, template):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Dangerous template syntax: {reason}",
                    pattern=pattern,
                    suggestion="Use safe placeholder syntax like {placeholder_name}"
                ))
        
        # Check for valid placeholders only
        placeholders = re.findall(r"\{([^}]+)\}", template)
        for placeholder in placeholders:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", placeholder):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Potentially unsafe placeholder: {placeholder}",
                    suggestion="Use alphanumeric placeholders only"
                ))
        
        # Use input sanitizer for additional security checks
        sanitization_result = self.sanitizer.sanitize(template, context="template")
        
        for threat in sanitization_result.threats_detected:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Security threat in template: {threat.value}"
            ))
        
        is_valid = not any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
            for issue in issues
        )
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            security_level=self._assess_security_level(issues)
        )
    
    def get_schema_info(self, prompt_type: PromptType) -> Dict[str, Any]:
        """Get schema information for a prompt type."""
        schema_key = f"{prompt_type.value}_template"
        return self.schemas.get("template_schemas", {}).get(schema_key, {})


def create_secure_validator(schema_path: Optional[str] = None) -> PromptValidator:
    """Factory function to create a secure prompt validator."""
    return PromptValidator(schema_path)


# Export main classes and functions
__all__ = [
    "PromptValidator",
    "PromptType",
    "ValidationSeverity", 
    "ValidationIssue",
    "ValidationResult",
    "SafePromptData",
    "ResearchPromptData",
    "create_secure_validator",
]