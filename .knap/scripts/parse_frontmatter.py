#!/usr/bin/env python3
"""Shared frontmatter parsing for all knap scripts.

Provides ParsedFile class that reads a file once and exposes frontmatter,
body, and error as properties.

Usage:
    from parse_frontmatter import ParsedFile

    parsed = ParsedFile("wiki/transcripts/foo.md")
    if parsed.error:
        # handle error
    fm = parsed.frontmatter
    body = parsed.body
"""

from pathlib import Path

import yaml


class ParsedFile:
    """Read a markdown file once and expose frontmatter, body, and error.

    Attributes:
        frontmatter: Parsed YAML dict from the --- block, or None on error/missing.
        body: Content after the second ---, or empty string if absent.
        error: Human-readable error string, or None if parsing succeeded.
        path: The Path object for the file.
    """

    def __init__(self, filepath: str | Path):
        self.path = Path(filepath)
        self.frontmatter: dict | None = None
        self.body: str = ""
        self.error: str | None = None
        self._parse()

    def _parse(self) -> None:
        """Read file once and populate frontmatter, body, error."""
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.error = f"File not found: {self.path}"
            return
        except OSError as e:
            self.error = f"Cannot read {self.path}: {e}"
            return

        if not content:
            self.error = f"Empty file: {self.path}"
            return

        if not content.startswith("---"):
            self.error = f"Missing frontmatter (---): {self.path}"
            return

        end = content.find("---", 3)
        if end == -1:
            self.error = f"Unclosed frontmatter: {self.path}"
            return

        try:
            data = yaml.safe_load(content[3:end])
        except yaml.YAMLError as e:
            self.error = f"YAML error in {self.path}: {e}"
            return

        if not isinstance(data, dict):
            self.error = f"Frontmatter is not a mapping: {self.path}"
            return

        self.frontmatter = data
        # Body is everything after the second --- (skip leading blank lines)
        self.body = content[end + 3:].lstrip("\n")
