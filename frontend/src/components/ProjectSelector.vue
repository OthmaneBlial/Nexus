<script setup lang="ts">
import { computed } from "vue";

import type { FilesystemEntry } from "@/types/api";

const props = defineProps<{
  currentPath: string;
  selectedPath: string;
  entries: FilesystemEntry[];
  loading: boolean;
  error: string | null;
}>();

const emits = defineEmits<{
  (e: "select", entry: FilesystemEntry): void;
  (e: "refresh"): void;
}>();

const WORKSPACE_ROOT = "apps";

const breadcrumbs = computed(() => {
  return [WORKSPACE_ROOT];
});

const visibleEntries = computed(() => {
  const directories = new Map<string, FilesystemEntry>();
  for (const entry of props.entries) {
    if (entry.name.startsWith(".")) continue;
    if (entry.type !== "directory") continue;

    if (entry.path === WORKSPACE_ROOT) {
      continue;
    }

    if (entry.path.startsWith(`${WORKSPACE_ROOT}/`)) {
      const remainder = entry.path.slice(WORKSPACE_ROOT.length + 1);
      const [firstSegment] = remainder.split("/").filter(Boolean);
      if (!firstSegment) continue;
      const normalizedPath = `${WORKSPACE_ROOT}/${firstSegment}`;
      if (!directories.has(normalizedPath)) {
        directories.set(normalizedPath, {
          ...entry,
          name: firstSegment,
          path: normalizedPath,
          type: "directory",
        });
      }
      continue;
    }

    directories.set(entry.path, entry);
  }

  return Array.from(directories.values()).sort((a, b) => a.name.localeCompare(b.name));
});

const sortedEntries = computed(() => {
  return [...visibleEntries.value].sort((a, b) => {
    if (a.type === b.type) {
      return a.name.localeCompare(b.name);
    }
    return a.type === "directory" ? -1 : 1;
  });
});
</script>

<template>
  <section class="surface-card p-4 text-sm">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-[0.4em] text-secondary">Project Source</p>
        <p class="text-base font-semibold text-primary">Filesystem Browser</p>
      </div>
      <div class="flex flex-wrap items-center gap-2 text-xs">
        <button
          class="inline-flex items-center gap-2 rounded-full border border-theme-soft px-3 py-1 text-secondary transition hover:text-primary"
          :disabled="props.loading"
          @click="emits('refresh')"
        >
          <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>
    </header>

    <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-secondary">
      <span class="uppercase tracking-[0.3em] text-primary">{{ breadcrumbs[0] }}</span>
    </div>

    <div class="mt-4 rounded-2xl border border-theme-soft" :style="{ background: 'var(--color-surface-muted)' }">
      <div v-if="loading" class="flex h-72 items-center justify-center">
        <span class="h-7 w-7 animate-spin rounded-full border-2 border-theme-soft border-t-transparent"></span>
      </div>
      <div v-else-if="error" class="flex h-72 flex-col items-center justify-center px-6 text-center text-sm text-secondary">
        <p class="text-base font-semibold text-primary">Unable to load directory</p>
        <p class="mt-2 text-xs text-secondary">{{ error }}</p>
      </div>
      <ul v-else class="max-h-72 space-y-2 overflow-y-auto p-3">
        <li
          v-for="entry in sortedEntries"
          :key="`${entry.type}-${entry.path}`"
          class="rounded-2xl border border-theme-soft bg-transparent transition hover:border-theme hover:shadow-sm"
          :style="
            entry.type === 'directory' && entry.path === props.selectedPath
              ? { borderColor: 'var(--color-chip-border)', background: 'var(--color-chip-bg)' }
              : {}
          "
        >
          <div class="flex items-center justify-between gap-3 px-3 py-2">
            <button class="flex flex-1 items-center gap-3 text-left" type="button" @click="emits('select', entry)">
              <span
                class="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-theme-soft text-secondary"
                :style="
                  entry.type === 'directory'
                    ? { background: 'var(--color-chip-bg)', color: 'var(--color-chip-text)', borderColor: 'var(--color-chip-border)' }
                    : { background: 'transparent' }
                "
              >
                {{ entry.type === "directory" ? "DIR" : "FILE" }}
              </span>
              <div>
                <p class="text-sm font-medium text-primary">{{ entry.name }}</p>
                <p class="text-[11px] uppercase tracking-[0.4em] text-secondary">{{ entry.type }}</p>
              </div>
            </button>
            <div class="flex items-center gap-2">
              <button
                v-if="entry.type === 'directory'"
                class="hidden rounded-full border border-theme-soft px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-secondary transition hover:text-primary sm:inline-flex"
                type="button"
                @click.stop="emits('select', entry)"
              >
                Select
              </button>
              <button
                v-if="entry.type === 'directory'"
                class="inline-flex h-7 w-7 items-center justify-center rounded-full border border-theme-soft text-secondary transition hover:text-primary sm:hidden"
                type="button"
                @click.stop="emits('select', entry)"
              >
                <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </li>
        <li
          v-if="sortedEntries.length === 0"
          class="rounded-xl border border-dashed border-theme-soft px-3 py-6 text-center text-xs uppercase tracking-[0.35em] text-secondary"
        >
          Drop projects into apps/ to get started
        </li>
      </ul>
    </div>
  </section>
</template>
