from __future__ import annotations

import sys
from pathlib import Path

from app.core.orchestrator import AnalysisOrchestrator
from app.core.plugins import PluginManager

PY_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "python_analyzer" / "src"
JS_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "javascript_analyzer" / "src"
JAVA_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "java_analyzer" / "src"

for plugin_src in (PY_PLUGIN_SRC, JS_PLUGIN_SRC, JAVA_PLUGIN_SRC):
    if str(plugin_src) not in sys.path:
        sys.path.append(str(plugin_src))

from nexus_analyzer_python.plugin import PythonAnalyzer  # type: ignore  # noqa: E402
from nexus_analyzer_java.plugin import JavaAnalyzer  # type: ignore  # noqa: E402


def test_python_analyzer_reports_code_units(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    package = project_dir / "demo_pkg"
    package.mkdir(parents=True)
    (project_dir / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "module.py").write_text(
        "def handler(value: int) -> int:\n"
        "    total = 0\n"
        "    for idx in range(value):\n"
        "        if idx % 2 == 0:\n"
        "            total += idx\n"
        "    return total\n",
        encoding="utf-8",
    )

    manager = PluginManager()
    manager.register(PythonAnalyzer())
    orchestrator = AnalysisOrchestrator(plugin_manager=manager)

    udm = orchestrator.analyze(str(project_dir))

    assert udm.projectName == "demo"
    assert udm.summary.totalFiles >= 1
    assert udm.summary.totalLinesOfCode > 0
    assert any(unit.path.endswith("module.py") for unit in udm.codeUnits)


def test_java_analyzer_handles_pom(tmp_path: Path) -> None:
    project_dir = tmp_path / "java-demo"
    src_dir = project_dir / "src" / "main" / "java" / "example"
    src_dir.mkdir(parents=True)
    (project_dir / "pom.xml").write_text(
        """
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>demo</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-context</artifactId>
      <version>5.3.0</version>
    </dependency>
  </dependencies>
</project>
""",
        encoding="utf-8",
    )
    (src_dir / "App.java").write_text(
        "package example;\npublic class App {\n  public static void main(String[] args) {\n    System.out.println(\"hi\");\n  }\n}\n",
        encoding="utf-8",
    )

    manager = PluginManager()
    manager.register(JavaAnalyzer())
    orchestrator = AnalysisOrchestrator(plugin_manager=manager)

    udm = orchestrator.analyze(str(project_dir))

    assert udm.projectName == "java-demo"
    assert udm.summary.totalFiles == 1
    assert any(dep.name.startswith("com.example:demo") or dep.name.startswith("org.springframework") for dep in udm.dependencies)
