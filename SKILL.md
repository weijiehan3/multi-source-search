---
name: multi-source-search
description: >
  Use when the user needs web search, information retrieval, thread deep-fetching,
  or URL content extraction — especially multi-source research, GitHub/forum thread
  tracking, comparison analysis, or anti-crawler page parsing. Do NOT use for simple
  single-fact lookups that the host's built-in web search can answer directly.
---

# Multi-Source Search

Agent-neutral, multi-source search and content extraction skill.
Combine host web search + Exa + Tavily + Grok for high-coverage retrieval,
thread pulling for deep context, and MinerU for anti-crawler page parsing.

## When to Use This Skill

| Scenario | Use This Skill | Use Host Built-in Search |
|----------|---------------|-------------------------|
| Multi-source research / deep investigation | Yes | No |
| Comparison analysis (X vs Y) | Yes | As supplement |
| GitHub issue / PR / forum thread deep-fetch | Yes | No |
| Latest news or status tracking | Yes | Either |
| Anti-crawler page extraction (WeChat, Zhihu) | Yes | No |
| Quick single-fact lookup ("What is X") | No | Yes |
| Simple URL fetch (no anti-crawler) | No | Yes (web_fetch) |

**Decision rule**: If a single host search call can answer, use host search.
If multi-source coverage, scoring, thread-pulling, or anti-crawler extraction is needed, use this skill.

## Execution Protocol

### Step 1: Classify Intent

Before searching, classify the user query into one of seven intent types.
Do not ask the user which mode to use — infer from the query.

| Intent | Signal Words | Mode | Freshness |
|--------|-------------|------|-----------|
| **Factual** | "what is", "define", "meaning" | answer | — |
| **Status** | "latest", "update", "progress" | deep | pw/pm |
| **Comparison** | "vs", "difference", "or" | deep | py |
| **Tutorial** | "how to", "guide", "tutorial" | answer | py |
| **Exploratory** | "deep dive", "ecosystem", "about" | deep | — |
| **News** | "news", "this week", "announcement" | deep | pd/pw |
| **Resource** | "official site", "GitHub", "docs" | fast | — |

Full classification guide with scoring weights: see [references/intent-guide.md](references/intent-guide.md)

### Step 2: Expand Queries

- Expand technical synonyms automatically (k8s->Kubernetes, JS->JavaScript, etc.)
- Chinese technical queries: generate English variants in parallel
- Comparison intent: split into 3 sub-queries (A vs B, A advantages, B advantages)
- Status/News intent: inject current year into query

### Step 3: Multi-Source Retrieval

Each source has a distinct role — they complement, not duplicate:

| Source | Positioning | Best For |
|--------|------------|---------|
| **Host search** | General web recall | First-layer broad coverage |
| **Exa** | Source-first (evidence) | Official docs, API refs, canonical pages, low-noise results, text extraction |
| **Tavily** | General + AI answer | Balanced coverage, factual Q&A with citations |
| **Grok** | Freshness-first (direction) | Real-time info, community chatter, breaking news, multi-source synthesis |

> **Exa finds evidence. Grok finds direction. Tavily fills the middle. Host search provides breadth.**

Route by intent:

| Intent | Primary Sources | Rationale |
|--------|----------------|-----------|
| Factual / Tutorial | Tavily (answer mode) + Exa | Need authoritative answers + canonical sources |
| Status / News | Grok + Tavily + host search | Need freshness and real-time awareness |
| Comparison | All sources (deep mode) | Need breadth + multiple perspectives |
| Resource | Exa (fast mode) | Need precise source-first retrieval |
| Exploratory | All sources + research-light | Need maximum coverage |

When the user wants to **compare official claims vs community discussion** (docs-compare pattern),
run Exa for official sources and Grok for community/social discussion, then synthesize both perspectives.

Run host web search (agent-layer) in parallel with the search script:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py \
  --queries "sub-query-1" "sub-query-2" \
  --mode deep --intent status --freshness pw --num 5
```

Source participation by mode:

| Mode | Exa | Tavily | Grok | When to Use |
|------|-----|--------|------|------------|
| fast | Yes | — | fallback | Resource lookup, quick source finding |
| deep | Yes | Yes | Yes | Research, comparison, status, exploratory |
| answer | — | Yes | — | Factual Q&A, tutorials |

### Step 4: Thread Pulling (Conditional)

When results contain GitHub issue/PR links and intent is `status` or `exploratory`,
deepen context with thread fetching:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/fetch_thread.py \
  "https://github.com/owner/repo/issues/123" --format json
```

Supported platforms: GitHub Issue/PR, Hacker News, Reddit, V2EX, generic web pages.

### Step 5: Content Extraction (On Demand)

When user provides a URL to extract, or search results need full-text:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/content_extract.py --url "<URL>"
```

For anti-crawler sites (WeChat, Zhihu), automatic fallback to MinerU:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/mineru_parse_documents.py \
  --file-sources "<URL>" --model-version MinerU-HTML \
  --emit-markdown --max-chars 20000
```

## Output Contract

### Synthesis Rules

- **Answer first, then cite sources** — do not start with "I searched..."
- **Group by topic, not by source** — never "Exa results: ... Tavily results: ..."
- **Flag conflicting information** explicitly when sources disagree
- **Confidence expression**:
  - Multi-source agreement + fresh -> state directly
  - Single source or dated -> "According to [source], ..."
  - Conflicting -> "Different views exist: A says ..., B says ..."

### Result Format

For small result sets (<=5): list each with source tag and score.
For medium result sets (5-15): cluster by topic with summary.
For large result sets (15+): high-level synthesis + Top 5 + "want to dig deeper?" prompt.

## Constraints

1. **Never block on a failed source** — if one API errors, continue with remaining sources
2. **Fallback chain**: Exa/Tavily/Grok any fail -> continue with others -> all fail -> host search only
3. **Do not fabricate sources** — every claim must trace to a real URL
4. **Confirm with user** before executing thread-pulling chains deeper than 3 levels
5. **Host search is orchestrated by the agent**, not called from scripts — scripts handle Exa/Tavily/Grok only

## Configuration

Credentials via environment variables (recommended) or `.env` file in skill root.
For detailed setup: see [references/setup-guide.md](references/setup-guide.md)

Required keys: `EXA_API_KEY`, `TAVILY_API_KEY`
Optional keys: `GROK_API_KEY` + `GROK_API_URL`, `MINERU_TOKEN`

## Bundled Resources

| Path | Content |
|------|---------|
| [references/intent-guide.md](references/intent-guide.md) | Intent classification with scoring weights |
| [references/setup-guide.md](references/setup-guide.md) | Credential configuration and migration guide |
| [references/script-usage.md](references/script-usage.md) | Detailed script parameters and examples |
| [references/authority-domains.json](references/authority-domains.json) | Domain authority scoring table |
| [references/research-light-regression-samples.md](references/research-light-regression-samples.md) | Research-light trigger boundary test cases |
