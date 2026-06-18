#!/usr/bin/env python3
"""Lint planning documents for internal consistency.

Checks:
  S1. Requirement ID coverage — all defined IDs referenced in units
  S2. Unit requirement references — all referenced IDs exist in Requirements
  S3. Unit dependency references — all U-IDs exist
  S4. File path cross-reference — Files paths mentioned in Approach
  S5. Deferred item resolution — referenced files exist
  S6. Key term drift — Goal terms appear in Approach
  S7. Cross-unit terminology — substring overlaps between units

Usage:
    python3 .knap/scripts/plan_lint.py <plan-file>
"""

import re
import sys
from pathlib import Path


# --- Parsing helpers ---

def parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter as a dict."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm_text = content[3:end].strip()
    # Simple key: value parsing (no full YAML dependency needed)
    result = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"')
    return result


def parse_sections(content: str) -> dict[str, str]:
    """Split document into sections by ## and ### headings."""
    sections = {}
    current_heading = None
    current_body = []

    for line in content.split("\n"):
        # Match ## or ### headings
        m = re.match(r'^(#{2,3})\s+(.+)$', line)
        if m:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_body)
            current_heading = m.group(2).strip()
            current_body = []
        elif current_heading is not None:
            current_body.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_body)

    return sections


def parse_requirements_section(text: str) -> list[str]:
    """Extract requirement IDs from Requirements section (definition pattern: 'ID. text')."""
    ids = []
    for m in re.finditer(r'(?:^|\s)([A-Z]+\d+)\.\s', text, re.MULTILINE):
        ids.append(m.group(1))
    return ids


def parse_unit_subsections(text: str) -> dict[str, str]:
    """Parse a unit's content into named subsections (Goal, Requirements, etc.)."""
    subsections = {}
    current_key = None
    current_lines = []

    for line in text.split("\n"):
        # Match bold subsection headers like **Goal:** or **Requirements:**
        # Handle optional leading "- " or "  - "
        m = re.match(r'^[\s-]*\*\*(\w[\w\s]*?):\*\*\s*(.*)$', line)
        if m:
            if current_key is not None:
                subsections[current_key] = "\n".join(current_lines).strip()
            current_key = m.group(1).strip()
            current_lines = [m.group(2)]
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        subsections[current_key] = "\n".join(current_lines).strip()

    return subsections


def extract_requirement_refs(text: str) -> list[str]:
    """Extract requirement IDs from a reference line (comma-separated, no periods)."""
    return re.findall(r'[A-Z]+\d+', text)


def extract_uid_refs(text: str) -> list[str]:
    """Extract U-ID references from a Dependencies line."""
    return re.findall(r'U\d+', text)


def extract_file_paths(text: str) -> list[str]:
    """Extract file paths from a Files section."""
    paths = []
    for m in re.finditer(r'`([^`]+\.\w+)`', text):
        paths.append(m.group(1))
    return paths


def extract_significant_terms(text: str) -> list[str]:
    """Extract requirement IDs, quoted/backticked terms, and 3+ word phrases from text."""
    terms = []
    # Requirement IDs
    terms.extend(re.findall(r'[A-Z]+\d+', text))

    # Extract quoted terms and backtick-wrapped terms as significant
    terms.extend(re.findall(r'"([^"]+)"', text))
    terms.extend(re.findall(r'`([^`]+)`', text))

    # Extract 3+ word phrases (as specified in plan)
    words = re.findall(r'[a-z][a-z0-9-]{2,}', text.lower())
    stop_words = {"implement", "create", "add", "update", "fix", "the", "for", "and", "with", "from", "that", "this", "knap", "scripts", "src", "lib", "new", "old", "use", "run", "get", "set", "put"}
    for length in [3]:
        for i in range(len(words) - length + 1):
            phrase_words = words[i:i + length]
            # Skip phrases that start with stop words
            if phrase_words[0] in stop_words:
                continue
            # Skip phrases that are mostly stop words
            non_stop = [w for w in phrase_words if w not in stop_words]
            if len(non_stop) < 2:
                continue
            phrase = " ".join(phrase_words)
            if len(phrase) > 8:  # Skip very short phrases
                terms.append(phrase)
    return terms


