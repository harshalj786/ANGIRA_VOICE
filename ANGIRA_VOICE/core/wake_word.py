"""
Wake word detection module for Agnira Voice Assistant.
Uses microphone input and Gemini for transcription-based detection.
"""

import asyncio
import logging
import struct
from typing import Optional

import numpy as np
import pyaudio
from google import genai
from google.genai import types

from config.settings import settings
from config.constants import (
    WAKE_WORD,
    WAKE_WORD_CONFIDENCE_THRESHOLD,
    SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    SILENCE_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Global audio handler for wake word detection
_audio_handler: Optional["WakeWordDetector"] = None


class WakeWordDetector:
    """
    Detects the wake word "Angira" using microphone input.
    Uses Gemini for transcription-based wake word detection.
    """

    def __init__(self):
        """Initialize wake word detector."""
        self.api_key = settings.get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.pya = pyaudio.PyAudio()
        
        # Audio config
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = SAMPLE_RATE
        self.chunk_size = AUDIO_CHUNK_SIZE
        
        self._stream: Optional[pyaudio.Stream] = None
        logger.info("WakeWordDetector initialized")

    def _calculate_rms(self, audio_data: bytes) -> float:
        """Calculate RMS for silence detection."""
        try:
            samples = struct.unpack(f"{len(audio_data)//2}h", audio_data)
            rms = np.sqrt(np.mean(np.square(np.array(samples, dtype=np.float32))))
            return rms / 32768.0
        except Exception:
            return 0.0

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM data to WAV format by adding a proper header."""
        sample_rate = self.rate
        channels = self.channels
        bits_per_sample = 16
        
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        data_size = len(pcm_data)
        
        # WAV header (44 bytes)
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,  # File size - 8
            b'WAVE',
            b'fmt ',
            16,  # Subchunk1 size (16 for PCM)
            1,   # Audio format (1 = PCM)
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b'data',
            data_size
        )
        
        return header + pcm_data

    def _open_stream(self) -> pyaudio.Stream:
        """Open microphone stream."""
        mic_info = self.pya.get_default_input_device_info()
        return self.pya.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=int(mic_info["index"]),
            frames_per_buffer=self.chunk_size,
        )

    def listen_for_wake_word(self, timeout: float = 10.0) -> bool:
        """
        Listen for the wake word "Angira" in audio stream.
        
        Args:
            timeout: Maximum seconds to listen.
            
        Returns:
            bool: True if wake word detected, False otherwise.
        """
        logger.debug(f"Listening for wake word: '{WAKE_WORD}' (timeout: {timeout}s)")
        
        try:
            stream = self._open_stream()
            audio_chunks = []
            has_speech = False
            silence_frames = 0
            max_silence = int(1.5 * self.rate / self.chunk_size)  # 1.5s silence
            max_frames = int(timeout * self.rate / self.chunk_size)
            
            for frame_count in range(max_frames):
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as e:
                    logger.warning(f"Audio read error: {e}")
                    continue
                
                rms = self._calculate_rms(data)
                
                if rms > SILENCE_THRESHOLD:
                    has_speech = True
                    silence_frames = 0
                    audio_chunks.append(data)
                elif has_speech:
                    silence_frames += 1
                    audio_chunks.append(data)
                    
                    # Stop after 1.5s of silence following speech
                    if silence_frames >= max_silence:
                        break
            
            stream.stop_stream()
            stream.close()
            
            if not audio_chunks:
                logger.debug("No speech detected")
                return False
            
            # Transcribe and check for wake word
            audio_data = b"".join(audio_chunks)
            logger.debug(f"Captured {len(audio_data)} bytes, transcribing...")
            
            try:
                # Convert PCM to WAV format
                wav_data = self._pcm_to_wav(audio_data)
                
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        types.Content(
                            parts=[
                                types.Part.from_bytes(
                                    data=wav_data,
                                    mime_type="audio/wav"
                                ),
                                types.Part.from_text(
                                    text="Transcribe this audio. Return only the transcription."
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
                
                transcription = response.text.strip().lower()
                logger.debug(f"Transcription: '{transcription}'")
                
                # Check for wake word (fuzzy match)
                wake_word_lower = WAKE_WORD.lower()
                detected = (
                    wake_word_lower in transcription or
                    "angira" in transcription or  # Primary wake word
                    "anira" in transcription or   # Common mishearing
                    "agira" in transcription or
                    "anjira" in transcription
                )
                
                if detected:
                    logger.info(f"Wake word detected in: '{transcription}'")
                    return True
                    
            except Exception as e:
                logger.warning(f"Transcription error: {e}")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Wake word detection failed: {e}")
            return False

    async def listen_for_wake_word_async(self, timeout: float = 10.0) -> bool:
        """Async version of listen_for_wake_word."""
        return await asyncio.to_thread(self.listen_for_wake_word, timeout)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._stream:
            self._stream.close()
        self.pya.terminate()


def get_detector() -> WakeWordDetector:
    """Get or create the global wake word detector."""
    global _audio_handler
    if _audio_handler is None:
        _audio_handler = WakeWordDetector()
    return _audio_handler


def listen_for_wake_word(timeout: float = 10.0, use_demo_mode: bool = False) -> bool:
    """
    Listen for the wake word \"Angira\" in audio stream.
    
    Args:
        timeout: Maximum seconds to listen.
        use_demo_mode: If True, skip real audio and return True immediately.

    Returns:
        bool: True if wake word detected, False otherwise.
    """
    if use_demo_mode:
        logger.debug("Demo mode: Simulating wake word detection")
        return True
    
    detector = get_detector()
    return detector.listen_for_wake_word(timeout)


async def listen_for_wake_word_async(timeout: float = 10.0, use_demo_mode: bool = False) -> bool:
    """Async version of listen_for_wake_word."""
    if use_demo_mode:
        return True
    
    detector = get_detector()
    return await detector.listen_for_wake_word_async(timeout)
