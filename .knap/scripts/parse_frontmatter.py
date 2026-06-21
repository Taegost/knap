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

    @classmethod
    def from_content(cls, content: str) -> "ParsedFile":
        """Parse frontmatter from a content string (no file read).

        Unlike the constructor, body is NOT stripped of leading newlines.
        Used by scripts that need raw body preservation (e.g., convert_frontmatter.py).
        """
        instance = cls.__new__(cls)
        instance.path = None
        instance.frontmatter = None
        instance.body = ""
        instance.error = None
        instance._parse_content(content, strip_body=False)
        return instance

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

        self._parse_content(content, strip_body=True)

    def _parse_content(self, content: str, strip_body: bool = True) -> None:
        """Parse frontmatter from a content string.

        Args:
            content: Full file content to parse.
            strip_body: If True, strip leading newlines from body (file-based
                parsing). If False, preserve raw body (content-string parsing).
        """
        if not content:
            self.error = "Empty file"
            return

        if not content.startswith("---"):
            self.error = "Missing frontmatter (---)"
            return

        end = content.find("---", 3)
        if end == -1:
            self.error = "Unclosed frontmatter"
            return

        # Extract body before YAML parsing — body is available even if YAML fails
        raw_body = content[end + 3:]
        self.body = raw_body.lstrip("\n") if strip_body else raw_body

        try:
            data = yaml.safe_load(content[3:end])
        except yaml.YAMLError as e:
            self.error = f"YAML error: {e}"
            return

        if not isinstance(data, dict):
            self.error = "Frontmatter is not a mapping"
            return

        self.frontmatter = data
