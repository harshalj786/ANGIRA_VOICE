"""
Reasoning engine module for Agnira Voice Assistant.
Uses Google Gemini API (new google.genai SDK) for reasoning, problem-solving, and complex analysis.
"""

import logging
import time
from typing import Optional, List, Dict

from google import genai
from google.genai import types

from config.settings import settings
from config.constants import (
    GEMINI_REASONING_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    REASONING_SYSTEM_PROMPT,
    CONVERSATION_MEMORY_MAX_TURNS,
    CONVERSATION_MEMORY_TTL,
)

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation history for CONCEPTUAL and COMPLEX queries.
    SIMPLE queries are stateless and don't use memory.
    """

    def __init__(self, max_turns: int = CONVERSATION_MEMORY_MAX_TURNS, ttl: int = CONVERSATION_MEMORY_TTL):
        """Initialize conversation memory.
        
        Args:
            max_turns: Maximum number of Q&A pairs to retain.
            ttl: Time-to-live in seconds before memory expires.
        """
        self.max_turns = max_turns
        self.ttl = ttl
        self._history: List[types.Content] = []
        self._last_update: float = time.time()

    def add(self, user_message: str, assistant_message: str) -> None:
        """Add a Q&A pair to memory."""
        self._history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )
        self._history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=assistant_message)])
        )
        self._last_update = time.time()

        # Trim to max turns (each turn = 2 messages)
        max_messages = self.max_turns * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]
        
        logger.debug(f"Memory updated: {len(self._history) // 2} turns stored")

    def get_history(self) -> List[types.Content]:
        """Get conversation history if not expired."""
        if self._is_expired():
            self.clear()
            return []
        return self._history.copy()

    def _is_expired(self) -> bool:
        """Check if memory has expired."""
        return (time.time() - self._last_update) > self.ttl

    def clear(self) -> None:
        """Clear conversation history."""
        self._history = []
        self._last_update = time.time()
        logger.debug("Conversation memory cleared")

    def __len__(self) -> int:
        """Return number of turns in memory."""
        return len(self._history) // 2


class ReasoningEngine:
    """
    Reasoning engine using Google Gemini API (new google.genai SDK).
    Handles reasoning tasks, problem-solving, and complex analysis.
    
    Conversation memory is enabled for CONCEPTUAL and COMPLEX queries only.
    SIMPLE queries are stateless for speed and cost efficiency.
    """

    def __init__(self):
        """Initialize ReasoningEngine with Gemini API credentials."""
        self.api_key = settings.get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.model_name = GEMINI_REASONING_MODEL
        self.memory = ConversationMemory()
        logger.info(f"ReasoningEngine initialized with Gemini model: {self.model_name}")

    def solve(self, query: str, intent: str = "simple") -> str:
        """
        Solve a query using Gemini reasoning capabilities.

        Args:
            query (str): User query requiring reasoning or problem-solving.
            intent (str): Query intent (simple/conceptual/complex) for context.

        Returns:
            str: Detailed solution or explanation from Gemini.

        Raises:
            ValueError: If query is empty.
            Exception: If API call fails.
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        logger.info(f"Sending query to Gemini ({self.model_name}): {query[:100]}...")

        # Adjust max tokens based on intent
        max_tokens = GEMINI_MAX_TOKENS
        if intent == "simple":
            max_tokens = min(256, GEMINI_MAX_TOKENS)
        elif intent == "conceptual":
            max_tokens = min(512, GEMINI_MAX_TOKENS)

        # Use memory for CONCEPTUAL and COMPLEX only
        use_memory = intent in ("conceptual", "complex")

        try:
            # Build contents with history if applicable
            contents = []
            
            if use_memory:
                history = self.memory.get_history()
                if history:
                    logger.debug(f"Including {len(history) // 2} turns of conversation history")
                    contents.extend(history)
            
            # Add current query
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=query)])
            )

            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=REASONING_SYSTEM_PROMPT,
                    max_output_tokens=max_tokens,
                    temperature=GEMINI_TEMPERATURE,
                    automaticFunctionCalling=types.AutomaticFunctionCallingConfig(
                        maximumRemoteCalls=100
                    ),
                ),
            )

            response_text = response.text.strip()

            logger.info(f"Gemini response received: {len(response_text)} chars")

            # Store in memory for CONCEPTUAL and COMPLEX
            if use_memory:
                self.memory.add(query, response_text)

            return response_text

        except Exception as e:
            logger.error(f"Reasoning engine failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini API error: {e}") from e

    def clear_memory(self) -> None:
        """Clear conversation memory manually."""
        self.memory.clear()
        logger.info("Conversation memory cleared by user")

    def get_memory_status(self) -> dict:
        """Get current memory status."""
        return {
            "turns_stored": len(self.memory),
            "max_turns": self.memory.max_turns,
            "ttl_seconds": self.memory.ttl,
        }

    def get_model_info(self) -> dict:
        """Get information about the current reasoning model."""
        return {
            "model": self.model_name,
            "api": "Google Gemini (google.genai SDK)",
            "max_tokens": GEMINI_MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
            "purpose": "Reasoning and problem-solving",
            "capabilities": [
                "complex-reasoning",
                "step-by-step-solutions",
                "mathematical-analysis",
                "code-generation",
            ],
            "memory": {
                "enabled_for": ["conceptual", "complex"],
                "disabled_for": ["simple"],
                "max_turns": CONVERSATION_MEMORY_MAX_TURNS,
                "ttl_seconds": CONVERSATION_MEMORY_TTL,
            },
        }
