from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from radon.complexity import cc_visit

from backend.app.core.analyzer import AnalyzerPlugin

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}


class PythonAnalyzer(AnalyzerPlugin):
    name = "Python"

    def discover(self, path: str) -> bool:
        root = Path(path)
        if not root.is_dir():
            return False

        markers = ("pyproject.toml", "requirements.txt", "setup.cfg", "setup.py")
        if any((root / marker).exists() for marker in markers):
            return True

        return any(self._iter_python_files(root, limit=5))

    def analyze(self, path: str) -> dict:
        root = Path(path)
        python_files = list(self._iter_python_files(root))
        code_units = []
        total_loc = 0
        complexity_scores: List[float] = []

        for file_path in python_files:
            rel_path = file_path.relative_to(root)
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            loc = len(text.splitlines())
            total_loc += loc

            cc_results = cc_visit(text)
            file_complexity = [block.complexity for block in cc_results]
            if file_complexity:
                avg_complexity = sum(file_complexity) / len(file_complexity)
                complexity_scores.extend(file_complexity)
            else:
                avg_complexity = 0.0

            code_units.append(
                {
                    "id": ".".join(rel_path.with_suffix("").parts),
                    "type": "FILE",
                    "path": str(rel_path),
                    "metrics": {
                        "loc": loc,
                        "complexity": round(avg_complexity, 2),
                    },
                }
            )

        dependencies = self._collect_dependencies(root)
        avg_complexity = round(sum(complexity_scores) / len(complexity_scores), 2) if complexity_scores else 0.0

        return {
            "languages": ["Python"],
            "summary": {
                "totalFiles": len(python_files),
                "totalLinesOfCode": total_loc,
                "avgComplexity": avg_complexity,
                "dependencyCount": len(dependencies),
            },
            "codeUnits": code_units,
            "dependencies": dependencies,
            "connections": [],
        }

    def _iter_python_files(self, root: Path, limit: int | None = None) -> Iterable[Path]:
        count = 0
        for path in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                yield path
                count += 1
                if limit is not None and count >= limit:
                    return

    def _collect_dependencies(self, root: Path) -> List[dict]:
        requirements_file = root / "requirements.txt"
        dependencies: List[dict] = []
        if requirements_file.exists():
            for line in requirements_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                name, version = self._split_requirement(line)
                dependencies.append(
                    {
                        "id": f"{name}:{version}" if version else name,
                        "name": name,
                        "version": version,
                        "type": "DIRECT",
                    }
                )
        return dependencies

    def _split_requirement(self, requirement: str) -> tuple[str, str | None]:
        separators = ["==", ">=", "<=", "~=", "!=", ">"]
        for sep in separators:
            if sep in requirement:
                name, version = requirement.split(sep, 1)
                return name.strip(), version.strip()
        return requirement.strip(), None
