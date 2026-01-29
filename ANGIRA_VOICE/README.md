# Angira Voice Assistant 🎤

A wake-word–activated, cost-aware speech-to-speech assistant built around Google Gemini for transcription, reasoning, and text-to-speech. It normalizes math-heavy queries, classifies intent (simple / conceptual / complex), and routes responses to keep API usage lean.

## What it does

- Listens for the wake word **“Angira”** (transcription-based fuzzy detection).
- Accepts **text (demo mode)** or **real audio (audio mode)**.
- Converts speech → text with Gemini; verbalizes math symbols/shorthand to words.
- Classifies intent as **simple**, **conceptual**, or **complex** with rule-based logic.
- Runs reasoning through **Gemini 2.0 Flash** (with short conversation memory for conceptual/complex queries).
- Routes responses cost-consciously: always print; TTS strategy depends on intent (full / short / acknowledgment).
- Logs to console + rotating files; includes unit tests for the intent classifier.

## Pipeline at a glance

```
Audio/Text Input
    ↓
Wake Word Detection ("Angira" via transcription match)
    ↓
Speech-to-Text (Gemini, 16 kHz PCM)
    ↓
Verbalizer (math symbol & shorthand normalization)
    ↓
Intent Classifier (simple | conceptual | complex)
    ↓
Reasoning (Gemini 2.0 Flash, memory for conceptual/complex)
    ↓
Response Router (print + intent-aware TTS policy)
    ↓
Output (console + audio)
```

## Project layout

```
ANGIRA_VOICE/
├── main.py                  # Entry point (demo/audio modes)
├── pipelines/agnira_pipeline.py   # Orchestrates STT → verbalize → intent → reasoning → routing
├── core/
│   ├── audio_live.py        # Gemini Live audio handler (mic, STT, TTS streaming)
│   ├── wake_word.py         # Wake-word detection via transcription
│   ├── speech_to_text.py    # STT (Gemini generate_content)
│   ├── text_to_speech.py    # TTS (Gemini Live API)
│   ├── verbalizer.py        # Math symbol/shorthand → natural language
│   ├── intent_classifier.py # Rule-based intent (simple/conceptual/complex)
│   ├── reasoning_engine.py  # Gemini reasoning + short conversation memory
│   └── response_router.py   # Cost-aware response/TT S routing
├── config/
│   ├── settings.py          # Env vars loader (dotenv)
│   └── constants.py         # Thresholds, model names, audio/tts limits
├── utils/
│   ├── audio_utils.py       # Normalize, silence detect, duration, resample
│   ├── math_utils.py        # Extract/normalize/evaluate simple math
│   └── logger.py            # Console + rotating file logging
├── models/intent_rules.py   # Dataclasses for rules and processed query
├── tests/test_intent_classifier.py # Unit tests
├── .env.example             # Env template (replace with your keys)
└── requirements.txt         # Dependencies
```

## Requirements

- Python 3.10+ recommended
- Network access for Gemini APIs
- For audio mode: working microphone & speakers, PyAudio-compatible drivers

Dependencies (see `requirements.txt`): `google-genai>=1.0.0`, `pyaudio`, `numpy`, `scipy`, `librosa`, `soundfile`, `python-dotenv`, `pydantic`, `openai` (present but not currently used in the pipeline).

## Setup

1) Create & activate a virtual environment (optional but recommended).
2) Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3) Configure environment variables:
   - Copy `.env.example` to `.env`.
   - Set `GEMINI_API_KEY=<your_key>` (required).
   - Optional legacy: `GPT_API_KEY=<your_key>` (not used in current flow).
   - `LOG_LEVEL` (e.g., `INFO` or `DEBUG`), `ENVIRONMENT` (e.g., `development`).
   - Keep `.env` out of version control.

## Running the app

- **Demo mode (text, default):**
  ```
  python main.py
  ```
  - Simulated wake word; type your questions; prints response (no audio hardware needed).

