import type {
  AnalyzeRequest,
  AnalyzeResponse,
  FilesystemResponse,
  JobStatusResponse,
  UserRecord,
  CreateUserPayload,
  ReportSummary,
  ReportDetail,
} from "@/types/api";
import type { UnifiedDataModel } from "@/types/udm";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function buildUrl(path: string): string {
  if (!API_BASE) {
    return path;
  }
  if (API_BASE.startsWith("http://") || API_BASE.startsWith("https://")) {
    return `${API_BASE}${path}`;
  }
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildUrl(path), {
    headers: {
      "Content-Type": "application/json",
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function browseFilesystem(path?: string): Promise<FilesystemResponse> {
  const params = new URLSearchParams();
  if (path && path !== "." && path.trim().length > 0) {
    params.set("path", path);
  }
  const qs = params.toString();
  return request<FilesystemResponse>(`/api/filesystem${qs ? `?${qs}` : ""}`);
}

export async function triggerAnalysis(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(`/api/status/${jobId}`);
}

export async function fetchReport(jobId: string): Promise<UnifiedDataModel> {
  return request<UnifiedDataModel>(`/api/report/${jobId}`);
}

export async function listUsers(): Promise<UserRecord[]> {
  return request<UserRecord[]>("/api/users");
}

export async function registerUser(payload: CreateUserPayload): Promise<UserRecord> {
  return request<UserRecord>("/api/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchReportsForUser(userId: string): Promise<ReportSummary[]> {
  return request<ReportSummary[]>(`/api/reports/user/${userId}`);
}

export async function fetchReportDetail(jobId: string): Promise<ReportDetail> {
  return request<ReportDetail>(`/api/reports/${jobId}`);
}
