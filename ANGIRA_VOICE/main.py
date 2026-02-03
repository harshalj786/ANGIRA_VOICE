"""
Main entry point for Angira Voice Assistant.
Supports both real audio mode and demo (text) mode.
"""

import argparse
import asyncio
import logging
import sys
import signal
from typing import Optional

from utils.logger import setup_logging, get_logger
from config.settings import settings
from core.wake_word import listen_for_wake_word
from core.audio_live import AudioLiveHandler
from core.response_router import route_response_async
from pipelines.agnira_pipeline import AgniraPipeline

# Setup logging
setup_logging()
logger = get_logger(__name__)


class AgniraApp:
    """
    Main Agnira Voice Assistant Application.

    Supports two modes:
    - Real audio mode: Uses microphone for input, speakers for output
    - Demo mode: Uses text input for testing
    """

    def __init__(self, use_audio: bool = True):
        """
        Initialize Agnira application.
        
        Args:
            use_audio: If True, use real microphone/speaker. If False, use text demo.
        """
        self.running = True
        self.use_audio = use_audio
        self.pipeline = AgniraPipeline()
        
        if use_audio:
            self.audio_handler = AudioLiveHandler()
            logger.info("Agnira Voice Assistant initialized with REAL AUDIO mode")
        else:
            self.audio_handler = None
            logger.info("Agnira Voice Assistant initialized in DEMO (text) mode")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame: Optional[object]) -> None:
        """Handle application shutdown gracefully."""
        logger.info("Shutdown signal received")
        self.running = False
        print("\n\nAgnira shutting down gracefully...")
        
        if self.audio_handler:
            self.audio_handler.cleanup()
        
        sys.exit(0)

    def run(self) -> None:
        """Start the main application loop."""
        if self.use_audio:
            asyncio.run(self._run_audio_mode())
        else:
            self._run_demo_mode()

    async def _run_audio_mode(self) -> None:
        """Run in real audio mode with microphone and speakers."""
        try:
            logger.info("Starting Angira in AUDIO mode (streaming)")
            print("\n" + "=" * 80)
            print("ANGIRA VOICE ASSISTANT - STREAMING MODE")
            print("=" * 80)
            print(f"Model: {self.audio_handler.get_model_info()['model']}")
            print("🚀 Ultra-low latency mode: Response starts as you speak!")
            print("💡 You can interrupt Angira anytime by speaking!")
            print("Speak your question directly (no wake word needed).")
            print("Press Ctrl+C to exit\n")

            while self.running:
                try:
                    # Streaming mode - audio → reasoning → TTS all in one stream
                    print("\n🎤 Listening... Speak your question now!")
                    logger.info("Starting streaming conversation...")
                    
                    user_text = ""
                    response_text = ""
                    was_interrupted = False
                    
                    def on_transcription(text: str):
                        nonlocal user_text
                        user_text = text
                        print(f"\r🗣️ You: \"{text}\"", end="", flush=True)
                    
                    def on_response_chunk(chunk: str):
                        nonlocal response_text
                        response_text += chunk
                        # Print response as it streams
                        if len(response_text) == len(chunk):
                            print(f"\n\n💬 Angira: {chunk}", end="", flush=True)
                        else:
                            print(chunk, end="", flush=True)
                    
                    def on_interrupted():
                        print("\n\n⚡ [Interrupted by user]", flush=True)
                    
                    # Use streaming conversation for ultra-low latency
                    user_text, response_text, was_interrupted = await self.audio_handler.stream_conversation(
                        on_transcription=on_transcription,
                        on_response_text=on_response_chunk,
                        on_interrupted=on_interrupted,
                    )
                    
                    if was_interrupted:
                        print("\n[Response was interrupted - ready for your next question]")
                        logger.info(f"Conversation interrupted - partial response: {len(response_text)} chars")
                    elif user_text and response_text:
                        print("\n")  # New line after streaming output
                        print("\n" + "=" * 80)
                        print("FULL RESPONSE:")
                        print("=" * 80)
                        print(response_text)
                        print("=" * 80)
                        logger.info(f"Conversation complete - User: '{user_text[:50]}', Response: {len(response_text)} chars")
                    elif not user_text:
                        print("\n❌ No speech detected. Please try again.")
                    
                    print("\n" + "-" * 80)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error in streaming loop: {e}", exc_info=True)
                    print(f"\nError: {e}")
                    continue

        except Exception as e:
            logger.critical(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            self._cleanup()

    def _run_demo_mode(self) -> None:
        """Run in demo mode with text input."""
        try:
            logger.info("Starting Agnira in DEMO mode")
            print("\n" + "=" * 80)
            print("AGNIRA VOICE ASSISTANT - DEMO MODE")
            print("=" * 80)
            print("Type your questions (no microphone required)")
            print("Type 'quit' to exit\n")

            # Simulate wake word detection
            print("✓ Wake word simulated. Ready for questions.\n")
            print("-" * 80)

            while self.running:
                try:
                    user_input = input("\nYour question: ").strip()

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        print("Goodbye!")
                        break

                    if not user_input:
                        continue

                    logger.info(f"Processing: {user_input}")
                    result = self.pipeline.process_text(user_input)

                    if result:
                        logger.info(
                            f"Query processed - Intent: {result.intent}, "
                            f"Confidence: {result.confidence}"
                        )

                    print("\n" + "-" * 80)
                    print("Ready for next question... (or 'quit' to exit)")

                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    print(f"Error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Demo mode failed: {e}", exc_info=True)
            raise
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Perform cleanup before application exit."""
        try:
            logger.info("Performing cleanup")
            if self.audio_handler:
                self.audio_handler.cleanup()
            print("\nAgnira Voice Assistant terminated.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main() -> None:
    """Main entry point for Agnira Voice Assistant."""
    parser = argparse.ArgumentParser(description="Agnira Voice Assistant")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode (text input instead of microphone)"
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Run in audio mode (use microphone and speakers)"
    )
    args = parser.parse_args()

    # Default to demo mode if neither specified
    use_audio = args.audio and not args.demo
    
    if not args.audio and not args.demo:
        print("\nNo mode specified. Options:")
        print("  --audio  : Use real microphone and speakers")
        print("  --demo   : Use text input (no microphone needed)")
        print("\nStarting in DEMO mode by default...\n")
        use_audio = False

    try:
        # Validate settings
        logger.info("Validating configuration...")
        settings.validate()
        logger.info("Configuration valid")

        # Start application
        app = AgniraApp(use_audio=use_audio)
        app.run()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}")
        print("Please ensure .env file has GEMINI_API_KEY set")
        sys.exit(1)

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"Startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
