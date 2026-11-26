"""
BiofilmAI Backend — Configuration

Set the environment variables or use the defaults for local development.
The real AI model will later be wired in; the current implementation is a
DEMO MODEL that generates clearly labeled simulated predictions.
"""

import os


class Settings:
    """Application settings loaded from environment variables."""

    APP_NAME: str = "BiofilmAI API"
    APP_VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "Research prototype for multimodal prediction of biofilm-associated infection."
    )

    # Server
    HOST: str = os.getenv("BIOFILM_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BIOFILM_PORT", "8000"))
    DEBUG: bool = os.getenv("BIOFILM_DEBUG", "true").lower() == "true"

    # CORS — comma-separated list of allowed origins for the frontend.
    # Includes the common preview / loopback hosts so the same backend
    # works for `localhost`, `127.0.0.1`, and `169.254.0.21` (the
    # container's link-local address that the Arena preview uses).
    CORS_ORIGINS: list[str] = os.getenv(
        "BIOFILM_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://169.254.0.21:3000",
    ).split(",")

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("BIOFILM_MAX_UPLOAD_MB", "50"))

    # Model settings
    MODEL_WEIGHTS_PATH: str = os.getenv("BIOFILM_WEIGHTS_PATH", "weights/biofilm_model.pt")
    MODEL_DEVICE: str = os.getenv("BIOFILM_DEVICE", "cpu")
    DEMO_MODE: bool = os.getenv("BIOFILM_DEMO_MODE", "true").lower() == "true"

    # Allowed file extensions per modality
    MICROSCOPY_EXTENSIONS: list[str] = [".png", ".jpg", ".jpeg", ".tiff", ".tif"]
    SPECTROSCOPY_EXTENSIONS: list[str] = [".csv", ".txt", ".xlsx"]
    GENOMICS_EXTENSIONS: list[str] = [".csv", ".txt", ".fasta", ".fa", ".fna"]

    # Microscopy MIME types
    MICROSCOPY_MIMES: list[str] = [
        "image/png",
        "image/jpeg",
        "image/tiff",
        "application/octet-stream",
    ]

    # Maximum modalities
    MAX_MODALITIES: int = 4


settings = Settings()