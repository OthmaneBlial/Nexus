from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CodeUnitType(str, Enum):
    FILE = "FILE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    INTERFACE = "INTERFACE"


class DependencyType(str, Enum):
    DIRECT = "DIRECT"
    TRANSITIVE = "TRANSITIVE"


class ConnectionType(str, Enum):
    CALL = "CALL"
    IMPORT = "IMPORT"
    INHERITANCE = "INHERITANCE"
    IMPLEMENTATION = "IMPLEMENTATION"


class CodeUnitMetrics(BaseModel):
    loc: Optional[int] = None
    complexity: Optional[float] = None
    comment_lines: Optional[int] = Field(default=None, alias="commentLines")

    model_config = {"populate_by_name": True}


class CodeUnit(BaseModel):
    id: str
    type: CodeUnitType
    path: str
    metrics: CodeUnitMetrics = Field(default_factory=CodeUnitMetrics)


class Dependency(BaseModel):
    id: str
    name: str
    version: Optional[str] = None
    type: DependencyType = DependencyType.DIRECT
    license: Optional[str] = None
    vulnerabilities: List[str] = Field(default_factory=list)


class Connection(BaseModel):
    sourceUnitId: str
    targetUnitId: str
    type: ConnectionType


class Summary(BaseModel):
    totalFiles: int = 0
    totalLinesOfCode: int = 0
    avgComplexity: float = 0.0
    dependencyCount: int = 0


class UnifiedDataModel(BaseModel):
    nexusVersion: str = "1.0.0"
    projectName: str
    languages: List[str] = Field(default_factory=list)
    analysisTimestamp: datetime
    summary: Summary = Field(default_factory=Summary)
    codeUnits: List[CodeUnit] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}
