export type EntryType = "directory" | "file";

export interface FilesystemEntry {
  name: string;
  path: string;
  type: EntryType;
}

export interface FilesystemResponse {
  path: string;
  entries: FilesystemEntry[];
}

export interface AnalyzeRequest {
  projectPath: string;
  userId?: string;
}

export interface AnalyzeResponse {
  jobId: string;
}

export type JobStateStatus = "pending" | "running" | "completed" | "failed";

export interface JobStatusResponse {
  status: JobStateStatus;
  progress: number;
  message?: string | null;
  error?: string | null;
}

export interface UserRecord {
  id: string;
  email: string;
  displayName: string;
}

export interface CreateUserPayload {
  email: string;
  displayName: string;
}

export type AnalysisStatus = "pending" | "running" | "completed" | "failed";

export interface ReportSummary {
  jobId: string;
  projectPath: string;
  status: AnalysisStatus;
  summary?: string | null;
  createdAt: string;
  completedAt?: string | null;
}

export interface ReportDetail extends ReportSummary {
  udm?: Record<string, unknown> | null;
}
