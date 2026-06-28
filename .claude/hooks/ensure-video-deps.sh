#!/usr/bin/env bash
# SessionStart hook for the /watch skill (bradautomates/claude-video).
#
# The web/remote container is ephemeral, so ffmpeg + yt-dlp must be (re)installed
# at the start of each session for /watch to work. This is best-effort and never
# fails the session: it exits 0 even if installation cannot complete.

set -u
LOG="/tmp/watch-deps-install.log"

have() { command -v "$1" >/dev/null 2>&1; }

# Already good? exit fast and quiet.
if have ffmpeg && have ffprobe && have yt-dlp; then
  exit 0
fi

{
  echo "[ensure-video-deps] $(date -u 2>/dev/null) installing missing video deps"

  # yt-dlp via pip (fast, no root needed).
  if ! have yt-dlp; then
    if have pip3; then pip3 install -q yt-dlp || true
    elif have pip; then pip install -q yt-dlp || true
    fi
  fi

  # ffmpeg/ffprobe via the system package manager.
  if ! have ffmpeg || ! have ffprobe; then
    SUDO=""; [ "$(id -u)" -ne 0 ] && have sudo && SUDO="sudo"
    if have apt-get; then
      $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg || true
    elif have dnf; then
      $SUDO dnf install -y -q ffmpeg || true
    elif have apk; then
      $SUDO apk add --no-cache ffmpeg || true
    elif have brew; then
      brew install ffmpeg || true
    fi
  fi

  echo "[ensure-video-deps] ffmpeg=$(command -v ffmpeg || echo none) yt-dlp=$(command -v yt-dlp || echo none)"
} >>"$LOG" 2>&1

exit 0
