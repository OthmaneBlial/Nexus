<script setup lang="ts">
import { computed, ref } from "vue";

import type { UserRecord } from "@/types/api";

const props = defineProps<{
  users: UserRecord[];
  selectedUserId: string | null;
  loading: boolean;
}>();

const emits = defineEmits<{
  (e: "select", userId: string): void;
  (e: "create", payload: { email: string; displayName: string }): void;
}>();

const email = ref("");
const displayName = ref("");
const showForm = ref(false);

const hasUsers = computed(() => props.users.length > 0);

function toggleForm() {
  showForm.value = !showForm.value;
}

function handleSelect(userId: string) {
  emits("select", userId);
}

function submitForm() {
  if (!email.value.trim() || !displayName.value.trim()) return;
  emits("create", { email: email.value.trim(), displayName: displayName.value.trim() });
  email.value = "";
  displayName.value = "";
  showForm.value = false;
}
</script>

<template>
  <section class="surface-card p-4 text-sm">
    <header class="flex items-start justify-between gap-3">
      <div>
        <p class="text-[10px] font-semibold uppercase tracking-[0.4em] text-secondary">User Context</p>
        <p class="mt-1 text-lg font-semibold text-primary">Active Analyst</p>
        <p class="text-xs text-secondary">Analyses, history, and access control are scoped per user.</p>
      </div>
      <button
        class="rounded-full border border-theme-soft px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-secondary transition hover:text-primary"
        type="button"
        @click="toggleForm"
      >
        {{ showForm ? "Close" : "New" }}
      </button>
    </header>

    <div class="mt-4 space-y-3">
      <div
        v-if="props.loading"
        class="flex items-center gap-2 rounded-xl border border-theme-soft bg-transparent px-3 py-2 text-xs text-secondary"
      >
        <span class="h-3 w-3 animate-spin rounded-full border-2 border-theme-soft border-t-transparent"></span>
        Loading users…
      </div>

      <template v-else>
        <p
          v-if="!hasUsers"
          class="rounded-xl border border-dashed border-theme-soft bg-transparent px-3 py-2 text-xs uppercase tracking-[0.3em] text-secondary"
        >
          No users yet · Create one to get started.
        </p>

        <ul v-else class="space-y-2">
          <li v-for="user in props.users" :key="user.id">
            <button
              class="flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left transition"
              :class="[
                user.id === props.selectedUserId
                  ? 'border-theme-soft'
                  : 'border-theme-soft hover:border-theme',
              ]"
              :style="user.id === props.selectedUserId ? { background: 'var(--color-chip-bg)', borderColor: 'var(--color-chip-border)' } : { background: 'transparent' }"
              type="button"
              @click="handleSelect(user.id)"
            >
              <div>
                <p class="text-sm font-semibold text-primary">{{ user.displayName }}</p>
                <p class="text-xs text-secondary">{{ user.email }}</p>
              </div>
              <svg
                v-if="user.id === props.selectedUserId"
                class="h-4 w-4 text-primary"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </li>
        </ul>
      </template>
    </div>

    <transition name="fade">
      <form v-if="showForm" class="mt-4 space-y-3 rounded-2xl border border-theme-soft bg-transparent p-4" @submit.prevent="submitForm">
        <label class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Email</label>
        <input
          v-model="email"
          type="email"
          class="w-full rounded-xl border border-theme-soft px-3 py-2 text-sm text-primary placeholder:text-secondary focus:outline-none"
          :style="{ background: 'var(--color-surface)' }"
          placeholder="analyst@nexus.dev"
          required
        />
        <label class="text-xs font-semibold uppercase tracking-[0.3em] text-secondary">Display Name</label>
        <input
          v-model="displayName"
          type="text"
          class="w-full rounded-xl border border-theme-soft px-3 py-2 text-sm text-primary placeholder:text-secondary focus:outline-none"
          :style="{ background: 'var(--color-surface)' }"
          placeholder="Analyst Name"
          required
        />
        <button
          class="w-full rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 px-4 py-2 text-sm font-semibold uppercase tracking-[0.3em] text-white transition hover:opacity-90 disabled:opacity-30"
          type="submit"
          :disabled="!email.trim() || !displayName.trim()"
        >
          Create User
        </button>
      </form>
    </transition>
  </section>
</template>
