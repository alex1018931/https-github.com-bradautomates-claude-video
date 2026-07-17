"""Skript-Generierung mit Claude (claude-sonnet-4-6).

Pro Top-Video ruft dieses Modul Claude auf und lässt ein NEUES, besseres
Faceless-Reel-Skript auf Deutsch schreiben – inklusive Begründung, warum die
neue Version stärker hookt.

Defensiv: Einzelne fehlgeschlagene Generierungen brechen den Lauf NICHT ab;
das betroffene Video bekommt eine Fehlermarkierung, der Rest läuft weiter.
"""

from __future__ import annotations

import time

from .config import Config
from .logging_setup import get_logger
from .models import ScriptResult, Video

# System-Prompt: definiert Tonalität, Zielgruppe und Ausgabeformat.
SYSTEM_PROMPT = """\
Du bist ein erfahrener Scriptwriter für deutschsprachige Faceless-Reels
(TikTok/Instagram) im Themenfeld Online-Business für Anfänger.

Zielgruppe: deutschsprachige Einsteiger:innen im Online-Business.

Stil-Regeln (strikt einhalten):
- Ehrlich, realistisch, bodenständig. KEIN Hype.
- KEINE Reichtums-Versprechen, keine "schnell reich"-Behauptungen, keine
  unrealistischen Zahlen-Versprechen.
- Klare, einfache Sprache. Du-Form.
- Faceless: keine Person im Bild – arbeite mit B-Roll, Text-Overlays, Screen-Recordings.

Ausgabeformat (immer exakt diese Struktur, auf Deutsch):

HOOK (Sek 0-3):
<ein bis zwei Sätze, die sofort fesseln>

SZENEN:
1. [Bild/B-Roll-Idee] – Text-Overlay: "<kurzer Overlay-Text>"
2. ...
(3 bis 5 Szenen insgesamt)

CTA:
<konkreter, ehrlicher Call-to-Action>

BEGRÜNDUNG:
<2-4 Sätze: Warum hookt diese Version stärker als das Original? Beziehe dich
auf den Aufhänger, die Spannungskurve und die Zielgruppe.>
"""


def _build_user_prompt(video: Video, patterns: dict) -> str:
    """Baut den nutzerseitigen Prompt aus Video-Metadaten + erkannten Mustern."""
    hook_types = ", ".join(
        f"{name} ({count}x)" for name, count in patterns.get("hook_types", [])
    ) or "keine Daten"
    length = patterns.get("caption_length", {})

    return f"""\
Hier ist ein viral performendes Faceless-Reel aus der Nische. Schreibe ein NEUES,
stärkeres Skript zum gleichen Thema – nicht abschreiben, sondern verbessern.

ORIGINAL-VIDEO:
- Plattform: {video.platform}
- Views: {video.views:,}
- Likes: {video.likes:,}
- Kommentare: {video.comments:,}
- Engagement-Rate: {video.engagement_rate:.2%}
- Hashtags: {", ".join("#" + h for h in video.hashtags) or "-"}
- Audio: {video.audio_name or "-"}
- Original-Hook / Caption: "{video.hook}"

ERKANNTE MUSTER IN DEN TOP-VIDEOS (zur Orientierung):
- Häufigste Hook-Typen: {hook_types}
- Caption-Länge (Zeichen) – Median: {length.get("median", "?")}, max: {length.get("max", "?")}

Schreibe jetzt das neue Skript exakt im vorgegebenen Format.
"""


def _split_script_and_reasoning(text: str) -> tuple[str, str]:
    """Trennt den Skript-Teil von der Begründung anhand der Marke 'BEGRÜNDUNG:'."""
    marker = "BEGRÜNDUNG:"
    if marker in text:
        script, _, reasoning = text.partition(marker)
        return script.strip(), reasoning.strip()
    # Fallback: keine klare Trennung -> alles als Skript, keine Begründung.
    return text.strip(), ""


def _generate_one(client, model: str, max_tokens: int, video: Video, patterns: dict) -> tuple[str, str]:
    """Ein einzelner Claude-Aufruf mit Retry bei Rate-Limit/Serverfehler."""
    import anthropic

    user_prompt = _build_user_prompt(video, patterns)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # Ersten Text-Block einsammeln.
            text = next(
                (block.text for block in response.content if block.type == "text"), ""
            )
            return _split_script_and_reasoning(text)
        except (anthropic.RateLimitError, anthropic.APIStatusError) as exc:
            last_exc = exc
            wait = 2 * (2**attempt)
            get_logger().warning(
                "Claude-Aufruf fehlgeschlagen (Versuch %d/3): %s – erneut in %ds",
                attempt + 1,
                exc,
                wait,
            )
            time.sleep(wait)
    assert last_exc is not None
    raise last_exc


def generate_scripts(videos: list[Video], patterns: dict, config: Config) -> list[ScriptResult]:
    """Generiert für jedes Top-Video ein neues Skript.

    Args:
        videos: die Top-N Videos (bereits sortiert).
        patterns: erkannte Muster aus dem Analyzer.
        config: globale Konfiguration (Modell, Token-Limit, API-Key).

    Returns:
        Liste von ScriptResult – fehlgeschlagene Einträge tragen .error.

    Raises:
        RuntimeError: wenn gar kein Anthropic-Key konfiguriert ist.
    """
    logger = get_logger()

    if not config.anthropic_configured:
        raise RuntimeError(
            "ANTHROPIC_API_KEY ist nicht gesetzt – Skript-Generierung nicht möglich. "
            "Bitte in der .env eintragen."
        )

    import anthropic

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    results: list[ScriptResult] = []
    for rank, video in enumerate(videos, start=1):
        logger.info("Claude: generiere Skript %d/%d für %s", rank, len(videos), video.url)
        try:
            script, reasoning = _generate_one(
                client, config.claude_model, config.claude_max_tokens, video, patterns
            )
            results.append(
                ScriptResult(video=video, rank=rank, new_script=script, reasoning=reasoning)
            )
        except Exception as exc:
            # Einzelfehler protokollieren, aber Lauf fortsetzen.
            logger.error("Claude: Skript %d fehlgeschlagen: %s", rank, exc)
            results.append(
                ScriptResult(
                    video=video,
                    rank=rank,
                    error=f"Skript-Generierung fehlgeschlagen: {exc}",
                )
            )
    return results
