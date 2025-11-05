<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

import UserSelector from "@/components/UserSelector.vue";
import ProjectSelector from "@/components/ProjectSelector.vue";
import AnalysisPanel from "@/components/AnalysisPanel.vue";
import HistoryPanel from "@/components/HistoryPanel.vue";
import DashboardView from "@/components/DashboardView.vue";
import type { FilesystemEntry, JobStateStatus, ReportSummary, UserRecord } from "@/types/api";
import type { UnifiedDataModel } from "@/types/udm";
import {
  browseFilesystem,
  fetchJobStatus,
  fetchReport,
  fetchReportDetail,
  fetchReportsForUser,
  listUsers,
  registerUser,
  triggerAnalysis,
} from "@/api/client";

const entries = ref<FilesystemEntry[]>([]);
const WORKSPACE_ROOT = "apps";
const currentPath = ref(WORKSPACE_ROOT);
const analysisPath = ref(WORKSPACE_ROOT);
const isLoadingEntries = ref(false);
const filesystemError = ref<string | null>(null);

const USER_STORAGE_KEY = "nexus.selectedUserId";
const initialUserId = typeof window !== "undefined" ? window.localStorage.getItem(USER_STORAGE_KEY) : null;
const users = ref<UserRecord[]>([]);
const selectedUserId = ref<string | null>(initialUserId);
const isLoadingUsers = ref(false);
const reports = ref<ReportSummary[]>([]);
const isLoadingReports = ref(false);

const jobId = ref<string | null>(null);
const jobStatus = reactive({
  status: "pending" as JobStateStatus,
  progress: 0,
  message: "Idle" as string | null,
  error: null as string | null,
});

const udm = ref<UnifiedDataModel | null>(null);
const isSubmittingAnalysis = ref(false);
const isSidebarOpen = ref(false);
let pollHandle: number | null = null;

const isJobActive = computed(
  () => (jobStatus.status === "running" || jobStatus.status === "pending") && jobId.value !== null,
);
const isUnsupportedPath = computed(() => {
  const path = analysisPath.value;
  if (!path || path === ".") return false;
  return path.split("/").some((segment) => segment === ".git");
});
const analysisWarning = computed(() => {
  if (isUnsupportedPath.value) {
    return "Git metadata directories are not supported. Select a project root instead.";
  }
  return null;
});
const canAnalyze = computed(() => !isSubmittingAnalysis.value && !isJobActive.value && !isUnsupportedPath.value);
const statusBadgeClass = computed(() => {
  switch (jobStatus.status) {
    case "completed":
      return "status-pill status-pill--success";
    case "running":
      return "status-pill status-pill--running";
    case "failed":
      return "status-pill status-pill--failed";
    default:
      return "status-pill";
  }
});

const activeUser = computed(() => users.value.find((user) => user.id === selectedUserId.value) ?? null);
const roundedJobProgress = computed(() => Math.min(100, Math.max(0, Math.round(jobStatus.progress))));

function prettifyPath(path: string | null | undefined): string {
  if (!path || path === ".") {
    return "apps";
  }
  return path;
}

const displayAnalysisPath = computed(() => prettifyPath(analysisPath.value));
const displayCurrentPath = computed(() => prettifyPath(currentPath.value));
const displayJobMessage = computed(() => {
  const message = jobStatus.message?.trim();
  if (!message) {
    return "No updates yet.";
  }
  return message;
});

type ThemeMode = "light" | "dark";
const THEME_STORAGE_KEY = "nexus.theme";
const storedTheme =
  typeof window !== "undefined" ? (window.localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null) : null;
const theme = ref<ThemeMode>(storedTheme ?? "light");

function applyTheme(value: ThemeMode) {
  if (typeof document === "undefined") return;
  document.body.classList.remove("theme-dark", "theme-light");
  document.body.classList.add(`theme-${value}`);
}

watch(
  theme,
  (value) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(THEME_STORAGE_KEY, value);
    }
    applyTheme(value);
  },
  { immediate: true },
);

function toggleTheme() {
  theme.value = theme.value === "dark" ? "light" : "dark";
}

