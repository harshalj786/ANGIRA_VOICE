"""
Response router module for Angira Voice Assistant.
Routes responses based on query complexity to optimize cost and user experience.
"""

import logging
from typing import Literal
from config.constants import (
    SHORT_ACKNOWLEDGMENT,
    RESPONSE_PRINT_LENGTH_LIMIT,
    MAX_CONCEPTUAL_RESPONSE_LENGTH,
)

logger = logging.getLogger(__name__)


def route_response(
    intent: Literal["simple", "conceptual", "complex"], response_text: str
) -> None:
    """
    Route response based on query complexity (sync version - no TTS).

    Use route_response_async for full TTS support in async contexts.

    Args:
        intent (Literal["simple", "conceptual", "complex"]): Query intent classification.
        response_text (str): Response text to route.
    """
    try:
        if not response_text or not isinstance(response_text, str):
            logger.warning("Invalid response text for routing")
            return

        # Always print the response
        _print_response(response_text)
        
        # Log what TTS would do (sync version skips actual TTS to avoid async issues)
        if intent == "simple":
            logger.info("Routing to full TTS (simple query)")
        elif intent == "conceptual":
            logger.info("Routing to short explanation TTS (conceptual query)")
        elif intent == "complex":
            logger.info("Routing to brief acknowledgment (complex query)")

    except Exception as e:
        logger.error(f"Response routing failed: {e}")
        raise


async def route_response_async(
    intent: Literal["simple", "conceptual", "complex"], 
    response_text: str,
    audio_handler=None
) -> None:
    """
    Route response based on query complexity (async version with TTS).

    Handles response output with cost optimization:
    - SIMPLE queries: Print and speak full response (up to 2000 chars)
    - CONCEPTUAL queries: Print full, speak short explanation (up to 300 chars)
    - COMPLEX queries: Print full response, speak only brief acknowledgment

    Args:
        intent: Query intent classification.
        response_text: Response text to route.
        audio_handler: AudioLiveHandler for TTS playback.
    """
    try:
        if not response_text or not isinstance(response_text, str):
            logger.warning("Invalid response text for routing")
            return

        # Always print the response
        _print_response(response_text)

        # Route TTS based on intent
        if audio_handler:
            if intent == "simple":
                await _speak_full_response_async(response_text, audio_handler)
            elif intent == "conceptual":
                await _speak_conceptual_response_async(response_text, audio_handler)
            elif intent == "complex":
                await _speak_acknowledgment_async(audio_handler)

    except Exception as e:
        logger.error(f"Response routing failed: {e}")
        raise


def _print_response(response_text: str) -> None:
    """Print response to console."""
    try:
        display_text = response_text
        if len(response_text) > RESPONSE_PRINT_LENGTH_LIMIT:
            display_text = response_text[: RESPONSE_PRINT_LENGTH_LIMIT] + "\n...[truncated]"

        print("\n" + "=" * 80)
        print("ANGIRA RESPONSE:")
        print("=" * 80)
        print(display_text)
        print("=" * 80 + "\n")

        logger.info(f"Printed response ({len(response_text)} chars)")

    except Exception as e:
        logger.error(f"Failed to print response: {e}")
        raise


async def _speak_full_response_async(response_text: str, audio_handler) -> None:
    """Speak full response using TTS for simple queries."""
    try:
        logger.info("Speaking full response (simple query)")
        await audio_handler.speak_text(response_text)
        logger.info("Successfully played full speech output")
    except Exception as e:
        logger.error(f"Failed to speak full response: {e}")


async def _speak_conceptual_response_async(response_text: str, audio_handler) -> None:
    """Speak short explanation for conceptual queries."""
    try:
        logger.info("Speaking short explanation (conceptual query)")
        
        # Truncate to MAX_CONCEPTUAL_RESPONSE_LENGTH, ending at sentence boundary
        if len(response_text) > MAX_CONCEPTUAL_RESPONSE_LENGTH:
            truncated = response_text[:MAX_CONCEPTUAL_RESPONSE_LENGTH]
            last_period = truncated.rfind(".")
            if last_period > MAX_CONCEPTUAL_RESPONSE_LENGTH // 2:
                short_response = truncated[:last_period + 1]
            else:
                short_response = truncated.rstrip() + "..."
        else:
            short_response = response_text

        logger.debug(f"Conceptual TTS length: {len(short_response)} chars")
        await audio_handler.speak_text(short_response)
        logger.info("Successfully played conceptual speech output")
    except Exception as e:
        logger.error(f"Failed to speak conceptual response: {e}")


async def _speak_acknowledgment_async(audio_handler) -> None:
    """Speak brief acknowledgment for complex queries."""
    try:
        logger.info("Speaking acknowledgment (complex query)")
        await audio_handler.speak_text(SHORT_ACKNOWLEDGMENT)
        logger.info("Successfully played acknowledgment speech")
    except Exception as e:
        logger.error(f"Failed to speak acknowledgment: {e}")
        raise
