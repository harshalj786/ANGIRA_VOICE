"""
Main pipeline for Agnira Voice Assistant.
Orchestrates the complete flow: STT → Verbalization → Intent Classification → Reasoning → Routing
"""

import logging
from typing import Optional, Tuple
from core.speech_to_text import SpeechToText
from core.verbalizer import verbalize_query
from core.intent_classifier import classify_intent
from core.reasoning_engine import ReasoningEngine
from core.response_router import route_response
from models.intent_rules import ProcessedQuery

logger = logging.getLogger(__name__)


class AgniraPipeline:
    """
    Main pipeline orchestrating the complete Agnira conversation flow.

    Flow:
    1. Speech-to-text transcription
    2. Query verbalization (normalize math symbols)
    3. Intent classification (simple vs complex)
    4. GPT reasoning (only for reasoning, never speech)
    5. Response routing (print + TTS based on intent)
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.stt = SpeechToText()
        self.reasoning_engine = ReasoningEngine()
        logger.info("AgniraPipeline initialized")

    def process_audio(self, audio_input: bytes) -> Optional[ProcessedQuery]:
        """
        Process audio through the complete pipeline.

        Args:
            audio_input (bytes): Raw audio bytes or file path.

        Returns:
            Optional[ProcessedQuery]: Processed query with all transformations,
                                      or None if processing fails.
        """
        try:
            logger.info("Starting audio processing pipeline")

            # Step 1: Speech-to-Text
            logger.debug("Step 1: Transcribing speech to text...")
            transcribed_text = self.stt.transcribe(audio_input)

            if not transcribed_text:
                logger.warning("STT returned empty result")
                return None

            logger.info(f"Transcribed: '{transcribed_text}'")

            # Step 2: Verbalize query
            logger.debug("Step 2: Verbalizing query...")
            verbalized_text = verbalize_query(transcribed_text)
            logger.info(f"Verbalized: '{verbalized_text}'")

            # Step 3: Classify intent
            logger.debug("Step 3: Classifying intent...")
            intent = classify_intent(verbalized_text)
            logger.info(f"Intent classified as: {intent}")

            # Step 4: Get reasoning response
            logger.debug("Step 4: Sending to reasoning engine...")
            response = self.reasoning_engine.solve(verbalized_text, intent=intent)
            logger.info(f"Received response ({len(response)} chars)")

            # Create processed query result (response routing done by caller)
            processed_query = ProcessedQuery(
                original=transcribed_text,
                verbalized=verbalized_text,
                intent=intent,
                confidence=1.0,
                response=response,
            )

            logger.info("Audio processing pipeline completed successfully")
            return processed_query

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return None

    def process_text(self, text: str) -> Optional[ProcessedQuery]:
        """
        Process text query through the pipeline (bypassing STT).

        Useful for testing and debugging.

        Args:
            text (str): User query text.

        Returns:
            Optional[ProcessedQuery]: Processed query with all transformations,
                                      or None if processing fails.
        """
        try:
            logger.info(f"Starting text processing pipeline: '{text}'")

            if not text:
                logger.warning("Empty text input")
                return None

            # Step 1: Verbalize query
            logger.debug("Step 1: Verbalizing query...")
            verbalized_text = verbalize_query(text)
            logger.info(f"Verbalized: '{verbalized_text}'")

            # Step 2: Classify intent
            logger.debug("Step 2: Classifying intent...")
            intent = classify_intent(verbalized_text)
            logger.info(f"Intent classified as: {intent}")

            # Step 3: Get reasoning response
            logger.debug("Step 3: Sending to reasoning engine...")
            response = self.reasoning_engine.solve(verbalized_text, intent=intent)
            logger.info(f"Received response ({len(response)} chars)")

            # Create processed query result (response routing done by caller)
            processed_query = ProcessedQuery(
                original=text,
                verbalized=verbalized_text,
                intent=intent,
                confidence=1.0,
                response=response,
            )

            logger.info("Text processing pipeline completed successfully")
            return processed_query

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return None

    def get_pipeline_info(self) -> dict:
        """
        Get information about the pipeline components.

        Returns:
            dict: Information about all pipeline stages.
        """
        return {
            "stages": [
                "speech_to_text",
                "verbalization",
                "intent_classification",
                "reasoning",
                "response_routing",
            ],
            "components": {
                "stt": self.stt.get_model_info(),
                "reasoning_engine": self.reasoning_engine.get_model_info(),
            },
            "optimization": "Cost-efficient response routing based on intent",
        }
