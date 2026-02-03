"""
Gemini Live API Audio Handler for real-time bidirectional audio streaming.
Handles microphone input, speech-to-text, text-to-speech, and audio playback.
"""

import asyncio
import logging
import struct
import numpy as np
from typing import Optional, Callable, AsyncGenerator
from dataclasses import dataclass

import pyaudio
from google import genai
from google.genai import types

from config.settings import settings
from config.constants import (
    SAMPLE_RATE,
    OUTPUT_SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    MAX_AUDIO_DURATION,
    GEMINI_LIVE_MODEL,
    WAKE_WORD,
    REASONING_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio configuration for PyAudio."""
    format: int = pyaudio.paInt16
    channels: int = 1
    input_rate: int = SAMPLE_RATE
    output_rate: int = OUTPUT_SAMPLE_RATE
    chunk_size: int = AUDIO_CHUNK_SIZE


class AudioLiveHandler:
    """
    Handles real-time audio streaming with Gemini Live API.
    
    Supports:
    - Microphone capture with silence detection
    - Real-time speech-to-text via Gemini
    - Text-to-speech output via Gemini
    - Audio playback through speakers
    """

    def __init__(self):
        """Initialize AudioLiveHandler with Gemini client and PyAudio."""
        self.api_key = settings.get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        self.config = AudioConfig()
        self.pya = pyaudio.PyAudio()
        
        # Audio streams
        self._input_stream: Optional[pyaudio.Stream] = None
        self._output_stream: Optional[pyaudio.Stream] = None
        
        # Async queues for audio data
        self._mic_queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._speaker_queue: asyncio.Queue = asyncio.Queue()
        
        # State
        self._is_recording = False
        self._is_playing = False
        
        logger.info(f"AudioLiveHandler initialized with model: {GEMINI_LIVE_MODEL}")

    def _open_input_stream(self) -> pyaudio.Stream:
        """Open microphone input stream."""
        mic_info = self.pya.get_default_input_device_info()
        logger.info(f"Using input device: {mic_info['name']}")
        
        return self.pya.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.input_rate,
            input=True,
            input_device_index=int(mic_info["index"]),
            frames_per_buffer=self.config.chunk_size,
        )

    def _open_output_stream(self) -> pyaudio.Stream:
        """Open speaker output stream."""
        return self.pya.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.output_rate,
            output=True,
        )

    def _calculate_rms(self, audio_data: bytes) -> float:
        """Calculate RMS (root mean square) of audio chunk for silence detection."""
        try:
            samples = struct.unpack(f"{len(audio_data)//2}h", audio_data)
            rms = np.sqrt(np.mean(np.square(np.array(samples, dtype=np.float32))))
            return rms / 32768.0  # Normalize to 0-1 range
        except Exception:
            return 0.0

    def _calculate_energy_features(self, audio_data: bytes, prev_rms: float = 0.0) -> tuple[float, float, float]:
        """
        Calculate multiple energy features for aggressive speech detection.
        
        Returns:
            Tuple of (rms, zero_crossing_rate, energy_delta)
        """
        try:
            samples = struct.unpack(f"{len(audio_data)//2}h", audio_data)
            samples_array = np.array(samples, dtype=np.float32)
            
            # RMS
            rms = np.sqrt(np.mean(np.square(samples_array))) / 32768.0
            
            # Zero-crossing rate (normalized)
            zero_crossings = np.sum(np.abs(np.diff(np.sign(samples_array)))) / 2
            zcr = zero_crossings / len(samples_array)
            
            # Energy delta (spike detection)
            energy_delta = abs(rms - prev_rms)
            
            return rms, zcr, energy_delta
        except Exception:
            return 0.0, 0.0, 0.0
            samples = struct.unpack(f"{len(audio_data)//2}h", audio_data)
            rms = np.sqrt(np.mean(np.square(np.array(samples, dtype=np.float32))))
            return rms / 32768.0  # Normalize to 0-1 range
        except Exception:
            return 0.0

    async def capture_audio_until_silence(self) -> bytes:
        """
        Capture audio from microphone until silence is detected.
        
        Returns:
            bytes: Captured audio data in PCM format.
        """
        logger.info("Starting audio capture...")
        self._input_stream = await asyncio.to_thread(self._open_input_stream)
        
        audio_chunks = []
        silence_frames = 0
        silence_threshold_frames = int(SILENCE_DURATION * self.config.input_rate / self.config.chunk_size)
        max_frames = int(MAX_AUDIO_DURATION * self.config.input_rate / self.config.chunk_size)
        total_frames = 0
        has_speech = False
        
        try:
            while total_frames < max_frames:
                data = await asyncio.to_thread(
                    self._input_stream.read,
                    self.config.chunk_size,
                    exception_on_overflow=False
                )
                audio_chunks.append(data)
                total_frames += 1
                
                rms = self._calculate_rms(data)
                
                if rms > SILENCE_THRESHOLD:
                    has_speech = True
                    silence_frames = 0
                else:
                    silence_frames += 1
                
                # Stop if we've had speech and then silence
                if has_speech and silence_frames >= silence_threshold_frames:
                    logger.info(f"Silence detected after {total_frames} frames")
                    break
                    
        finally:
            self._input_stream.stop_stream()
            self._input_stream.close()
            self._input_stream = None
        
        audio_data = b"".join(audio_chunks)
        duration = len(audio_data) / (self.config.input_rate * 2)  # 16-bit = 2 bytes
        logger.info(f"Captured {duration:.2f}s of audio ({len(audio_data)} bytes)")
        
        return audio_data

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Convert raw PCM data to WAV format by adding a proper header."""
        import struct
        
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

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio to text using Gemini.
        
        Args:
            audio_data: Raw PCM audio bytes.
            
        Returns:
            Transcribed text.
        """
        logger.info("Transcribing audio with Gemini...")
        
        try:
            # Convert PCM to WAV format for Gemini API
            wav_data = self._pcm_to_wav(audio_data, sample_rate=self.config.input_rate)
            
            # Use standard Gemini model for transcription
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(
                                data=wav_data,
                                mime_type="audio/wav"
                            ),
                            types.Part.from_text(text="Transcribe this audio exactly as spoken, word for word. If you hear a name like 'Angira', 'Anjira', or similar, transcribe it exactly. Return only the transcription, nothing else.")
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    automaticFunctionCalling=types.AutomaticFunctionCallingConfig(
                        maximumRemoteCalls=100
                    )
                )
            )
            
            transcription = response.text.strip()
            # Print to console so user can see what's being heard
            print(f"   📝 Heard: \"{transcription}\"")
            logger.info(f"Transcription: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def listen_for_wake_word(self, timeout: float = 5.0) -> bool:
        """
        Listen for wake word in audio stream.
        
        Args:
            timeout: Maximum seconds to listen for wake word.
            
        Returns:
            True if wake word detected, False otherwise.
        """
        logger.info(f"Listening for wake word '{WAKE_WORD}'...")
        
        try:
            # Capture short audio segment
            self._input_stream = await asyncio.to_thread(self._open_input_stream)
            
            chunks_needed = int(timeout * self.config.input_rate / self.config.chunk_size)
            audio_chunks = []
            
            for _ in range(chunks_needed):
                data = await asyncio.to_thread(
                    self._input_stream.read,
                    self.config.chunk_size,
                    exception_on_overflow=False
                )
                audio_chunks.append(data)
                
                # Check for speech activity
                rms = self._calculate_rms(data)
                if rms > SILENCE_THRESHOLD:
                    # Capture a bit more after detecting speech
                    for _ in range(int(2.0 * self.config.input_rate / self.config.chunk_size)):
                        data = await asyncio.to_thread(
                            self._input_stream.read,
                            self.config.chunk_size,
                            exception_on_overflow=False
                        )
                        audio_chunks.append(data)
                        if self._calculate_rms(data) < SILENCE_THRESHOLD:
                            break
                    break
                    
        finally:
            if self._input_stream:
                self._input_stream.stop_stream()
                self._input_stream.close()
                self._input_stream = None
        
        audio_data = b"".join(audio_chunks)
        
        if len(audio_data) < 1000:
            return False
            
        # Transcribe and check for wake word
        try:
            transcription = await self.transcribe_audio(audio_data)
            transcription_lower = transcription.lower()
            
            # Fuzzy matching for various pronunciations/transcriptions
            wake_word_variants = [
                WAKE_WORD.lower(),  # angira
                "angira",
                "angeera",
                "anjira",
                "anira",
                "angela",  # common mishearing
                "anger",   # partial match
                "on gira",
                "an gira",
            ]
            
            detected = any(variant in transcription_lower for variant in wake_word_variants)
            
            if detected:
                logger.info(f"Wake word detected in: '{transcription}'")
            else:
                logger.debug(f"No wake word in: '{transcription}'")
            return detected
        except Exception as e:
            logger.warning(f"Wake word detection failed: {e}")
            return False

    async def speak_text(self, text: str) -> None:
        """
        Convert text to speech and play through speakers using Gemini Live API.
        
        Args:
            text: Text to speak.
        """
        if not text:
            return
            
        logger.info(f"Speaking: {text[:50]}...")
        
        try:
            # Configure Live API for TTS with system instruction to read verbatim
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Charon"  # Available: Puck, Charon, Kore, Fenrir, Aoede
                        )
                    )
                ),
                system_instruction=types.Content(
                    parts=[types.Part.from_text(
                        text="You are a text-to-speech system. Read the following text EXACTLY as written, word for word. Do not add, remove, or change any words. Do not add commentary or responses. Simply read the text aloud verbatim."
                    )]
                ),
            )
            
            async with self.client.aio.live.connect(
                model=GEMINI_LIVE_MODEL,
                config=config
            ) as session:
                # Send text to be spoken with explicit instruction
                await session.send_client_content(
                    turns=[types.Content(parts=[types.Part.from_text(text=f"Read this exactly: {text}")])],
                    turn_complete=True
                )
                
                # Open output stream
                output_stream = await asyncio.to_thread(self._open_output_stream)
                
                try:
                    # Receive and play audio
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    await asyncio.to_thread(
                                        output_stream.write,
                                        part.inline_data.data
                                    )
                        
                        # Check if turn is complete
                        if response.server_content and response.server_content.turn_complete:
                            break
                finally:
                    output_stream.stop_stream()
                    output_stream.close()
                    
            logger.info("Speech playback complete")
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise

    async def converse_realtime(
        self,
        system_instruction: str = "You are Angira, a helpful voice assistant."
    ) -> tuple[str, str]:
        """
        Have a real-time conversation: listen to user, get Gemini response.
        
        Args:
            system_instruction: System prompt for Gemini.
            
        Returns:
            Tuple of (user_transcription, assistant_response).
        """
        logger.info("Starting real-time conversation...")
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO", "TEXT"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=system_instruction)]
            ),
        )
        
        user_text = ""
        assistant_text = ""
        
        async with self.client.aio.live.connect(
            model=GEMINI_LIVE_MODEL,
            config=config
        ) as session:
            # Open streams
            input_stream = await asyncio.to_thread(self._open_input_stream)
            output_stream = await asyncio.to_thread(self._open_output_stream)
            
            try:
                # Send audio in real-time
                async def send_audio():
                    nonlocal user_text
                    silence_count = 0
                    max_silence = int(SILENCE_DURATION * self.config.input_rate / self.config.chunk_size)
                    has_speech = False
                    
                    while True:
                        data = await asyncio.to_thread(
                            input_stream.read,
                            self.config.chunk_size,
                            exception_on_overflow=False
                        )
                        
                        rms = self._calculate_rms(data)
                        if rms > SILENCE_THRESHOLD:
                            has_speech = True
                            silence_count = 0
                        else:
                            silence_count += 1
                        
                        await session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type="audio/pcm")
                        )
                        
                        if has_speech and silence_count >= max_silence:
                            break
                
                # Receive response
                async def receive_response():
                    nonlocal assistant_text
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    await asyncio.to_thread(
                                        output_stream.write,
                                        part.inline_data.data
                                    )
                                if part.text:
                                    assistant_text += part.text
                        
                        # Get transcription from input
                        if response.server_content and response.server_content.input_transcription:
                            user_text = response.server_content.input_transcription.text or ""
                        
                        if response.server_content and response.server_content.turn_complete:
                            break
                
                # Run send and receive concurrently
                await asyncio.gather(send_audio(), receive_response())
                
            finally:
                input_stream.stop_stream()
                input_stream.close()
                output_stream.stop_stream()
                output_stream.close()
        
        logger.info(f"User said: {user_text}")
        logger.info(f"Assistant replied: {assistant_text[:100]}...")
        
        return user_text, assistant_text

    async def stream_conversation(
        self,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_response_text: Optional[Callable[[str], None]] = None,
        on_interrupted: Optional[Callable[[], None]] = None,
    ) -> tuple[str, str, bool]:
        """
        Ultra-low latency streaming conversation with <100ms interruption detection.
        
        Architecture:
        1. Single mic capture task pushes to shared queue
        2. Gemini streaming consumes from queue (1024-frame chunks)
        3. Interruption detector consumes from queue (256-frame windows)
        4. Hard audio flush on interruption for instant silence
        
        Args:
            on_transcription: Callback when user transcription is available.
            on_response_text: Callback when response text chunks arrive.
            on_interrupted: Callback when user interrupts the response.
            
        Returns:
            Tuple of (user_transcription, assistant_response_text, was_interrupted).
        """
        logger.info("Starting streaming conversation (ultra-low latency mode)...")
        
        # Shorter system prompt for Live API compatibility
        short_system_prompt = (
            "You are Angira, a JEE doubt-solving voice assistant. "
            "Speak clearly and concisely. Explain concepts step by step. "
            "Use verbal math descriptions like 'x squared' instead of 'x^2'. "
            "Be patient and teacher-like. Never be condescending."
        )
        
        config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": short_system_prompt,
        }
        
        # Shared state
        user_text = ""
        assistant_text = ""
        was_interrupted = False
        prev_rms = 0.0
        
        # Events for coordination
        interrupt_detected = asyncio.Event()
        response_complete = asyncio.Event()
        send_complete = asyncio.Event()
        playback_started = asyncio.Event()
        
        # Shared audio queue for single-reader architecture
        # Small chunks (256 frames = 16ms) for fast interruption detection
        INTERRUPT_CHUNK_SIZE = 256
        audio_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        
        async with self.client.aio.live.connect(
            model=GEMINI_LIVE_MODEL,
            config=config
        ) as session:
            # Open streams
            input_stream = await asyncio.to_thread(self._open_input_stream)
            output_stream = await asyncio.to_thread(self._open_output_stream)
            
            try:
                async def mic_capture():
                    """
                    SINGLE microphone reader - pushes ALL audio to shared queue.
                    This is the ONLY task that reads from input_stream.
                    """
                    logger.debug("Mic capture started (single reader)")
                    
                    while not response_complete.is_set() or not send_complete.is_set():
                        try:
                            # Read smaller chunks for faster interruption detection
                            data = await asyncio.to_thread(
                                input_stream.read,
                                INTERRUPT_CHUNK_SIZE,
                                exception_on_overflow=False
                            )
                            
                            # Non-blocking put - drop frames if queue is full
                            try:
                                audio_queue.put_nowait(data)
                            except asyncio.QueueFull:
                                pass  # Drop frame rather than block
                                
                        except Exception as e:
                            logger.warning(f"Mic capture error: {e}")
                            break
                    
                    logger.debug("Mic capture ended")
                
                async def send_audio():
                    """Stream audio to Gemini - consumes from shared queue."""
                    nonlocal user_text
                    silence_count = 0
                    max_silence = int(SILENCE_DURATION * self.config.input_rate / INTERRUPT_CHUNK_SIZE)
                    has_speech = False
                    audio_buffer = b""
                    
                    logger.debug("Audio send loop started")
                    
                    while True:
                        try:
                            # Get audio from shared queue with timeout
                            try:
                                data = await asyncio.wait_for(
                                    audio_queue.get(), 
                                    timeout=0.1
                                )
                            except asyncio.TimeoutError:
                                continue
                            
                            # Accumulate small chunks into larger buffer for Gemini
                            audio_buffer += data
                            
                            rms = self._calculate_rms(data)
                            if rms > SILENCE_THRESHOLD:
                                has_speech = True
                                silence_count = 0
                            else:
                                silence_count += 1
                            
                            # Send to Gemini when we have enough data (1024 frames worth)
                            if len(audio_buffer) >= self.config.chunk_size * 2:  # 2 bytes per sample
                                await session.send_realtime_input(
                                    audio={"data": audio_buffer, "mime_type": "audio/pcm"}
                                )
                                audio_buffer = b""
                            
                            # Stop after detecting end of speech
                            if has_speech and silence_count >= max_silence:
                                # Send any remaining buffer
                                if audio_buffer:
                                    await session.send_realtime_input(
                                        audio={"data": audio_buffer, "mime_type": "audio/pcm"}
                                    )
                                logger.debug("End of speech detected")
                                break
                                
                        except Exception as e:
                            logger.warning(f"Audio send error: {e}")
                            break
                    
                    send_complete.set()
                    logger.debug("Audio send complete")
                
                async def monitor_interruption():
                    """
                    Aggressive interruption detection with <100ms latency.
                    Uses energy spike detection, not conservative VAD.
                    """
                    nonlocal was_interrupted, prev_rms
                    
                    # Wait for playback to start
                    try:
                        await asyncio.wait_for(playback_started.wait(), timeout=10.0)
                    except asyncio.TimeoutError:
                        return
                    
                    if response_complete.is_set():
                        return
                    
                    logger.debug("Interruption monitor active")
                    
                    # Aggressive detection thresholds
                    ENERGY_SPIKE_THRESHOLD = 0.008  # Sudden energy increase
                    ZCR_SPIKE_THRESHOLD = 0.15      # Voice typically has higher ZCR
                    RMS_THRESHOLD = SILENCE_THRESHOLD * 1.0  # Lowered for sensitivity
                    
                    while not response_complete.is_set():
                        try:
                            # Get audio from shared queue (non-blocking peek equivalent)
                            try:
                                data = await asyncio.wait_for(
                                    audio_queue.get(),
                                    timeout=0.02  # 20ms timeout for responsiveness
                                )
                            except asyncio.TimeoutError:
                                continue
                            
                            # Calculate multiple features for aggressive detection
                            rms, zcr, energy_delta = self._calculate_energy_features(data, prev_rms)
                            prev_rms = rms
                            
                            # AGGRESSIVE: Trigger on ANY of these conditions
                            is_interrupt = (
                                rms > RMS_THRESHOLD or           # Basic energy threshold
                                energy_delta > ENERGY_SPIKE_THRESHOLD or  # Sudden spike
                                (zcr > ZCR_SPIKE_THRESHOLD and rms > RMS_THRESHOLD * 0.5)  # Voice-like
                            )
                            
                            if is_interrupt:
                                logger.info(f"INTERRUPT! RMS={rms:.4f}, ZCR={zcr:.3f}, Delta={energy_delta:.4f}")
                                was_interrupted = True
                                interrupt_detected.set()
                                
                                # HARD FLUSH: Stop speaker immediately
                                try:
                                    output_stream.stop_stream()
                                    output_stream.start_stream()
                                except Exception as e:
                                    logger.warning(f"Flush error: {e}")
                                
                                if on_interrupted:
                                    on_interrupted()
                                break
                                
                        except Exception as e:
                            logger.warning(f"Interruption monitor error: {e}")
                            break
                    
                    logger.debug("Interruption monitor ended")
                
                async def receive_response():
                    """Receive and play response audio with instant-stop capability."""
                    nonlocal assistant_text, user_text
                    
                    logger.debug("Response receive loop started")
                    
                    async for response in session.receive():
                        # Check for interruption FIRST
                        if interrupt_detected.is_set():
                            logger.debug("Response interrupted by user")
                            break
                            
                        try:
                            if response.server_content:
                                # Handle input transcription
                                if response.server_content.input_transcription:
                                    transcript = response.server_content.input_transcription.text or ""
                                    if transcript:
                                        user_text = transcript
                                        if on_transcription:
                                            on_transcription(transcript)
                                
                                # Handle model response
                                if response.server_content.model_turn:
                                    for part in response.server_content.model_turn.parts:
                                        if interrupt_detected.is_set():
                                            break
                                            
                                        if part.inline_data and part.inline_data.data:
                                            # Signal that playback has started
                                            if not playback_started.is_set():
                                                playback_started.set()
                                                logger.debug("Playback started")
                                            
                                            # Check interrupt before EVERY write
                                            if not interrupt_detected.is_set():
                                                await asyncio.to_thread(
                                                    output_stream.write,
                                                    part.inline_data.data
                                                )
                                        
                                        if part.text:
                                            assistant_text += part.text
                                            if on_response_text:
                                                on_response_text(part.text)
                                
                                if response.server_content.turn_complete:
                                    logger.debug("Turn complete")
                                    break
                                    
                        except Exception as e:
                            logger.warning(f"Response receive error: {e}")
                            break
                    
                    response_complete.set()
                    logger.debug("Response receive complete")
                
                # Run all tasks concurrently
                await asyncio.gather(
                    mic_capture(),
                    send_audio(),
                    receive_response(),
                    monitor_interruption(),
                    return_exceptions=True
                )
                
            finally:
                # Clean shutdown
                try:
                    input_stream.stop_stream()
                    input_stream.close()
                except Exception:
                    pass
                    
                try:
                    output_stream.stop_stream()
                    output_stream.close()
                except Exception:
                    pass
                    
                # Clear queue
                while not audio_queue.empty():
                    try:
                        audio_queue.get_nowait()
                    except:
                        break
                
                # Brief delay for audio device reset
                await asyncio.sleep(0.05)
        
        logger.info(f"Conversation complete - User: '{user_text[:50] if user_text else ''}...', Response: {len(assistant_text)} chars, Interrupted: {was_interrupted}")
        
        return user_text, assistant_text, was_interrupted

    def play_audio_sync(self, audio_data: bytes, sample_rate: int = OUTPUT_SAMPLE_RATE) -> None:
        """
        Play audio data synchronously through speakers.
        
        Args:
            audio_data: PCM audio bytes to play.
            sample_rate: Sample rate of audio data.
        """
        stream = self.pya.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=sample_rate,
            output=True,
        )
        
        try:
            stream.write(audio_data)
        finally:
            stream.stop_stream()
            stream.close()

    def get_model_info(self) -> dict:
        """Get information about the current configuration."""
        return {
            "model": GEMINI_LIVE_MODEL,
            "api": "Google Gemini Live API",
            "input_sample_rate": self.config.input_rate,
            "output_sample_rate": self.config.output_rate,
            "chunk_size": self.config.chunk_size,
        }

    def cleanup(self) -> None:
        """Clean up PyAudio resources."""
        if self._input_stream:
            self._input_stream.close()
        if self._output_stream:
            self._output_stream.close()
        self.pya.terminate()
        logger.info("AudioLiveHandler cleaned up")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass
