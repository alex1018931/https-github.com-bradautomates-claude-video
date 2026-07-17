"""Konfiguration laden und validieren.

Liest config.yaml (Einstellungen) und .env (geheime Schlüssel) ein und
liefert ein typisiertes Config-Objekt zurück. Fehlende oder unsinnige Werte
führen zu einer klaren ConfigError, die run.py in einen Telegram-Alert
übersetzen kann.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


class ConfigError(Exception):
    """Wird geworfen, wenn die Konfiguration ungültig oder unvollständig ist."""


@dataclass
class Config:
    """Alle Einstellungen + Secrets, die das Tool zum Laufen braucht."""

    # Aus config.yaml
    hashtags: list[str]
    platform: str
    min_views: int
    top_n: int
    max_videos_per_source: int
    delay_min: float
    delay_max: float
    max_retries: int
    claude_model: str
    claude_max_tokens: int
    schedule_hint: str = ""

    # Aus .env (Secrets)
    anthropic_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Abgeleitete Pfade
    project_dir: Path = field(default_factory=Path.cwd)

    @property
    def output_dir(self) -> Path:
        return self.project_dir / "output"

    @property
    def logs_dir(self) -> Path:
        return self.project_dir / "logs"

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)


_VALID_PLATFORMS = {"tiktok", "instagram", "beide"}


def load_config(config_path: str | Path = "config.yaml") -> Config:
    """Lädt config.yaml + .env und validiert die Werte.

    Args:
        config_path: Pfad zur YAML-Konfiguration.

    Returns:
        Ein validiertes Config-Objekt.

    Raises:
        ConfigError: bei fehlender Datei oder ungültigen Werten.
    """
    config_path = Path(config_path)
    project_dir = config_path.resolve().parent

    if not config_path.exists():
        raise ConfigError(f"config.yaml nicht gefunden unter: {config_path}")

    # .env aus dem Projektverzeichnis laden (überschreibt keine echten Umgebungsvars).
    load_dotenv(project_dir / ".env")

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"config.yaml ist kein gültiges YAML: {exc}") from exc

    # --- Hashtags ---
    hashtags = raw.get("hashtags") or []
    if not isinstance(hashtags, list) or not hashtags:
        raise ConfigError(
            "config.yaml: 'hashtags' muss eine nicht-leere Liste sein."
        )
    # '#' und Leerzeichen entfernen, Kleinschreibung vereinheitlichen.
    hashtags = [str(h).lstrip("#").strip().lower() for h in hashtags if str(h).strip()]
    if not hashtags:
        raise ConfigError("config.yaml: 'hashtags' enthält keine gültigen Einträge.")

    # --- Plattform ---
    platform = str(raw.get("platform", "beide")).strip().lower()
    if platform not in _VALID_PLATFORMS:
        raise ConfigError(
            f"config.yaml: 'platform' muss eines von {sorted(_VALID_PLATFORMS)} sein, "
            f"war aber '{platform}'."
        )

    # --- Numerische Werte mit sinnvollen Defaults ---
    def _int(key: str, default: int, minimum: int = 0) -> int:
        val = raw.get(key, default)
        try:
            val = int(val)
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"config.yaml: '{key}' muss eine ganze Zahl sein.") from exc
        if val < minimum:
            raise ConfigError(f"config.yaml: '{key}' muss >= {minimum} sein.")
        return val

    min_views = _int("min_views", 0, minimum=0)
    top_n = _int("top_n", 20, minimum=1)
    max_videos_per_source = _int("max_videos_per_source", 40, minimum=1)
    max_retries = _int("max_retries", 3, minimum=0)
    claude_max_tokens = _int("claude_max_tokens", 4000, minimum=256)

    # --- Delay (min/max) ---
    delay = raw.get("request_delay_seconds", {}) or {}
    try:
        delay_min = float(delay.get("min", 2.0))
        delay_max = float(delay.get("max", 5.0))
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            "config.yaml: 'request_delay_seconds.min/max' müssen Zahlen sein."
        ) from exc
    if delay_min < 0 or delay_max < delay_min:
        raise ConfigError(
            "config.yaml: 'request_delay_seconds' muss 0 <= min <= max erfüllen."
        )

    claude_model = str(raw.get("claude_model", "claude-sonnet-4-6")).strip()
    schedule_hint = str(raw.get("schedule_hint", "")).strip()

    return Config(
        hashtags=hashtags,
        platform=platform,
        min_views=min_views,
        top_n=top_n,
        max_videos_per_source=max_videos_per_source,
        delay_min=delay_min,
        delay_max=delay_max,
        max_retries=max_retries,
        claude_model=claude_model,
        claude_max_tokens=claude_max_tokens,
        schedule_hint=schedule_hint,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        project_dir=project_dir,
    )
