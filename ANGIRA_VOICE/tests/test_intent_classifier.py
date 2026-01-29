"""
Tests for intent classification module.
Validates simple vs complex query routing behavior.
"""

import unittest
from core.intent_classifier import classify_intent


class TestIntentClassifier(unittest.TestCase):
    """Test cases for intent classification logic."""

    def test_simple_arithmetic(self) -> None:
        """Test classification of simple arithmetic queries."""
        queries = [
            "What is 2 plus 2?",
            "Calculate 15 times 3",
            "How much is 100 divided by 5?",
        ]

        for query in queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, "simple", f"Failed for: {query}")

    def test_complex_reasoning(self) -> None:
        """Test classification of complex reasoning queries."""
        queries = [
            "Derive the quadratic formula step by step",
            "Prove that the sum of angles in a triangle is 180 degrees",
            "Explain how integration works with detailed examples",
            "Why does E=mc² and what does it mean?",
        ]

        for query in queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, "complex", f"Failed for: {query}")

    def test_long_query_complexity(self) -> None:
        """Test that very long queries are classified as complex."""
        long_query = (
            "This is a very long query that exceeds the maximum simple query length "
            "and should therefore be classified as complex even without special keywords "
            "because it is simply too long for a simple mathematical operation."
        )

        result = classify_intent(long_query)
        self.assertEqual(result, "complex", "Long query should be complex")

    def test_math_operators_complexity(self) -> None:
        """Test that queries with multiple operators are complex."""
        queries = [
            "Calculate the derivative of x^2 + 3x + 5",
            "Integrate ∫ x³ sin(x) dx",
            "Solve ∂f/∂x = 0",
        ]

        for query in queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, "complex", f"Failed for: {query}")

    def test_keyword_detection(self) -> None:
        """Test detection of complex reasoning keywords."""
        complex_keywords_queries = [
            "Derive the solution",
            "Prove this theorem",
            "Explain the concept",
            "Analyze the function",
            "How does this work?",
        ]

        for query in complex_keywords_queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, "complex", f"Failed for: {query}")

    def test_empty_input(self) -> None:
        """Test handling of empty input."""
        result = classify_intent("")
        self.assertEqual(result, "simple", "Empty query should default to simple")

    def test_invalid_input(self) -> None:
        """Test handling of invalid input types."""
        result = classify_intent(None)  # type: ignore
        self.assertEqual(result, "simple", "None input should default to simple")

    def test_case_insensitivity(self) -> None:
        """Test that classification is case-insensitive."""
        queries = [
            ("DERIVE THE FORMULA", "complex"),
            ("PROVE THIS STATEMENT", "complex"),
        ]

        for query, expected in queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, expected, f"Failed for: {query}")

    def test_conceptual_queries(self) -> None:
        """Test classification of conceptual probe queries."""
        queries = [
            "entropy?",
            "gravity?",
            "photosynthesis?",
            "DNA?",
            "black holes?",
        ]

        for query in queries:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, "conceptual", f"Failed for: {query}")

    def test_conceptual_vs_complex(self) -> None:
        """Test distinction between conceptual probes and complex questions."""
        test_cases = [
            ("entropy?", "conceptual"),
            ("what is entropy?", "complex"),
            ("gravity?", "conceptual"),
            ("explain gravity", "complex"),
            ("DNA?", "conceptual"),
            ("how does DNA work?", "complex"),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, expected, f"Failed for: {query}")

    def test_acceptance_criteria(self) -> None:
        """Test the specific acceptance criteria from requirements."""
        test_cases = [
            ("entropy?", "conceptual"),
            ("what is entropy?", "complex"),
            ("2 + 2", "simple"),
        ]

        for query, expected in test_cases:
            with self.subTest(query=query):
                result = classify_intent(query)
                self.assertEqual(result, expected, f"Failed for: {query}")


if __name__ == "__main__":
    unittest.main()
