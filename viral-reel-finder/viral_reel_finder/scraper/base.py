"""Gemeinsame, defensive Bausteine für alle Scraper.

Enthält:
- eine Liste rotierender User-Agents (gegen simple Bot-Erkennung),
- eine höfliche Zufalls-Pause zwischen Requests (Rate-Limiting),
- einen Retry-Decorator mit exponentiellem Backoff.

Hinweis zur Realität: Scraping öffentlicher Seiten verstößt gegen die ToS von
TikTok/Instagram und ist fragil. Diese Helfer machen es robuster, nicht legal
oder unfehlbar. Bei Totalausfall reichen die Scraper die Exception nach oben,
damit run.py einen lauten Telegram-Alert schicken kann.
"""

from __future__ import annotations

import functools
import random
import time
from typing import Callable, TypeVar

from ..logging_setup import get_logger

# Eine Handvoll realistischer Desktop-User-Agents zum Rotieren.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

T = TypeVar("T")


def random_user_agent() -> str:
    """Liefert einen zufälligen User-Agent-String."""
    return random.choice(USER_AGENTS)


def polite_delay(delay_min: float, delay_max: float) -> None:
    """Wartet eine zufällige Zeitspanne zwischen min und max Sekunden (Jitter)."""
    if delay_max <= 0:
        return
    pause = random.uniform(delay_min, delay_max)
    time.sleep(pause)


def retry(max_retries: int = 3, base_delay: float = 2.0):
    """Decorator: wiederholt die Funktion bei Exception mit exp. Backoff.

    Args:
        max_retries: Anzahl zusätzlicher Versuche nach dem ersten Fehlschlag.
        base_delay: Basis-Wartezeit; verdoppelt sich pro Versuch (+ Jitter).
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = get_logger()
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # bewusst breit: Netzwerk/Parsing variieren
                    last_exc = exc
                    if attempt < max_retries:
                        wait = base_delay * (2**attempt) + random.uniform(0, 1)
                        logger.warning(
                            "%s fehlgeschlagen (Versuch %d/%d): %s – erneut in %.1fs",
                            func.__name__,
                            attempt + 1,
                            max_retries + 1,
                            exc,
                            wait,
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            "%s endgültig fehlgeschlagen nach %d Versuchen: %s",
                            func.__name__,
                            max_retries + 1,
                            exc,
                        )
            # Alle Versuche erschöpft -> Exception nach oben reichen.
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
