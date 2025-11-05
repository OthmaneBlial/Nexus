<script setup lang="ts">
import { computed, ref, watch } from "vue";

import DependencyGraph from "@/components/DependencyGraph.vue";
import CodeStructureTreemap from "@/components/CodeStructureTreemap.vue";
import MetricsCards from "@/components/MetricsCards.vue";
import type { UnifiedDataModel } from "@/types/udm";

const props = defineProps<{
  udm: UnifiedDataModel | null;
  loading: boolean;
}>();

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "structure", label: "Code Structure" },
  { id: "dependencies", label: "Dependencies" },
  { id: "raw", label: "Raw Data" },
] as const;

const activeTab = ref<(typeof tabs)[number]["id"]>(tabs[0].id);

const dependencyStats = computed(() => {
  const deps = props.udm?.dependencies ?? [];
  const direct = deps.filter((dep) => dep.type === "DIRECT").length;
  const transitive = deps.length - direct;
  return {
    total: deps.length,
    direct,
    transitive,
  };
});

const codeUnitStats = computed(() => ({
  files: props.udm?.summary.totalFiles ?? 0,
  units: props.udm?.codeUnits.length ?? 0,
  relationships: props.udm?.connections.length ?? 0,
}));

watch(
  () => props.udm,
  () => {
    activeTab.value = tabs[0].id;
  },
);
</script>

<template>
  <div class="space-y-6">
    <div v-if="loading" class="surface-card p-16 text-center">
      <div class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-theme-soft border-t-transparent"></div>
      <p class="mt-4 text-sm font-medium text-secondary">Processing Nexus analysis…</p>
    </div>

    <div
      v-else-if="!udm"
      class="surface-card border-dashed border-theme-soft p-12 text-center text-sm text-secondary"
    >
      <p class="text-base font-semibold text-primary">Run the analysis to unlock insights.</p>
      <p class="mt-2 text-secondary">
        Choose a directory in the control center, trigger the engine, and results will appear here in real time.
      </p>
    </div>

    <template v-else>
      <section class="surface-card p-6 text-primary">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.4em] text-secondary">Dashboard</p>
            <h2 class="text-2xl font-semibold text-primary">{{ udm.projectName }}</h2>
            <p class="text-sm text-secondary">{{ udm.languages.join(", ") }}</p>
          </div>
          <div class="grid gap-3 text-xs text-secondary sm:grid-cols-2 lg:text-right">
            <div>
              <p class="uppercase tracking-[0.3em] text-secondary">Analyzed</p>
              <p class="mt-1 text-base font-semibold text-primary">{{ new Date(udm.analysisTimestamp).toLocaleString() }}</p>
            </div>
            <div>
              <p class="uppercase tracking-[0.3em] text-secondary">Nexus Version</p>
              <p class="mt-1 text-base font-semibold text-primary">{{ udm.nexusVersion }}</p>
            </div>
          </div>
        </div>
      </section>

      <div class="surface-card p-4 text-sm">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab-button px-4 py-2 text-sm font-semibold"
            :class="activeTab === tab.id ? 'tab-button--active' : ''"
            type="button"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="mt-6 space-y-6">
          <div v-if="activeTab === 'overview'" class="space-y-6">
            <MetricsCards :summary="udm.summary" :languages="udm.languages" :analysis-timestamp="udm.analysisTimestamp" />

            <div class="grid gap-4 md:grid-cols-2">
              <div class="surface-panel p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Code Units</p>
                <div class="mt-3 grid grid-cols-3 gap-3 text-center text-sm">
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ codeUnitStats.files.toLocaleString() }}</p>
                    <p class="text-xs text-secondary">Files</p>
                  </div>
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ codeUnitStats.units.toLocaleString() }}</p>
                    <p class="text-xs text-secondary">Units</p>
                  </div>
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ codeUnitStats.relationships.toLocaleString() }}</p>
                    <p class="text-xs text-secondary">Links</p>
                  </div>
                </div>
              </div>
              <div class="surface-panel p-4">
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Dependencies</p>
                <div class="mt-3 grid grid-cols-3 gap-3 text-center text-sm">
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ dependencyStats.total }}</p>
                    <p class="text-xs text-secondary">Total</p>
                  </div>
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ dependencyStats.direct }}</p>
                    <p class="text-xs text-secondary">Direct</p>
                  </div>
                  <div>
                    <p class="text-2xl font-semibold text-primary">{{ dependencyStats.transitive }}</p>
                    <p class="text-xs text-secondary">Transitive</p>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <div v-if="activeTab === 'structure'" class="space-y-4">
            <div class="surface-panel p-4 text-sm text-secondary">
              Navigate the treemap to understand how LOC and complexity are distributed across the repo.
            </div>
            <CodeStructureTreemap :code-units="udm.codeUnits" />
          </div>

          <div v-if="activeTab === 'dependencies'" class="space-y-4">
            <div class="surface-panel p-4 text-sm text-secondary">
              Visualize direct and transitive dependencies, then drill into the list for metadata.
            </div>
            <DependencyGraph :dependencies="udm.dependencies" />
            <div class="surface-panel p-4">
              <div class="grid gap-3 sm:grid-cols-2">
                <div
                  v-for="dep in udm.dependencies"
                  :key="dep.id"
                  class="rounded-2xl border border-theme-soft bg-transparent p-4 text-sm transition hover:border-theme hover:shadow-sm"
                >
                  <p class="text-base font-semibold text-primary">{{ dep.name }}</p>
                  <p class="text-xs text-secondary">{{ dep.type }} · {{ dep.version ?? "unknown" }}</p>
                  <p v-if="dep.license" class="mt-2 text-xs text-secondary">License: {{ dep.license }}</p>
                  <p v-if="dep.vulnerabilities?.length" class="mt-1 text-xs text-rose-600">
                    Vulnerabilities: {{ dep.vulnerabilities.join(", ") }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'raw'" class="space-y-4">
            <div class="surface-panel p-4 text-sm text-secondary">
              Full Unified Data Model payload for debugging and integrations.
            </div>
            <pre class="max-h-[32rem] overflow-auto rounded-2xl border border-theme-soft bg-transparent p-4 text-xs text-primary"><code>{{ JSON.stringify(udm, null, 2) }}</code></pre>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
