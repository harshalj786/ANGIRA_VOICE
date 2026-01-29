"""
AGNIRA_VOICE: QUICK REFERENCE GUIDE
====================================

A comprehensive guide to the project structure and key modules.
"""

# PROJECT OVERVIEW
# ================
# Agnira is a wake-word activated speech-to-speech AI assistant that:
# 1. Listens for "Agnira" wake word
# 2. Captures user speech
# 3. Converts speech to text (Gemini STT)
# 4. Normalizes mathematical expressions
# 5. Classifies query as simple or complex
# 6. Routes to GPT reasoning engine
# 7. Responds with text + smart TTS (cost-optimized)


# QUICK SETUP
# ===========
# 1. pip install -r requirements.txt
# 2. cp .env.example .env (add your API keys)
# 3. python main.py


# KEY MODULES AT A GLANCE
# =======================

# config/settings.py
# - Load API keys safely from environment
# - settings.get_gemini_api_key()
# - settings.get_gpt_api_key()

# config/constants.py
# - Intent classification thresholds
# - Math operators and complex keywords
# - Audio processing parameters

# core/wake_word.py
# - listen_for_wake_word() → bool
# - Currently placeholder (TODO: real implementation)

# core/speech_to_text.py
# - SpeechToText.transcribe(audio_bytes) → str
# - Uses Gemini Flash 2.5 Live API

# core/text_to_speech.py
# - TextToSpeech.speak(text) → bytes
# - Uses Gemini Flash 2.5 Live API
# - Limited to 2000 chars for cost efficiency

# core/verbalizer.py
# - verbalize_query(text) → str
# - Converts: √x² dx → "square root of x squared dx"
# - Math symbol mapping + normalization

# core/intent_classifier.py
# - classify_intent(text) → "simple" | "complex"
# - Rule-based: length, keywords, operators
# - Returns "simple" or "complex"

# core/reasoning_engine.py
# - ReasoningEngine.solve(query) → str
# - Uses GPT-4 API for reasoning only
# - NEVER used for speech

# core/response_router.py
# - route_response(intent, response_text)
# - Simple: Print + Full TTS
# - Complex: Print + Brief acknowledgment

# pipelines/agnira_pipeline.py
# - AgniraPipeline.process_audio(audio) → ProcessedQuery
# - AgniraPipeline.process_text(text) → ProcessedQuery
# - Orchestrates complete flow

# utils/audio_utils.py
# - normalize_audio(data) → normalized_data
# - detect_silence(data) → bool
# - get_audio_duration(data) → float
# - resample_audio(data, orig_sr, target_sr) → resampled

# utils/math_utils.py
# - extract_math_expressions(text) → List[str]
# - normalize_math_expression(expr) → str
# - evaluate_simple_math(expr) → float

# utils/logger.py
# - setup_logging() → Logger
# - get_logger(name) → Logger
# - Logs to console, file, and error file


# COMMON USAGE PATTERNS
# ====================

# 1. Simple Text Processing
from core.verbalizer import verbalize_query
from core.intent_classifier import classify_intent

query = "Calculate √16"
verbalized = verbalize_query(query)  # "Calculate square root of 16"
intent = classify_intent(verbalized)  # "simple"


# 2. Using the Pipeline
from pipelines.agnira_pipeline import AgniraPipeline

pipeline = AgniraPipeline()
result = pipeline.process_text("What is 2+2?")
# Result includes: original, verbalized, intent, confidence


# 3. Logging
from utils.logger import setup_logging, get_logger

setup_logging()  # Call once at startup
logger = get_logger(__name__)
logger.info("Application started")


# 4. Running Tests
# python -m unittest tests.test_intent_classifier -v


# INTENT CLASSIFICATION RULES
# ============================

# SIMPLE (returns "simple"):
# - Short queries (5-150 characters)
# - No complex keywords (derive, prove, explain, etc.)
# - One or fewer math operators
# Examples:
#   "What is 2+2?"
#   "Calculate 15 times 3"
#   "How much is 100 divided by 5?"

# COMPLEX (returns "complex"):
# - Long queries (>150 characters)
# - Contains complex keywords: derive, prove, integrate, explain, analyze
# - Multiple math operators or special operators (^, ∫, ∂)
# - Contains "step by step" indicators
# Examples:
#   "Derive the quadratic formula step by step"
#   "Prove the Pythagorean theorem"
#   "Integrate x² from 0 to 10"


# RESPONSE ROUTING STRATEGY
# =========================

# SIMPLE QUERIES:
#   ✓ Print full response to console
#   ✓ Speak full response using TTS (Gemini)
#   ✓ User hears complete audio answer

# COMPLEX QUERIES:
#   ✓ Print full response to console
#   ✓ Speak ONLY brief acknowledgment
#   ✓ Acknowledgment: "Here's the complete solution on your screen."
#   ✓ Saves API costs dramatically


# API USAGE
# =========

