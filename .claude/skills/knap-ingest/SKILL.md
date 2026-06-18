---
name: knap-ingest
description: "Ingest content into the knowledge base. Handles YouTube transcripts, URLs, and existing raw files."
user_invocable: true
---

# Ingest Skill

Scaffolds and fills in content from external sources. Ingest means the full pipeline: fetch → validate → scaffold → write Summary and Analysis → lint. A file is not ingested until the judgment sections are filled.

## Usage

```
/knap-ingest <url or path>
/knap-ingest https://www.youtube.com/watch?v=...
/knap-ingest raw/transcripts/existing-file.md
```

## Process

### 1. Determine source type

- **YouTube URL** → fetch transcript
- **Web URL** → fetch and extract content
- **Existing raw file** → skip to step 3

### 2. Fetch content

**For YouTube:**
```bash
source .knap/.venv/bin/activate
python .knap/scripts/fetch_youtube_transcript.py "<url>" --out-dir raw/transcripts/
```

The script outputs the file path. Note it for step 3.

**For web URLs:**
Use WebFetch to get the content. Save to `raw/{category}/` with proper frontmatter.

### 3. Validate frontmatter

```bash
python .knap/scripts/validate.py <raw-file>
```

Fix any errors before proceeding. The raw file must have:
- `title` — content title
- `source_url` — where it came from
- `date_farmed` — today's date (YYYY-MM-DD)
- `category` — must match a category in `.knap/schema/categories.yaml`
- Category-specific required fields

### 4. Ingest into wiki

```bash
python .knap/scripts/ingest.py <raw-file>
```

This creates the wiki stub, updates the index, and appends to the log.

### 5. Write Summary, Analysis, and Prompts

Read the raw source file and the generated wiki stub. Fill in:
- **Summary** — 2-4 sentence synthesis of the content
- **Analysis** — category-specific judgment section (see `.knap/schema/categories.yaml` for the label)
- **Prompts** (for transcripts/videos) — extract all verbatim prompts mentioned or shown on screen. Use blockquotes (`>`) for exact text. Add `<!-- TODO -->` markers for prompts shown on screen but not captured in the transcript. These prompts are the most reusable artifacts — they should be copy-pasteable.

### 6. Lint

```bash
python .knap/scripts/lint.py
```

Must return 0 issues.

## Adding New Categories

To ingest content that doesn't fit existing categories:
1. Edit `.knap/schema/categories.yaml` — add the new category with required fields
2. Run the ingest pipeline
