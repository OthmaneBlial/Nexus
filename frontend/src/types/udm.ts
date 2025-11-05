export type CodeUnitType = "FILE" | "CLASS" | "FUNCTION" | "INTERFACE";
export type DependencyType = "DIRECT" | "TRANSITIVE";
export type ConnectionType = "CALL" | "IMPORT" | "INHERITANCE" | "IMPLEMENTATION";

export interface CodeUnitMetrics {
  loc?: number | null;
  complexity?: number | null;
  commentLines?: number | null;
}

export interface CodeUnit {
  id: string;
  type: CodeUnitType;
  path: string;
  metrics: CodeUnitMetrics;
}

export interface Dependency {
  id: string;
  name: string;
  version?: string | null;
  type: DependencyType;
  license?: string | null;
  vulnerabilities?: string[] | null;
}

export interface Connection {
  sourceUnitId: string;
  targetUnitId: string;
  type: ConnectionType;
}

export interface Summary {
  totalFiles: number;
  totalLinesOfCode: number;
  avgComplexity: number;
  dependencyCount: number;
}

export interface UnifiedDataModel {
  nexusVersion: string;
  projectName: string;
  languages: string[];
  analysisTimestamp: string;
  summary: Summary;
  codeUnits: CodeUnit[];
  dependencies: Dependency[];
  connections: Connection[];
}
