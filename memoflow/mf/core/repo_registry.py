"""Repository registry for MemoFlow.

Stores named repositories in a user-level config file, so that commands like
`mf repo list` and `mf repo info` can work across projects.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


REGISTRY_DIR = Path.home() / ".memoflow"
REGISTRY_FILE = REGISTRY_DIR / "repos.json"


@dataclass
class RegisteredRepo:
    name: str
    path: Path


class RepoRegistry:
    """Simple JSON-based registry of named MemoFlow repositories."""

    def __init__(self, registry_file: Path = REGISTRY_FILE) -> None:
        self.registry_file = registry_file
        self._repos: List[RegisteredRepo] = []
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.registry_file.exists():
            self._repos = []
            return
        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load repo registry {self.registry_file}: {e}")
            self._repos = []
            return

        repos: List[RegisteredRepo] = []
        for item in data.get("repos", []):
            name = item.get("name")
            path_str = item.get("path")
            if not name or not path_str:
                continue
            repos.append(RegisteredRepo(name=name, path=Path(path_str)))
        self._repos = repos

    def _save(self) -> None:
        REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "repos": [
                {"name": r.name, "path": str(r.path)} for r in self._repos
            ]
        }
        try:
            self.registry_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save repo registry {self.registry_file}: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_repos(self) -> List[RegisteredRepo]:
        return list(self._repos)

    def add_repo(self, name: str, path: Path) -> None:
        """Register or update a repo.

        - If name already exists with the same path, do nothing.
        - If name exists with a different path, keep the old one and log a warning.
        - If path already exists under another name, log info and skip.
        """
        path = path.resolve()
        # Check existing by name
        for repo in self._repos:
            if repo.name == name:
                if repo.path == path:
                    return
                logger.warning(
                    "Repo name '%s' already registered for %s, skipping new path %s",
                    name,
                    repo.path,
                    path,
                )
                return

        # If same path already registered under another name, don't add duplicate
        for repo in self._repos:
            if repo.path.resolve() == path:
                logger.info(
                    "Path %s already registered as '%s', skipping additional name '%s'",
                    path,
                    repo.name,
                    name,
                )
                return

        self._repos.append(RegisteredRepo(name=name, path=path))
        self._save()

    def get_by_name(self, name: str) -> Optional[RegisteredRepo]:
        for repo in self._repos:
            if repo.name == name:
                return repo
        return None

    def find_by_path(self, path: Path) -> Optional[RegisteredRepo]:
        path = path.resolve()
        for repo in self._repos:
            if repo.path.resolve() == path:
                return repo
        return None

    def remove_by_name(self, name: str) -> bool:
        """Remove repo by registered name. Returns True if removed."""
        before = len(self._repos)
        self._repos = [r for r in self._repos if r.name != name]
        if len(self._repos) != before:
            self._save()
            return True
        return False

    def remove_by_path(self, path: Path) -> bool:
        """Remove repo by path. Returns True if removed."""
        path = path.resolve()
        before = len(self._repos)
        self._repos = [r for r in self._repos if r.path.resolve() != path]
        if len(self._repos) != before:
            self._save()
            return True
        return False
