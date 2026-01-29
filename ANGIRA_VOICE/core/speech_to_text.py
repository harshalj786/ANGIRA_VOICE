"""
Speech-to-text module using Gemini Live API.
Converts user speech to text with real microphone capture.
"""

import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types

from config.settings import settings
from config.constants import SAMPLE_RATE, GEMINI_LIVE_MODEL

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Speech-to-text converter using Gemini API.
    Transcribes audio input to text.
    """

    def __init__(self):
        """Initialize SpeechToText with Gemini API credentials."""
        self.api_key = settings.get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.model = "gemini-2.0-flash"  # Use standard model for transcription
        logger.info("SpeechToText initialized with Gemini API")

    def transcribe(self, audio_input: bytes) -> str:
        """
        Transcribe audio to text using Gemini.

        Args:
            audio_input: Raw PCM audio bytes (16kHz, mono, 16-bit).

        Returns:
            str: Transcribed text from audio.

        Raises:
            ValueError: If audio input is invalid.
            Exception: If API call fails.
        """
        try:
            if isinstance(audio_input, str):
                # Handle file path
                logger.info(f"Transcribing audio from file: {audio_input}")
                with open(audio_input, "rb") as f:
                    audio_bytes = f.read()
            else:
                audio_bytes = audio_input

            if not audio_bytes or len(audio_bytes) < 100:
                raise ValueError("Audio input too short or empty")

            logger.info(f"Transcribing {len(audio_bytes)} bytes of audio...")

            # Use Gemini to transcribe audio
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(
                                data=audio_bytes,
                                mime_type=f"audio/pcm;rate={SAMPLE_RATE}"
                            ),
                            types.Part.from_text(
                                text="Transcribe this audio exactly as spoken. "
                                "Return only the transcription text, nothing else."
                            )
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    automaticFunctionCalling=types.AutomaticFunctionCallingConfig(
                        maximumRemoteCalls=100
                    )
                )
            )

            transcribed_text = response.text.strip()
            logger.info(f"Successfully transcribed: {transcribed_text[:50]}...")
            return transcribed_text

        except FileNotFoundError as e:
            logger.error(f"Audio file not found: {e}")
            raise ValueError(f"Audio file not found: {e}") from e
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def transcribe_async(self, audio_input: bytes) -> str:
        """
        Async version of transcribe.

        Args:
            audio_input: Raw PCM audio bytes.

        Returns:
            str: Transcribed text.
        """
        return await asyncio.to_thread(self.transcribe, audio_input)

    def transcribe_streaming(self, audio_chunks: list[bytes]) -> str:
        """
        Transcribe streaming audio chunks.

        Args:
            audio_chunks: List of PCM audio byte chunks.

        Returns:
            str: Combined transcription.
        """
        combined_audio = b"".join(audio_chunks)
        return self.transcribe(combined_audio)

    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            dict: Model information and capabilities.
        """
        return {
            "model": self.model,
            "api": "Google Gemini",
            "capabilities": ["speech-to-text", "audio-transcription"],
            "sample_rate": SAMPLE_RATE,
        }
