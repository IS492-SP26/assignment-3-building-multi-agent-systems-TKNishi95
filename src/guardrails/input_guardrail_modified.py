"""
Input Guardrail
Checks user inputs for safety violations.
"""

from typing import Dict, Any, List
import re
import logging

from guardrails import Guard
from guardrails.hub import ToxicLanguage, DetectPII

logger = logging.getLogger(__name__)


class InputGuardrail:
    """
    Guardrail for checking input safety.

    TODO: YOUR CODE HERE
    - Integrate with Guardrails AI or NeMo Guardrails
    - Define validation rules
    - Implement custom validators
    - Handle different types of violations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize input guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # TODO: Initialize guardrail framework
        # Suggested implementation:
        # - Read safety settings from config.yaml
        # - Store min/max query length thresholds
        # - Prepare policy categories such as harmful content,
        #   prompt injection, and off-topic queries
        # - Optionally initialize Guardrails AI / NeMo Guardrails here
        safety_config = config.get("safety", {})
        self.max_query_length = safety_config.get("max_query_length", 2000)
        self.min_query_length = safety_config.get("min_query_length", 5)
        self.prohibited_categories = safety_config.get("prohibited_categories", [])

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

    def validate(self, query: str) -> Dict[str, Any]:
        """
        Validate input query.

        Args:
            query: User input to validate

        Returns:
            Validation result

        TODO: YOUR CODE HERE
        - Implement validation logic
        - Check for toxic language
        - Check for prompt injection attempts
        - Check query length and format
        - Check for off-topic queries
        """
        violations = []

        # TODO: Implement actual validation
        # Suggested implementation:
        # 1. Normalize the input (strip spaces, lowercase copy for keyword checks)
        # 2. Add length checks using thresholds from config
        # 3. Call helper methods like _check_toxic_language(),
        #    _check_prompt_injection(), and _check_relevance()
        # 4. Decide whether violations should block, sanitize, or warn
        # 5. Return both the raw violations and a sanitized_input if applicable

        query = query.strip().lower()

        # Length checks
        if len(query) < self.min_query_length:
            violations.append({
                "validator": "length",
                "reason": "Query too short",
                "severity": "low"
            })

        if len(query) > self.max_query_length:
            violations.append({
                "validator": "length",
                "reason": "Query too long",
                "severity": "medium"
            })

        # Run all helper checks
        violations += self._check_toxic_language(query)
        violations += self._check_prompt_injection(query)
        violations += self._check_relevance(query)

        # Determine action based on highest severity found
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
                "Input guardrail triggered | action=%s | violations=%s",
                action,
                [v["validator"] for v in violations],
            )

        return {
            "valid": valid,
            "violations": violations,
            "sanitized_input": query,
            "action": action,
        }

    def _check_toxic_language(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for toxic/harmful language.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Use a moderation API, Guardrails validator, or keyword/rule-based classifier
        - Return a list of violations with validator name, reason, and severity
        - Mark clearly unsafe requests as high severity
        """
        violations = []

        try:
            self._toxic_guard.validate(text)
        except Exception as exc:
            violations.append({
                "validator": "toxic_language",
                "reason": f"Toxic or harmful language detected: {exc}",
                "severity": "high",
            })

        return violations

    def _check_prompt_injection(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for prompt injection attempts.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Detect phrases like \"ignore previous instructions\",
        #   attempts to reveal system prompts, or role-confusion attacks
        - Consider whether the result should block the request or sanitize it
        """
        violations = []
        # Check for common prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "disregard",
            "forget everything",
            "system:",
            "sudo",
            "you are now",
            "act as",
            "pretend you are",
            "jailbreak",
            "dan mode",
            "reveal your instructions",
            "repeat everything above",
            "override safety",
            "bypass guardrail",
        ]

        for pattern in injection_patterns:
            if pattern.lower() in text.lower():
                violations.append({
                    "validator": "prompt_injection",
                    "reason": f"Potential prompt injection: {pattern}",
                    "severity": "high"
                })
                break  # one match is enough to flag

        return violations

    def _check_relevance(self, query: str) -> List[Dict[str, Any]]:
        """
        Check if query is relevant to the system's purpose.

        TODO: YOUR CODE HERE
        Suggested implementation:
        - Compare the query to the configured topic in config.yaml
        - Use keyword heuristics or an LLM classifier
        - Return low/medium severity violations for off-topic requests
        """
        violations = []

        # Check if query is about sentiment analysis research (or configured topic)
        hci_keywords = [
            # Core sentiment analysis terms
            "sentiment", "sentiment analysis", "opinion mining", "emotion detection",
            "opinion", "subjectivity", "polarity", "valence", "affect",
            "positive", "negative", "neutral", "stance", "tone",
            # Emotion and affect
            "emotion", "emotions", "mood", "feelings", "affective computing",
            "anger", "joy", "sadness", "fear", "disgust", "surprise",
            "emotional", "empathy", "arousal",
            # NLP and ML methods
            "nlp", "natural language processing", "text classification",
            "machine learning", "deep learning", "transformer", "bert", "llm",
            "ai", "neural network", "fine-tuning", "embeddings",
            # Data and evaluation
            "review", "reviews", "feedback", "corpus", "dataset", "annotation",
            "lexicon", "aspect", "aspect-based", "absa", "rating", "ratings",
            "survey", "evaluation", "benchmark", "accuracy", "f1",
            # Applications and domains
            "social media", "twitter", "reddit", "product review", "customer",
            "brand", "market", "public opinion", "news", "text", "document",
            # HCI overlap
            "user experience", "ux", "user study", "experiment",
        ]

        # Skip very short queries — likely follow-up clarifications
        if len(query.split()) <= 4:
            return violations

        lower = query.lower()
        if not any(kw in lower for kw in hci_keywords):
            violations.append({
                "validator": "relevance",
                "reason": (
                    "Query does not appear related to sentiment analysis or the "
                    "configured research topic. Please ask about sentiment analysis, "
                    "opinion mining, emotion detection, or related NLP areas."
                ),
                "severity": "low",
            })

        return violations

