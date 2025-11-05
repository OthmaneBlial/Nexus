from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, List

from backend.app.core.analyzer import AnalyzerPlugin

SKIP_DIRS = {".git", ".hg", "build", "out", ".idea", "target", ".gradle"}
JAVA_EXTENSIONS = {".java"}
POM_FILE = "pom.xml"
GRADLE_FILES = {"build.gradle", "build.gradle.kts"}


class JavaAnalyzer(AnalyzerPlugin):
    name = "Java"

    def discover(self, path: str) -> bool:
        root = Path(path)
        return any((root / marker).exists() for marker in [POM_FILE, *GRADLE_FILES])

    def analyze(self, path: str) -> dict:
        root = Path(path)
        java_files = list(self._iter_java_files(root))

        code_units = []
        total_loc = 0
        complexity_samples: List[float] = []

        for file_path in java_files:
            rel = file_path.relative_to(root)
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            loc = self._count_loc(text)
            total_loc += loc
            complexity = self._estimate_complexity(text)
            complexity_samples.append(complexity)

            code_units.append(
                {
                    "id": ".".join(rel.with_suffix("").parts),
                    "type": "FILE",
                    "path": str(rel),
                    "metrics": {
                        "loc": loc,
                        "complexity": round(complexity, 2),
                    },
                }
            )

        dependencies = self._collect_dependencies(root)
        avg_complexity = (
            round(sum(complexity_samples) / len(complexity_samples), 2) if complexity_samples else 0.0
        )

        return {
            "languages": ["Java"],
            "summary": {
                "totalFiles": len(java_files),
                "totalLinesOfCode": total_loc,
                "avgComplexity": avg_complexity,
                "dependencyCount": len(dependencies),
            },
            "codeUnits": code_units,
            "dependencies": dependencies,
            "connections": [],
        }

    def _iter_java_files(self, root: Path) -> Iterable[Path]:
        for file in root.rglob("*.java"):
            if any(part in SKIP_DIRS for part in file.parts):
                continue
            if file.suffix.lower() in JAVA_EXTENSIONS:
                yield file

    def _count_loc(self, text: str) -> int:
        return sum(1 for line in text.splitlines() if line.strip())

    def _estimate_complexity(self, text: str) -> float:
        decision_keywords = len(re.findall(r"\b(if|for|while|case|catch|switch)\b", text))
        logical_ops = len(re.findall(r"&&|\|\|", text))
        return max(1.0, decision_keywords + logical_ops * 0.5)

    def _collect_dependencies(self, root: Path) -> List[dict]:
        if (root / POM_FILE).exists():
            return self._parse_maven_dependencies(root / POM_FILE)

        for file_name in GRADLE_FILES:
            candidate = root / file_name
            if candidate.exists():
                return self._parse_gradle_dependencies(candidate)
        return []

    def _parse_maven_dependencies(self, pom_path: Path) -> List[dict]:
        dependencies: List[dict] = []
        try:
            tree = ET.parse(pom_path)
        except ET.ParseError:
            return dependencies

        namespace = {"mvn": tree.getroot().tag.split("}")[0].strip("{")}
        for dep in tree.findall(".//mvn:dependency", namespace):
            group = (dep.findtext("mvn:groupId", default="", namespaces=namespace) or "").strip()
            artifact = (dep.findtext("mvn:artifactId", default="", namespaces=namespace) or "").strip()
            version = (dep.findtext("mvn:version", default="", namespaces=namespace) or "").strip() or None
            if not artifact:
                continue
            name = f"{group}:{artifact}" if group else artifact
            dep_id = f"{name}:{version}" if version else name
            dependencies.append(
                {
                    "id": dep_id,
                    "name": name,
                    "version": version,
                    "type": "DIRECT",
                }
            )
        return dependencies

    def _parse_gradle_dependencies(self, gradle_file: Path) -> List[dict]:
        dependencies: List[dict] = []
        try:
            text = gradle_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return dependencies

        pattern = re.compile(r'^\s*(implementation|api|compileOnly|runtimeOnly)\s+["\']([^"\']+)["\']', re.MULTILINE)
        for match in pattern.finditer(text):
            _, coordinate = match.groups()
            coordinate = coordinate.strip()
            if ":" not in coordinate:
                continue
            parts = coordinate.split(":")
            name = ":".join(parts[:2])
            version = parts[2] if len(parts) > 2 else None
            dep_id = coordinate if version else name
            dependencies.append(
                {
                    "id": dep_id,
                    "name": name,
                    "version": version,
                    "type": "DIRECT",
                }
            )
        return dependencies
