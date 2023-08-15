"""Any model or helper useful for creating or interacting with a horde API."""
import os

import dotenv
from loguru import logger

# If the current working directory contains a `.env` file, import the environment variables from it.
# This is useful for development.
dotenv.load_dotenv()

if os.getenv("AI_HORDE_DEV_URL"):
    logger.warning(
        "AI_HORDE_DEV_URL is set.",
    )

if os.getenv("RATINGS_DEV_URL"):
    logger.warning(
        "RATINGS_DEV_URL is set.",
    )

if os.getenv("AIWORKER_CACHE_HOME"):
    logger.warning(
        "AIWORKER_CACHE_HOME is set.",
    )