def extract_multi_word_phrases(text: str, min_words: int = 2, max_words: int = 4) -> list[str]:
    """Extract multi-word phrases of specified length range."""
    phrases = []
    # Split on whitespace and punctuation, keeping only meaningful words
    words = re.findall(r'[a-z][a-z0-9-]{2,}', text.lower())
    # Filter out common path components and filler words
    stop_words = {"knap", "scripts", "src", "lib", "test", "docs", "the", "for", "and", "with", "from", "that", "this"}
    for length in range(min_words, max_words + 1):
        for i in range(len(words) - length + 1):
            phrase_words = words[i:i + length]
            # Skip phrases that are mostly stop words
            non_stop = [w for w in phrase_words if w not in stop_words]
            if len(non_stop) < 2:
                continue
            phrase = " ".join(phrase_words)
            if len(phrase) > 10:  # Skip short phrases
                phrases.append(phrase)
    return phrases


# --- Check functions ---

def check_s1_requirement_coverage(defined_ids: list[str], units: dict[str, dict]) -> list[str]:
    """S1: Verify all defined requirement IDs are referenced in at least one unit."""
    findings = []
    referenced = set()

    for uid, unit in units.items():
        req_line = unit.get("Requirements", "")
        refs = extract_requirement_refs(req_line)
        referenced.update(refs)

    for req_id in defined_ids:
        if req_id not in referenced:
            findings.append(f"S1: Requirement {req_id} defined but not referenced in any unit")

    return findings


def check_s2_dangling_requirement_refs(defined_ids: list[str], units: dict[str, dict]) -> list[str]:
    """S2: Verify every referenced requirement ID exists in Requirements section."""
    findings = []
    defined_set = set(defined_ids)

    for uid, unit in units.items():
        req_line = unit.get("Requirements", "")
        refs = extract_requirement_refs(req_line)
        for ref in refs:
            if ref not in defined_set:
                findings.append(f"S2: {uid} references undefined requirement {ref}")

    return findings


def check_s3_dangling_dependencies(units: dict[str, dict]) -> list[str]:
    """S3: Verify every dependency U-ID exists."""
    findings = []
    all_uids = set(units.keys())

    for uid, unit in units.items():
        deps_line = unit.get("Dependencies", "")
        if not deps_line:
            continue
        refs = extract_uid_refs(deps_line)
        for ref in refs:
            if ref not in all_uids:
                findings.append(f"S3: {uid} depends on undefined unit {ref}")

    return findings


def check_s4_file_cross_reference(units: dict[str, dict]) -> list[str]:
    """S4: Verify file paths in Files are mentioned in Approach."""
    findings = []

    for uid, unit in units.items():
        files_text = unit.get("Files", "")
        approach_text = unit.get("Approach", "")

        if not files_text or not approach_text:
            continue

        file_paths = extract_file_paths(files_text)
        approach_lower = approach_text.lower()

        for fpath in file_paths:
            fname = Path(fpath).name
            # Check if filename or full path appears in approach
            if fname.lower() not in approach_lower and fpath.lower() not in approach_lower:
                # Check for "no change needed" or "unchanged" patterns near the filename
                # Only suppress if the pattern appears in the same line as the filename reference
                file_line_pattern = re.compile(
                    rf'{re.escape(fname)}.*?(no change|unchanged|existing)|'
                    rf'(no change|unchanged|existing).*?{re.escape(fname)}',
                    re.IGNORECASE
                )
                if not file_line_pattern.search(approach_text):
                    findings.append(f"S4: {uid} lists {fpath} in Files but not mentioned in Approach")

    return findings


def check_s5_deferred_items(sections: dict[str, str], plan_dir: Path = None) -> list[str]:
    """S5: Verify referenced files in 'Deferred for later' exist."""
    findings = []

    # Find deferred section
    deferred_text = ""
    for key in sections:
        if "deferred" in key.lower() or "deferred for later" in key.lower():
            deferred_text = sections[key]
            break

    if not deferred_text:
        return findings

    # Extract file references (paths ending in .md)
    for m in re.finditer(r'`([^`]+\.md)`', deferred_text):
        ref_path = m.group(1)
        # Check relative to plan directory if provided, otherwise use CWD
        if plan_dir:
            full_path = plan_dir / ref_path
        else:
            full_path = Path(ref_path)
        if not full_path.exists():
            findings.append(f"S5: Deferred item references {ref_path} — file not found")

    return findings


