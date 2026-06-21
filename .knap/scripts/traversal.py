#!/usr/bin/env python3
"""Shared file traversal for knap scripts.

Scans working and system folders, respecting folder classification from
.knap/schema/folders.yaml.

Usage:
    from traversal import traverse_files

    all_files = traverse_files()
    indexed_files = traverse_files(indexed_only=True)
"""

from pathlib import Path

from load_folders import get_working_folders, get_system_folders, get_excluded_folders


def _is_excluded(path: Path, excluded: list[Path]) -> bool:
    """Check if a path falls under any excluded folder."""
    parts = path.parts
    for exc in excluded:
        exc_parts = exc.parts
        # Check if any prefix of the path matches the excluded folder
        for i in range(len(parts) - len(exc_parts) + 1):
            if parts[i : i + len(exc_parts)] == exc_parts:
                return True
    return False


def _has_index(folder: Path, folder_type: str) -> bool:
    """Check if a folder has an associated index file."""
    if folder_type == "system":
        return (folder / "ROUTER.md").exists()
    # working folders use index.md
    return (folder / "index.md").exists()


def traverse_files(indexed_only: bool = False) -> list[Path]:
    """Traverse all files in working and system folders.

    Args:
        indexed_only: If True, only return files from folders that have
            an associated index (index.md for working, ROUTER.md for system).

    Returns:
        Sorted list of Path objects (repo-root-relative).
    """
    working = get_working_folders()
    system = get_system_folders()
    excluded = get_excluded_folders()

    result: list[Path] = []

    for folder_list, folder_type in [(working, "working"), (system, "system")]:
        for folder in folder_list:
            if not folder.exists() or not folder.is_dir():
                continue

            if indexed_only and not _has_index(folder, folder_type):
                continue

            for p in sorted(folder.rglob("*")):
                if not p.is_file():
                    continue
                rel = p.relative_to(Path("."))
                if _is_excluded(rel, excluded):
                    continue
                result.append(rel)

    return sorted(result)
