"""Viralitäts-Analyse: Score berechnen, Top-N bilden, Muster erkennen.

Der Viral-Score kombiniert zwei Signale:
1. Engagement-Rate  = (Likes + Kommentare) / Views   -> wie stark interagiert das Publikum?
2. Views-pro-Tag    = Views / Alter in Tagen          -> wie schnell wächst das Video gerade?

Beide werden über die aktuelle Kandidatenmenge normalisiert (0..1) und gewichtet
zusammengefasst. So ranken frische, schnell wachsende UND hoch interagierte Videos oben.
"""

from __future__ import annotations

import re
from collections import Counter
from statistics import median

from .logging_setup import get_logger
from .models import Video

# Gewichtung der beiden Signale im Viral-Score (Summe = 1.0).
WEIGHT_ENGAGEMENT = 0.5
WEIGHT_VELOCITY = 0.5


def _compute_raw_metrics(videos: list[Video]) -> None:
    """Berechnet engagement_rate und views_per_day je Video (in-place)."""
    for v in videos:
        v.engagement_rate = (v.likes + v.comments) / max(v.views, 1)
        v.views_per_day = v.views / v.age_in_days


def _normalize(values: list[float]) -> list[float]:
    """Min-Max-Normalisierung auf 0..1. Bei konstanter Eingabe -> alle 0.5."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5 for _ in values]
    return [(x - lo) / (hi - lo) for x in values]


def score_videos(videos: list[Video], min_views: int) -> list[Video]:
    """Filtert nach min_views, berechnet Roh-Metriken und den Viral-Score.

    Args:
        videos: alle gescrapten Videos.
        min_views: Mindest-Viewzahl-Filter.

    Returns:
        Gefilterte Liste mit gesetztem viral_score (unsortiert).
    """
    logger = get_logger()

    # Duplikate (gleiche URL) entfernen – Hashtags überschneiden sich oft.
    seen: set[str] = set()
    unique: list[Video] = []
    for v in videos:
        if v.url not in seen:
            seen.add(v.url)
            unique.append(v)

    filtered = [v for v in unique if v.views >= min_views]
    logger.info(
        "Analyse: %d Videos gesamt, %d eindeutig, %d über min_views=%d",
        len(videos),
        len(unique),
        len(filtered),
        min_views,
    )

    if not filtered:
        return []

    _compute_raw_metrics(filtered)

    eng_norm = _normalize([v.engagement_rate for v in filtered])
    vel_norm = _normalize([v.views_per_day for v in filtered])

    for v, e, vel in zip(filtered, eng_norm, vel_norm):
        v.viral_score = WEIGHT_ENGAGEMENT * e + WEIGHT_VELOCITY * vel

    return filtered


def top_n(videos: list[Video], n: int) -> list[Video]:
    """Sortiert nach Viral-Score absteigend und gibt die besten n zurück."""
    return sorted(videos, key=lambda v: v.viral_score, reverse=True)[:n]


# --- Mustererkennung -------------------------------------------------------

def _classify_hook(caption: str) -> str:
    """Grobe heuristische Klassifikation des Hook-Typs anhand des Captionanfangs."""
    text = caption.strip()
    if not text:
        return "Ohne Caption"

    first = text.split("\n", 1)[0].strip()
    lower = first.lower()

    # Frage-Hook: endet mit ? oder beginnt mit typischen Fragewörtern.
    if first.endswith("?") or re.match(
        r"^(warum|wie|was|wieso|weshalb|wer|wann|kennst du|wusstest du)\b", lower
    ):
        return "Frage"
    # Listen-/Zahl-Hook: beginnt mit einer Zahl ("3 Nischen ...").
    if re.match(r"^\d+\s", first):
        return "Zahl/Liste"
    # Story-/Ich-Hook: persönlicher Erfahrungsbericht.
    if re.match(r"^(ich|mein|meine|als ich|letztes jahr|vor \d)", lower):
        return "Story/Persönlich"
    # Imperativ-/CTA-Hook.
    if re.match(r"^(speicher|merk|stop|hör auf|mach|starte|vergiss)", lower):
        return "Aufforderung"
    return "Behauptung/Aussage"


def detect_patterns(videos: list[Video]) -> dict:
    """Erkennt wiederkehrende Muster in den (Top-)Videos.

    Liefert ein Dict mit: häufigste Hook-Typen, Caption-Längen-Statistik,
    häufigste Audios und beste Posting-Stunden. Wird im Report und im
    Claude-Prompt verwendet.
    """
    if not videos:
        return {}

    hook_counts = Counter(_classify_hook(v.caption) for v in videos)

    caption_lengths = [len(v.caption) for v in videos if v.caption]
    length_stats = {
        "min": min(caption_lengths) if caption_lengths else 0,
        "median": int(median(caption_lengths)) if caption_lengths else 0,
        "max": max(caption_lengths) if caption_lengths else 0,
    }

    audio_counts = Counter(v.audio_name for v in videos if v.audio_name.strip())

    # Beste Posting-Zeiten: Stunde (UTC) der Veröffentlichung.
    hour_counts = Counter(
        v.date.hour for v in videos if v.date is not None
    )

    return {
        "hook_types": hook_counts.most_common(),
        "caption_length": length_stats,
        "top_audios": audio_counts.most_common(5),
        "best_hours_utc": hour_counts.most_common(5),
        "sample_size": len(videos),
    }
