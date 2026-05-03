"""Ingestion sync module. 12-Factor: config from env vars."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
from git import GitCommandError, Repo

from hope_jarvis.config import get_data_path, get_repos_config, get_sync_state_path


def clone_or_pull_repo(repo_config: Dict[str, Any]) -> str:
    """Clone or pull a GitHub repository."""
    repo_url = repo_config["github_url"]
    repo_name = repo_config["name"]
    local_path = get_data_path() / repo_name

    if local_path.exists():
        try:
            repo = Repo(local_path)
            repo.remotes.origin.pull()
            print(f"Pulled updates for {repo_name}")
        except GitCommandError as e:
            print(f"Error pulling {repo_name}: {e}")
    else:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        Repo.clone_from(repo_url, str(local_path))
        print(f"Cloned {repo_name}")

    print(f"Repo path: {local_path} (exists: {local_path.exists()})")
    return str(local_path)


def get_file_hash(file_path: Path) -> str:
    """Get MD5 hash of a file for change detection."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_markdown_files(repo_path: str, docs_dir: str) -> List[Path]:
    """Find all markdown files in the docs directory."""
    docs_path = Path(repo_path) / docs_dir
    if not docs_path.exists():
        print(f"Docs dir not found: {docs_path}")
        return []
    files = list(docs_path.rglob("*.md"))
    print(f"Found {len(files)} markdown files in {docs_path}")
    return files


def _load_sync_state() -> Dict:
    """Load previous sync state (file hashes)."""
    state_path = get_sync_state_path()
    if state_path.exists():
        with open(state_path, "r") as f:
            return json.load(f)
    return {}


def _save_sync_state(state: Dict) -> None:
    """Save current sync state."""
    state_path = get_sync_state_path()
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def _process_repo(
    repo_config: Dict[str, Any], sync_state: Dict, force: bool = False
) -> List[Dict]:
    """Sync a single repo and return changed files."""
    repo_path = clone_or_pull_repo(repo_config)
    docs_dir = repo_config.get("docs_dir")
    if docs_dir is None:
        raise ValueError(f"docs_dir not specified for repo {repo_config['name']}")
    branch = repo_config.get("branch", "main")

    md_files = find_markdown_files(repo_path, docs_dir)
    repo_path_obj = Path(repo_path)
    changed_files = []

    for md_file in md_files:
        rel_path = str(md_file.relative_to(repo_path_obj))
        file_hash = get_file_hash(md_file)
        state_key = f"{repo_config['name']}/{rel_path}"

        if force or state_key not in sync_state or sync_state[state_key] != file_hash:
            changed_files.append(
                {
                    "repo_name": repo_config["name"],
                    "file_path": rel_path,
                    "full_path": str(md_file),
                    "github_url": repo_config["github_url"],
                    "rendered_base_url": repo_config["rendered_base_url"],
                    "docs_dir": docs_dir,
                    "branch": branch,
                }
            )
            sync_state[state_key] = file_hash

    return changed_files


def sync_all_repos(force: bool = False) -> List[Dict]:
    """Sync all repositories and return list of changed files with metadata."""
    repos_config_path = get_repos_config()
    with open(repos_config_path, "r") as f:
        config = yaml.safe_load(f)

    sync_state = {} if force else _load_sync_state()
    changed_files = []

    for repo_config in config["repos"]:
        changed = _process_repo(repo_config, sync_state, force)
        changed_files.extend(changed)

    _save_sync_state(sync_state)
    return changed_files


def sync_repo_by_name(repo_name: str, force: bool = False) -> List[Dict]:
    """Sync a single repository by name and return changed files."""
    repos_config_path = get_repos_config()
    with open(repos_config_path, "r") as f:
        config = yaml.safe_load(f)

    sync_state = {} if force else _load_sync_state()
    changed_files = []

    for repo_config in config["repos"]:
        if repo_config["name"] == repo_name:
            changed_files = _process_repo(repo_config, sync_state, force)
            break

    if not changed_files:
        print(f"Repo '{repo_name}' not found or no changes detected.")

    _save_sync_state(sync_state)
    return changed_files
