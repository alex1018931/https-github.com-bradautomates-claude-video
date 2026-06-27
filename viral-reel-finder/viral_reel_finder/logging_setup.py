"""Zentrales Logging: schreibt in eine Tagesdatei UND auf die Konsole.

Wichtig für den unbeaufsichtigten Betrieb: Jeder Lauf hinterlässt eine
nachvollziehbare Log-Datei unter logs/run_YYYY-MM-DD.log.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

_LOGGER_NAME = "viral_reel_finder"


def setup_logging(logs_dir: Path, verbose: bool = True) -> logging.Logger:
    """Richtet den Logger ein und gibt ihn zurück.

    Args:
        logs_dir: Verzeichnis für die Log-Dateien (wird bei Bedarf erstellt).
        verbose: Wenn True, auch auf die Konsole loggen.

    Returns:
        Der konfigurierte Logger.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"run_{date.today().isoformat()}.log"

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    # Doppelte Handler vermeiden, falls setup_logging mehrfach aufgerufen wird.
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Datei-Handler (immer)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Konsolen-Handler (optional)
    if verbose:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)

    logger.info("Logging initialisiert – Datei: %s", log_file)
    return logger


def get_logger() -> logging.Logger:
    """Gibt den bereits eingerichteten Logger zurück (oder einen Default)."""
    return logging.getLogger(_LOGGER_NAME)
