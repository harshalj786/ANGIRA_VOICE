"""
Mathematical utilities for expression parsing and normalization.
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


def extract_math_expressions(text: str) -> List[str]:
    """
    Extract mathematical expressions from text.

    Args:
        text (str): Text containing mathematical expressions.

    Returns:
        List[str]: List of detected mathematical expressions.
    """
    try:
        # Match common mathematical patterns
        patterns = [
            r"\d+\s*[\+\-\*/]\s*\d+",  # Simple arithmetic
            r"[a-zA-Z]+\s*\(\s*[^)]+\s*\)",  # Function calls
            r"∫.*?dx",  # Integrals
            r"√\d+",  # Square roots
        ]

        expressions = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            expressions.extend(matches)

        logger.debug(f"Extracted {len(expressions)} mathematical expressions")
        return expressions

    except Exception as e:
        logger.error(f"Expression extraction failed: {e}")
        raise


def normalize_math_expression(expr: str) -> str:
    """
    Normalize mathematical expression to standard form.

    Args:
        expr (str): Mathematical expression to normalize.

    Returns:
        str: Normalized expression.
    """
    try:
        normalized = expr

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Standardize operators
        normalized = normalized.replace("×", "*")
        normalized = normalized.replace("÷", "/")

        logger.debug(f"Normalized expression: '{expr}' -> '{normalized}'")
        return normalized

    except Exception as e:
        logger.error(f"Expression normalization failed: {e}")
        raise


def evaluate_simple_math(expr: str) -> float:
    """
    Safely evaluate simple mathematical expressions.

    Uses restricted eval with allowed operations only.
    DO NOT use for untrusted input!

    Args:
        expr (str): Mathematical expression to evaluate.

    Returns:
        float: Evaluation result.

    Raises:
        ValueError: If expression is invalid or contains unsafe operations.
    """
    try:
        import math

        # Allowed functions in evaluation
        safe_dict = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "ln": math.log,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }

        # Validate expression
        if not re.match(r"^[0-9+\-*/().a-z\s]*$", expr.lower()):
            raise ValueError("Expression contains invalid characters")

        result = eval(expr, {"__builtins__": {}}, safe_dict)
        logger.info(f"Evaluated expression: {expr} = {result}")
        return float(result)

    except SyntaxError as e:
        logger.error(f"Invalid mathematical expression syntax: {e}")
        raise ValueError(f"Invalid expression: {e}") from e
    except Exception as e:
        logger.error(f"Mathematical evaluation failed: {e}")
        raise
