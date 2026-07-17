# Viral Reel Finder

Ein Python-Tool, das **automatisch per Zeitplan** (Windows-Aufgabenplaner / Cron) läuft,
die viralsten **Faceless-Reels/TikToks** in deiner Nische findet, sie nach Performance
rankt, mit **Claude** bessere deutsche Skripte generiert und dir das Ergebnis per
**Telegram** schickt.

> ⚠️ **Ehrlicher Hinweis zur Realität:** Dieses Tool nutzt **keine offizielle API**.
> Es scrapt öffentliche Daten. Das verstößt gegen die ToS von TikTok/Instagram und ist
> **fragil** – Plattformen ändern ständig ihre Seiten, und es kann zu Blocks oder
> 0-Ergebnissen kommen. Das Tool ist deshalb so gebaut, dass es bei **jedem Fehler laut
> ist**: Es loggt in eine Datei **und** schickt dir eine Telegram-Warnung. Zum Testen
> gibt es einen **Trockenlauf-Modus** mit Beispieldaten (`--dry-run`), der zuverlässig
> funktioniert.

---

## Was das Tool tut

1. **Scrapen** – TikTok (über `yt-dlp`) und Instagram (über `instaloader`) zu deinen Hashtags.
2. **Ranken** – „Viral-Score" aus Engagement-Rate **und** Views-pro-Tag (frische, schnell
   wachsende Videos kommen nach oben). Top 20 (konfigurierbar).
3. **Muster erkennen** – häufigste Hook-Typen, Caption-Längen, Audios, beste Posting-Zeiten.
4. **Skripte generieren** – pro Top-Video ein neues, besseres Faceless-Reel-Skript auf
   Deutsch (Hook → 3–5 Bildszenen mit Text-Overlay → CTA) inkl. Begründung.
5. **Speichern** – `output/results_YYYY-MM-DD.md` und `.csv`.
6. **Melden** – Telegram-Zusammenfassung bei Erfolg, Warnung bei Fehler/0 Ergebnissen.

---

## a) Setup unter Windows

### 1. Python installieren
Lade Python 3.10+ von <https://www.python.org/downloads/> und **aktiviere beim Installieren
die Checkbox „Add Python to PATH"**.

### 2. Projekt vorbereiten
Öffne die **Eingabeaufforderung (cmd)** im Projektordner `viral-reel-finder` und führe aus:

```bat
:: Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
.venv\Scripts\activate

:: Abhängigkeiten installieren
pip install -r requirements.txt
```

### 3. Geheime Schlüssel eintragen
Kopiere die Vorlage und trage deine Werte ein:

```bat
copy .env.example .env
notepad .env
```

In der `.env` brauchst du:
- `ANTHROPIC_API_KEY` – von <https://console.anthropic.com/> (→ API Keys)
- `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` – siehe Abschnitt **c)**

### 4. Nische anpassen
Öffne `config.yaml` und passe `hashtags`, `min_views`, `top_n` und `platform` an deine
Nische an.

### 5. Erst einmal trocken testen (ohne Scraping)
```bat
python run.py --dry-run
```
Danach liegen in `output/` eine `.md`- und eine `.csv`-Datei, und (falls Telegram
eingerichtet ist) bekommst du eine Nachricht. So prüfst du, dass Keys, Claude und
Telegram funktionieren, bevor du echtes Scraping startest.

### 6. Echter Lauf
```bat
python run.py
```

**Befehlsoptionen:**
| Befehl | Wirkung |
|---|---|
| `python run.py` | Echter Lauf, Plattform aus `config.yaml` |
| `python run.py --dry-run` | Test mit Beispieldaten (kein Scraping) |
| `python run.py --platform tiktok` | Plattform überschreiben (`tiktok`/`instagram`/`beide`) |
| `python run.py --config pfad.yaml` | Andere Konfigurationsdatei nutzen |

---

## b) Automatisch starten mit dem Windows-Aufgabenplaner

Damit das Tool z. B. **täglich um 7:00 Uhr** läuft.

### Empfohlen: kleine Start-Datei (`run.bat`)
Lege im Projektordner eine Datei `run.bat` mit diesem Inhalt an (Pfad anpassen):

```bat
@echo off
cd /d C:\Pfad\zu\viral-reel-finder
call .venv\Scripts\activate
python run.py
```

> Die `.bat` aktiviert die virtuelle Umgebung und startet das Tool – so musst du im
> Aufgabenplaner nur eine einzige Datei angeben.

