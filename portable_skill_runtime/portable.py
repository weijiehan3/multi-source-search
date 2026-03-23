from __future__ import annotations

import os
from pathlib import Path


def _iter_parent_dirs(start: Path) -> list[Path]:
    current = start if start.is_dir() else start.parent
    return [current, *current.parents]


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _skill_root(start: Path) -> Path | None:
    for candidate in _iter_parent_dirs(start.resolve()):
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def _skills_root(start: Path) -> Path | None:
    skill_root = _skill_root(start)
    if skill_root is None:
        return None
    return skill_root.parent


def _host_home(skills_root: Path | None) -> Path | None:
    if skills_root is None:
        return None
    if skills_root.name == "skills" and skills_root.parent.name == "workspace":
        return skills_root.parent.parent
    return skills_root.parent


def _derived_workspace(skills_root: Path | None) -> Path | None:
    if skills_root is None:
        return None
    if skills_root.name == "skills" and skills_root.parent.name == "workspace":
        return skills_root.parent
    return skills_root.parent / "workspace"


def _env_path(*names: str) -> Path | None:
    for name in names:
        if value := os.environ.get(name):
            return Path(value).expanduser()
    return None


def load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_env_chain(start: Path) -> None:
    skill_root = _skill_root(start)
    skills_root = _skills_root(start)
    candidates: list[Path] = [start.resolve().parent / ".env"]
    if skill_root is not None:
        candidates.append(skill_root / ".env")
    if skills_root is not None:
        candidates.append(skills_root / ".env")
    for candidate in _unique_paths(candidates):
        load_env_file(candidate)


def default_workspace_root(start: Path) -> Path:
    if env_path := _env_path(
        "PORTABLE_SKILLS_WORKSPACE",
        "AGENT_SKILLS_WORKSPACE",
        "OPENCLAW_WORKSPACE",
    ):
        return env_path

    skills_root = _skills_root(start)
    if derived_workspace := _derived_workspace(skills_root):
        return derived_workspace

    return Path.home() / ".agent-skills" / "workspace"


def find_search_credentials_file(start: Path) -> Path | None:
    direct_env = _env_path(
        "SEARCH_CREDENTIALS_FILE",
        "PORTABLE_SKILLS_CREDENTIALS_FILE",
    )
    if direct_env and direct_env.is_file():
        return direct_env

    if env_dir := _env_path(
        "PORTABLE_SKILLS_CREDENTIALS_DIR",
        "AGENT_SKILLS_CREDENTIALS_DIR",
    ):
        candidate = env_dir / "search.json"
        if candidate.is_file():
            return candidate

    skill_root = _skill_root(start)
    skills_root = _skills_root(start)
    host_home = _host_home(skills_root)

    candidates: list[Path] = [
        Path.cwd() / "credentials" / "search.json",
        Path.home() / ".agent-skills" / "credentials" / "search.json",
    ]
    if skill_root is not None:
        candidates.append(skill_root / "credentials" / "search.json")
    if skills_root is not None:
        candidates.append(skills_root / "credentials" / "search.json")
    if host_home is not None:
        candidates.append(host_home / "credentials" / "search.json")

    for candidate in _unique_paths(candidates):
        if candidate.is_file():
            return candidate
    return None


def find_sibling_skill_script(
    start: Path,
    skill_name: str,
    relative_path: str | Path,
) -> Path | None:
    relative = Path(relative_path)
    skills_root = _skills_root(start)
    workspace_root = default_workspace_root(start)

    candidates: list[Path] = []
    if skills_root is not None:
        candidates.append(skills_root / skill_name / relative)
    candidates.append(workspace_root / "skills" / skill_name / relative)

    for candidate in _unique_paths(candidates):
        if candidate.exists():
            return candidate
    return None
