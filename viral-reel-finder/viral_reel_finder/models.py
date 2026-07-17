"""Datenstrukturen, die durch die gesamte Pipeline gereicht werden.

Bewusst als einfache @dataclass gehalten – leicht zu serialisieren (CSV/MD)
und überall gut lesbar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Video:
    """Ein einzelnes gescraptes Video (TikTok oder Instagram)."""

    url: str
    platform: str  # "tiktok" oder "instagram"
    views: int = 0
    likes: int = 0
    comments: int = 0
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    audio_name: str = ""
    # Veröffentlichungsdatum (UTC). Kann None sein, wenn die Quelle es nicht liefert.
    date: datetime | None = None

    # Wird vom Analyzer befüllt:
    engagement_rate: float = 0.0
    views_per_day: float = 0.0
    viral_score: float = 0.0

    @property
    def hook(self) -> str:
        """Der "Hook" eines Videos = die ersten ~120 Zeichen der Caption.

        Faceless-Reels leben vom Aufhänger in den ersten 3 Sekunden; in der
        Caption steht meist genau dieser Aufhänger zuerst.
        """
        clean = " ".join(self.caption.split())
        return clean[:120] if clean else "(keine Caption)"

    @property
    def age_in_days(self) -> float:
        """Alter des Videos in Tagen (mind. ~0, nie negativ)."""
        if self.date is None:
            # Ohne Datum nehmen wir konservativ 7 Tage an, damit views_per_day
            # nicht künstlich explodiert.
            return 7.0
        now = datetime.now(timezone.utc)
        # Falls das Datum naiv (ohne Zeitzone) ist, als UTC interpretieren.
        ref = self.date if self.date.tzinfo else self.date.replace(tzinfo=timezone.utc)
        delta_days = (now - ref).total_seconds() / 86400.0
        return max(delta_days, 0.04)  # mind. ~1 Stunde, gegen Division durch 0


@dataclass
class ScriptResult:
    """Das von Claude generierte neue Skript für ein Top-Video."""

    video: Video
    rank: int
    new_script: str = ""
    reasoning: str = ""
    error: str | None = None  # gesetzt, wenn die Generierung fehlschlug


@dataclass
class RunResult:
    """Gesamtergebnis eines Laufs – Basis für Report und Telegram-Nachricht."""

    scraped_count: int = 0
    analyzed_count: int = 0
    patterns: dict = field(default_factory=dict)
    scripts: list[ScriptResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    md_path: str | None = None
    csv_path: str | None = None