### Aufgabe einrichten
1. **Startmenü → „Aufgabenplanung"** öffnen.
2. Rechts auf **„Einfache Aufgabe erstellen…"** klicken.
3. **Name:** z. B. `Viral Reel Finder` → Weiter.
4. **Trigger:** „Täglich" → Weiter → Uhrzeit **07:00** einstellen → Weiter.
5. **Aktion:** „Programm starten" → Weiter.
6. **Programm/Skript:** den vollen Pfad zur `run.bat` eintragen, z. B.
   `C:\Pfad\zu\viral-reel-finder\run.bat`
   - **„Starten in (optional)":** `C:\Pfad\zu\viral-reel-finder`
7. **Fertig stellen.**

**Ohne `.bat`** (direkt Python) ginge es auch so:
- **Programm/Skript:** `C:\Pfad\zu\viral-reel-finder\.venv\Scripts\python.exe`
- **Argumente:** `run.py`
- **Starten in:** `C:\Pfad\zu\viral-reel-finder`

> 💡 Tipp: In den Aufgaben-Eigenschaften „Unabhängig von der Benutzeranmeldung ausführen"
> wählen, damit es auch ohne aktive Sitzung läuft.

### Cron-Äquivalent (Linux/macOS)
```cron
# Täglich 07:00 Uhr
0 7 * * * cd /pfad/zu/viral-reel-finder && /pfad/zu/.venv/bin/python run.py >> logs/cron.log 2>&1
```

---

## c) Telegram-Bot erstellen und Chat-ID finden

### 1. Bot anlegen (BotFather)
1. In Telegram **@BotFather** suchen und Chat öffnen.
2. `/newbot` senden.
3. Namen und Benutzernamen (muss auf `bot` enden) vergeben.
4. BotFather schickt dir den **Token** (sieht aus wie `123456789:AAxxxx...`).
   → in der `.env` als `TELEGRAM_BOT_TOKEN` eintragen.

### 2. Chat-ID herausfinden
1. Schreibe deinem neuen Bot in Telegram **irgendeine Nachricht** (z. B. „hallo"),
   damit ein Chat existiert.
2. Öffne im Browser (Token einsetzen):
   ```
   https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates
   ```
3. Suche im JSON nach `"chat":{"id":...}`. Diese Zahl ist deine **Chat-ID**.
   → in der `.env` als `TELEGRAM_CHAT_ID` eintragen.

> Alternativ: Schreibe **@userinfobot** an – er nennt dir direkt deine numerische ID.

---

## Projektstruktur

```
viral-reel-finder/
├── config.yaml              # deine Einstellungen
├── .env                     # deine Keys (NICHT einchecken)
├── requirements.txt
├── run.py                   # Hauptbefehl
├── viral_reel_finder/
│   ├── config.py            # Konfiguration laden/validieren
│   ├── logging_setup.py     # Datei- + Konsolen-Logging
│   ├── models.py            # Datenstrukturen
│   ├── analyzer.py          # Viral-Score + Mustererkennung
│   ├── script_generator.py  # Claude-Skripte
│   ├── notifier.py          # Telegram
│   ├── report.py            # Markdown + CSV
│   └── scraper/
│       ├── base.py          # Delay, User-Agent-Rotation, Retry
│       ├── tiktok.py        # yt-dlp
│       ├── instagram.py     # instaloader
│       └── sample_data.py   # Beispieldaten (Dry-Run)
├── output/                  # Ergebnisse (.md / .csv)
└── logs/                    # Log-Dateien
```

---

## Fehlerbehebung

| Symptom | Ursache / Lösung |
|---|---|
| Telegram „🚨 0 Videos über dem Filter" | Scraper hat nichts geliefert ODER `min_views` zu hoch. Senke `min_views` oder prüfe das Log unter `logs/`. |
| Telegram „Skript-Generierung fehlgeschlagen" | `ANTHROPIC_API_KEY` fehlt/ungültig, oder Rate-Limit. Key in `.env` prüfen. |
| Keine Telegram-Nachricht | `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` prüfen. Ohne diese loggt das Tool die Nachricht nur. |
| TikTok/Instagram liefert plötzlich nichts | Normal – Scraping ist fragil. Plattformänderungen können den Scraper brechen. Log prüfen; ggf. `yt-dlp`/`instaloader` aktualisieren (`pip install -U yt-dlp instaloader`). |

> Jeder Lauf schreibt ein vollständiges Log nach `logs/run_YYYY-MM-DD.log` – dort steht
> immer, was genau passiert ist.