def check_s6_key_term_drift(units: dict[str, dict]) -> list[str]:
    """S6: Check if Goal terms appear in Approach."""
    findings = []

    for uid, unit in units.items():
        goal_text = unit.get("Goal", "")
        approach_text = unit.get("Approach", "")

        if not goal_text or not approach_text:
            continue

        goal_terms = extract_significant_terms(goal_text)
        approach_lower = approach_text.lower()

        for term in goal_terms:
            if term.lower() not in approach_lower:
                findings.append(f"S6: {uid} Goal term '{term}' not found in Approach")

    return findings


def check_s7_cross_unit_terminology(units: dict[str, dict]) -> list[str]:
    """S7: Flag substring overlaps between phrases in different units."""
    findings = []

    # Collect phrases per unit
    unit_phrases = {}
    for uid, unit in units.items():
        all_text = " ".join([
            unit.get("Goal", ""),
            unit.get("Files", ""),
            unit.get("Approach", "")
        ])
        unit_phrases[uid] = extract_multi_word_phrases(all_text)

    # Compare across units
    all_uids = list(unit_phrases.keys())
    seen_overlaps = set()  # Track (uid1, uid2, base_phrase) to avoid duplicates

    for i, uid1 in enumerate(all_uids):
        for uid2 in all_uids[i + 1:]:
            # Collect all phrases from both units
            phrases1 = set(unit_phrases[uid1])
            phrases2 = set(unit_phrases[uid2])

            # Find the longest common substring for each pair
            for p1 in phrases1:
                for p2 in phrases2:
                    if p1 == p2:
                        continue

                    # Check if one is a substring of the other
                    if p1 in p2 or p2 in p1:
                        longer = p1 if len(p1) > len(p2) else p2
                        shorter = p1 if len(p1) <= len(p2) else p2

                        # Use the shorter phrase as the key to avoid duplicate overlaps
                        overlap_key = (uid1, uid2, shorter)
                        if overlap_key not in seen_overlaps:
                            seen_overlaps.add(overlap_key)
                            findings.append(
                                f"S7: Terminology drift — '{shorter}' vs '{longer}' "
                                f"(between {uid1} and {uid2})"
                            )

    return findings


# --- Main ---

def parse_plan(filepath: str) -> tuple[dict, list[str], dict[str, dict]]:
    """Parse a plan document and return (frontmatter, defined_req_ids, units)."""
    content = Path(filepath).read_text()

    frontmatter = parse_frontmatter(content)
    if not frontmatter:
        print(f"Error: {filepath} has no parseable frontmatter", file=sys.stderr)
        sys.exit(1)

    sections = parse_sections(content)

    # Find Requirements section
    defined_ids = []
    for key in sections:
        if key.lower().startswith("requirements"):
            defined_ids.extend(parse_requirements_section(sections[key]))

    # Find Implementation Units
    units = {}
    for key in sections:
        # Match unit headings like "U1. Plan parser script" or "### U1. Create context layer"
        m = re.match(r'^(U\d+)\.\s+(.+)$', key)
        if m:
            uid = m.group(1)
            subsections = parse_unit_subsections(sections[key])
            units[uid] = subsections

    if not units:
        print(f"Error: {filepath} has no Implementation Units section", file=sys.stderr)
        sys.exit(1)

    return frontmatter, defined_ids, units


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 .knap/scripts/plan_lint.py <plan-file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)

    plan_path = Path(filepath)
    plan_dir = plan_path.parent
    frontmatter, defined_ids, units = parse_plan(filepath)
    sections = parse_sections(plan_path.read_text())

    all_findings = []

    # Run checks
    all_findings.extend(check_s1_requirement_coverage(defined_ids, units))
    all_findings.extend(check_s2_dangling_requirement_refs(defined_ids, units))
    all_findings.extend(check_s3_dangling_dependencies(units))
    all_findings.extend(check_s4_file_cross_reference(units))
    all_findings.extend(check_s5_deferred_items(sections, plan_dir))
    all_findings.extend(check_s6_key_term_drift(units))
    all_findings.extend(check_s7_cross_unit_terminology(units))

    # Output
    if not all_findings:
        print(f"✓ {filepath} — no issues found")
        sys.exit(0)

    print(f"\n## Plan Lint: {filepath}")
    print(f"   {len(all_findings)} finding(s)\n")

    # Group by check type
    by_check = {}
    for f in all_findings:
        check_id = f.split(":")[0]
        by_check.setdefault(check_id, []).append(f)

    for check_id in sorted(by_check.keys()):
        print(f"### {check_id}")
        for finding in by_check[check_id]:
            print(f"  - {finding}")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
