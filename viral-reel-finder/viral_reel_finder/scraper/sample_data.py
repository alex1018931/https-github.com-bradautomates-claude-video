"""Beispieldaten für den Trockenlauf-Modus (--dry-run).

Damit kannst du die komplette Pipeline (Analyse, Skript-Generierung, Report,
Telegram) testen, ohne tatsächlich zu scrapen. Die Daten sind realistische,
deutschsprachige Faceless-Online-Business-Beispiele.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Video


def get_sample_videos() -> list[Video]:
    """Liefert eine feste Liste von Beispiel-Videos zurück."""
    now = datetime.now(timezone.utc)

    samples = [
        Video(
            url="https://www.tiktok.com/@beispiel/video/1000000000000000001",
            platform="tiktok",
            views=1_250_000,
            likes=210_000,
            comments=3_400,
            caption="3 Faceless-Nischen, die 2024 noch keiner ernst nimmt – "
            "Nummer 2 hat mir die ersten 500€ gebracht. #facelesscontent #nebeneinkommen",
            hashtags=["facelesscontent", "nebeneinkommen", "onlinebusiness"],
            audio_name="original sound - growth_de",
            date=now - timedelta(days=3),
        ),
        Video(
            url="https://www.tiktok.com/@beispiel/video/1000000000000000002",
            platform="tiktok",
            views=890_000,
            likes=64_000,
            comments=1_100,
            caption="Warum dein digitales Produkt sich nicht verkauft (ehrlich erklärt). "
            "#digitaleprodukte #onlinebusiness",
            hashtags=["digitaleprodukte", "onlinebusiness"],
            audio_name="aesthetic ambient",
            date=now - timedelta(days=10),
        ),
        Video(
            url="https://www.instagram.com/reel/ABCdef00001/",
            platform="instagram",
            views=540_000,
            likes=48_000,
            comments=920,
            caption="Ich habe 30 Tage lang Faceless-Reels gepostet. Das ist wirklich passiert. "
            "#facelesscontent #sidehustle",
            hashtags=["facelesscontent", "sidehustle"],
            audio_name="lofi study beats",
            date=now - timedelta(days=2),
        ),
        Video(
            url="https://www.instagram.com/reel/ABCdef00002/",
            platform="instagram",
            views=320_000,
            likes=21_000,
            comments=410,
            caption="Passives Einkommen ist kein Mythos – aber auch kein Selbstläufer. "
            "Meine 3 ehrlichen Learnings. #passiveseinkommen #onlinebusiness",
            hashtags=["passiveseinkommen", "onlinebusiness"],
            audio_name="original sound - finanztipps",
            date=now - timedelta(days=18),
        ),
        Video(
            url="https://www.tiktok.com/@beispiel/video/1000000000000000005",
            platform="tiktok",
            views=2_100_000,
            likes=305_000,
            comments=5_600,
            caption="Diese eine Routine hat meinen Side-Hustle verändert. "
            "Speicher dir das für später. #sidehustle #nebeneinkommen #produktivität",
            hashtags=["sidehustle", "nebeneinkommen", "produktivität"],
            audio_name="motivational piano",
            date=now - timedelta(days=1),
        ),
        Video(
            url="https://www.tiktok.com/@beispiel/video/1000000000000000006",
            platform="tiktok",
            views=75_000,
            likes=3_200,
            comments=85,
            caption="Tool-Stack für Faceless-Content (komplett kostenlos). "
            "#facelesscontent #digitaleprodukte",
            hashtags=["facelesscontent", "digitaleprodukte"],
            audio_name="original sound - toolnerd",
            date=now - timedelta(days=5),
        ),
        Video(
            url="https://www.instagram.com/reel/ABCdef00007/",
            platform="instagram",
            views=410_000,
            likes=39_500,
            comments=730,
            caption="Wenn ich nochmal mit 0 Followern starten müsste, würde ich GENAU das tun. "
            "#onlinebusiness #nebeneinkommen",
            hashtags=["onlinebusiness", "nebeneinkommen"],
            audio_name="trending audio de",
            date=now - timedelta(days=4),
        ),
        Video(
            url="https://www.tiktok.com/@beispiel/video/1000000000000000008",
            platform="tiktok",
            views=160_000,
            likes=12_800,
            comments=240,
            caption="5 Hooks, die bei Faceless-Reels fast immer funktionieren. "
            "#facelesscontent #onlinebusiness",
            hashtags=["facelesscontent", "onlinebusiness"],
            audio_name="upbeat corporate",
            date=now - timedelta(days=7),
        ),
    ]
    return samples
