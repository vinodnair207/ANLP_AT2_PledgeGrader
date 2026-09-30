"""Shared helpers: configuration loading, logging setup and seeding."""
import logging
import random
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Reads the YAML configuration file and returns it as a dictionary."""
    with open(path, "r", encoding="utf8") as handle:
        return yaml.safe_load(handle)


def setup_logging(level: int = logging.INFO) -> None:
    """Configures one consistent log format for every module."""
    logging.basicConfig(
        level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )


def set_seed(seed: int) -> None:
    """Fixes the Python random seed so that runs are reproducible."""
    random.seed(seed)
