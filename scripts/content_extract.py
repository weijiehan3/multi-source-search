#!/usr/bin/env python3
"""content-extract: deterministic MinerU-only extractor for portable skills.

Why this exists:
- Host-provided `web_fetch` tools are not available inside scripts.
- This script provides a stable "fallback engine" that the agent can call
  after probing with `web_fetch`.

It wraps mineru-extract's MCP-aligned script and returns a compact JSON contract.

Usage:
  python3 scripts/content_extract.py --url <URL> [--model MinerU-HTML]

Output (stdout):
  { ok, source_url, engine, markdown, artifacts, sources, notes }

"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys


def _bootstrap_portable_runtime() -> None:
    current = pathlib.Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "portable_skill_runtime"
        if candidate.is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return


_bootstrap_portable_runtime()

from portable_skill_runtime import find_sibling_skill_script, load_env_chain

load_env_chain(pathlib.Path(__file__).resolve())


def _error_output(source_url: str, notes: list[str]) -> dict:
    return {
        "ok": False,
        "source_url": source_url,
        "engine": "mineru",
        "markdown": None,
        "artifacts": {},
        "sources": [source_url],
        "notes": notes,
    }


def _find_mineru_wrapper() -> str:
    """Locate mineru_parse_documents.py relative to this script or via env."""
    # 1. Env override
    if v := os.environ.get("MINERU_WRAPPER_PATH"):
        return v

    # 2. Unified-suite local script
    local_candidate = pathlib.Path(__file__).resolve().parent / "mineru_parse_documents.py"
    if local_candidate.exists():
        return str(local_candidate)

    # 3. Fallback to split-skill layout
    candidate = find_sibling_skill_script(
        pathlib.Path(__file__).resolve(),
        "mineru-extract",
        pathlib.Path("scripts") / "mineru_parse_documents.py",
    )
    if candidate is not None:
        return str(candidate)

    raise FileNotFoundError(
        "Cannot find mineru_parse_documents.py. "
        "Set MINERU_WRAPPER_PATH or keep mineru_parse_documents.py in the same scripts directory."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", default="MinerU-HTML")
    ap.add_argument("--language", default="ch")
    ap.add_argument("--emit-markdown", action="store_true", default=True)
    ap.add_argument("--max-chars", type=int, default=20000)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    try:
        wrapper = _find_mineru_wrapper()
    except FileNotFoundError as e:
        out = _error_output(args.url, [str(e)])
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 2

    cmd = [
        sys.executable,
        wrapper,
        "--file-sources",
        args.url,
        "--model-version",
        args.model,
        "--language",
        args.language,
        "--emit-markdown",
        "--max-chars",
        str(args.max_chars),
    ]
    if args.force:
        cmd.append("--force")

    p = subprocess.run(cmd, capture_output=True, text=True)

    try:
        j = json.loads(p.stdout)
    except Exception:
        j = None

    if j is not None and not isinstance(j, dict):
        j = None

    if j is None:
        if p.returncode != 0:
            out = _error_output(
                args.url,
                [
                    "mineru wrapper crashed",
                    (p.stderr or "").strip()[:500],
                ],
            )
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
            return 2

        out = _error_output(
            args.url,
            ["mineru wrapper returned non-json", (p.stdout or "")[:300]],
        )
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 2

    if not j.get("items"):
        notes = []
        if error := j.get("error"):
            notes.append(str(error))
        if errors := j.get("errors"):
            notes.append(json.dumps(errors, ensure_ascii=False)[:800])
        if not notes:
            notes.append("no items")
        out = _error_output(args.url, notes)
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return p.returncode if p.returncode else 1

    item = j["items"][0]
    sources = [args.url]
    if item.get("full_zip_url"):
        sources.append(item["full_zip_url"])
    if item.get("markdown_path"):
        sources.append(item["markdown_path"])

    out = {
        "ok": True,
        "source_url": args.url,
        "engine": "mineru",
        "markdown": item.get("markdown"),
        "artifacts": {
            "out_dir": item.get("out_dir"),
            "markdown_path": item.get("markdown_path"),
            "zip_path": item.get("zip_path"),
            "task_id": item.get("task_id"),
            "cache_key": item.get("cache_key"),
        },
        "sources": sources,
        "notes": ["mcp-aligned: mineru_parse_documents"],
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
