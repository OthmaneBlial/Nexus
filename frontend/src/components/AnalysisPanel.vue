<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    targetPath: string;
    canAnalyze: boolean;
    jobId: string | null;
    jobStatus: string;
    progress: number;
    message: string | null;
    error: string | null;
    isSubmitting: boolean;
    warning?: string | null;
  }>(),
  {
    progress: 0,
    warning: null,
  },
);

const emits = defineEmits<{
  (e: "analyze"): void;
}>();

const statusCopy = computed(() => {
  switch (props.jobStatus) {
    case "completed":
      return { label: "Completed", className: "status-pill status-pill--success" };
    case "running":
      return { label: "Running", className: "status-pill status-pill--running" };
    case "failed":
      return { label: "Failed", className: "status-pill status-pill--failed" };
    default:
      return { label: "Pending", className: "status-pill" };
  }
});

const roundedProgress = computed(() => Math.min(100, Math.max(0, Math.round(props.progress))));
const displayTargetPath = computed(() => (props.targetPath && props.targetPath !== "." ? props.targetPath : "apps"));
</script>

<template>
  <section class="surface-card p-4 text-sm">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-[0.4em] text-secondary">Analysis</p>
        <p class="text-lg font-semibold text-primary">Nexus Engine</p>
        <p class="text-xs text-secondary">Runs against the currently selected directory.</p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-sky-500 to-cyan-400 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white transition hover:opacity-90 disabled:opacity-30"
        type="button"
        :disabled="!props.canAnalyze || props.isSubmitting"
        @click="emits('analyze')"
      >
        {{ props.isSubmitting ? "Starting" : "Run" }}
      </button>
    </header>

    <dl class="mt-4 grid grid-cols-2 gap-3 text-xs text-secondary">
      <div class="rounded-xl border border-theme-soft bg-transparent p-3">
        <dt class="uppercase tracking-[0.3em]">Selected Path</dt>
        <dd class="mt-2 truncate text-sm font-semibold text-primary">{{ displayTargetPath }}</dd>
      </div>
      <div class="rounded-xl border border-theme-soft bg-transparent p-3">
        <dt class="uppercase tracking-[0.3em]">Job Id</dt>
        <dd class="mt-2 truncate text-sm font-semibold text-primary">{{ props.jobId ?? "—" }}</dd>
      </div>
    </dl>

    <div class="mt-4 space-y-3">
      <div class="flex items-center justify-between text-xs">
        <span class="text-secondary">Progress</span>
        <span class="text-primary">{{ roundedProgress }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-bar transition-all" :style="{ width: `${roundedProgress}%` }"></div>
      </div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-secondary">Status</span>
        <span class="inline-flex items-center gap-2 px-3 py-0.5 text-[11px] font-semibold uppercase" :class="statusCopy.className">
          <span class="h-1.5 w-1.5 rounded-full bg-current"></span>
          {{ statusCopy.label }}
        </span>
      </div>
      <p v-if="props.message" class="rounded-xl border border-theme-soft bg-transparent px-3 py-2 text-xs text-secondary">
        {{ props.message }}
      </p>
      <p v-if="props.warning" class="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700">
        {{ props.warning }}
      </p>
      <p v-if="props.error" class="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-600">
        {{ props.error }}
      </p>
    </div>
  </section>
</template>