const themeIcon = computed(() => (theme.value === "dark" ? "☀️" : "🌙"));

function openSidebar() {
  isSidebarOpen.value = true;
}

function closeSidebar() {
  isSidebarOpen.value = false;
}

function closeSidebarIfMobile() {
  if (typeof window === "undefined") return;
  if (window.matchMedia("(max-width: 1023px)").matches) {
    closeSidebar();
  }
}

async function loadDirectory(path?: string, options: { updateSelection?: boolean } = {}): Promise<boolean> {
  const { updateSelection = true } = options;
  isLoadingEntries.value = true;
  filesystemError.value = null;
  let succeeded = true;
  try {
    const targetPath = path && path.trim().length ? path : WORKSPACE_ROOT;
    const response = await browseFilesystem(targetPath);
    entries.value = response.entries;
    currentPath.value = response.path || targetPath;
    if (updateSelection) {
      analysisPath.value = response.path || targetPath;
    }
  } catch (error) {
    filesystemError.value = error instanceof Error ? error.message : "Failed to browse filesystem.";
    succeeded = false;
  } finally {
    isLoadingEntries.value = false;
  }
  return succeeded;
}

function selectEntry(entry: FilesystemEntry) {
  if (entry.type === "directory") {
    analysisPath.value = entry.path;
    jobStatus.message = `Selected ${prettifyPath(entry.path)} for analysis`;
    jobStatus.error = null;
  }
}

function handleSetTarget(entry: FilesystemEntry) {
  if (entry.type !== "directory") return;
  analysisPath.value = entry.path;
  jobStatus.message = `Selected ${prettifyPath(entry.path)} for analysis`;
  jobStatus.error = null;
}

function refreshDirectory() {
  loadDirectory(currentPath.value, { updateSelection: false });
}

function persistSelectedUser() {
  if (typeof window === "undefined") return;
  if (selectedUserId.value) {
    window.localStorage.setItem(USER_STORAGE_KEY, selectedUserId.value);
  } else {
    window.localStorage.removeItem(USER_STORAGE_KEY);
  }
}

async function loadUsers() {
  isLoadingUsers.value = true;
  try {
    const results = await listUsers();
    users.value = results;
    const firstUser = users.value[0];
    if (!users.value.length) {
      selectedUserId.value = null;
      persistSelectedUser();
    } else if (!selectedUserId.value || !users.value.some((user) => user.id === selectedUserId.value)) {
      selectedUserId.value = firstUser ? firstUser.id : null;
      persistSelectedUser();
    }
  } catch (error) {
    jobStatus.error = error instanceof Error ? error.message : "Failed to load users.";
    jobStatus.message = "User management error";
  } finally {
    isLoadingUsers.value = false;
  }
  await loadReports();
}

async function loadReports() {
  if (!selectedUserId.value) {
    reports.value = [];
    isLoadingReports.value = false;
    return;
  }
  isLoadingReports.value = true;
  try {
    reports.value = await fetchReportsForUser(selectedUserId.value);
  } catch (error) {
    jobStatus.error = error instanceof Error ? error.message : "Failed to load reports.";
    jobStatus.message = "History retrieval error";
  } finally {
    isLoadingReports.value = false;
  }
}

async function handleSelectUser(userId: string) {
  selectedUserId.value = userId;
  persistSelectedUser();
  await loadReports();
}

async function handleCreateUser(payload: { email: string; displayName: string }) {
  try {
    const user = await registerUser(payload);
    await loadUsers();
    selectedUserId.value = user.id;
    persistSelectedUser();
    await loadReports();
  } catch (error) {
    jobStatus.error = error instanceof Error ? error.message : "Failed to create user.";
    jobStatus.message = "User creation failed";
  }
}

async function viewHistoricalReport(jobIdentifier: string) {
  clearPolling();
  try {
    const detail = await fetchReportDetail(jobIdentifier);
    if (detail.udm && typeof detail.udm === "object") {
      udm.value = detail.udm as unknown as UnifiedDataModel;
      jobId.value = detail.jobId;
      jobStatus.status = "completed";
      jobStatus.progress = 100;
      jobStatus.message = "Historical report loaded";
      jobStatus.error = null;
    } else {
      jobStatus.status = "pending";
      jobStatus.progress = 0;
      jobStatus.message = "Report payload unavailable";
    }
  } catch (error) {
    jobStatus.status = "failed";
    jobStatus.error = error instanceof Error ? error.message : "Failed to load report.";
  } finally {
    closeSidebarIfMobile();
  }
}

