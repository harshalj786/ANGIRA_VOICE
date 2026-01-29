"""
Utility module for audio processing and manipulation.
"""

import logging
import numpy as np
from typing import Tuple
from config.constants import SAMPLE_RATE, SILENCE_THRESHOLD

logger = logging.getLogger(__name__)


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio to [-1, 1] range.

    Args:
        audio_data (np.ndarray): Raw audio data.

    Returns:
        np.ndarray: Normalized audio data.
    """
    try:
        if len(audio_data) == 0:
            logger.warning("Empty audio data for normalization")
            return audio_data

        max_val = np.max(np.abs(audio_data))
        if max_val == 0:
            logger.warning("Audio data contains only zeros")
            return audio_data

        normalized = audio_data / max_val
        logger.debug("Audio normalized successfully")
        return normalized

    except Exception as e:
        logger.error(f"Audio normalization failed: {e}")
        raise


def detect_silence(audio_data: np.ndarray, threshold: float = SILENCE_THRESHOLD) -> bool:
    """
    Detect if audio contains only silence.

    Args:
        audio_data (np.ndarray): Audio data to check.
        threshold (float): Amplitude threshold for silence.

    Returns:
        bool: True if audio is silent, False otherwise.
    """
    try:
        if len(audio_data) == 0:
            return True

        rms = np.sqrt(np.mean(audio_data**2))
        is_silent = rms < threshold

        if is_silent:
            logger.debug("Silence detected")
        else:
            logger.debug(f"Audio detected (RMS: {rms:.4f})")

        return is_silent

    except Exception as e:
        logger.error(f"Silence detection failed: {e}")
        raise


def get_audio_duration(audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float:
    """
    Calculate audio duration in seconds.

    Args:
        audio_data (np.ndarray): Audio data.
        sample_rate (int): Sample rate in Hz.

    Returns:
        float: Duration in seconds.
    """
    try:
        if sample_rate <= 0:
            raise ValueError("Sample rate must be positive")

        duration = len(audio_data) / sample_rate
        logger.debug(f"Audio duration: {duration:.2f} seconds")
        return duration

    except Exception as e:
        logger.error(f"Duration calculation failed: {e}")
        raise


def resample_audio(
    audio_data: np.ndarray, orig_sr: int, target_sr: int = SAMPLE_RATE
) -> np.ndarray:
    """
    Resample audio to target sample rate.

    Args:
        audio_data (np.ndarray): Original audio data.
        orig_sr (int): Original sample rate.
        target_sr (int): Target sample rate.

    Returns:
        np.ndarray: Resampled audio data.

    Note:
        Requires librosa library for high-quality resampling.
    """
    try:
        import librosa

        if orig_sr == target_sr:
            logger.debug("No resampling needed")
            return audio_data

        resampled = librosa.resample(audio_data, orig_sr=orig_sr, target_sr=target_sr)
        logger.info(f"Resampled audio from {orig_sr} Hz to {target_sr} Hz")
        return resampled

    except ImportError:
        logger.error("librosa not installed for audio resampling")
        raise
    except Exception as e:
        logger.error(f"Audio resampling failed: {e}")
        raise
