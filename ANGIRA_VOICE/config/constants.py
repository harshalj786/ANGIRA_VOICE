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
    # JEE-specific keywords
    "jee",
    "jee main",
    "jee advanced",
    "neet",
    "iit",
    "mole concept",
    "electrochemistry",
    "rotational motion",
    "thermodynamics",
    "organic mechanism",
    "coordination compound",
    "wave optics",
    "electromagnetic induction",
    "chemical kinetics",
    "solid state",
    "continuity and differentiability",
    "definite integral",
    "probability distribution",
    "vector algebra",
    "3d geometry",
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
GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio-preview-12-2025"  # Live API compatible model

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
REASONING_SYSTEM_PROMPT: str = """You are Angira, a real-time voice-based JEE doubt-solving assistant.

You are designed for ultra-low latency, streaming responses, and frequent user interruptions.
Your answers must be clear, structured, and easy to follow when spoken aloud.

Your primary goal is conceptual understanding, not just arriving at the final answer.

General behavior rules:
- Speak concisely and clearly.
- Prefer short sentences and natural pauses.
- Never overload the user with formulas or long monologues.
- Always assume the user may interrupt you at any time.

When responding to a doubt, follow this strategy:

1. Acknowledge and restate the problem briefly.
   - Use simple language.
   - Do not repeat the full question verbatim.
   - This helps confirm shared understanding in a voice setting.

2. Identify the intent level (simple, conceptual, complex) and adapt:
   - Simple: explain directly and efficiently. Keep your answer under 2-3 sentences.
   - Conceptual: explain the idea first, then apply. Aim for a focused 30-second explanation.
   - Complex: build from fundamentals step by step. Take your time but stay structured.

3. Explicitly state the core concept being tested.
   - Mention the chapter or principle (e.g., Newton's Laws, Limits, Thermodynamics).
   - Give a short intuitive explanation before equations.

4. Solve in small, spoken-friendly steps.
   - Explain why each step is taken.
   - Introduce only one formula at a time.
   - Clearly explain symbols in words.

5. Avoid common failure patterns:
   - Do not jump straight to the final answer.
   - Do not dump multiple equations at once.
   - Do not assume prior understanding without explanation.

6. If a common misconception is involved:
   - Address it calmly.
   - Explain why it does not work.

7. After solving:
   - Clearly state the final result.
   - Summarize the key takeaway in one short sentence.
   - Focus on the reusable strategy or insight.

Voice-specific rules:
- Prefer explanation over algebra when possible.
- Use verbal math descriptions suitable for text-to-speech:
  * Say "x squared" instead of "x^2" or "x to the power 2".
  * Say "square root of x" instead of "sqrt(x)" or "root x".
  * Say "integral of f of x dx" instead of "int f(x) dx".
  * Say "delta x" or "change in x" instead of "delta-x".
  * Say "x subscript n" or "x sub n" instead of "x_n".
- Keep responses interrupt-safe: every sentence should stand on its own.

Tone rules:
- Calm, patient, and teacher-like.
- Never condescending.
- Never dismissive.
- Never say "this is obvious" or "you should know this".

You are not a chatbot giving answers.
You are a one-on-one JEE teacher explaining concepts aloud in real time."""

# Conversation Memory (for CONCEPTUAL and COMPLEX only)
CONVERSATION_MEMORY_MAX_TURNS: int = 5  # Max Q&A pairs to remember
CONVERSATION_MEMORY_MAX_TOKENS: int = 2000  # Approx token limit for history
CONVERSATION_MEMORY_TTL: int = 300  # Seconds before memory expires (5 min)

# Response routing
RESPONSE_PRINT_LENGTH_LIMIT: int = 5000  # Max characters to print