async function startAnalysis() {
  if (!canAnalyze.value) {
    if (isUnsupportedPath.value) {
      jobStatus.message = "Select a supported directory";
      jobStatus.error = "Git metadata directories are excluded from analysis.";
    }
    return;
  }
  isSubmittingAnalysis.value = true;
  jobStatus.status = "pending";
  jobStatus.progress = 0;
  jobStatus.message = "Queued for analysis";
  jobStatus.error = null;
  udm.value = null;

  try {
    const response = await triggerAnalysis({
      projectPath: analysisPath.value,
      userId: selectedUserId.value || undefined,
    });
    jobId.value = response.jobId;
    beginPolling();
    if (selectedUserId.value) {
      void loadReports();
    }
  } catch (error) {
    jobStatus.status = "failed";
    jobStatus.error = error instanceof Error ? error.message : "Failed to start analysis.";
  } finally {
    isSubmittingAnalysis.value = false;
    closeSidebarIfMobile();
  }
}

function beginPolling() {
  if (!jobId.value) return;
  clearPolling();
  pollHandle = window.setInterval(async () => {
    if (!jobId.value) return;
    try {
      const status = await fetchJobStatus(jobId.value);
      jobStatus.status = status.status;
      jobStatus.progress = status.progress;
      jobStatus.message = status.message ?? null;
      jobStatus.error = status.error ?? null;

      if (status.status === "completed") {
        clearPolling();
        try {
          const report = await fetchReport(jobId.value);
          udm.value = report;
          if (selectedUserId.value) {
            void loadReports();
          }
        } catch (error) {
          jobStatus.status = "failed";
          jobStatus.error = error instanceof Error ? error.message : "Failed to fetch analysis report.";
        }
      } else if (status.status === "failed") {
        clearPolling();
        if (selectedUserId.value) {
          void loadReports();
        }
      }
    } catch (error) {
      clearPolling();
      jobStatus.status = "failed";
      jobStatus.error = error instanceof Error ? error.message : "Failed to retrieve job status.";
    }
  }, 1500);
}

function clearPolling() {
  if (pollHandle !== null) {
    window.clearInterval(pollHandle);
    pollHandle = null;
  }
}

onMounted(() => {
  void loadUsers();
  loadDirectory(WORKSPACE_ROOT);
});

