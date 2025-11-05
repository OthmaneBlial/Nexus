from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

from fastapi import HTTPException, status

KEY_PROJECT_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
}


def get_allowed_root() -> Path:
    root = os.environ.get("NEXUS_ALLOWED_ROOT")
    if root:
        base = Path(root).expanduser().resolve()
    else:
        base = (Path.cwd() / "apps").resolve()
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    if not base.is_dir():
        raise RuntimeError(f"Configured Nexus root {base} is invalid")
    return base


def resolve_path(requested_path: str | None) -> Path:
    root = get_allowed_root()
    if not requested_path:
        return root

    candidate = Path(requested_path).expanduser()
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if not candidate.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path does not exist")

    if not is_within_root(candidate, root):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Path is outside allowed root")

    return candidate


def list_directory(path: Path) -> List[dict]:
    entries: List[dict] = []
    root = get_allowed_root()
    for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        if entry.is_dir():
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry.relative_to(root)),
                    "type": "directory",
                }
            )
        elif entry.name in KEY_PROJECT_FILES:
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry.relative_to(root)),
                    "type": "file",
                }
            )
    return entries


def is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
