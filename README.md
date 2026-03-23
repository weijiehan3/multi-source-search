# Multi-Source Search

Agent-neutral multi-source search skill for **Claude Code**, **Codex**, and **OpenClaw**.

Combine host web search + Exa + Tavily + Grok for high-coverage retrieval, thread pulling for deep context, and MinerU for anti-crawler page parsing.

Copy the folder into any agent's skills directory — no code changes needed.

## Source Philosophy

> **Exa finds evidence. Grok finds direction. Tavily fills the middle. Host search provides breadth.**

| Source | Positioning | Best For |
|--------|------------|---------|
| **Host search** | General web recall | First-layer broad coverage |
| **Exa** | Source-first (evidence) | Official docs, API refs, canonical pages |
| **Tavily** | General + AI answer | Balanced coverage, factual Q&A with citations |
| **Grok** | Freshness-first (direction) | Real-time info, community chatter, breaking news |

Each source has a distinct role — they complement, not duplicate.

## Features

- **Intent-aware search** — 7 intent types (factual / status / comparison / tutorial / exploratory / news / resource) with automatic strategy selection and weighted scoring
- **Multi-source aggregation** — Exa + Tavily + Grok parallel search with deduplication
- **Thread pulling** — Deep-fetch GitHub issues/PRs, Hacker News, Reddit, V2EX discussions with reference extraction
- **Chain tracking** — Recursive link following with LLM relevance gate
- **Content extraction** — URL-to-Markdown with MinerU fallback for anti-crawler sites (WeChat, Zhihu)
- **Research-light lane** — Automatic escalation for complex queries (comparison with judgment signals, exploratory with causal reasoning)
- **Docs-compare pattern** — Compare official claims vs community discussion via source routing
- **Portable runtime** — Agent-agnostic path resolution and credential loading

## Quick Start

```bash
# 1. Copy to your agent's skills directory
cp -r multi-source-search ~/.claude/skills/      # Claude Code
cp -r multi-source-search ~/.codex/skills/       # Codex
cp -r multi-source-search ~/.openclaw/workspace/skills/  # OpenClaw

# 2. Configure API keys
cd <your-skills-dir>/multi-source-search
cp .env.example .env
# Edit .env with your API keys

# 3. Install dependencies
pip install requests                               # required
pip install trafilatura beautifulsoup4 lxml        # optional: for thread pulling
```

## API Keys

### Required