- **Audio mode (wake word + mic + TTS):**
  ```
  python main.py --audio
  ```
  - Waits for “Agnira,” captures speech until silence, transcribes, runs pipeline, and speaks per intent routing.
  - Requires microphone/speakers and working PyAudio backend.

## How the pipeline works (module map)

1. **Wake word** (`core.wake_word` or `core.audio_live.listen_for_wake_word`): transcription-based fuzzy match for “Agnira.”
2. **Capture** (`core.audio_live`): mic capture with silence detection and duration guards.
3. **STT** (`core.speech_to_text` or `audio_live.transcribe_audio`): Gemini `generate_content` on PCM/WAV.
4. **Verbalize** (`core.verbalizer`): replaces math symbols (√, ∫, ∑, superscripts) and shorthand.
5. **Intent** (`core.intent_classifier`): rules for simple / conceptual / complex (length, math operators, keywords, short “concept probes”).
6. **Reasoning** (`core.reasoning_engine`): Gemini 2.0 Flash with adjustable max tokens by intent and short conversation memory for conceptual/complex.
7. **Routing** (`core.response_router`): always prints; TTS policy by intent (full | short | acknowledgment). Async helpers integrate with `AudioLiveHandler` for playback.

## Testing

- Intent classifier tests:
  ```
  python -m pytest tests/test_intent_classifier.py -v
  ```
  (or `python -m unittest tests.test_intent_classifier -v`).

## Configuration reference

- **Env vars** (`config/settings.py`): `GEMINI_API_KEY` (required), `GPT_API_KEY` (unused), `LOG_LEVEL`, `ENVIRONMENT`.
- **Constants** (`config/constants.py` highlights):
  - Intent thresholds: `MIN_QUERY_LENGTH_SIMPLE=5`, `MAX_QUERY_LENGTH_SIMPLE=150`, math operators list, complex keywords list.
  - Audio: `SAMPLE_RATE=16000`, `OUTPUT_SAMPLE_RATE=24000`, `SILENCE_THRESHOLD=0.01`, `SILENCE_DURATION=1.0`, `MAX_AUDIO_DURATION=30s`.
  - Models: `GEMINI_REASONING_MODEL="gemini-2.0-flash"`, `GEMINI_LIVE_MODEL="gemini-2.5-flash-native-audio-latest"`.
  - TTS routing: `MAX_SIMPLE_RESPONSE_LENGTH=2000`, `MAX_CONCEPTUAL_RESPONSE_LENGTH=300`, `SHORT_ACKNOWLEDGMENT` string.
  - Conversation memory: `CONVERSATION_MEMORY_MAX_TURNS=5`, `CONVERSATION_MEMORY_TTL=300s` (conceptual/complex only).

## Cost & behavior notes

- Complex/conceptual queries use conversation memory; simple queries are stateless.
- TTS is trimmed for conceptual and replaced with a brief acknowledgment for complex to reduce audio costs.
- STT/TTS and reasoning all call Gemini; ensure key/quotas are set accordingly.

## Limitations / TODOs

- Wake-word detection is transcription-based; consider a dedicated wake-word model for robustness/latency.
- Audio mode depends on PyAudio drivers; device selection is basic (default input/output).
- Reasoning currently uses Gemini; the `openai` dependency is unused and kept only for potential future routing.
- No long-term session persistence beyond the short in-memory history for conceptual/complex.

## Troubleshooting

- **Missing key**: ensure `.env` has `GEMINI_API_KEY` and the shell session can read it.
- **PyAudio errors**: install system audio dev libraries/drivers; ensure default input/output devices exist.
- **No transcription / TTS**: check network connectivity and Gemini API availability; try `LOG_LEVEL=DEBUG` for more detail.
- **Demo mode only**: run without `--audio` to bypass audio hardware while validating logic.

## Contributing

- Follow existing type hints/docstrings.
- Add tests for new logic under `tests/`.
- Update docs when changing pipeline behavior or configuration defaults.

---

**Last Updated**: January 2026
**Version**: 1.0.0-alpha
**Status**: In Development
