#!/usr/bin/env python3
"""
YouTube metadata + English transcript extractor

Rules enforced:
    - Transcript must be in English (en)
    - Output folder name = video_id only
    - If no English transcript exists -> video is rejected
    - Script keeps running until user exits

Dependencies:
  pip install yt-dlp youtube-transcript-api

System Requirements (RECOMMENDED for stability):
  - Python 3.10+
  - Node.js (LTS)  # required by yt-dlp for YouTube JS extraction
  - ffmpeg         # recommended by yt-dlp (not strictly required for transcripts)
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
import glob
import re
import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)


# -------------------------
# Utilities
# -------------------------

def get_video_id(youtube_url: str) -> str | None:
    """
    Extract YouTube video ID from various URL formats.
    Examples:
        https://www.youtube.com/watch?v=VIDEO_ID
        https://youtu.be/VIDEO_ID
        https://www.youtube.com/shorts/VIDEO_ID
    :param youtube_url:
    :return:
    """
    parsed = urlparse(youtube_url.strip())
    host = (parsed.hostname or "").lower()

    if host in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        return parse_qs(parsed.query).get("v", [None])[0]

    if host == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0]

    if parsed.path.startswith("/shorts/"):
        parts = parsed.path.split("/")
        return parts[2] if len(parts) > 2 else None

    return None


def extract_metadata(youtube_url: str) -> dict:
    """
    Extract youtube video metadata.
    :param youtube_url:
    :return:
    """
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    upload_date = info.get("upload_date")
    if isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit():
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

    return {
        "title": info.get("title"),
        "video_id": info.get("id"),
        "webpage_url": info.get("webpage_url"),
        "channel": info.get("channel"),
        "uploader": info.get("uploader"),
        "upload_date": upload_date,
        "duration_seconds": info.get("duration"),
        "view_count": info.get("view_count"),
        "description": info.get("description"),
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _vtt_to_text(vtt_path: str) -> str:
    """
    Convert .vtt captions to clean text:
    - removes <c> tags and other HTML-like tags
    - removes inline word timestamps like <00:00:01.650>
    - removes duplicate consecutive lines
    - keeps only cue start timestamps as [seconds]
    """
    ts_line = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+-->")
    inline_ts = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>")
    html_tags = re.compile(r"</?c[^>]*>|<[^>]+>")  # remove <c> and any other <...>

    def hms_to_seconds(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    out = []
    last_text = None
    current_ts = None

    with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if line.startswith("NOTE"):
                continue

            m = ts_line.match(line)
            if m:
                # cue timing line
                current_ts = hms_to_seconds(*m.groups())
                continue

            # skip any other timing lines
            if "-->" in line:
                continue

            # clean text line
            line = inline_ts.sub("", line)
            line = html_tags.sub("", line)
            line = line.replace("&nbsp;", " ").replace("&amp;", "&").strip()
            line = re.sub(r"\s+", " ", line)

            if not line:
                continue

            # de-duplicate consecutive identical caption lines
            if line == last_text:
                continue
            last_text = line

            # attach a timestamp marker when we have one (cue start)
            if current_ts is not None:
                out.append(f"[{current_ts:.2f}] {line}")
                current_ts = None
            else:
                out.append(line)

    return "\n".join(out).strip()


def extract_english_transcript(video_id: str, url: str, base_dir: str = "dataset") -> str | None:
    """
    Strict English-only transcript extractor.
    Tries youtube-transcript-api first, then falls back to yt-dlp subtitles (.vtt).
    Returns transcript string or None (reject).
    """
    english_codes = ["en", "en-US", "en-GB", "en-CA", "en-AU", "en-IN"]

    # --- 1) Try youtube-transcript-api ---
    last_err = None
    for code in english_codes:
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id, languages=[code])
            lines = []
            for e in entries:
                start = float(e.get("start", 0.0))
                text = str(e.get("text", "")).replace("\n", " ").strip()
                lines.append(f"[{start:.2f}] {text}")
            return "\n".join(lines).strip()
        except Exception as e:
            last_err = e

    # If transcript-api failed (often AttributeError), fallback to yt-dlp subtitles.
    # --- 2) Try yt-dlp subtitles ---
    try:
        tmp_dir = os.path.join(base_dir, "__tmp_subs__")
        os.makedirs(tmp_dir, exist_ok=True)

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            # Accept English variants from yt-dlp
            "subtitleslangs": ["en", "en.*"],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmp_dir, f"{video_id}.%(ext)s"),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # yt-dlp may name files like: <id>.en.vtt or <id>.en-US.vtt, etc.
        candidates = glob.glob(os.path.join(tmp_dir, f"{video_id}.en*.vtt"))
        if not candidates:
            # No English subtitles retrieved
            return None

        # Pick the first candidate (you can add sorting if you prefer manual over auto)
        vtt_path = sorted(candidates)[0]
        text = _vtt_to_text(vtt_path)

        # cleanup temp files (optional)
        for p in candidates:
            try:
                os.remove(p)
            except Exception:
                pass

        return text if text else None

    except Exception:
        # Still strict: if we can't retrieve English transcript, reject
        # You can print the error type for debugging:
        # print(f"   (Debug) transcript-api last error: {type(last_err).__name__}: {last_err}")
        return None


# -------------------------
# Main Loop
# -------------------------

def process_video():
    url = input("\nEnter YouTube video URL (or 'q' to quit): ").strip()

    if url.lower() in {"q", "quit", "exit"}:
        print("\n👋 Exiting extractor.")
        sys.exit(0)

    video_id = get_video_id(url)
    if not video_id:
        print("❌ Invalid YouTube URL.")
        return

    print("▶ Checking for English transcript...")
    transcript = extract_english_transcript(video_id, url, base_dir="dataset")

    if transcript is None:
        print("❌ This video does NOT have an English transcript.")
        print("❌ It cannot be used in the dataset.")
        return

    print("▶ Extracting metadata...")
    try:
        metadata = extract_metadata(url)
    except Exception as e:
        print(f"❌ Failed to extract metadata: {e}")
        return

    base_dir = "dataset"
    out_dir = os.path.join(base_dir, video_id)
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write(transcript)

    print("✅ Video accepted into dataset.")
    print(f"📁 Saved to: {out_dir}")


def main():
    print("\n=== TranscriptToCode Dataset Extractor (Persistent Mode) ===")
    print("Paste a YouTube URL to process it.")
    print("Type 'q' or 'quit' to exit.\n")

    while True:
        process_video()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting.\n")
        sys.exit(130)