# Gemini Flash 2.5 Live is ONLY used for:
# - Speech-to-text (transcribe)
# - Text-to-speech (speak)
# - Voice I/O operations
# - NOT for reasoning

# GPT API is ONLY used for:
# - Reasoning and problem-solving
# - Step-by-step explanations
# - Complex analysis
# - NOT for speech

# This separation ensures:
# - Cost efficiency (specialized models for specialized tasks)
# - Lower latency (smaller, faster models where possible)
# - Better accuracy (domain-specific models)


# ENVIRONMENT SETUP
# =================

# Required .env variables:
GEMINI_API_KEY=sk-...
GPT_API_KEY=sk-...
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=development  # or production


# TROUBLESHOOTING
# ===============

# Problem: "GEMINI_API_KEY not set"
# Solution: Check .env file has GEMINI_API_KEY=your_key

# Problem: Tests fail
# Solution: Run: python -m unittest discover tests/ -v

# Problem: Demo mode stuck
# Solution: Press Ctrl+C to exit gracefully

# Problem: No audio output
# Solution: Check audio hardware and pyaudio installation

# Problem: High API costs
# Solution: Most complex queries default to brief TTS - this is intentional!


# FILE STRUCTURE REFERENCE
# ========================

AGNIRA_VOICE/
├── .env.example           ← Copy to .env and add keys
├── main.py                ← START HERE: python main.py
├── README.md              ← Full documentation
├── requirements.txt       ← pip install -r requirements.txt
│
├── config/
│   ├── settings.py        ← Load config from environment
│   └── constants.py       ← All constants defined here
│
├── core/
│   ├── wake_word.py       ← Listen for "Agnira" (TODO: real impl)
│   ├── speech_to_text.py  ← Gemini STT (TODO: real impl)
│   ├── text_to_speech.py  ← Gemini TTS (TODO: real impl)
│   ├── verbalizer.py      ← Normalize math symbols
│   ├── intent_classifier.py ← Simple vs Complex
│   ├── reasoning_engine.py  ← Send to GPT
│   └── response_router.py   ← Route response output
│
├── pipelines/
│   └── agnira_pipeline.py ← Orchestrate everything
│
├── utils/
│   ├── audio_utils.py     ← Audio processing
│   ├── math_utils.py      ← Math operations
│   └── logger.py          ← Logging setup
│
├── models/
│   └── intent_rules.py    ← Data structures
│
└── tests/
    └── test_intent_classifier.py ← Run tests here


# NEXT STEPS FOR FULL IMPLEMENTATION
# ===================================

# 1. Implement Real Wake-Word Detection
#    Location: core/wake_word.py
#    Use: Porcupine, custom model, or Gemini multimodal

# 2. Implement Real Gemini API Calls
#    Location: core/speech_to_text.py, core/text_to_speech.py
#    Replace: TODO placeholders with actual API calls

# 3. Implement Real GPT API Calls
#    Location: core/reasoning_engine.py
#    Replace: TODO placeholder with actual API call

# 4. Implement Audio Capture
#    Location: main.py
#    Add: Microphone input using PyAudio

# 5. Implement Audio Playback
#    Location: core/text_to_speech.py and response_router.py
#    Add: System audio output


# PERFORMANCE TIPS
# ================

# - Use simple queries to test (faster responses)
# - Check logs in logs/ directory for debugging
# - Complex queries intentionally use brief TTS (cost-saving feature)
# - Disable logging in production for better performance


# SECURITY REMINDERS
# ==================

# ✓ NEVER commit .env file to git
# ✓ Use .env.example as template only
# ✓ API keys should ONLY be in .env
# ✓ Never hardcode secrets in code
# ✓ Use git ignore to prevent accidents


# VERSION HISTORY
# ===============

# v1.0.0-alpha
# - Complete project scaffold
# - All modules implemented (with TODOs for real APIs)
# - Full documentation
# - Unit tests for intent classifier
# - Production-ready structure


# CONTACT & SUPPORT
# =================

# For issues:
# 1. Check logs (logs/ directory)
# 2. Enable DEBUG logging: LOG_LEVEL=DEBUG in .env
# 3. Review README.md for comprehensive guides
# 4. Check TODO items for known issues


# QUICK COMMAND REFERENCE
# =======================

# Setup:
#   python -m venv venv
#   source venv/bin/activate  (or venv\Scripts\activate on Windows)
#   pip install -r requirements.txt

# Configure:
#   cp .env.example .env
#   # Edit .env with your API keys

# Run:
#   python main.py

# Test:
#   python -m unittest tests.test_intent_classifier -v

# Debug:
#   Set LOG_LEVEL=DEBUG in .env

# Clean:
#   rm -rf __pycache__ logs/*.log
#   Or on Windows:
#   rmdir /s /q __pycache__


"""
END OF QUICK REFERENCE
For full documentation, see README.md
For detailed testing, see tests/test_intent_classifier.py
For implementation details, see module docstrings
"""
