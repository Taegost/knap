#!/usr/bin/env python3
"""Convert markdown frontmatter to yaml.dump() format.

This script transforms markdown file frontmatter from manual string-based
formatting to yaml.dump() output. It processes all .md files in the repo,
preserves data integrity through round-trip consistency, and includes
comprehensive inline documentation for use in both init workflows and
one-time repo fixes.

Purpose:
    The current ingestion script (ingest.py) serializes frontmatter fields
    using manual string formatting (f"  - {item}"). This works for simple
    string lists but produces Python repr for dicts, force-quotes all strings,
    and doesn't follow markdown-first conventions. The Typed Links plan needs
    yaml.dump() for all frontmatter to properly serialize list-of-dict
    structures like `links`, but switching serialization without converting
    existing pages would create formatting inconsistencies between old and new
    pages.

Usage:
    # Convert all .md files in the repo
    python3 .knap/scripts/convert_frontmatter.py

    # Preview changes without writing
    python3 .knap/scripts/convert_frontmatter.py --dry-run

    # Convert only files in a specific directory
    python3 .knap/scripts/convert_frontmatter.py --path wiki/

    # Convert and validate before/after
    python3 .knap/scripts/convert_frontmatter.py --validate

Edge cases:
    - Files without frontmatter (no opening ---) are skipped silently
    - Files with malformed frontmatter log an error and continue
    - Original line endings are preserved throughout
    - Round-trip consistency is verified before replacing the original file
    - The script preserves data types (dates, booleans, strings, etc.)

Integration:
    This script is a prerequisite for the Typed Links plan, which needs
    yaml.dump() to properly serialize list-of-dict structures. It can be
    run independently during init or as a one-time fix.
"""

import argparse
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from parse_frontmatter import ParsedFile


# Directories to skip during file discovery
SKIP_DIRS = {".venv", ".git", "__pycache__", "node_modules", ".claude", ".pytest_cache"}


def discover_md_files(root_dir: str, path_filter: str | None = None) -> list[str]:
    """Find all .md files in the repo, skipping non-content directories.

    Args:
        root_dir: Root directory to scan (typically repo root)
        path_filter: Optional subdirectory to limit scanning to

    Returns:
        Sorted list of absolute paths to .md files
    """
    root = Path(root_dir)
    if path_filter:
        scan_dir = root / path_filter
        if not scan_dir.exists():
            print(f"✗ Path not found: {scan_dir}", file=sys.stderr)
            return []
    else:
        scan_dir = root

    files = set()
    for md_file in scan_dir.rglob("*.md"):
        # Skip files in non-content directories
        parts = md_file.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        files.add(str(md_file.resolve()))

    return sorted(files)


def detect_line_ending(content: str) -> str:
    """Detect the line ending style used in the content.

    Args:
        content: File content to analyze

    Returns:
        '\\r\\n' for Windows-style, '\\n' for Unix-style
    """
    if "\r\n" in content:
        return "\r\n"
    return "\n"




def serialize_frontmatter(data: dict) -> str:
    """Serialize frontmatter dict to yaml.dump() format.

    Uses default_flow_style=False for block-style YAML (one key per line)
    and sort_keys=False to preserve original field order.

    Args:
        data: Frontmatter dict to serialize

    Returns:
        YAML string with trailing newline
    """
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def verify_roundtrip(original_data: dict, new_content: str) -> tuple[bool, str | None]:
    """Verify that converted content produces identical data structure.

    This ensures the conversion didn't alter any data types or values.

    Args:
        original_data: The parsed data from the original file
        new_content: The full converted file content

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if round-trip produces identical data
        - error_message: Description of mismatch, or None if valid
    """
    new_parsed = ParsedFile.from_content(new_content)
    new_data = new_parsed.frontmatter
    error = new_parsed.error
    if error:
        return False, f"Failed to parse converted content: {error}"

    if new_data != original_data:
        return False, f"Data mismatch: {original_data} != {new_data}"

    return True, None


