"""
Configuration settings module for Agnira Voice Assistant.
Loads environment variables and exposes API keys and settings safely.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GPT_API_KEY: str = os.getenv("GPT_API_KEY", "")

    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required settings are present.

        Returns:
            bool: True if all required settings are present, False otherwise.
        """
        # Only GEMINI_API_KEY is required now (GPT is optional)
        required_keys = ["GEMINI_API_KEY"]
        missing_keys = [key for key in required_keys if not getattr(cls, key)]

        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )
        return True

    @classmethod
    def get_gemini_api_key(cls) -> str:
        """
        Get Gemini API key safely.

        Returns:
            str: Gemini API key

        Raises:
            ValueError: If Gemini API key is not set.
        """
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return cls.GEMINI_API_KEY

    @classmethod
    def get_gpt_api_key(cls) -> str:
        """
        Get GPT API key safely.

        Returns:
            str: GPT API key

        Raises:
            ValueError: If GPT API key is not set.
        """
        if not cls.GPT_API_KEY:
            raise ValueError("GPT_API_KEY environment variable not set")
        return cls.GPT_API_KEY


# Initialize settings
settings = Settings()
