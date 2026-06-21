#!/usr/bin/env python3
"""Link validation helper.

Provides check_link() for verifying whether a link target exists.
Provides resolve_wikilink() and extract_wikilinks() for wikilink support.
Used by lint.py and add_frontmatter_link.py.

Usage:
    from check_links import check_link, resolve_wikilink, extract_wikilinks
    result = check_link("[Page](wiki/transcripts/foo.md)")
    print(result.exists, result.is_external)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class LinkResult:
    """Result of checking a link target."""
    exists: bool
    is_external: bool


# Pattern to extract URL from markdown link format [name](url)
_MD_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

# Pattern to match wikilinks [[...]] (with optional pipe)
_WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

# URI schemes that indicate external resources
_EXTERNAL_SCHEMES = {"http", "https", "ftp", "ftps", "smb", "nfs"}


def _extract_url(link: str) -> str:
    """Extract the URL from markdown link format, or return the string as-is."""
    m = _MD_LINK_RE.match(link)
    if m:
        return m.group(2)
    return link


def check_link(link: str, relative_to: str | None = None) -> LinkResult:
    """Check whether a link target exists.

    Args:
        link: A markdown link [name](url) or plain path/URI.
        relative_to: If None, resolve repo-root-relative.
                     If a file path, resolve relative to that file's directory.

    Returns:
        LinkResult with exists and is_external booleans.
    """
    url = _extract_url(link)

    # Check for external URI scheme
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme.lower() in _EXTERNAL_SCHEMES:
        # External URL — we can't reliably check existence
        # Return exists=True optimistically (lint.py treats failures as warnings)
        return LinkResult(exists=True, is_external=True)

    # Resolve the path
    if relative_to is not None:
        base_dir = Path(relative_to).parent
        target = (base_dir / url).resolve()
    else:
        target = Path.cwd() / url

    return LinkResult(exists=target.exists(), is_external=False)


def resolve_wikilink(wikilink: str, source_file: str) -> Path | None:
    """Resolve a wikilink to an absolute path.

    Wikilinks without pipe: exact filename match with .md extension,
    searching within the same category folder as source_file.
    Wikilinks with pipe: extract path portion and resolve as standard link.

    Args:
        wikilink: The content inside [[...]] (e.g. "Birthday Party" or "path|display").
        source_file: The file containing the wikilink (repo-root-relative path).

    Returns:
        Path to the resolved file, or None if not found.
    """
    if "|" in wikilink:
        # Standard link: extract path portion
        path_part = wikilink.split("|", 1)[0].strip()
        if not path_part:
            return None
        target = Path.cwd() / path_part
        return target if target.exists() else None

    # No pipe: exact filename match with .md in same category folder
    source_path = Path(source_file)
    category_dir = source_path.parent
    target = Path.cwd() / category_dir / f"{wikilink}.md"
    return target if target.exists() else None


def extract_wikilinks(body: str) -> list[str]:
    """Extract all wikilinks from body text.

    Returns list of wikilink contents (inside [[...]]).
    Skips empty wikilinks [[]].
    """
    return [m for m in _WIKILINK_RE.findall(body) if m.strip()]
