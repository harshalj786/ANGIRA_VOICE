"""
Text-to-speech module using Gemini Live API.
Converts text responses to speech with real audio output.
"""

import asyncio
import logging
from typing import Optional

import pyaudio
from google import genai
from google.genai import types

from config.settings import settings
from config.constants import (
    MAX_SIMPLE_RESPONSE_LENGTH,
    MAX_CONCEPTUAL_RESPONSE_LENGTH,
    OUTPUT_SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    GEMINI_LIVE_MODEL,
)

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Text-to-speech converter using Gemini Live API.
    Generates and plays speech output through speakers.
    """

    def __init__(self):
        """Initialize TextToSpeech with Gemini API credentials."""
        self.api_key = settings.get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.model = GEMINI_LIVE_MODEL
        self.pya = pyaudio.PyAudio()
        
        # Audio configuration
        self.format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = OUTPUT_SAMPLE_RATE
        
        logger.info(f"TextToSpeech initialized with Gemini Live API model: {self.model}")

    def speak(self, text: str, play_audio: bool = True) -> bytes:
        """
        Convert text to speech using Gemini Live API.

        Args:
            text: Text to convert to speech.
            play_audio: Whether to play audio through speakers (default True).

        Returns:
            bytes: Audio content in PCM format.

        Raises:
            ValueError: If text is empty or too long.
            Exception: If API call fails.
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        if len(text) > MAX_SIMPLE_RESPONSE_LENGTH:
            logger.warning(
                f"Text length {len(text)} exceeds maximum {MAX_SIMPLE_RESPONSE_LENGTH}. "
                "Truncating for TTS."
            )
            text = text[:MAX_SIMPLE_RESPONSE_LENGTH]

        logger.info(f"Generating speech for: {text[:50]}...")
        
        # Handle being called from within an existing event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self._speak_async(text, play_audio))
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self._speak_async(text, play_audio))

    async def _speak_async(self, text: str, play_audio: bool = True) -> bytes:
        """
        Async implementation of speak.
        
        Args:
            text: Text to speak.
            play_audio: Whether to play audio.
            
        Returns:
            bytes: Audio data.
        """
        audio_chunks = []
        
        try:
            # Configure Live API for TTS
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Charon"  # Options: Puck, Charon, Kore, Fenrir, Aoede
                        )
                    )
                ),
            )
            
            output_stream = None
            if play_audio:
                output_stream = self.pya.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                )
            
            try:
                async with self.client.aio.live.connect(
                    model=self.model,
                    config=config
                ) as session:
                    # Send text to be spoken
                    await session.send_client_content(
                        turns=[types.Content(parts=[types.Part.from_text(text=text)])],
                        turn_complete=True
                    )
                    
                    # Receive and play audio
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    chunk = part.inline_data.data
                                    audio_chunks.append(chunk)
                                    if play_audio and output_stream:
                                        output_stream.write(chunk)
                        
                        if response.server_content and response.server_content.turn_complete:
                            break
                            
            finally:
                if output_stream:
                    output_stream.stop_stream()
                    output_stream.close()
                    
            audio_data = b"".join(audio_chunks)
            logger.info(f"Generated speech: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise

    async def speak_async(self, text: str, play_audio: bool = True) -> bytes:
        """
        Public async method to convert text to speech.
        
        Args:
            text: Text to speak.
            play_audio: Whether to play through speakers.
            
        Returns:
            bytes: Audio data.
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        if len(text) > MAX_SIMPLE_RESPONSE_LENGTH:
            text = text[:MAX_SIMPLE_RESPONSE_LENGTH]
            
        return await self._speak_async(text, play_audio)

    def play_audio(self, audio_bytes: bytes) -> None:
        """
        Play audio bytes through speakers.
        
        Args:
            audio_bytes: PCM audio data to play.
        """
        stream = self.pya.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
        )
        
        try:
            stream.write(audio_bytes)
        finally:
            stream.stop_stream()
            stream.close()

    def save_speech(self, audio_bytes: bytes, output_path: str) -> None:
        """
        Save speech output to file.

        Args:
            audio_bytes: Audio content to save.
            output_path: Path to save audio file.

        Raises:
            IOError: If file cannot be written.
        """
        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Speech saved to {output_path}")
        except IOError as e:
            logger.error(f"Failed to save speech to {output_path}: {e}")
            raise

    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            dict: Model information and capabilities.
        """
        return {
            "model": self.model,
            "api": "Gemini Live API",
            "capabilities": ["text-to-speech", "real-time-audio"],
            "sample_rate": self.sample_rate,
            "voice": "Puck",
        }

    def cleanup(self) -> None:
        """Clean up PyAudio resources."""
        self.pya.terminate()
        logger.info("TextToSpeech cleaned up")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass
