"""
PyTaskAI - Input Sanitization Module

Comprehensive input sanitization to prevent prompt injection attacks and protect
against malicious inputs in AI service prompts.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)


class SanitizationLevel(str, Enum):
    """Levels of input sanitization."""
    STRICT = "strict"
    MODERATE = "moderate"
    MINIMAL = "minimal"


class SecurityThreat(str, Enum):
    """Types of security threats detected."""
    PROMPT_INJECTION = "prompt_injection"
    TEMPLATE_INJECTION = "template_injection"
    SYSTEM_OVERRIDE = "system_override"
    DATA_EXTRACTION = "data_extraction"
    COMMAND_INJECTION = "command_injection"
    XSS_ATTEMPT = "xss_attempt"


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    original_input: str
    sanitized_input: str
    threats_detected: List[SecurityThreat]
    risk_level: str  # "low", "medium", "high", "critical"
    modifications_made: List[str]
    safe_to_proceed: bool


class InputSanitizer:
    """
    Advanced input sanitizer for AI prompts with multi-layered protection.
    
    Implements defense-in-depth approach with:
    - Pattern-based threat detection
    - Content filtering and replacement
    - Context-aware sanitization
    - Audit logging
    """

    def __init__(self, sanitization_level: SanitizationLevel = SanitizationLevel.STRICT):
        self.sanitization_level = sanitization_level
        self._init_threat_patterns()
        self._init_replacement_patterns()

    def _init_threat_patterns(self):
        """Initialize patterns for threat detection."""
        
        # Prompt injection patterns
        self.prompt_injection_patterns = [
            # Direct instruction overrides
            r"(?i)ignore\s+(all\s+)?previous\s+instructions?",
            r"(?i)forget\s+(all\s+)?previous\s+(instructions?|context)",
            r"(?i)disregard\s+(all\s+)?previous\s+(instructions?|prompts?)",
            r"(?i)override\s+(previous\s+)?(instructions?|settings?|rules?)",
            
            # System prompt extraction attempts
            r"(?i)what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions?)",
            r"(?i)show\s+me\s+your\s+(system\s+)?(prompt|instructions?)",
            r"(?i)reveal\s+your\s+(system\s+)?(prompt|instructions?)",
            r"(?i)print\s+your\s+(system\s+)?(prompt|instructions?)",
            
            # Role reversal attempts
            r"(?i)you\s+are\s+now\s+(a\s+)?(?!helping|assisting)",
            r"(?i)act\s+as\s+(if\s+you\s+are\s+)?(?!helpful|assistant)",
            r"(?i)pretend\s+(to\s+be\s+|that\s+you\s+are\s+)?",
            
            # Jailbreak attempts
            r"(?i)for\s+educational\s+purposes\s+only",
            r"(?i)hypothetically\s+speaking",
            r"(?i)in\s+a\s+fictional\s+world",
            r"(?i)developer\s+mode",
            r"(?i)jailbreak",
            
            # Data extraction attempts
            r"(?i)export\s+(all\s+)?(data|tasks?|information)",
            r"(?i)dump\s+(all\s+)?(data|database|content)",
            r"(?i)show\s+me\s+all\s+(tasks?|data|information)",
            r"(?i)list\s+all\s+(confidential|private|secret)",
        ]

        # Template injection patterns
        self.template_injection_patterns = [
            # Jinja2/Django template syntax
            r"\{\{.*?\}\}",
            r"\{%.*?%\}",
            
            # Handlebars syntax
            r"\{\{\{.*?\}\}\}",
            
            # JavaScript template literals
            r"\$\{.*?\}",
            
            # Format string injection
            r"\{.*?\}",
            r"%\([^)]*\)[sdixXeEfFgGcrbaAo%]",
            
            # Environment variable injection
            r"\$[A-Z_][A-Z0-9_]*",
            r"ENV\[['\"]?[^'\]]*['\"]?\]",
        ]

        # System override patterns
        self.system_override_patterns = [
            # Direct system commands
            r"(?i)sudo\s+",
            r"(?i)rm\s+-rf",
            r"(?i)chmod\s+",
            r"(?i)chown\s+",
            
            # File system access
            r"(?i)\.\.\/",
            r"(?i)\/etc\/",
            r"(?i)\/var\/",
            r"(?i)\/tmp\/",
            
            # Network commands
            r"(?i)curl\s+",
            r"(?i)wget\s+",
            r"(?i)netcat\s+",
            r"(?i)nc\s+",
        ]

        # Command injection patterns
        self.command_injection_patterns = [
            r";\s*[a-z]+",
            r"\|\s*[a-z]+",
            r"&&\s*[a-z]+",
            r"`[^`]*`",
            r"\$\([^)]*\)",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on[a-z]+=",
            r"eval\s*\(",
            r"document\.",
            r"window\.",
        ]

    def _init_replacement_patterns(self):
        """Initialize patterns for safe replacement."""
        
        self.safe_replacements = {
            # Common placeholder replacements
            "{{": "[[",
            "}}": "]]",
            "${": "$[[",
            "}": "]]",
            
            # Command separators
            ";": ",",
            "|": " OR ",
            "&&": " AND ",
            
            # Script tags
            "<script": "&lt;script",
            "</script>": "&lt;/script&gt;",
            
            # JavaScript
            "javascript:": "js-protocol:",
            "eval(": "eval-function(",
        }

    def sanitize(
        self, 
        input_text: str, 
        context: str = "general",
        preserve_formatting: bool = True
    ) -> SanitizationResult:
        """
        Sanitize input text with comprehensive threat detection.
        
        Args:
            input_text: Text to sanitize
            context: Context of the input ("task_description", "title", etc.)
            preserve_formatting: Whether to preserve basic formatting
            
        Returns:
            SanitizationResult with sanitized text and threat analysis
        """
        if not input_text or not isinstance(input_text, str):
            return SanitizationResult(
                original_input=str(input_text) if input_text else "",
                sanitized_input="",
                threats_detected=[],
                risk_level="low",
                modifications_made=[],
                safe_to_proceed=True
            )

        original_input = input_text
        sanitized_input = input_text
        threats_detected = []
        modifications_made = []

        # Phase 1: Threat Detection
        threats_detected.extend(self._detect_prompt_injection(sanitized_input))
        threats_detected.extend(self._detect_template_injection(sanitized_input))
        threats_detected.extend(self._detect_system_override(sanitized_input))
        threats_detected.extend(self._detect_command_injection(sanitized_input))
        threats_detected.extend(self._detect_xss(sanitized_input))

        # Phase 2: Content Sanitization
        if self.sanitization_level in [SanitizationLevel.STRICT, SanitizationLevel.MODERATE]:
            sanitized_input, mods = self._sanitize_content(sanitized_input, preserve_formatting)
            modifications_made.extend(mods)

        # Phase 3: Risk Assessment
        risk_level = self._assess_risk_level(threats_detected, len(modifications_made))
        safe_to_proceed = self._determine_safety(risk_level, threats_detected)

        # Phase 4: Audit Logging
        self._log_sanitization_result(
            original_input, sanitized_input, threats_detected, risk_level
        )

        return SanitizationResult(
            original_input=original_input,
            sanitized_input=sanitized_input,
            threats_detected=threats_detected,
            risk_level=risk_level,
            modifications_made=modifications_made,
            safe_to_proceed=safe_to_proceed
        )

    def _detect_prompt_injection(self, text: str) -> List[SecurityThreat]:
        """Detect prompt injection attempts."""
        threats = []
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat.PROMPT_INJECTION)
                logger.warning(f"Prompt injection detected: {pattern[:50]}...")
                break  # One detection per threat type
        return threats

    def _detect_template_injection(self, text: str) -> List[SecurityThreat]:
        """Detect template injection attempts."""
        threats = []
        for pattern in self.template_injection_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat.TEMPLATE_INJECTION)
                logger.warning(f"Template injection detected: {pattern[:50]}...")
                break
        return threats

    def _detect_system_override(self, text: str) -> List[SecurityThreat]:
        """Detect system override attempts."""
        threats = []
        for pattern in self.system_override_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat.SYSTEM_OVERRIDE)
                logger.warning(f"System override detected: {pattern[:50]}...")
                break
        return threats

    def _detect_command_injection(self, text: str) -> List[SecurityThreat]:
        """Detect command injection attempts."""
        threats = []
        for pattern in self.command_injection_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat.COMMAND_INJECTION)
                logger.warning(f"Command injection detected: {pattern[:50]}...")
                break
        return threats

    def _detect_xss(self, text: str) -> List[SecurityThreat]:
        """Detect XSS attempts."""
        threats = []
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(SecurityThreat.XSS_ATTEMPT)
                logger.warning(f"XSS attempt detected: {pattern[:50]}...")
                break
        return threats

    def _sanitize_content(self, text: str, preserve_formatting: bool) -> tuple[str, List[str]]:
        """Sanitize content by replacing dangerous patterns."""
        sanitized = text
        modifications = []

        # Apply safe replacements
        for dangerous, safe in self.safe_replacements.items():
            if dangerous in sanitized:
                sanitized = sanitized.replace(dangerous, safe)
                modifications.append(f"Replaced '{dangerous}' with '{safe}'")

        # Remove or neutralize dangerous patterns
        if self.sanitization_level == SanitizationLevel.STRICT:
            # Remove script tags completely
            sanitized = re.sub(r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove javascript: protocols
            sanitized = re.sub(r"javascript:[^\"'\s]*", "", sanitized, flags=re.IGNORECASE)
            
            # Neutralize template syntax
            sanitized = re.sub(r"\{\{.*?\}\}", lambda m: f"[[{m.group(0)[2:-2]}]]", sanitized)
            sanitized = re.sub(r"\{%.*?%\}", lambda m: f"[[{m.group(0)[2:-2]}]]", sanitized)

        # Length limits based on context
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "... [truncated for security]"
            modifications.append("Content truncated due to length")

        return sanitized, modifications

    def _assess_risk_level(self, threats: List[SecurityThreat], modification_count: int) -> str:
        """Assess overall risk level."""
        if not threats:
            return "low"
        
        critical_threats = [
            SecurityThreat.SYSTEM_OVERRIDE,
            SecurityThreat.COMMAND_INJECTION
        ]
        
        high_threats = [
            SecurityThreat.PROMPT_INJECTION,
            SecurityThreat.DATA_EXTRACTION
        ]
        
        if any(threat in critical_threats for threat in threats):
            return "critical"
        elif any(threat in high_threats for threat in threats):
            return "high"
        elif len(threats) > 2 or modification_count > 5:
            return "medium"
        else:
            return "low"

    def _determine_safety(self, risk_level: str, threats: List[SecurityThreat]) -> bool:
        """Determine if input is safe to proceed with."""
        if self.sanitization_level == SanitizationLevel.STRICT:
            return risk_level in ["low", "medium"]
        elif self.sanitization_level == SanitizationLevel.MODERATE:
            return risk_level != "critical"
        else:  # MINIMAL
            return risk_level != "critical" or len(threats) < 3

    def _log_sanitization_result(
        self, 
        original: str, 
        sanitized: str, 
        threats: List[SecurityThreat], 
        risk_level: str
    ):
        """Log sanitization results for audit purposes."""
        if threats:
            logger.warning(
                f"Input sanitization: {len(threats)} threats detected, "
                f"risk level: {risk_level}, "
                f"input length: {len(original)}, "
                f"threats: {[t.value for t in threats]}"
            )
        else:
            logger.debug(f"Input sanitization: Clean input, length: {len(original)}")

    @lru_cache(maxsize=1000)
    def is_safe_placeholder(self, placeholder: str) -> bool:
        """Check if a placeholder pattern is safe to use."""
        safe_patterns = [
            r"^[a-zA-Z_][a-zA-Z0-9_]*$",  # Simple variable names
            r"^user_input$",
            r"^task_\w+$",
            r"^project_\w+$",
        ]
        
        return any(re.match(pattern, placeholder) for pattern in safe_patterns)

    def validate_template_safety(self, template: str) -> tuple[bool, List[str]]:
        """Validate that a template is safe for use."""
        issues = []
        
        # Check for unsafe placeholder patterns
        placeholders = re.findall(r"\{([^}]+)\}", template)
        for placeholder in placeholders:
            if not self.is_safe_placeholder(placeholder):
                issues.append(f"Unsafe placeholder: {placeholder}")
        
        # Check for template injection vulnerabilities
        result = self.sanitize(template, context="template")
        if result.threats_detected:
            issues.extend([f"Template threat: {t.value}" for t in result.threats_detected])
        
        return len(issues) == 0, issues


def create_secure_prompt_builder(
    template: str, 
    sanitizer: InputSanitizer,
    validate_template: bool = True
) -> 'SecurePromptBuilder':
    """Factory function to create a secure prompt builder."""
    return SecurePromptBuilder(template, sanitizer, validate_template)


class SecurePromptBuilder:
    """
    Secure prompt builder that sanitizes all user inputs before template substitution.
    """
    
    def __init__(
        self, 
        template: str, 
        sanitizer: InputSanitizer,
        validate_template: bool = True
    ):
        self.template = template
        self.sanitizer = sanitizer
        
        if validate_template:
            is_safe, issues = sanitizer.validate_template_safety(template)
            if not is_safe:
                raise ValueError(f"Unsafe template: {issues}")
    
    def build(self, **kwargs) -> tuple[str, List[SecurityThreat]]:
        """
        Build prompt with sanitized inputs.
        
        Returns:
            Tuple of (built_prompt, all_threats_detected)
        """
        sanitized_kwargs = {}
        all_threats = []
        
        for key, value in kwargs.items():
            if isinstance(value, str):
                result = self.sanitizer.sanitize(value, context=key)
                sanitized_kwargs[key] = result.sanitized_input
                all_threats.extend(result.threats_detected)
                
                if not result.safe_to_proceed:
                    logger.error(f"Unsafe input for {key}: {result.threats_detected}")
                    raise ValueError(f"Input '{key}' contains dangerous content")
            else:
                sanitized_kwargs[key] = value
        
        try:
            prompt = self.template.format(**sanitized_kwargs)
        except KeyError as e:
            raise ValueError(f"Template placeholder {e} not provided")
        
        return prompt, all_threats


# Export main classes and functions
__all__ = [
    "InputSanitizer",
    "SanitizationLevel",
    "SecurityThreat",
    "SanitizationResult",
    "SecurePromptBuilder",
    "create_secure_prompt_builder",
]