| Key | Source | Get it from |
|-----|--------|-------------|
| `EXA_API_KEY` | Exa | [exa.ai](https://exa.ai) |
| `TAVILY_API_KEY` | Tavily | [tavily.com](https://tavily.com) |

### Optional

| Key | Source | Get it from |
|-----|--------|-------------|
| `GROK_API_KEY` + `GROK_API_URL` | Grok | [console.x.ai](https://console.x.ai) (official) or via [grok2api](https://github.com/chenyme/grok2api) (free reverse proxy) |
| `MINERU_TOKEN` | MinerU | [mineru.net/apiManage](https://mineru.net/apiManage) |

If Grok is not configured, automatic fallback to Exa + Tavily dual-source mode.

See [references/setup-guide.md](references/setup-guide.md) for detailed configuration including grok2api local proxy setup.

## Usage

### Search

```bash
# Deep research with intent-aware scoring
python3 scripts/search.py "RAG framework comparison" --mode deep --intent comparison --num 5

# Latest news with time filter
python3 scripts/search.py "AI news" --mode deep --intent news --freshness pw

# Multi-query parallel search
python3 scripts/search.py --queries "Bun vs Deno" "Bun advantages" "Deno advantages" \
  --mode deep --intent comparison

# Single source test
python3 scripts/search.py "Claude Code updates" --source grok --num 3

# Search + reference extraction
python3 scripts/search.py "OpenClaw config bug" --mode deep --intent status --extract-refs
```

### Thread Pulling

```bash
# GitHub issue / PR
python3 scripts/fetch_thread.py "https://github.com/owner/repo/issues/123"
python3 scripts/fetch_thread.py "https://github.com/owner/repo/pull/456" --format markdown

# Hacker News / Reddit / V2EX
python3 scripts/fetch_thread.py "https://news.ycombinator.com/item?id=43197966"
python3 scripts/fetch_thread.py "https://www.reddit.com/r/Python/comments/abc123/title/"
```

### Content Extraction

```bash
# General URL -> Markdown
python3 scripts/content_extract.py --url "https://example.com/article"

# Anti-crawler sites via MinerU
python3 scripts/mineru_parse_documents.py \
  --file-sources "https://mp.weixin.qq.com/s/example" \
  --model-version MinerU-HTML --emit-markdown
```

See [references/script-usage.md](references/script-usage.md) for full parameter reference.

## Directory Structure

```
multi-source-search/
  SKILL.md                        # AI behavioral instructions (the skill itself)
  .env.example                    # Configuration template
  .gitignore
  credentials/
    search.example.json           # Alternative credential format
  portable_skill_runtime/
    __init__.py                   # Shared runtime helpers
    portable.py                   # Path resolution, env chain loading
  references/
    intent-guide.md               # 7 intent types with scoring weights
    setup-guide.md                # Credential setup + grok2api guide
    script-usage.md               # Full script parameter reference
    authority-domains.json        # Domain authority scoring table (60+ domains)
    research-light-regression-samples.md  # 18 test cases for research-light trigger
  scripts/
    search.py                     # Multi-source search (Exa + Tavily + Grok)
    fetch_thread.py               # Thread deep-fetch (GitHub/HN/Reddit/V2EX/web)
    chain_tracker.py              # Recursive chain tracking with LLM gate
    relevance_gate.py             # LLM-based relevance scoring
    content_extract.py            # URL-to-Markdown extraction
    mineru_extract.py             # MinerU low-level single URL parser
    mineru_parse_documents.py     # MinerU MCP-aligned batch wrapper
```

## How It Works (for AI agents)

When this skill is loaded, the AI agent follows a 5-step execution protocol defined in `SKILL.md`:

1. **Classify Intent** — Infer query intent from signal words (don't ask the user)
2. **Expand Queries** — Technical synonym expansion, Chinese-English parallel, sub-query generation
3. **Multi-Source Retrieval** — Route to appropriate sources based on intent, run in parallel
4. **Thread Pulling** — Conditionally deep-fetch GitHub/forum threads when relevant
5. **Content Extraction** — On-demand URL-to-Markdown with anti-crawler fallback

The agent synthesizes results by topic (not by source), flags conflicting information, and expresses confidence based on source agreement.

## Migration Between Agents

Copy the entire folder to the target agent's skills directory. The `.env` and `credentials/` travel with the skill.

| Agent | Target Directory |
|-------|-----------------|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| OpenClaw | `~/.openclaw/workspace/skills/` |

Restart the agent after copying.

## Credits

This project is built upon and inspired by:

- **[openclaw-search-skills](https://github.com/blessonism/openclaw-search-skills)** by [@blessonism](https://github.com/blessonism) — Intent-aware multi-source search architecture, thread pulling, research-light escalation, and the original search/fetch scripts
- **[openclaw-dae-skills](https://github.com/jikssha/openclaw-dae-skills)** by [@jikssha](https://github.com/jikssha) — Source positioning philosophy: Exa as source-first (evidence), Grok as freshness-first (direction), and the docs-compare pattern
- **[grok2api](https://github.com/chenyme/grok2api)** by [@chenyme](https://github.com/chenyme) — Grok reverse proxy enabling free-tier access via local API

The portable runtime, SKILL.md restructuring (AI behavioral instructions with decision trees, output contracts, and constraints), and agent-neutral credential loading were developed for this project.

## License

MIT
