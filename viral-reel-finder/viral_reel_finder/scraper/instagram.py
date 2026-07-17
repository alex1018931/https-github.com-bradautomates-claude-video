"""Instagram-Scraper auf Basis von instaloader.

instaloader greift öffentliche Hashtag-Seiten anonym (ohne Login) ab. Das ist
für den unbeaufsichtigten Betrieb am risikoärmsten (kein Account, der gesperrt
werden kann), aber anonym ist Instagram besonders restriktiv – mit Rate-Limits
und gelegentlichen Blocks ist zu rechnen.

WICHTIG: Anonymer Zugriff ist fragil. Bricht der Abruf, reicht dieses Modul die
Exception nach oben – run.py meldet das per Telegram.
"""

from __future__ import annotations

from datetime import timezone

from ..config import Config
from ..logging_setup import get_logger
from ..models import Video
from .base import polite_delay, retry


def _post_to_video(post) -> Video | None:
    """Mappt einen instaloader-Post auf unser Video-Modell.

    Nur Videos/Reels sind relevant (Bild-Posts überspringen wir).
    """
    if not getattr(post, "is_video", False):
        return None

    shortcode = getattr(post, "shortcode", "")
    url = f"https://www.instagram.com/reel/{shortcode}/" if shortcode else ""
    if not url:
        return None

    caption = post.caption or ""
    hashtags = []
    try:
        # instaloader liefert caption_hashtags als Liste ohne '#'.
        hashtags = [h.lower() for h in (post.caption_hashtags or [])]
    except Exception:
        hashtags = [t.lstrip("#").lower() for t in caption.split() if t.startswith("#")]

    # view_count gibt es nur für Videos; fällt sonst auf video_view_count/0 zurück.
    views = getattr(post, "video_view_count", None) or getattr(post, "view_count", 0) or 0

    date = getattr(post, "date_utc", None)
    if date is not None and date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return Video(
        url=url,
        platform="instagram",
        views=int(views),
        likes=int(getattr(post, "likes", 0) or 0),
        comments=int(getattr(post, "comments", 0) or 0),
        caption=caption,
        hashtags=hashtags,
        audio_name="",  # Anonym liefert instaloader keinen verlässlichen Audio-Namen.
        date=date,
    )


@retry(max_retries=3)
def _get_hashtag_posts(loader, hashtag: str):
    """Holt einen iterierbaren Post-Generator für einen Hashtag (mit Retry)."""
    import instaloader

    return instaloader.Hashtag.by_name(loader.context, hashtag).get_posts()


def scrape_hashtag(hashtag: str, config: Config) -> list[Video]:
    """Scrapt öffentliche Reels zu einem Hashtag von Instagram.

    Args:
        hashtag: Hashtag ohne '#'.
        config: globale Konfiguration.

    Returns:
        Liste von Video-Objekten (ggf. leer).
    """
    logger = get_logger()
    logger.info("Instagram: scrape Hashtag #%s", hashtag)

    # Import lokal, damit der Dry-Run ohne installiertes instaloader läuft.
    import instaloader

    loader = instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    videos: list[Video] = []
    posts = _get_hashtag_posts(loader, hashtag)

    count = 0
    for post in posts:
        if count >= config.max_videos_per_source:
            break
        try:
            video = _post_to_video(post)
            if video:
                videos.append(video)
            count += 1
            polite_delay(config.delay_min, config.delay_max)
        except Exception as exc:  # Einzelner Post bricht den Hashtag nicht ab.
            logger.warning("Instagram: Post übersprungen (#%s): %s", hashtag, exc)
            continue

    logger.info("Instagram #%s: %d Videos erfasst", hashtag, len(videos))
    return videos


def scrape(config: Config) -> list[Video]:
    """Scrapt alle konfigurierten Hashtags von Instagram.

    Einzelne Hashtag-Fehler werden geloggt, brechen aber nicht den ganzen Lauf ab.
    """
    logger = get_logger()
    all_videos: list[Video] = []
    for hashtag in config.hashtags:
        try:
            all_videos.extend(scrape_hashtag(hashtag, config))
        except Exception as exc:
            logger.error("Instagram: Hashtag #%s komplett fehlgeschlagen: %s", hashtag, exc)
            continue
    return all_videos
