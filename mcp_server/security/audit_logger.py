"""
PyTaskAI - Security Audit Logger

Comprehensive security audit logging system with SHA-256 hashing and threat tracking.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of security audit events."""
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    INPUT_SANITIZED = "input_sanitized"
    TEMPLATE_VALIDATED = "template_validated"
    THREAT_BLOCKED = "threat_blocked"
    AI_REQUEST_MADE = "ai_request_made"
    AUTHENTICATION_ATTEMPT = "authentication_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONFIGURATION_CHANGED = "configuration_changed"


class SecurityLevel(str, Enum):
    """Security levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Security audit event record."""
    event_id: str
    timestamp: str
    event_type: AuditEventType
    security_level: SecurityLevel
    source_ip: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    
    # Event-specific data
    prompt_hash: Optional[str]
    original_input_hash: Optional[str]
    sanitized_input_hash: Optional[str]
    threats_detected: List[str]
    modifications_made: List[str]
    
    # Context information
    mcp_tool: Optional[str]
    ai_model: Optional[str]
    operation_context: Optional[str]
    
    # Additional metadata
    metadata: Dict[str, Any]


class SecurityAuditLogger:
    """
    Advanced security audit logger with structured logging and threat tracking.
    """
    
    def __init__(
        self, 
        audit_log_path: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize the security audit logger.
        
        Args:
            audit_log_path: Path to audit log file
            enable_file_logging: Whether to log to file
            enable_console_logging: Whether to log to console
            log_level: Logging level
        """
        self.audit_log_path = audit_log_path or "logs/security_audit.jsonl"
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        
        # Ensure log directory exists
        if self.enable_file_logging:
            Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging(log_level)
        
        # Event counters for statistics
        self.event_counts = {event_type: 0 for event_type in AuditEventType}
        self.threat_counts = {}
    
    def _setup_logging(self, log_level: str):
        """Setup structured logging for security events."""
        # Create security audit logger
        self.security_logger = logging.getLogger("pytaskai.security.audit")
        self.security_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers to avoid duplicates
        self.security_logger.handlers.clear()
        
        # File handler for audit logs
        if self.enable_file_logging:
            file_handler = logging.FileHandler(self.audit_log_path)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.security_logger.addHandler(file_handler)
        
        # Console handler for immediate alerts
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '🔒 SECURITY: %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.security_logger.addHandler(console_handler)
    
    def generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = str(int(time.time() * 1000000))  # microsecond precision
        random_component = hashlib.sha256(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
        return f"evt_{timestamp}_{random_component}"
    
    def hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content for audit trail."""
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def log_prompt_injection_detected(
        self,
        original_input: str,
        threats_detected: List[str],
        mcp_tool: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log prompt injection detection event."""
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.PROMPT_INJECTION_DETECTED,
            security_level=SecurityLevel.CRITICAL,
            source_ip=None,  # Could be extracted from request context
            user_agent=None,
            session_id=session_id,
            prompt_hash=self.hash_content(original_input),
            original_input_hash=self.hash_content(original_input),
            sanitized_input_hash=None,
            threats_detected=threats_detected,
            modifications_made=[],
            mcp_tool=mcp_tool,
            ai_model=None,
            operation_context="prompt_injection_detection",
            metadata=metadata or {}
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, threats_detected)
    
    def log_input_sanitized(
        self,
        original_input: str,
        sanitized_input: str,
        threats_detected: List[str],
        modifications_made: List[str],
        mcp_tool: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log input sanitization event."""
        # Determine security level based on threats
        if threats_detected:
            security_level = SecurityLevel.WARNING
        elif modifications_made:
            security_level = SecurityLevel.INFO
        else:
            security_level = SecurityLevel.INFO
        
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.INPUT_SANITIZED,
            security_level=security_level,
            source_ip=None,
            user_agent=None,
            session_id=session_id,
            prompt_hash=self.hash_content(original_input),
            original_input_hash=self.hash_content(original_input),
            sanitized_input_hash=self.hash_content(sanitized_input),
            threats_detected=threats_detected,
            modifications_made=modifications_made,
            mcp_tool=mcp_tool,
            ai_model=None,
            operation_context="input_sanitization",
            metadata=metadata or {}
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, threats_detected)
    
    def log_template_validated(
        self,
        template: str,
        template_type: str,
        validation_result: bool,
        issues_found: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log template validation event."""
        security_level = SecurityLevel.ERROR if not validation_result else SecurityLevel.INFO
        
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.TEMPLATE_VALIDATED,
            security_level=security_level,
            source_ip=None,
            user_agent=None,
            session_id=None,
            prompt_hash=self.hash_content(template),
            original_input_hash=None,
            sanitized_input_hash=None,
            threats_detected=issues_found if not validation_result else [],
            modifications_made=[],
            mcp_tool=None,
            ai_model=None,
            operation_context=f"template_validation_{template_type}",
            metadata=metadata or {}
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, issues_found if not validation_result else [])
    
    def log_threat_blocked(
        self,
        threat_type: str,
        blocked_content: str,
        blocking_reason: str,
        mcp_tool: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log blocked threat event."""
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.THREAT_BLOCKED,
            security_level=SecurityLevel.CRITICAL,
            source_ip=None,
            user_agent=None,
            session_id=session_id,
            prompt_hash=self.hash_content(blocked_content),
            original_input_hash=self.hash_content(blocked_content),
            sanitized_input_hash=None,
            threats_detected=[threat_type],
            modifications_made=[],
            mcp_tool=mcp_tool,
            ai_model=None,
            operation_context="threat_blocking",
            metadata={
                "blocking_reason": blocking_reason,
                **(metadata or {})
            }
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, [threat_type])
    
    def log_ai_request(
        self,
        model_name: str,
        prompt_hash: str,
        operation_type: str,
        mcp_tool: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log AI model request for audit trail."""
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.AI_REQUEST_MADE,
            security_level=SecurityLevel.INFO,
            source_ip=None,
            user_agent=None,
            session_id=session_id,
            prompt_hash=prompt_hash,
            original_input_hash=None,
            sanitized_input_hash=None,
            threats_detected=[],
            modifications_made=[],
            mcp_tool=mcp_tool,
            ai_model=model_name,
            operation_context=operation_type,
            metadata=metadata or {}
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, [])
    
    def log_rate_limit_exceeded(
        self,
        provider: str,
        model: str,
        current_usage: int,
        limit: int,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log rate limit exceeded event."""
        event = AuditEvent(
            event_id=self.generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            security_level=SecurityLevel.WARNING,
            source_ip=None,
            user_agent=None,
            session_id=session_id,
            prompt_hash=None,
            original_input_hash=None,
            sanitized_input_hash=None,
            threats_detected=[],
            modifications_made=[],
            mcp_tool=None,
            ai_model=model,
            operation_context="rate_limiting",
            metadata={
                "provider": provider,
                "current_usage": current_usage,
                "limit": limit,
                **(metadata or {})
            }
        )
        
        self._write_audit_event(event)
        self._update_counters(event.event_type, [])
    
    def _write_audit_event(self, event: AuditEvent):
        """Write audit event to log file and console."""
        # Convert to dict for JSON serialization
        event_dict = asdict(event)
        
        # Write to file as JSONL (newline-delimited JSON)
        if self.enable_file_logging:
            try:
                with open(self.audit_log_path, 'a') as f:
                    f.write(json.dumps(event_dict) + '\\n')
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
        
        # Log to console/logging system
        log_message = self._format_log_message(event)
        
        if event.security_level == SecurityLevel.CRITICAL:
            self.security_logger.critical(log_message)
        elif event.security_level == SecurityLevel.ERROR:
            self.security_logger.error(log_message)
        elif event.security_level == SecurityLevel.WARNING:
            self.security_logger.warning(log_message)
        else:
            self.security_logger.info(log_message)
    
    def _format_log_message(self, event: AuditEvent) -> str:
        """Format audit event for human-readable logging."""
        base_msg = f"{event.event_type.value.upper()}"
        
        if event.mcp_tool:
            base_msg += f" | Tool: {event.mcp_tool}"
        
        if event.threats_detected:
            base_msg += f" | Threats: {', '.join(event.threats_detected)}"
        
        if event.ai_model:
            base_msg += f" | Model: {event.ai_model}"
        
        if event.prompt_hash:
            base_msg += f" | Hash: {event.prompt_hash[:16]}..."
        
        return base_msg
    
    def _update_counters(self, event_type: AuditEventType, threats: List[str]):
        """Update internal counters for statistics."""
        self.event_counts[event_type] += 1
        
        for threat in threats:
            if threat not in self.threat_counts:
                self.threat_counts[threat] = 0
            self.threat_counts[threat] += 1
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics summary."""
        return {
            "event_counts": dict(self.event_counts),
            "threat_counts": dict(self.threat_counts),
            "total_events": sum(self.event_counts.values()),
            "total_threats": sum(self.threat_counts.values()),
            "log_file": self.audit_log_path
        }
    
    def search_audit_events(
        self,
        event_type: Optional[AuditEventType] = None,
        security_level: Optional[SecurityLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        threat_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search audit events with filters."""
        if not self.enable_file_logging or not Path(self.audit_log_path).exists():
            return []
        
        events = []
        try:
            with open(self.audit_log_path, 'r') as f:
                for line in f:
                    if len(events) >= limit:
                        break
                    
                    try:
                        event_data = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and event_data.get('event_type') != event_type.value:
                            continue
                        
                        if security_level and event_data.get('security_level') != security_level.value:
                            continue
                        
                        if threat_type and threat_type not in event_data.get('threats_detected', []):
                            continue
                        
                        # Time filtering
                        if start_time or end_time:
                            event_time = datetime.fromisoformat(event_data.get('timestamp', ''))
                            if start_time and event_time < start_time:
                                continue
                            if end_time and event_time > end_time:
                                continue
                        
                        events.append(event_data)
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to search audit events: {e}")
        
        return events


# Global audit logger instance
_audit_logger: Optional[SecurityAuditLogger] = None


def get_audit_logger(
    audit_log_path: Optional[str] = None,
    **kwargs
) -> SecurityAuditLogger:
    """Get or create global audit logger instance."""
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger(audit_log_path, **kwargs)
    
    return _audit_logger


# Export main classes and functions
__all__ = [
    "SecurityAuditLogger",
    "AuditEvent",
    "AuditEventType",
    "SecurityLevel",
    "get_audit_logger",
]