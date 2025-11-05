<script setup lang="ts">
import type { ReportSummary } from "@/types/api";

const props = defineProps<{
  reports: ReportSummary[];
  loading: boolean;
}>();

const emits = defineEmits<{
  (e: "view", jobId: string): void;
}>();

function statusBadgeClass(status: ReportSummary["status"]) {
  switch (status) {
    case "completed":
      return "status-pill status-pill--success";
    case "failed":
      return "status-pill status-pill--failed";
    case "running":
      return "status-pill status-pill--running";
    default:
      return "status-pill";
  }
}
</script>

<template>
  <section class="surface-card p-4 text-sm">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-[0.4em] text-secondary">History</p>
        <p class="text-lg font-semibold text-primary">Recent Analyses</p>
      </div>
    </header>
    <div class="mt-3">
      <div v-if="props.loading" class="flex h-28 items-center justify-center text-xs text-secondary">
        Loading history…
      </div>
      <div v-else-if="!props.reports.length" class="rounded-xl border border-dashed border-theme-soft px-4 py-6 text-center text-xs uppercase tracking-[0.4em] text-secondary">
        No analyses yet
      </div>
      <ul v-else class="space-y-3">
        <li
          v-for="report in props.reports.slice(0, 5)"
          :key="report.jobId"
          class="rounded-2xl border border-theme-soft bg-[var(--color-surface)] p-4 transition hover:border-theme hover:shadow-sm"
        >
          <button class="grid w-full gap-2 text-left md:grid-cols-[minmax(0,1fr)_auto]" type="button" @click="emits('view', report.jobId)">
            <div>
              <p class="text-sm font-semibold text-primary clamp-1">{{ report.projectPath }}</p>
              <p class="text-xs text-secondary">{{ new Date(report.createdAt).toLocaleString() }}</p>
              <p v-if="report.summary" class="mt-2 text-xs text-secondary clamp-2">{{ report.summary }}</p>
            </div>
            <span class="inline-flex h-max items-center justify-center gap-2 rounded-full px-3 py-1 text-[11px] font-semibold uppercase" :class="statusBadgeClass(report.status)">
              <span class="h-1.5 w-1.5 rounded-full bg-current"></span>
              {{ report.status }}
            </span>
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>
