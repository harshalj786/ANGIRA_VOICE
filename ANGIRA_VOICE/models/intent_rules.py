"""
Intent rules and models for Agnira Voice Assistant.
Defines data structures for intent classification and routing rules.
"""

from dataclasses import dataclass
from typing import List, Literal


@dataclass
class IntentRule:
    """
    Rule for intent classification.

    Attributes:
        keywords: List of keywords to match
        operators: Mathematical operators to detect
        min_length: Minimum query length
        max_length: Maximum query length
        complexity_score: Complexity score (0-10)
    """

    keywords: List[str]
    operators: List[str]
    min_length: int
    max_length: int
    complexity_score: int


# Simple query rules
SIMPLE_INTENT_RULES = IntentRule(
    keywords=["what", "how much", "calculate"],
    operators=["+", "-", "*", "/"],
    min_length=5,
    max_length=150,
    complexity_score=1,
)

# Conceptual query rules (short concept probes)
CONCEPTUAL_INTENT_RULES = IntentRule(
    keywords=[],  # No specific keywords - detected by pattern
    operators=[],
    min_length=1,
    max_length=30,  # Very short queries
    complexity_score=3,
)

# Complex query rules
COMPLEX_INTENT_RULES = IntentRule(
    keywords=[
        "derive",
        "prove",
        "integrate",
        "explain",
        "step by step",
        "why",
        "how does",
        "what is",
    ],
    operators=["^", "**", "∫", "∂"],
    min_length=20,
    max_length=5000,
    complexity_score=8,
)


@dataclass
class ProcessedQuery:
    """
    Processed query with all transformations applied.

    Attributes:
        original: Original user query
        verbalized: Query after verbalization
        intent: Classified intent (simple, conceptual, or complex)
        confidence: Classification confidence (0-1)
        response: Generated response text from reasoning engine
    """

    original: str
    verbalized: str
    intent: Literal["simple", "conceptual", "complex"]
    confidence: float = 1.0
    response: str = ""
