"""
Safety Manager
Coordinates safety guardrails and logs safety events.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from src.guardrails.input_guardrail import InputGuardrail
from src.guardrails.output_guardrail import OutputGuardrail


class SafetyManager:
    """
    Manages safety guardrails for the multi-agent system.

    TODO: YOUR CODE HERE
    - Integrate with Guardrails AI or NeMo Guardrails
    - Define safety policies
    - Implement logging of safety events
    - Handle different violation types with appropriate responses
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize safety manager.

        Args:
            config: Safety configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.log_events = config.get("log_events", True)
        self.logger = logging.getLogger("safety")

        # Safety event log
        self.safety_events: List[Dict[str, Any]] = []

        # Prohibited categories
        self.prohibited_categories = config.get("prohibited_categories", [
            "harmful_content",
            "personal_attacks",
            "misinformation",
            "off_topic_queries"
        ])

        # Violation response strategy
        self.on_violation = config.get("on_violation", {})

        # TODO: Initialize guardrail framework
        # Suggested implementation:
        # - Initialize InputGuardrail and OutputGuardrail instances here
        # - Read safety_log path from config
        # - Decide how refusal, sanitization, or redirect actions should be handled
        self.input_guardrail = InputGuardrail(config)
        self.output_guardrail = OutputGuardrail(config)
        self.safety_log_file = config.get("safety_log_file")
        self.default_refusal_message = config.get(
            "refusal_message",
            "I cannot process this request due to safety policies."
        )

    def check_input_safety(self, query: str) -> Dict[str, Any]:
        """
        Check if input query is safe to process.

        Args:
            query: User query to check

        Returns:
            Dictionary with 'safe' boolean and optional 'violations' list

        TODO: YOUR CODE HERE
        - Implement guardrail checks
        - Detect harmful/inappropriate content
        - Detect off-topic queries
        - Return detailed violation information
        """
        if not self.enabled:
            return {"safe": True}

        # TODO: Implement actual safety checks
        # Suggested implementation:
        # - Call InputGuardrail.validate(query)
        # - Use config.on_violation to decide whether to refuse or sanitize
        # - Log safety events via _log_safety_event()
        # - Return safe/query/violations/action fields for the UI layer

        result = self.input_guardrail.validate(query)
        violations = result.get("violations", [])
        action = result.get("action", "allow")
        is_safe = result.get("valid", True)

        # Resolve the query the caller should actually use
        if action == "block":
            safe_query = None
            message = self.on_violation.get("message", self.default_refusal_message)
        elif action == "sanitize":
            safe_query = result.get("sanitized_input", query)
            message = None
        else:
            safe_query = result.get("sanitized_input", query)
            message = None

        if not is_safe and self.log_events:
            self._log_safety_event("input", query, violations, is_safe)

        return {
            "safe": is_safe,
            "violations": violations,
            "action": action,
            "query": safe_query,
            "message": message,
        }

    def check_output_safety(
        self,
        response: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if output response is safe to return.

        Args:
            response: Generated response to check
            sources: Optional source metadata used by output validation

        Returns:
            Dictionary with 'safe' boolean and optional 'violations' list

        TODO: YOUR CODE HERE
        - Implement output guardrail checks
        - Detect harmful content in responses
        - Detect potential misinformation
        - Sanitize or redact unsafe content
        """
        if not self.enabled:
            return {"safe": True, "response": response}

        # TODO: Implement actual output safety checks
        # Suggested implementation:
        # - Call OutputGuardrail.validate(response, sources)
        # - Decide whether to return the raw, sanitized, or refused response
        # - Attach violations and action metadata so the UI can display them

        result = self.output_guardrail.validate(response, sources)
        violations = result.get("violations", [])
        action = result.get("action", "allow")
        is_safe = result.get("valid", True)

        if not is_safe and self.log_events:
            self._log_safety_event("output", response, violations, is_safe)

        safe_response = response

        # Apply sanitization if configured
        if not is_safe:
            configured_action = self.on_violation.get("action", action)
            if configured_action == "sanitize":
                safe_response = result.get(
                    "sanitized_output",
                    self._sanitize_response(response, violations),
                )
            elif configured_action == "refuse":
                safe_response = self.on_violation.get(
                    "message",
                    "I cannot provide this response due to safety policies."
                )

        return {
            "safe": is_safe,
            "violations": violations,
            "action": action,
            "response": safe_response,
        }

    def _sanitize_response(self, response: str, violations: List[Dict[str, Any]]) -> str:
        """
        Sanitize response by removing or redacting unsafe content.
        """
        # TODO: YOUR CODE HERE
        # Suggested implementation:
        # - Redact PII or unsafe spans
        # - Replace severe outputs with a refusal message
        # - Preserve enough information for the user to know what happened

        # Block entirely for high-severity violations
        high_severity = [v for v in violations if v.get("severity") == "high"]
        if high_severity:
            categories = list({v.get("validator", "unknown") for v in high_severity})
            return (
                f"[RESPONSE BLOCKED: content violated safety policies "
                f"({', '.join(categories)}). Please rephrase your query.]"
            )

        # For medium/low severity, redact PII matches and return with a notice
        sanitized = response
        for violation in violations:
            if violation.get("validator") == "pii":
                for match in violation.get("matches", []):
                    sanitized = sanitized.replace(match, "[REDACTED]")

        sanitized += "\n\n⚠️ Note: Parts of this response were reviewed for safety compliance."
        return sanitized

    def _log_safety_event(
        self,
        event_type: str,
        content: str,
        violations: List[Dict[str, Any]],
        is_safe: bool
    ):
        """
        Log a safety event.

        Args:
            event_type: "input" or "output"
            content: The content that was checked
            violations: List of violations found
            is_safe: Whether content passed safety checks
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "safe": is_safe,
            "violations": violations,
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }

        self.safety_events.append(event)
        self.logger.warning(f"Safety event: {event_type} - safe={is_safe}")

        # Write to safety log file if configured
        log_file = self.config.get("safety_log_file")
        if log_file and self.log_events:
            try:
                with open(log_file, "a") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write safety log: {e}")

    def get_safety_events(self) -> List[Dict[str, Any]]:
        """Get all logged safety events."""
        return self.safety_events

    def get_safety_stats(self) -> Dict[str, Any]:
        """
        Get statistics about safety events.

        Returns:
            Dictionary with safety statistics
        """
        total = len(self.safety_events)
        input_events = sum(1 for e in self.safety_events if e["type"] == "input")
        output_events = sum(1 for e in self.safety_events if e["type"] == "output")
        violations = sum(1 for e in self.safety_events if not e["safe"])

        return {
            "total_events": total,
            "input_checks": input_events,
            "output_checks": output_events,
            "violations": violations,
            "violation_rate": violations / total if total > 0 else 0
        }

    def clear_events(self):
        """Clear safety event log."""
        self.safety_events = []