onBeforeUnmount(() => {
  clearPolling();
});
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="hero-banner border-b border-theme-soft">
      <div class="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between lg:hidden">
          <button
            class="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-theme-soft bg-transparent text-primary"
            aria-label="Open sidebar"
            @click="openSidebar"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h10" />
            </svg>
          </button>
          <span :class="statusBadgeClass" class="px-3 py-1 text-[11px]">
            {{ jobStatus.status }}
          </span>
        </div>

        <div class="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div class="flex items-center gap-3 rounded-2xl border border-theme-soft bg-[var(--color-surface)] px-3 py-2 text-xs">
            <svg class="h-6 w-6 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.35em] text-secondary">User</p>
              <p class="text-sm font-semibold text-primary">{{ activeUser ? activeUser.displayName : "Not selected" }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3 rounded-2xl border border-theme-soft bg-[var(--color-surface)] px-3 py-2 text-xs">
            <svg class="h-6 w-6 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 7.5A1.5 1.5 0 014.5 6h6.55a1.5 1.5 0 01.948.339l2.501 2.001H19.5A1.5 1.5 0 0121 9.84V18a2 2 0 01-2 2H5a2 2 0 01-2-2V7.5z" />
            </svg>
              <div class="flex-1">
                <p class="text-[10px] font-semibold uppercase tracking-[0.35em] text-secondary">Target</p>
                <p class="mt-1 text-sm font-semibold text-primary clamp-1">{{ displayAnalysisPath }}</p>
                <p class="mt-1 text-[11px] text-secondary clamp-1">Browsing: {{ displayCurrentPath }}</p>
              </div>
          </div>
          <div class="flex items-center gap-3 rounded-2xl border border-theme-soft bg-[var(--color-surface)] px-3 py-2 text-xs">
            <svg class="h-6 w-6 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 18a6 6 0 110-12 6 6 0 010 12z" />
            </svg>
            <div class="flex-1">
              <p class="text-[10px] font-semibold uppercase tracking-[0.35em] text-secondary">Status</p>
              <p class="text-sm font-semibold text-primary capitalize">{{ jobStatus.status }}</p>
              <p class="mt-1 text-[11px] text-secondary clamp-1">{{ displayJobMessage }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3 rounded-2xl border border-theme-soft bg-[var(--color-surface)] px-3 py-2 text-xs">
            <svg class="h-6 w-6 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m6-4a10 10 0 11-20 0 10 10 0 0120 0z" />
            </svg>
            <div class="flex-1">
              <div class="flex items-center justify-between text-[10px] font-semibold uppercase tracking-[0.3em] text-secondary">
                <span>Progress</span>
                <span>{{ roundedJobProgress }}%</span>
              </div>
              <div class="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--color-border-soft)]">
                <div class="h-full rounded-full bg-gradient-to-r from-sky-500 via-indigo-500 to-cyan-500 transition-all" :style="{ width: `${roundedJobProgress}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="relative flex w-full flex-1 overflow-hidden">
      <transition name="fade">
        <div
          v-if="isSidebarOpen"
          class="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm lg:hidden"
          @click="closeSidebar"
        />
      </transition>

      <aside
        class="fixed inset-y-0 left-0 z-30 flex w-full max-w-xs transform flex-col border-r border-theme-soft px-4 py-6 shadow-2xl transition-transform duration-200 lg:static lg:z-0 lg:max-w-sm lg:translate-x-0"
        :style="{ background: 'var(--color-bg)' }"
        :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
      >
        <div class="mb-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="chip-brand">Nexus</span>
              <span class="hidden text-sm font-semibold text-primary lg:inline">Universal Software Analysis</span>
            </div>
            <button class="rounded-full border border-theme-soft p-2 text-primary lg:hidden" aria-label="Close sidebar" @click="closeSidebar">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
              </svg>
            </button>
          </div>
          <div class="flex items-center justify-between gap-2 text-xs">
            <button
              class="inline-flex h-8 w-8 items-center justify-center rounded-full border border-theme-soft bg-transparent text-primary"
              type="button"
              @click="toggleTheme"
            >
              {{ themeIcon }}
            </button>
            <span :class="statusBadgeClass" class="px-3 py-1 text-[11px]">
              {{ jobStatus.status }}
            </span>
          </div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.35em] text-secondary">Control Center</p>
        </div>
        <div class="flex h-full flex-col gap-6 overflow-y-auto pr-2">
          <UserSelector
            :users="users"
            :selected-user-id="selectedUserId"
            :loading="isLoadingUsers"
            @select="handleSelectUser"
            @create="handleCreateUser"
          />
          <ProjectSelector
            :current-path="currentPath"
            :selected-path="analysisPath"
            :entries="entries"
            :loading="isLoadingEntries"
            :error="filesystemError"
            @select="selectEntry"
            @refresh="refreshDirectory"
            @set-target="handleSetTarget"
          />
          <AnalysisPanel
            :target-path="analysisPath"
            :can-analyze="canAnalyze"
            :job-id="jobId"
            :job-status="jobStatus.status"
            :progress="jobStatus.progress"
            :message="jobStatus.message"
            :error="jobStatus.error"
            :is-submitting="isSubmittingAnalysis"
            :warning="analysisWarning"
            @analyze="startAnalysis"
          />
          <HistoryPanel :reports="reports" :loading="isLoadingReports" @view="viewHistoricalReport" />
        </div>
      </aside>

      <main class="flex-1 overflow-y-auto">
        <div class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-10">
          <DashboardView :udm="udm" :loading="isJobActive && !udm" />
        </div>
      </main>
    </div>

  </div>
</template>
