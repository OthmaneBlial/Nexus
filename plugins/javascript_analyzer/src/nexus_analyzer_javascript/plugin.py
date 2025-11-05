from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List

from backend.app.core.analyzer import AnalyzerPlugin

SKIP_DIRS = {".git", ".hg", "node_modules", "dist", "build", ".next", ".nuxt", ".cache", ".turbo"}
SOURCE_EXTENSIONS = {".js", ".jsx", ".cjs", ".mjs", ".ts", ".tsx", ".vue"}


class JavaScriptAnalyzer(AnalyzerPlugin):
    name = "JavaScript"

    def discover(self, path: str) -> bool:
        root = Path(path)
        return (root / "package.json").exists()

    def analyze(self, path: str) -> dict:
        root = Path(path)
        source_files = list(self._iter_source_files(root))
        code_units = []
        total_loc = 0
        complexity_samples: List[float] = []

        for file_path in source_files:
            rel_path = file_path.relative_to(root)
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            loc = self._count_loc(text)
            total_loc += loc

            complexity_score = self._estimate_complexity(text)
            complexity_samples.append(complexity_score)

            code_units.append(
                {
                    "id": ".".join(rel_path.with_suffix("").parts),
                    "type": "FILE",
                    "path": str(rel_path),
                    "metrics": {
                        "loc": loc,
                        "complexity": round(complexity_score, 2),
                    },
                }
            )

        dependencies = self._collect_dependencies(root)
        avg_complexity = (
            round(sum(complexity_samples) / len(complexity_samples), 2) if complexity_samples else 0.0
        )

        return {
            "languages": ["JavaScript"],
            "summary": {
                "totalFiles": len(source_files),
                "totalLinesOfCode": total_loc,
                "avgComplexity": avg_complexity,
                "dependencyCount": len(dependencies),
            },
            "codeUnits": code_units,
            "dependencies": dependencies,
            "connections": [],
        }

    def _iter_source_files(self, root: Path) -> Iterable[Path]:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in SOURCE_EXTENSIONS:
                yield path

    def _count_loc(self, text: str) -> int:
        return sum(1 for line in text.splitlines() if line.strip())

    def _estimate_complexity(self, text: str) -> float:
        function_count = len(re.findall(r"\bfunction\b|=>", text))
        decision_points = len(
            re.findall(r"\b(if|for|while|case|catch|switch)\b|&&|\|\|", text)
        )
        return max(1.0, function_count + decision_points * 0.5)

    def _collect_dependencies(self, root: Path) -> List[dict]:
        package_json = root / "package.json"
        if not package_json.exists():
            return []
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        deps = []
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            section_data = data.get(section, {})
            if not isinstance(section_data, dict):
                continue
            for name, version in section_data.items():
                deps.append(
                    {
                        "id": f"{name}:{version}",
                        "name": name,
                        "version": version,
                        "type": "DIRECT",
                        "license": None,
                    }
                )
        return deps
