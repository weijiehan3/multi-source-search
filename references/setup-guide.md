# Setup Guide

Credential configuration for the Portable Search Suite.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration Priority

Higher priority overrides lower:

1. **Environment variables** (highest) — set in shell or agent settings
2. **`.env` file** in skill root directory
3. **`credentials/search.json`** in skill root directory
4. **Default values** in scripts (lowest)

The `.env` file only sets variables that are not already present in the environment.

---

## Search Provider Keys

### Exa (Required)

Role: **Source-first retrieval** — official docs, API refs, canonical pages, text extraction.

Get your API key from [exa.ai](https://exa.ai).

```bash
EXA_API_KEY=your-exa-key
```

Custom endpoint (for self-hosted or proxy):

```bash
EXA_API_BASE=https://exa.example.com       # auto-appends /search
# or
EXA_API_URL=https://exa.example.com/search  # full URL
```

Default: `https://api.exa.ai/search`

### Tavily (Required)

Role: **Balanced search + AI answer** — general coverage with citation-backed summaries.

Get your API key from [tavily.com](https://tavily.com).

```bash
TAVILY_API_KEY=your-tavily-key
```

### Grok (Optional but Recommended)

Role: **Freshness-first research** — real-time info, community chatter, breaking news.

Two options for Grok API access:

#### Option A: Official xAI API

Get your key from [console.x.ai](https://console.x.ai).

```bash
GROK_API_URL=https://api.x.ai/v1
GROK_API_KEY=your-xai-key
GROK_MODEL=grok-4.1-fast
```

#### Option B: grok2api Local Reverse Proxy (Recommended for Free Users)

Use [grok2api](https://github.com/chenyme/grok2api) to run a local proxy that converts
Grok web interface calls to an OpenAI-compatible API.

Setup:

```bash
git clone https://github.com/chenyme/grok2api
cd grok2api
docker compose up -d
# Admin panel: http://localhost:8000/admin (default password: grok2api)
# Import your Grok tokens in the admin panel
```

Then configure the skill:

```bash
GROK_API_URL=http://localhost:8000/v1
GROK_API_KEY=your-grok2api-api-key   # set in grok2api config as api_key
GROK_MODEL=grok-4.1-fast             # or grok-4, grok-4.20-beta, etc.
```

Rate limits with grok2api:
- Basic account: ~80 calls / 20 hours
- Super account: ~140 calls / 2 hours

Available models: grok-3, grok-4, grok-4-fast, grok-4-heavy, grok-4.1-fast, grok-4.1-expert,
grok-4.1-thinking, grok-4.20-beta, etc.

If Grok is not configured, the skill automatically falls back to Exa + Tavily dual-source mode.

### MinerU (Optional)

Only needed for anti-crawler page extraction (WeChat, Zhihu, Xiaohongshu, etc.).

Get your token from [mineru.net/apiManage](https://mineru.net/apiManage).

```bash
MINERU_TOKEN=your-mineru-token
MINERU_API_BASE=https://mineru.net
```

---

## Credentials File (Alternative)

Create `credentials/search.json` in the skill root:

```json
{
  "exa": "your-exa-key",
  "tavily": "your-tavily-key",
  "grok": {
    "apiUrl": "http://localhost:8000/v1",
    "apiKey": "your-grok2api-key",
    "model": "grok-4.1-fast"
  }
}
```

Custom Exa endpoint:

```json
{
  "exa": { "apiKey": "your-key", "apiUrl": "https://exa.example.com/search" }
}
```

---

## Workspace Directory

MinerU downloads and other output files are stored in a workspace directory:

1. `PORTABLE_SKILLS_WORKSPACE` env var (if set)
2. Auto-derived from skill installation path
3. Fallback: `~/.agent-skills/workspace/`

---

## Migration Between Agents

Copy the entire `portable-search-suite/` folder:

| Agent | Target Directory |
|-------|-----------------|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| OpenClaw | `~/.openclaw/workspace/skills/` |

The `.env` and `credentials/` travel with the skill. Restart the agent after copying.

---

## Python Dependencies

```bash
# Required (all scripts)
pip install requests

# Optional (only for fetch_thread.py thread pulling)
pip install trafilatura beautifulsoup4 lxml
```

---

## Security Notes

- `.env` contains real API keys — do not commit to version control
- Share `.env.example` (without keys) when distributing the skill
- `credentials/search.example.json` is safe to share
