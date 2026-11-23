
import os
from pathlib import Path

from dotenv import load_dotenv

# Locate the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the project root
load_dotenv(BASE_DIR / ".env")

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("MODEL_NAME", "openrouter/free")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1"
)

# Application configuration
APP_NAME = "CodePilot: Agentic Software Factory"
APP_VERSION = "1.0.0"

# Execution safety settings
MAX_DEBUG_RETRIES = 2
CODE_EXECUTION_TIMEOUT = 10

# Workspace configuration
WORKSPACE_DIR = BASE_DIR / "workspace"


def validate_settings():
    """Check whether the required application settings are configured."""
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is missing. "
            "Please configure it in the project .env file."
        )

    return True
