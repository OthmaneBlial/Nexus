<script setup lang="ts">
import type { Summary } from "@/types/udm";

defineProps<{
  summary: Summary;
  languages: string[];
  analysisTimestamp: string;
}>();
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Files</p>
      <p class="mt-3 text-3xl font-semibold text-primary">{{ summary.totalFiles.toLocaleString() }}</p>
      <p class="text-xs text-secondary">Analyzed source files</p>
    </div>
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Lines Of Code</p>
      <p class="mt-3 text-3xl font-semibold text-primary">{{ summary.totalLinesOfCode.toLocaleString() }}</p>
      <p class="text-xs text-secondary">Aggregated LOC</p>
    </div>
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Avg Complexity</p>
      <p class="mt-3 text-3xl font-semibold text-primary">{{ summary.avgComplexity.toFixed(2) }}</p>
      <p class="text-xs text-secondary">Cyclomatic complexity (avg)</p>
    </div>
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Dependencies</p>
      <p class="mt-3 text-3xl font-semibold text-primary">{{ summary.dependencyCount }}</p>
      <p class="text-xs text-secondary">Direct + transitive</p>
    </div>
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Languages</p>
      <p class="mt-3 text-lg font-semibold text-primary">{{ languages.join(", ") || "—" }}</p>
      <p class="text-xs text-secondary">Detected during analysis</p>
    </div>
    <div class="surface-panel p-4">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Analysis Timestamp</p>
      <p class="mt-3 text-lg font-semibold text-primary">{{ new Date(analysisTimestamp).toLocaleString() }}</p>
      <p class="text-xs text-secondary">Local timezone</p>
    </div>
  </div>
</template>
