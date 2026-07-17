"""Telegram-Benachrichtigungen.

Bei Erfolg: kurze Zusammenfassung + die Top-3-Hooks.
Bei Fehler / 0 Ergebnissen: laute Warnmeldung.

Bewusst nur mit `requests` umgesetzt (kein schweres Bot-SDK). Der Notifier ist
selbst robust: Schlägt der Telegram-Versand fehl, wird das geloggt, aber keine
Exception nach oben geworfen – ein kaputter Notifier soll den Lauf nicht killen.
"""

from __future__ import annotations

import requests

from .config import Config
from .logging_setup import get_logger
from .models import RunResult

_API_BASE = "https://api.telegram.org"
_MAX_LEN = 4096  # Telegram-Limit pro Nachricht.


def _send(config: Config, text: str) -> bool:
    """Sendet eine einzelne Telegram-Nachricht. Gibt True bei Erfolg zurück."""
    logger = get_logger()

    if not config.telegram_configured:
        logger.warning(
            "Telegram nicht konfiguriert (Token/Chat-ID fehlen) – Nachricht "
            "wird nur geloggt:\n%s",
            text,
        )
        return False

    url = f"{_API_BASE}/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": text[:_MAX_LEN],
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, data=payload, timeout=20)
        if resp.status_code == 200:
            logger.info("Telegram-Nachricht erfolgreich gesendet.")
            return True
        logger.error(
            "Telegram-Versand fehlgeschlagen (HTTP %s): %s",
            resp.status_code,
            resp.text[:300],
        )
        return False
    except requests.RequestException as exc:
        # Notifier darf den Lauf nicht zum Absturz bringen.
        logger.error("Telegram-Versand fehlgeschlagen (Netzwerk): %s", exc)
        return False


def notify_success(config: Config, result: RunResult) -> None:
    """Sendet eine Erfolgs-Zusammenfassung mit den Top-3-Hooks."""
    lines = [
        "✅ Viral Reel Finder – Lauf erfolgreich",
        "",
        f"Gescrapt: {result.scraped_count} Videos",
        f"Analysiert (über Filter): {result.analyzed_count}",
        f"Skripte generiert: {len(result.scripts)}",
    ]

    if result.errors:
        lines.append(f"⚠️ Hinweise/Teilfehler: {len(result.errors)}")

    # Top-3-Hooks anhängen.
    top3 = result.scripts[:3]
    if top3:
        lines.append("")
        lines.append("🏆 Top 3 Hooks:")
        for sr in top3:
            lines.append(f"{sr.rank}. {sr.video.hook}")

    if result.md_path:
        lines.append("")
        lines.append(f"📄 Report: {result.md_path}")

    _send(config, "\n".join(lines))


def notify_error(config: Config, message: str) -> None:
    """Sendet eine laute Warnmeldung bei Fehler oder 0 Ergebnissen."""
    text = f"🚨 Viral Reel Finder – PROBLEM\n\n{message}"
    _send(config, text)
