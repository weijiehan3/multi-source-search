# Script Usage Guide

Detailed parameters and examples for all scripts in the Portable Search Suite.

---

## search.py — Multi-Source Search

### Synopsis

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py [QUERY] [OPTIONS]
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `QUERY` | Search query (positional) | — |
| `--queries` | Multiple sub-queries in parallel | — |
| `--mode` | `fast` / `deep` / `answer` | `deep` |
| `--intent` | Intent type (affects scoring weights) | none |
| `--freshness` | `pd` (24h) / `pw` (week) / `pm` (month) / `py` (year) | none |
| `--domain-boost` | Comma-separated domains to boost (+0.2 authority) | none |
| `--num` | Results per source per query | 5 |
| `--source` | Restrict to: `exa`, `tavily`, `grok` (comma-separated) | all |
| `--extract-refs` | Extract references from result URLs after search | off |
| `--extract-refs-urls` | Skip search, extract refs from URLs directly | — |

### Mode x Source Matrix

| Mode | Exa | Tavily | Grok | Use Case |
|------|-----|--------|------|----------|
| `fast` | Yes | — | fallback | Quick source lookup |
| `deep` | Yes | Yes | Yes | Full research |
| `answer` | — | Yes | — | Factual Q&A |

### Recommended Patterns

```bash
# Evidence-first: official docs and canonical sources
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py "OpenClaw API docs" \
  --mode fast --intent resource --num 5

# Direction-first: what's happening now
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py "OpenClaw latest changes" \
  --mode deep --intent status --freshness pw --num 5

# Docs-compare: official vs community
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py \
  --queries "OpenClaw official streaming docs" "OpenClaw streaming community discussion" \
  --mode deep --intent comparison --num 5

# Multi-query comparison
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py \
  --queries "Bun vs Deno" "Bun advantages" "Deno advantages" \
  --mode deep --intent comparison

# Single source testing
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py "AI news" \
  --mode deep --source grok --num 3

# Search + thread pulling
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py "OpenClaw config bug" \
  --mode deep --intent status --extract-refs

# Direct reference extraction (skip search)
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py --extract-refs-urls \
  "https://github.com/owner/repo/issues/123"
```

### Output Format (JSON to stdout)

```json
{
  "mode": "deep",
  "intent": "status",
  "queries": ["query1"],
  "count": 5,
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "published_date": "...",
      "source": "exa|tavily|grok",
      "score": 0.85,
      "meta": {}
    }
  ],
  "research": []
}
```

---

## fetch_thread.py — Thread Deep-Fetch

### Synopsis

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_thread.py URL [OPTIONS]
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `URL` | Thread URL (positional) | — |
| `--format` | `json` / `markdown` | `json` |
| `--extract-refs-only` | Only extract references | off |

### Platform Support

| Platform | Extracts |
|----------|----------|
| GitHub Issue/PR | Body, comments, timeline, cross-refs, commits |
| Hacker News | Post, comments tree |
| Reddit | Post, comments |
| V2EX | Post, replies |
| Generic web | Text, internal/external links |

### Examples

```bash
# GitHub issue full context
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_thread.py \
  "https://github.com/owner/repo/issues/123"

# Readable markdown output
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_thread.py \
  "https://github.com/owner/repo/pull/456" --format markdown

# Quick reference graph only
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_thread.py \
  "https://github.com/owner/repo/issues/123" --extract-refs-only
```

### Dependency Note

Requires `trafilatura`, `beautifulsoup4`, `lxml` for generic web extraction.
GitHub/HN/Reddit extraction only needs `requests`.

---

## content_extract.py — URL to Markdown

### Synopsis

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/content_extract.py --url URL
```

### Decision Tree

1. URL on anti-crawler whitelist (WeChat, Zhihu) -> MinerU directly
2. Otherwise -> lightweight extraction
3. Lightweight fails (403, empty, anti-bot) -> fallback to MinerU

### Output

```json
{
  "ok": true,
  "source_url": "...",
  "engine": "web_fetch|mineru",
  "markdown": "...",
  "sources": ["original URL", "local path"]
}
```

---

## mineru_parse_documents.py — MinerU API

### Synopsis

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/mineru_parse_documents.py \
  --file-sources URL [OPTIONS]
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--file-sources` | URL(s), comma/newline separated | — |
| `--model-version` | `pipeline` / `vlm` / `MinerU-HTML` | auto |
| `--emit-markdown` | Include markdown inline in JSON | off |
| `--max-chars` | Max chars for inline markdown | 20000 |
| `--language` | OCR language | `ch` |
| `--timeout` | Max wait seconds | 600 |

### Model Selection

| Content | Model |
|---------|-------|
| PDF, DOC, PPT, images | `pipeline` |
| Complex layouts | `vlm` |
| HTML (WeChat, Zhihu) | `MinerU-HTML` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: trafilatura` | Missing dep | `pip install trafilatura beautifulsoup4 lxml` |
| Exa returns empty | Bad API key | Check `EXA_API_KEY` |
| Grok timeout | Local proxy down | Start grok2api or remove Grok config |
| MinerU fails | Token expired | Refresh at mineru.net/apiManage |
| All scores 0 | No `--intent` | Add `--intent <type>` |
| Grok 429 rate limit | grok2api token exhausted | Wait for cooldown (Basic: 20h, Super: 2h) |
