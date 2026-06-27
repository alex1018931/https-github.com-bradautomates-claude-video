"""TikTok-Scraper auf Basis von yt-dlp.

yt-dlp ist deutlich robuster als eigenes HTML-Parsing, weil es die Extraktion
der TikTok-Seiten pflegt. Wir holen pro Hashtag eine flache Liste von Video-URLs
und reichern sie anschließend mit Metadaten an.

WICHTIG: TikTok ändert seine Seiten häufig. Bricht der Extraktor, reicht dieses
Modul die Exception nach oben – run.py meldet das dann per Telegram.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import Config
from ..logging_setup import get_logger
from ..models import Video
from .base import polite_delay, random_user_agent, retry


def _safe_int(value) -> int:
    """Wandelt yt-dlp-Felder defensiv in int um (None/Strings -> 0)."""
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _entry_to_video(entry: dict) -> Video | None:
    """Mappt einen yt-dlp-Info-Dict auf unser Video-Modell."""
    url = entry.get("webpage_url") or entry.get("url") or ""
    if not url:
        return None

    # Datum: yt-dlp liefert 'timestamp' (Unix) oder 'upload_date' (YYYYMMDD).
    date: datetime | None = None
    ts = entry.get("timestamp")
    if ts:
        try:
            date = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            date = None
    elif entry.get("upload_date"):
        try:
            date = datetime.strptime(str(entry["upload_date"]), "%Y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            date = None

    caption = entry.get("description") or entry.get("title") or ""
    # Hashtags aus der Caption herausziehen.
    hashtags = [tag.lstrip("#").lower() for tag in caption.split() if tag.startswith("#")]

    # Audio-/Track-Name aus diversen möglichen Feldern.
    audio_name = entry.get("track") or entry.get("artist") or ""

    return Video(
        url=url,
        platform="tiktok",
        views=_safe_int(entry.get("view_count")),
        likes=_safe_int(entry.get("like_count")),
        comments=_safe_int(entry.get("comment_count")),
        caption=caption,
        hashtags=hashtags,
        audio_name=audio_name,
        date=date,
    )


@retry(max_retries=3)
def _extract(url: str, ydl_opts: dict) -> dict:
    """Ein einzelner yt-dlp-Aufruf (mit Retry-Decorator umhüllt)."""
    # Import bewusst lokal: yt-dlp ist optional, soll den Dry-Run nicht blockieren.
    from yt_dlp import YoutubeDL

    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def scrape_hashtag(hashtag: str, config: Config) -> list[Video]:
    """Scrapt Videos zu einem Hashtag von TikTok.

    Args:
        hashtag: Hashtag ohne '#'.
        config: globale Konfiguration (Limits, Delays, Retries).

    Returns:
        Liste von Video-Objekten (ggf. leer, wenn nichts gefunden wurde).
    """
    logger = get_logger()
    tag_url = f"https://www.tiktok.com/tag/{hashtag}"
    logger.info("TikTok: scrape Hashtag #%s", hashtag)

    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "http_headers": {"User-Agent": random_user_agent()},
        "extractor_args": {"tiktok": {"webpage_download": ["1"]}},
    }

    # 1) Flache Liste der Videos zum Hashtag holen.
    flat_opts = {**base_opts, "extract_flat": True, "playlistend": config.max_videos_per_source}
    info = _extract(tag_url, flat_opts)
    entries = (info or {}).get("entries") or []
    logger.info("TikTok #%s: %d Einträge in der Liste gefunden", hashtag, len(entries))

    videos: list[Video] = []
    detail_opts = {**base_opts}

    for entry in entries[: config.max_videos_per_source]:
        # Bei flacher Extraktion fehlen oft die Metriken -> Detailabruf.
        entry_url = entry.get("url") or entry.get("webpage_url")
        if not entry_url:
            continue
        try:
            polite_delay(config.delay_min, config.delay_max)
            detail = _extract(entry_url, detail_opts)
            video = _entry_to_video(detail)
            if video:
                videos.append(video)
        except Exception as exc:  # Einzelnes Video soll den Hashtag nicht abbrechen.
            logger.warning("TikTok: Detailabruf fehlgeschlagen (%s): %s", entry_url, exc)
            continue

    logger.info("TikTok #%s: %d Videos mit Metadaten erfasst", hashtag, len(videos))
    return videos


def scrape(config: Config) -> list[Video]:
    """Scrapt alle konfigurierten Hashtags von TikTok.

    Einzelne Hashtag-Fehler werden geloggt, brechen aber nicht den ganzen Lauf ab.
    """
    logger = get_logger()
    all_videos: list[Video] = []
    for hashtag in config.hashtags:
        try:
            all_videos.extend(scrape_hashtag(hashtag, config))
        except Exception as exc:
            logger.error("TikTok: Hashtag #%s komplett fehlgeschlagen: %s", hashtag, exc)
            continue
    return all_videos
