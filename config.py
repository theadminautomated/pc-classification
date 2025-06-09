"""Application configuration module.

Loads configuration from environment variables or an optional YAML file.
"""

from dataclasses import dataclass
from pathlib import Path
import logging
import os
import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(os.environ.get("PCRC_CONFIG", "config.yaml"))

@dataclass
class AppConfig:
    """Configuration options for the app.

    Attributes
    ----------
    model_name: str
        Name of the model to use.
    ollama_url: str
        Base URL for the Ollama service.
    """

    model_name: str = "pierce-county-records-classifier-phi2:latest"
    ollama_url: str = "http://localhost:11434"


def load_config() -> AppConfig:
    """Load configuration from YAML file and environment variables.

    Returns
    -------
    AppConfig
        Configuration populated from `config.yaml` and environment variables.
    """
    data = {}
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            logger.warning("Failed to load %s: %s", CONFIG_PATH, exc)
            data = {}
    env_model = os.environ.get("PCRC_MODEL")
    env_url = os.environ.get("PCRC_OLLAMA_URL")
    if env_model:
        data["model_name"] = env_model
    if env_url:
        data["ollama_url"] = env_url
    return AppConfig(**data)

CONFIG = load_config()
