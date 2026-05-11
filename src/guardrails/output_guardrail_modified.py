"""
Output Guardrail
Checks system outputs for safety violations.
"""

from typing import Dict, Any, List
import re
import logging

from guardrails import Guard
from guardrails.hub import ToxicLanguage, DetectPII

logger = logging.getLogger(__name__)


class OutputGuardrail:
    """
    Guardrail for checking output safety.

    TODO: YOUR CODE HERE
    - Integrate with Guardrails AI or NeMo Guardrails
    - Check for harmful content in responses
    - Verify factual consistency
    - Detect potential misinformation
    - Remove PII (personal identifiable information)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # TODO: Initialize guardrail framework
        # Suggested implementation:
        # - Read output safety settings from config
        # - Decide which checks should block vs sanitize
        # - Optionally initialize Guardrails AI / NeMo Guardrails validators
        safety_config = config.get("safety", {})
        self.block_on_harmful = safety_config.get("block_on_harmful_output", True)
        self.block_on_pii = safety_config.get("block_on_pii_output", True)

        self._toxic_guard = Guard().use(
            ToxicLanguage(threshold=0.5, validation_method="sentence"),
            on_fail="exception",
        )

        self._pii_guard = Guard().use(
            DetectPII(
                pii_entities=[
                    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
                    "US_SSN", "IP_ADDRESS", "PERSON",
                ],
            ),
            on_fail="exception",
        )

    def validate(self, response: str, sources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate output response.

        Args:
            response: Generated response to validate
            sources: Optional list of sources used (for fact-checking)

        Returns:
            Validation result

        TODO: YOUR CODE HERE
        - Implement validation logic
        - Check for harmful content
        - Check for PII
        - Verify claims against sources
        - Check for bias
        """
        violations = []

        # TODO: Implement actual validation
        # Suggested implementation:
        # 1. Run helper checks such as _check_pii() and _check_harmful_content()
        # 2. If sources are available, compare claims/citations against them
        # 3. Decide whether to redact, refuse, or allow the response
        # 4. Return sanitized_output for UI display when applicable

        # Placeholder checks
        pii_violations = self._check_pii(response)
        violations.extend(pii_violations)

        harmful_violations = self._check_harmful_content(response)
        violations.extend(harmful_violations)

        bias_violations = self._check_bias(response)
        violations.extend(bias_violations)

        if sources:
            consistency_violations = self._check_factual_consistency(response, sources)
            violations.extend(consistency_violations)

        # Determine action based on highest severity
        severities = {v["severity"] for v in violations}
        if "high" in severities:
            action = "block"
            valid = False
        elif "medium" in severities:
            action = "sanitize"
            valid = False
        else:
            action = "allow"
            valid = len(violations) == 0

        if violations:
            logger.warning(
                "Output guardrail triggered | action=%s | violations=%s",
                action,
                [v["validator"] for v in violations],
            )

        return {
            "valid": valid,
            "violations": violations,
            "action": action,
            "sanitized_output": self._sanitize(response, violations) if violations else response
        }

    def _check_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for personally identifiable information.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Expand regex checks for emails, phone numbers, SSNs, addresses, etc.
        - Use a stronger PII detection library if desired
        - Return violation metadata needed for redaction
        """
        violations = []

        # Simple regex patterns for common PII
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                violations.append({
                    "validator": "pii",
                    "pii_type": pii_type,
                    "reason": f"Contains {pii_type}",
                    "severity": "high",
                    "matches": matches
                })

        # Also run Guardrails AI DetectPII for named entities (PERSON, etc.)
        try:
            self._pii_guard.validate(text)
        except Exception as exc:
            violations.append({
                "validator": "pii",
                "pii_type": "named_entity",
                "reason": f"Named-entity PII detected: {exc}",
                "severity": "high",
                "matches": [],
            })

        return violations

    def _check_harmful_content(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for harmful or inappropriate content.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Detect unsafe instructions, hateful content, or violent guidance
        - Use a moderation model, guardrail validator, or rule-based policy check
        - Return severity levels so the caller knows whether to refuse or sanitize
        """
        violations = []

        # Use Guardrails AI ToxicLanguage validator for robust detection
        try:
            self._toxic_guard.validate(text)
        except Exception as exc:
            violations.append({
                "validator": "harmful_content",
                "reason": f"Toxic or harmful content detected in output: {exc}",
                "severity": "high",
            })
            return violations

        # Placeholder - should use proper toxicity detection
        harmful_keywords = ["violent", "harmful", "dangerous"]
        for keyword in harmful_keywords:
            if keyword in text.lower():
                violations.append({
                    "validator": "harmful_content",
                    "reason": f"May contain harmful content: {keyword}",
                    "severity": "medium"
                })

        return violations

    def _check_factual_consistency(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check if response is consistent with sources.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Compare claims in the response against the retrieved evidence
        - Verify that citations actually support the statements made
        - Optionally use an LLM-based verifier or a citation-grounding check
        """
        violations = []

        # Placeholder - this is complex and could use LLM
        # to verify claims against sources

        # Basic citation presence check: warn if response cites sources
        # by index (e.g. [1], [2]) but fewer sources were actually provided
        cited_indices = re.findall(r'\[(\d+)\]', response)
        if cited_indices:
            max_cited = max(int(i) for i in cited_indices)
            if max_cited > len(sources):
                violations.append({
                    "validator": "factual_consistency",
                    "reason": (
                        f"Response cites source [{max_cited}] but only "
                        f"{len(sources)} source(s) were provided. "
                        "Possible hallucinated citation."
                    ),
                    "severity": "medium",
                })

        return violations

    def _check_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for biased language.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Look for stereotypes, blanket generalizations, or discriminatory language
        - Decide whether to redact, revise, or refuse the output
        """
        violations = []

        # Detect overly broad generalizations common in sentiment analysis outputs
        bias_patterns = [
            (r"\ball (women|men|blacks|whites|asians|muslims|christians|jews)\b", "demographic generalisation"),
            (r"\b(always|never) (feel|think|believe|say|act)\b", "absolute generalisation"),
            (r"\beveryone (knows|agrees|feels|thinks)\b", "false consensus"),
            (r"\bby nature\b", "essentialist claim"),
        ]

        for pattern, label in bias_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append({
                    "validator": "bias",
                    "reason": f"Potentially biased language detected: {label}",
                    "severity": "medium",
                })

        return violations

    def _sanitize(self, text: str, violations: List[Dict[str, Any]]) -> str:
        """
        Sanitize text by removing/redacting violations.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Redact matched PII spans
        - Replace unsafe sections with placeholder text
        - Optionally return a refusal message for severe violations
        """
        sanitized = text

        # Block entirely for high-severity harmful content
        high_harmful = [
            v for v in violations
            if v.get("validator") == "harmful_content" and v.get("severity") == "high"
        ]
        if high_harmful:
            return "[RESPONSE BLOCKED: harmful content detected and cannot be displayed.]"

        # Redact PII
        for violation in violations:
            if violation.get("validator") == "pii":
                for match in violation.get("matches", []):
                    sanitized = sanitized.replace(match, "[REDACTED]")

        # Append a bias disclaimer when bias violations are present
        bias_violations = [v for v in violations if v.get("validator") == "bias"]
        if bias_violations:
            sanitized += (
                " <br><br>Note: This response may contain generalised language. "
                "Please interpret findings with appropriate nuance."
            )

        return sanitized
