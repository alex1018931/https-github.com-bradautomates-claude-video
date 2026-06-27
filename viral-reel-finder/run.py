#!/usr/bin/env python3
"""Viral Reel Finder – Hauptbefehl.

Führt die gesamte Pipeline nacheinander aus:
  1. Konfiguration + Logging laden
  2. Scrapen (TikTok / Instagram / beide) – oder Beispieldaten im Dry-Run
  3. Analyse (Viral-Score, Top-N, Muster)
  4. Skript-Generierung mit Claude
  5. Report schreiben (Markdown + CSV)
  6. Telegram-Benachrichtigung (Erfolg ODER Fehler)

Designprinzip: KEIN Modul bricht still ab. Jeder Fehler wird geloggt und – wo es
einen Lauf wertlos macht (z.B. 0 Ergebnisse) – per Telegram laut gemeldet.

Aufruf-Beispiele:
    python run.py                      # echter Lauf, Plattform aus config.yaml
    python run.py --dry-run            # Test mit Beispieldaten (kein Scraping)
    python run.py --platform tiktok    # überschreibt die Plattform
    python run.py --config pfad.yaml   # andere Konfigurationsdatei
"""

from __future__ import annotations

import argparse
import sys

from viral_reel_finder import analyzer, notifier, report, script_generator
from viral_reel_finder.config import ConfigError, load_config
from viral_reel_finder.logging_setup import setup_logging
from viral_reel_finder.models import RunResult
from viral_reel_finder.scraper import instagram, tiktok
from viral_reel_finder.scraper.sample_data import get_sample_videos


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Viral Reel Finder")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mit Beispieldaten testen, ohne tatsächlich zu scrapen.",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Pfad zur Konfigurationsdatei (Standard: config.yaml).",
    )
    parser.add_argument(
        "--platform",
        choices=["tiktok", "instagram", "beide"],
        help="Überschreibt die Plattform aus der config.yaml.",
    )
    return parser.parse_args()


def _scrape(config, platform, dry_run, logger):
    """Sammelt Videos je nach Plattform/Modus. Gibt eine Liste von Video zurück."""
    if dry_run:
        logger.info("DRY-RUN: verwende Beispieldaten statt echtem Scraping.")
        videos = get_sample_videos()
        if platform in ("tiktok", "instagram"):
            videos = [v for v in videos if v.platform == platform]
        return videos

    videos = []
    if platform in ("tiktok", "beide"):
        videos.extend(tiktok.scrape(config))
    if platform in ("instagram", "beide"):
        videos.extend(instagram.scrape(config))
    return videos


def main() -> int:
    args = parse_args()

    # --- 1. Konfiguration + Logging -----------------------------------------
    # Config zuerst laden, weil wir die Logs/Telegram-Daten daraus brauchen.
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        # Hier gibt es noch keinen Logger/Telegram – auf stderr ausgeben.
        print(f"[KONFIGURATIONSFEHLER] {exc}", file=sys.stderr)
        return 2

    logger = setup_logging(config.logs_dir, verbose=True)
    platform = args.platform or config.platform
    logger.info(
        "Lauf gestartet – Plattform=%s, Dry-Run=%s, Hashtags=%s",
        platform,
        args.dry_run,
        ", ".join("#" + h for h in config.hashtags),
    )

    result = RunResult()

    # Ab hier: jeder Schritt gekapselt. Fehler -> Telegram-Alert + Abbruch
    # mit Exit-Code, NICHT stilles Scheitern.
    try:
        # --- 2. Scrapen -----------------------------------------------------
        try:
            scraped = _scrape(config, platform, args.dry_run, logger)
        except Exception as exc:
            msg = f"Scraping komplett fehlgeschlagen ({platform}): {exc}"
            logger.exception(msg)
            notifier.notify_error(config, msg)
            return 1

        result.scraped_count = len(scraped)
        logger.info("Scraping fertig: %d Videos insgesamt.", len(scraped))

        # --- 3. Analyse -----------------------------------------------------
        scored = analyzer.score_videos(scraped, config.min_views)
        result.analyzed_count = len(scored)

        if not scored:
            # Lauter Fehler: 0 verwertbare Ergebnisse.
            msg = (
                f"0 Videos über dem Filter (min_views={config.min_views}). "
                f"Gescrapt wurden {len(scraped)} Videos. "
                "Möglicher gebrochener Scraper oder zu strenger Filter."
            )
            logger.error(msg)
            notifier.notify_error(config, msg)
            return 1

        top_videos = analyzer.top_n(scored, config.top_n)
        result.patterns = analyzer.detect_patterns(top_videos)
        logger.info("Analyse fertig: %d Top-Videos ausgewählt.", len(top_videos))

        # --- 4. Skript-Generierung -----------------------------------------
        try:
            result.scripts = script_generator.generate_scripts(
                top_videos, result.patterns, config
            )
            # Teilfehler (einzelne Videos) als Hinweise sammeln.
            for sr in result.scripts:
                if sr.error:
                    result.errors.append(f"Rang {sr.rank}: {sr.error}")
        except Exception as exc:
            # Z.B. fehlender API-Key: Report trotzdem schreiben, aber melden.
            msg = f"Skript-Generierung fehlgeschlagen: {exc}"
            logger.exception(msg)
            result.errors.append(msg)
            # Ohne Skripte trotzdem Report mit Roh-Daten erzeugen.
            from viral_reel_finder.models import ScriptResult

            result.scripts = [
                ScriptResult(video=v, rank=i, error="Keine Generierung (siehe Fehler oben).")
                for i, v in enumerate(top_videos, start=1)
            ]
            notifier.notify_error(config, msg)

        # --- 5. Report ------------------------------------------------------
        result.md_path = str(report.write_markdown(result, config.output_dir))
        result.csv_path = str(report.write_csv(result, config.output_dir))

        # --- 6. Telegram ----------------------------------------------------
        # Erfolg melden, wenn mindestens ein Skript ohne Fehler erzeugt wurde.
        has_real_script = any(sr.error is None for sr in result.scripts)
        if has_real_script:
            notifier.notify_success(config, result)
        elif not result.errors:
            # Kein Skript, aber auch kein gemeldeter Fehler -> trotzdem melden.
            notifier.notify_error(
                config, "Lauf beendet, aber kein einziges Skript wurde erzeugt."
            )

        logger.info("Lauf erfolgreich beendet.")
        return 0

    except Exception as exc:
        # Letzte Sicherheitsleine: nichts darf still verschwinden.
        msg = f"Unerwarteter Fehler im Hauptlauf: {exc}"
        logger.exception(msg)
        notifier.notify_error(config, msg)
        return 1


if __name__ == "__main__":
    sys.exit(main())
