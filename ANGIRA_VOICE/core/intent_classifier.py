"""
Intent classifier module for Agnira Voice Assistant.
Classifies user queries as simple, conceptual, or complex to optimize response routing.
"""

import logging
import re
from typing import Literal
from config.constants import (
    MIN_QUERY_LENGTH_SIMPLE,
    MAX_QUERY_LENGTH_SIMPLE,
    COMPLEX_KEYWORDS,
    MATH_OPERATORS,
    MAX_CONCEPTUAL_WORDS,
)

logger = logging.getLogger(__name__)


def _is_conceptual_probe(text: str) -> bool:
    """
    Check if text is a short conceptual probe (e.g., "entropy?", "gravity?").

    A conceptual probe is:
    - Very short (≤ MAX_CONCEPTUAL_WORDS words)
    - Ends with a question mark
    - Does NOT start with question words like "what is", "how", etc.

    Args:
        text (str): Text to check.

    Returns:
        bool: True if text is a conceptual probe.
    """
    text_stripped = text.strip()

    # Must end with ?
    if not text_stripped.endswith("?"):
        return False

    # Count words (split on whitespace)
    words = text_stripped.split()
    if len(words) > MAX_CONCEPTUAL_WORDS:
        return False

    # Should not start with complex/explanatory question patterns
    text_lower = text_stripped.lower()
    non_conceptual_starters = [
        "what is",
        "what are",
        "what's",
        "how ",
        "why ",
        "explain",
        "derive",
        "prove",
        "can you",
        "could you",
    ]
    for starter in non_conceptual_starters:
        if text_lower.startswith(starter):
            return False

    logger.debug(f"Query '{text}' identified as conceptual probe")
    return True


def _is_what_is_concept_question(text: str) -> bool:
    """
    Check if text is a 'what is X?' question asking about a concept (not arithmetic).

    'What is entropy?' → True (concept explanation)
    'What is 2 plus 2?' → False (arithmetic)

    Args:
        text (str): Text to check.

    Returns:
        bool: True if it's a concept question requiring explanation.
    """
    text_lower = text.lower().strip()

    # Must start with "what is" or "what are" or "what's"
    what_patterns = ["what is ", "what are ", "what's "]
    is_what_question = any(text_lower.startswith(p) for p in what_patterns)

    if not is_what_question:
        return False

    # Extract the part after "what is/are/what's"
    for pattern in what_patterns:
        if text_lower.startswith(pattern):
            remainder = text_lower[len(pattern):].strip().rstrip("?")
            break

    # If remainder contains numbers or arithmetic words, it's likely arithmetic
    arithmetic_indicators = [
        "plus", "minus", "times", "divided", "multiplied",
        "+", "-", "*", "/", "x",
    ]

    # Check if remainder has digits
    has_digits = any(c.isdigit() for c in remainder)

    # Check if remainder has arithmetic words
    has_arithmetic = any(ind in remainder for ind in arithmetic_indicators)

    # If it has digits or arithmetic indicators, it's NOT a concept question
    if has_digits or has_arithmetic:
        return False

    # Otherwise, it's asking about a concept
    logger.debug(f"Query '{text}' identified as 'what is' concept question")
    return True


def classify_intent(text: str) -> Literal["simple", "conceptual", "complex"]:
    """
    Classify user query intent as simple, conceptual, or complex.

    Uses rule-based logic with priority order:
    1. Empty/invalid → SIMPLE
    2. Complex keywords, advanced math symbols, or long queries → COMPLEX
    3. Very short concept probes (≤3 words) ending with ? → CONCEPTUAL
    4. Fallback → SIMPLE

    Args:
        text (str): User query text to classify.

    Returns:
        Literal["simple", "conceptual", "complex"]: Intent classification.

    Example:
        >>> classify_intent("2 + 2")
        "simple"
        >>> classify_intent("entropy?")
        "conceptual"
        >>> classify_intent("what is entropy?")
        "complex"
    """
    # Rule 1: Empty/invalid → SIMPLE
    if not text or not isinstance(text, str):
        logger.warning("Invalid input to classify_intent")
        return "simple"

    text_lower = text.lower().strip()
    text_length = len(text)

    # Rule 2: Check for COMPLEX indicators

    # 2a: Query length exceeds threshold
    if text_length > MAX_QUERY_LENGTH_SIMPLE:
        logger.debug(f"Query length {text_length} exceeds threshold - classifying as complex")
        return "complex"

    # 2b: Multiple mathematical operators
    operator_count = sum(1 for op in MATH_OPERATORS if op in text_lower)
    if operator_count > 1:
        logger.debug(f"Found {operator_count} mathematical operators - classifying as complex")
        return "complex"

    # 2c: Complex reasoning keywords
    for keyword in COMPLEX_KEYWORDS:
        if keyword.lower() in text_lower:
            logger.debug(f"Found complex keyword '{keyword}' - classifying as complex")
            return "complex"

    # 2d: 'What is X?' concept questions (not arithmetic)
    if _is_what_is_concept_question(text):
        return "complex"

    # Rule 3: Check for CONCEPTUAL (short concept probes)
    if _is_conceptual_probe(text):
        logger.debug(f"Query classified as conceptual: '{text}'")
        return "conceptual"

    # Rule 4: Fallback → SIMPLE
    logger.debug(f"Query classified as simple (length: {text_length})")
    return "simple"
