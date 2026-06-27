"""Ergebnis-Export als Markdown und CSV.

- results_YYYY-MM-DD.md : menschlich lesbar (Rang, Link, Score, Original-Hook,
  neues Skript, Begründung) + Muster-Übersicht oben.
- results_YYYY-MM-DD.csv: flache Tabelle für Tabellenkalkulation.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .logging_setup import get_logger
from .models import RunResult


def _format_patterns(patterns: dict) -> str:
    """Formatiert die erkannten Muster als Markdown-Abschnitt."""
    if not patterns:
        return "_Keine Muster erkannt._\n"

    lines = ["## Erkannte Muster\n"]

    hooks = patterns.get("hook_types", [])
    if hooks:
        lines.append("**Häufigste Hook-Typen:**")
        for name, count in hooks:
            lines.append(f"- {name}: {count}x")
        lines.append("")

    length = patterns.get("caption_length", {})
    if length:
        lines.append(
            f"**Caption-Länge (Zeichen):** min {length.get('min', '?')}, "
            f"median {length.get('median', '?')}, max {length.get('max', '?')}\n"
        )

    audios = patterns.get("top_audios", [])
    if audios:
        lines.append("**Häufigste Audios:**")
        for name, count in audios:
            lines.append(f"- {name}: {count}x")
        lines.append("")

    hours = patterns.get("best_hours_utc", [])
    if hours:
        formatted = ", ".join(f"{h:02d}:00 ({c}x)" for h, c in hours)
        lines.append(f"**Beste Posting-Stunden (UTC):** {formatted}\n")

    return "\n".join(lines) + "\n"


def write_markdown(result: RunResult, output_dir: Path) -> Path:
    """Schreibt den Markdown-Report und gibt den Pfad zurück."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"results_{date.today().isoformat()}.md"

    parts = [
        f"# Viral Reel Finder – Ergebnisse {date.today().isoformat()}\n",
        f"- Gescrapte Videos: **{result.scraped_count}**",
        f"- Analysiert (über Filter): **{result.analyzed_count}**",
        f"- Generierte Skripte: **{len(result.scripts)}**\n",
        _format_patterns(result.patterns),
        "## Top-Videos & neue Skripte\n",
    ]

    for sr in result.scripts:
        v = sr.video
        parts.append(f"### Rang {sr.rank} – Viral-Score {v.viral_score:.3f}\n")
        parts.append(f"- **Link:** {v.url}")
        parts.append(f"- **Plattform:** {v.platform}")
        parts.append(
            f"- **Views:** {v.views:,} | **Engagement:** {v.engagement_rate:.2%} "
            f"| **Views/Tag:** {v.views_per_day:,.0f}"
        )
        parts.append(f"- **Original-Hook:** {v.hook}\n")

        if sr.error:
            parts.append(f"> ⚠️ {sr.error}\n")
        else:
            parts.append("**Neues Skript:**\n")
            parts.append("```")
            parts.append(sr.new_script)
            parts.append("```\n")
            if sr.reasoning:
                parts.append(f"**Begründung:** {sr.reasoning}\n")

        parts.append("---\n")

    path.write_text("\n".join(parts), encoding="utf-8")
    get_logger().info("Markdown-Report geschrieben: %s", path)
    return path


def write_csv(result: RunResult, output_dir: Path) -> Path:
    """Schreibt die CSV-Tabelle und gibt den Pfad zurück."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"results_{date.today().isoformat()}.csv"

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "Rang",
                "URL",
                "Plattform",
                "Viral-Score",
                "Views",
                "Likes",
                "Kommentare",
                "Engagement-Rate",
                "Views/Tag",
                "Original-Hook",
                "Neues Skript",
                "Begründung",
                "Fehler",
            ]
        )
        for sr in result.scripts:
            v = sr.video
            writer.writerow(
                [
                    sr.rank,
                    v.url,
                    v.platform,
                    f"{v.viral_score:.4f}",
                    v.views,
                    v.likes,
                    v.comments,
                    f"{v.engagement_rate:.4f}",
                    f"{v.views_per_day:.0f}",
                    v.hook,
                    sr.new_script,
                    sr.reasoning,
                    sr.error or "",
                ]
            )

    get_logger().info("CSV-Report geschrieben: %s", path)
    return path
