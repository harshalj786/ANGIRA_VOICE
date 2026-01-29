"""
Constants and configuration values for Agnira Voice Assistant.
Includes intent thresholds, keyword lists, and audio processing limits.
"""

# Intent Classification Thresholds
MIN_QUERY_LENGTH_SIMPLE: int = 5  
MAX_QUERY_LENGTH_SIMPLE: int = 150 

# Complex query keywords that indicate complex reasoning
COMPLEX_KEYWORDS: list[str] = [
    "derive",
    "prove",
    "integrate",
    "differentiate",
    "explain",
    "analyze",
    "solve step by step",
    "why",
    "how does",
    "algorithm",
]

# Conceptual query settings (short concept probes like "entropy?")
MAX_CONCEPTUAL_WORDS: int = 3  # Maximum words for conceptual queries

MATH_OPERATORS: list[str] = [
    "+",
    "-",
    "*",
    "/",
    "^",
    "**",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "log",
    "ln",
    "integral",
    "derivative",
    "∫",
    "∑",
    "∂",
]

# Audio processing constants
SAMPLE_RATE: int = 16000  # Hz - for input (mic)
OUTPUT_SAMPLE_RATE: int = 24000  # Hz - for output (speaker from Gemini)
AUDIO_CHUNK_DURATION: float = 0.1  # seconds
AUDIO_CHUNK_SIZE: int = 1024  # frames per buffer
MAX_AUDIO_DURATION: float = 30.0  # Maximum recording duration in seconds
SILENCE_THRESHOLD: float = 0.01  # Amplitude threshold for silence detection (lowered to capture softer speech)
SILENCE_DURATION: float = 1.0  # Seconds of silence to stop recording
AUDIO_FORMAT: str = "audio/pcm"  # PCM format for Gemini Live API

# Gemini Live API Model (for audio streaming)
GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio-latest"  # Native audio model for Live API

# TTS Constants (cost optimization)
MAX_SIMPLE_RESPONSE_LENGTH: int = 2000  # Max characters for full TTS
MAX_CONCEPTUAL_RESPONSE_LENGTH: int = 300  # Max characters for conceptual TTS
SHORT_ACKNOWLEDGMENT: str = "Here's the complete solution on your screen."
CONCEPTUAL_ACKNOWLEDGMENT: str = "Here's a brief explanation."

# Wake Word
WAKE_WORD: str = "angira"
WAKE_WORD_CONFIDENCE_THRESHOLD: float = 0.8

# Timeouts
SPEECH_RECOGNITION_TIMEOUT: float = 30.0  # seconds
API_TIMEOUT: float = 60.0  # seconds

# Gemini Reasoning Engine (switched from GPT)
GEMINI_REASONING_MODEL: str = "gemini-2.0-flash"  # Fast and capable
GEMINI_MAX_TOKENS: int = 1024  # Max response tokens
GEMINI_TEMPERATURE: float = 0.7  # Balance creativity and accuracy
REASONING_SYSTEM_PROMPT: str = """You are Angira, an intelligent voice assistant. 
Provide clear, concise, and accurate answers. 
For math problems, show step-by-step solutions. 
For concepts, explain simply but thoroughly."""

# Conversation Memory (for CONCEPTUAL and COMPLEX only)
CONVERSATION_MEMORY_MAX_TURNS: int = 5  # Max Q&A pairs to remember
CONVERSATION_MEMORY_MAX_TOKENS: int = 2000  # Approx token limit for history
CONVERSATION_MEMORY_TTL: int = 300  # Seconds before memory expires (5 min)

# Response routing
RESPONSE_PRINT_LENGTH_LIMIT: int = 5000  # Max characters to print
