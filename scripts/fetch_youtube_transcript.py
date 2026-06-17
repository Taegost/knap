#!/usr/bin/env python3
"""
Fetch YouTube video title and transcript by URL.
No API key required — uses youtube-transcript-api for captions
and YouTube oEmbed for the title.

Usage:
    python fetch_youtube_transcript.py <url> [--output raw|clean|text] [--language en]

Examples:
    python fetch_youtube_transcript.py "https://www.youtube.com/watch?v=4pm5C3erORo"
    python fetch_youtube_transcript.py "https://youtu.be/S8eX0MxfnB4" --output raw
    python fetch_youtube_transcript.py "https://www.youtube.com/watch?v=..." --language en

Output modes:
    raw     - Transcript entries with timestamps (default)
    clean   - Transcript text only, timestamps stripped
    text    - Clean text wrapped in the raw-notes header format used by knowledge/raw/
"""

import argparse
import os
import re
import sys
from datetime import date
from urllib.parse import urlparse, parse_qs

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    # youtu.be/VIDEO_ID
    if "youtu.be" in url:
        path = urlparse(url).path.strip("/")
        if path:
            return path

    # youtube.com/watch?v=VIDEO_ID
    # youtube.com/embed/VIDEO_ID
    # youtube.com/v/VIDEO_ID
    # youtube.com/shorts/VIDEO_ID
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        # /watch?v=...
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        # /embed/VIDEO_ID or /v/VIDEO_ID or /shorts/VIDEO_ID
        match = re.match(r"/(?:embed|v|shorts)/([a-zA-Z0-9_-]{11})", parsed.path)
        if match:
            return match.group(1)

    # Fallback: try to find an 11-char ID anywhere in the URL
    match = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a URL-friendly filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:max_len].rstrip("-")


def get_video_info(video_id: str) -> tuple[str, str]:
    """Fetch title and channel name via YouTube oEmbed (no API key needed)."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    resp = requests.get(oembed_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["title"], data.get("author_name", "YouTube")


def get_transcript_entries(video_id: str, language: str) -> list:
    """Fetch transcript entries from youtube-transcript-api."""
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=[language])
    return list(fetched)


def format_raw(entries: list) -> str:
    """Format entries with timestamps, similar to raw API output."""
    lines = []
    for entry in entries:
        seconds = int(entry.start)
        minutes = seconds // 60
        secs = seconds % 60
        timestamp = f"{minutes}:{secs:02d}"
        lines.append(f"[{timestamp}] {entry.text}")
    return "\n".join(lines)


def format_clean(entries: list) -> str:
    """Format entries as continuous text, no timestamps."""
    return " ".join(entry.text for entry in entries)


def format_text(title: str, channel: str, url: str, entries: list) -> str:
    """Format as knowledge/raw/ header + clean transcript."""
    text = format_clean(entries)
    today = date.today().isoformat()
    header = f"""# Raw Transcript: "{title}"

**Source:** {channel} YouTube video
**URL:** {url}
**Ingested:** {today}
**Format:** Transcript (auto-generated, lightly cleaned)

---

## Full Transcript

"""
    return header + text


def main():
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video title and transcript."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--output", "-o",
        choices=["raw", "clean", "text"],
        default="raw",
        help="Output mode: raw (timestamps), clean (text only), text (raw-notes header + clean text)",
    )
    parser.add_argument(
        "--language", "-l",
        default="en",
        help="Transcript language code (default: en)",
    )
    parser.add_argument(
        "--out-dir", "-d",
        default=None,
        help="Write output to a file in this directory instead of stdout. "
             "Filename is derived from the title: YYYY-MM-DD-slug.transcript.md. "
             "Prints the file path to stdout.",
    )
    args = parser.parse_args()

    try:
        video_id = extract_video_id(args.url)
        print(f"Video ID: {video_id}", file=sys.stderr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        title, channel = get_video_info(video_id)
        print(f"Title: {title}", file=sys.stderr)
        print(f"Channel: {channel}", file=sys.stderr)
    except Exception as e:
        print(f"Error fetching video info: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = get_transcript_entries(video_id, args.language)
        print(f"Transcript: {len(entries)} entries", file=sys.stderr)
    except NoTranscriptFound:
        print(
            f"Error: No transcript found for language '{args.language}'. "
            f"Try --language with a different code.",
            file=sys.stderr,
        )
        sys.exit(1)
    except TranscriptsDisabled:
        print("Error: Transcripts are disabled for this video.", file=sys.stderr)
        sys.exit(1)
    except VideoUnavailable:
        print("Error: Video is unavailable.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output == "raw":
        output = format_raw(entries)
    elif args.output == "clean":
        output = format_clean(entries)
    elif args.output == "text":
        output = format_text(title, channel, args.url, entries)

    if args.out_dir:
        slug = slugify(title)
        filename = f"{date.today().isoformat()}-{slug}.transcript.md"
        filepath = os.path.join(args.out_dir, filename)
        os.makedirs(args.out_dir, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(output)
            f.write("\n")
        print(filepath)
    else:
        print(output)


if __name__ == "__main__":
    main()
