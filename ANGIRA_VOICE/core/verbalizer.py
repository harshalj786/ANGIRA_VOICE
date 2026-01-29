"""
Query verbalizer module for Agnira Voice Assistant.
Converts mathematical symbols and shorthand to natural language.
"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)

# Mapping of mathematical symbols and shorthand to natural language
MATH_SYMBOL_MAP: Dict[str, str] = {
    "√": "square root of",
    "∑": "sum of",
    "∫": "integral of",
    "∞": "infinity",
    "π": "pi",
    "θ": "theta",
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "∂": "partial derivative of",
    "≈": "approximately equal to",
    "≠": "not equal to",
    "≤": "less than or equal to",
    "≥": "greater than or equal to",
    "∝": "proportional to",
}

SHORTHAND_MAP: Dict[str, str] = {
    "diff": "differentiate",
    "deriv": "derivative",
    "integ": "integral",
    "calc": "calculate",
    "comp": "complex",
    "eq": "equation",
    "eqn": "equation",
    "approx": "approximately",
    "w/": "with",
    "w.r.t": "with respect to",
    "w.r.t.": "with respect to",
}


def verbalize_query(text: str) -> str:
    """
    Convert mathematical symbols and shorthand to natural language.

    Transforms queries with mathematical notation into LLM-friendly text.
    Handles:
    - Mathematical symbols (√, ∫, ∑, etc.)
    - Greek letters
    - Comparison operators
    - Common mathematical shorthand

    Args:
        text (str): Input query potentially containing mathematical notation.

    Returns:
        str: Verbalized query with natural language instead of symbols.

    Example:
        >>> verbalize_query("Calculate ∫ x² dx from 0 to 1")
        "Calculate integral of x squared dx from 0 to 1"
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid input to verbalize_query")
        return ""

    verbalized = text

    # Replace mathematical symbols
    for symbol, word in MATH_SYMBOL_MAP.items():
        if symbol in verbalized:
            verbalized = verbalized.replace(symbol, word)
            logger.debug(f"Replaced symbol '{symbol}' with '{word}'")

    # Replace shorthand expressions (case-insensitive)
    for shorthand, expansion in SHORTHAND_MAP.items():
        pattern = r"\b" + re.escape(shorthand) + r"\b"
        if re.search(pattern, verbalized, re.IGNORECASE):
            verbalized = re.sub(pattern, expansion, verbalized, flags=re.IGNORECASE)
            logger.debug(f"Expanded shorthand '{shorthand}' to '{expansion}'")

    # Handle common superscript patterns (x², x³, etc.)
    verbalized = re.sub(r"([a-zA-Z0-9])\^(\d+)", r"\1 to the power of \2", verbalized)
    verbalized = re.sub(r"([a-zA-Z0-9])²", r"\1 squared", verbalized)
    verbalized = re.sub(r"([a-zA-Z0-9])³", r"\1 cubed", verbalized)

    # Remove multiple spaces
    verbalized = re.sub(r"\s+", " ", verbalized).strip()

    logger.info(f"Verbalized query: '{text}' -> '{verbalized}'")
    return verbalized