def verify_body_preservation(original_body: str, new_body: str) -> tuple[bool, str | None]:
    """Verify that body content is byte-identical after conversion.

    Args:
        original_body: Body content from original file
        new_body: Body content from converted file

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if bodies are identical
        - error_message: Description of mismatch, or None if valid
    """
    if original_body != new_body:
        # Show first difference for debugging
        for i, (a, b) in enumerate(zip(original_body, new_body)):
            if a != b:
                return False, f"Body differs at position {i}: {repr(a)} vs {repr(b)}"
        return False, f"Body length differs: {len(original_body)} vs {len(new_body)}"

    return True, None


def convert_file(filepath: str, dry_run: bool = False) -> tuple[str, str | None]:
    """Convert a single file's frontmatter to yaml.dump() format.

    Args:
        filepath: Absolute path to the markdown file
        dry_run: If True, preview changes without writing

    Returns:
        Tuple of (status, detail)
        - status: "converted", "skipped", "unchanged", or "failed"
        - detail: Description of what happened, or error message
    """
    # Read original file with preserved line endings
    with open(filepath, newline="") as f:
        content = f.read()

    line_ending = detect_line_ending(content)

    # Parse frontmatter
    parsed = ParsedFile.from_content(content)
    if parsed.error:
        return "skipped", parsed.error
    data = parsed.frontmatter
    body = parsed.body

    # Serialize with yaml.dump()
    new_yaml = serialize_frontmatter(data)

    # Reconstruct file: ---\nyaml_dump\n---body
    # Note: body already starts with line ending after closing ---
    new_content = f"---{line_ending}{new_yaml}---{body}"

    # Verify round-trip consistency
    data_ok, data_err = verify_roundtrip(data, new_content)
    if not data_ok:
        return "failed", f"Round-trip verification failed: {data_err}"

    # Verify body preservation
    body_ok, body_err = verify_body_preservation(body, new_content[new_content.find("---", 3) + 3:])
    if not body_ok:
        return "failed", f"Body preservation failed: {body_err}"

    # Check if content actually changed
    if content == new_content:
        return "unchanged", "Already in yaml.dump() format"

    # Preview or write
    if dry_run:
        return "would_convert", "Preview mode - no changes written"

    # Write to temp file first, then replace original
    try:
        # Preserve original line endings in output
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, newline=line_ending) as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        # Replace original with temp file
        os.replace(tmp_path, filepath)
        return "converted", "Converted to yaml.dump() format"

    except Exception as e:
        # Clean up temp file if it exists
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return "failed", f"Write error: {e}"


# Pattern to extract path from source field: [name](../raw/...)
_SOURCE_RE = re.compile(r'\[([^\]]*)\]\(\.\./(.+)\)')


def migrate_source_field(filepath: str, dry_run: bool = False) -> tuple[str, str | None]:
    """Convert a source frontmatter field to an IngestedFrom link.

    Args:
        filepath: Absolute path to the markdown file
        dry_run: If True, preview changes without writing

    Returns:
        Tuple of (status, detail)
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from add_frontmatter_link import _write_frontmatter_link

    with open(filepath, newline="") as f:
        content = f.read()

    parsed = ParsedFile.from_content(content)
    if parsed.error:
        return "skipped", parsed.error
    data = parsed.frontmatter
    body = parsed.body

    source = data.get("source")
    if source is None:
        # Check if IngestedFrom link exists — write reciprocal if raw file exists
        links = data.get("links", [])
        for entry in links:
            if isinstance(entry, dict) and entry.get("type") == "IngestedFrom":
                target = entry.get("target", "")
                from check_links import _extract_url
                raw_path = _extract_url(target)
                raw_full = Path.cwd() / raw_path
                if raw_full.exists() and raw_full.suffix == ".md":
                    source_rel = str(Path(filepath).resolve().relative_to(Path.cwd()))
                    source_name = Path(filepath).stem
                    _write_frontmatter_link(str(raw_full), f"[{source_name}]({source_rel})", "IngestedTo")
                return "unchanged", "No source field (IngestedFrom exists)"
        return "unchanged", "No source field"

    # Extract raw path from source markdown link
    m = _SOURCE_RE.match(str(source))
    if not m:
        return "failed", f"Malformed source field: {source}"

    name = m.group(1)
    raw_path = m.group(2)  # e.g., "raw/transcripts/file.md"

    if dry_run:
        return "would_migrate", f"source → IngestedFrom [{name}]({raw_path})"

    # Add IngestedFrom link using the sole entry point
    link_modified = _write_frontmatter_link(filepath, f"[{name}]({raw_path})", "IngestedFrom")

    # Re-read the file and remove source field
    source_removed = False
    with open(filepath, newline="") as f:
        content = f.read()
    parsed = ParsedFile.from_content(content)
    if parsed.error:
        return "failed", f"Failed to re-parse after link addition: {parsed.error}"
    data = parsed.frontmatter
    body = parsed.body

    if "source" in data:
        del data["source"]
        source_removed = True
        new_yaml = serialize_frontmatter(data)
        line_ending = detect_line_ending(content)
        new_content = f"---{line_ending}{new_yaml}---{body}"
        with open(filepath, "w", newline=line_ending) as f:
            f.write(new_content)

    # Write reciprocal IngestedTo to the raw file
    raw_full = Path.cwd() / raw_path
    if raw_full.exists() and raw_full.suffix == ".md":
        source_rel = str(Path(filepath).resolve().relative_to(Path.cwd()))
        source_name = Path(filepath).stem
        _write_frontmatter_link(str(raw_full), f"[{source_name}]({source_rel})", "IngestedTo")

    if not link_modified and not source_removed:
        return "unchanged", "Already migrated"

    return "migrated", f"source → IngestedFrom [{name}]({raw_path})"


def run_validate(paths: list[str] | None = None) -> dict[str, set[str]]:
    """Run validate.py and capture results.

    Args:
        paths: Optional list of paths to validate. If None, validates all.

    Returns:
        Dict with 'pass' and 'fail' sets of file paths
    """
    import subprocess

    cmd = [sys.executable, ".knap/scripts/validate.py"]
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse output to identify which files passed/failed
    # validate.py prints filenames for files with issues
    passed = set()
    failed = set()

    # Simple heuristic: files mentioned in output have issues
    # Files not mentioned are clean
    all_files = discover_md_files(".", None)
    mentioned_files = set()

    for line in result.stdout.split("\n"):
        line = line.strip()
        if line.endswith(".md"):
            # This is a filename with issues
            mentioned_files.add(line)

    for f in all_files:
        rel_path = str(Path(f).relative_to(Path.cwd()))
        if rel_path in mentioned_files:
            failed.add(f)
        else:
            passed.add(f)

    return {"pass": passed, "fail": failed}


def main():
    """Main entry point with CLI interface."""
    parser = argparse.ArgumentParser(
        description="Convert markdown frontmatter to yaml.dump() format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 .knap/scripts/convert_frontmatter.py
    python3 .knap/scripts/convert_frontmatter.py --dry-run
    python3 .knap/scripts/convert_frontmatter.py --path wiki/
    python3 .knap/scripts/convert_frontmatter.py --validate
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to files"
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Limit conversion to a specific directory (e.g., wiki/)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validate.py before and after conversion"
    )
    parser.add_argument(
        "--migrate-source",
        action="store_true",
        help="Migrate source frontmatter fields to IngestedFrom links"
    )

    args = parser.parse_args()

    # Get repo root (CWD-relative, per conventions.md)
    repo_root = Path.cwd()

    # Run baseline validation if requested
    baseline_pass = set()
    if args.validate:
        print("── Running baseline validation ──")
        baseline = run_validate()
        baseline_pass = baseline["pass"]
        print(f"   Baseline: {len(baseline_pass)} passing, {len(baseline['fail'])} failing")

    # Discover files
    files = discover_md_files(str(repo_root), args.path)
    if not files:
        print("No .md files found.", file=sys.stderr)
        sys.exit(1)

    if args.migrate_source:
        # Source → IngestedFrom migration mode
        print(f"\n── Migrating source fields in {len(files)} files ──")

        results = {"migrated": 0, "unchanged": 0, "skipped": 0, "failed": 0, "would_migrate": 0}
        errors = []

        for filepath in files:
            try:
                status, detail = migrate_source_field(filepath, dry_run=args.dry_run)
                rel_path = str(Path(filepath).relative_to(repo_root))

                if status == "migrated":
                    print(f"  ✓ {rel_path}: {detail}")
                    results["migrated"] += 1
                elif status == "would_migrate":
                    print(f"  → {rel_path}: {detail}")
                    results["would_migrate"] += 1
                elif status == "unchanged":
                    results["unchanged"] += 1
                elif status == "skipped":
                    results["skipped"] += 1
                elif status == "failed":
                    print(f"  ✗ {rel_path}: {detail}", file=sys.stderr)
                    results["failed"] += 1
                    errors.append((rel_path, detail))

            except Exception as e:
                rel_path = str(Path(filepath).relative_to(repo_root))
                print(f"  ✗ {rel_path}: Unexpected error: {e}", file=sys.stderr)
                results["failed"] += 1
                errors.append((rel_path, str(e)))

        print(f"\n── Summary ──")
        if args.dry_run:
            print(f"  Would migrate: {results['would_migrate']}")
        else:
            print(f"  Migrated: {results['migrated']}")
        print(f"  Unchanged: {results['unchanged']}")
        print(f"  Skipped:   {results['skipped']}")
        print(f"  Failed:    {results['failed']}")

        if results["failed"] > 0:
            print(f"\n✗ {results['failed']} files failed to migrate", file=sys.stderr)
            for filepath, error in errors:
                print(f"  - {filepath}: {error}", file=sys.stderr)
            sys.exit(1)

        if args.dry_run:
            print("\n✓ Dry run complete. Run without --dry-run to apply changes.")
        else:
            print("\n✓ Migration complete.")
        return

    # Standard frontmatter conversion mode
    print(f"\n── Processing {len(files)} files ──")

    # Track results
    results = {"converted": 0, "skipped": 0, "unchanged": 0, "failed": 0, "would_convert": 0}
    errors = []

    # Process each file
    for filepath in files:
        try:
            status, detail = convert_file(filepath, dry_run=args.dry_run)

            # Get relative path for display
            rel_path = str(Path(filepath).relative_to(repo_root))

            if status == "converted":
                print(f"  ✓ {rel_path}: {detail}")
                results["converted"] += 1
            elif status == "would_convert":
                print(f"  → {rel_path}: {detail}")
                results["would_convert"] += 1
            elif status == "unchanged":
                # Silent for unchanged files
                results["unchanged"] += 1
            elif status == "skipped":
                # Silent for skipped files (no frontmatter)
                results["skipped"] += 1
            elif status == "failed":
                print(f"  ✗ {rel_path}: {detail}", file=sys.stderr)
                results["failed"] += 1
                errors.append((rel_path, detail))

        except Exception as e:
            rel_path = str(Path(filepath).relative_to(repo_root))
            print(f"  ✗ {rel_path}: Unexpected error: {e}", file=sys.stderr)
            results["failed"] += 1
            errors.append((rel_path, str(e)))

    # Print summary
    print(f"\n── Summary ──")
    if args.dry_run:
        print(f"  Would convert: {results['would_convert']}")
    else:
        print(f"  Converted: {results['converted']}")
    print(f"  Unchanged: {results['unchanged']}")
    print(f"  Skipped:   {results['skipped']}")
    print(f"  Failed:    {results['failed']}")

    # Run post-validation if requested
    if args.validate:
        print("\n── Running post-validation ──")
        post = run_validate()
        post_pass = post["pass"]

        # Check for regressions
        regressions = baseline_pass - post_pass
        if regressions:
            print(f"\n  ✗ REGRESSION: {len(regressions)} files that were passing now fail:")
            for f in sorted(regressions):
                print(f"    - {str(Path(f).relative_to(repo_root))}")
            sys.exit(1)
        else:
            print(f"  ✓ No regressions detected")
            improvements = post_pass - baseline_pass
            if improvements:
                print(f"  ✓ {len(improvements)} files improved")

    # Exit with error if any files failed
    if results["failed"] > 0:
        print(f"\n✗ {results['failed']} files failed to convert", file=sys.stderr)
        for filepath, error in errors:
            print(f"  - {filepath}: {error}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("\n✓ Dry run complete. Run without --dry-run to apply changes.")
    else:
        print("\n✓ Conversion complete.")


if __name__ == "__main__":
    main()
