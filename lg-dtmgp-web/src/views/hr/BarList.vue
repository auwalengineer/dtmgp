<script setup lang="ts">
import { computed } from "vue";

/**
 * Horizontal bar list: one row per category, value always printed beside the bar,
 * so the list doubles as the accessible table view (no colour-only encoding).
 * An optional `secondary` value is drawn as an inner bar (e.g. verified within active).
 */
const props = defineProps<{
  rows: { label: string; value: number; secondary?: number }[];
  unit?: string;
  secondaryLabel?: string;
  emptyText?: string;
}>();

const max = computed(() => Math.max(1, ...props.rows.map((row) => row.value)));
function width(value: number) { return `${Math.max((value / max.value) * 100, value ? 1.5 : 0)}%`; }
function tooltip(row: { label: string; value: number; secondary?: number }) {
  const base = `${row.label}: ${row.value.toLocaleString()} ${props.unit || ""}`.trim();
  return row.secondary === undefined ? base : `${base} · ${row.secondary.toLocaleString()} ${props.secondaryLabel || ""}`.trim();
}
</script>

<template>
  <p v-if="!rows.length" class="users-empty">{{ emptyText || "No records in scope yet." }}</p>
  <ol v-else class="bar-list">
    <li v-for="row in rows" :key="row.label" :title="tooltip(row)">
      <span class="bar-list-label">{{ row.label }}</span>
      <span class="bar-list-track" aria-hidden="true">
        <span class="bar-list-fill" :style="{ width: width(row.value) }" />
        <span v-if="row.secondary !== undefined" class="bar-list-fill secondary" :style="{ width: width(row.secondary) }" />
      </span>
      <span class="bar-list-value">
        {{ row.value.toLocaleString() }}<small v-if="row.secondary !== undefined"> / {{ row.secondary.toLocaleString() }}</small>
      </span>
    </li>
  </ol>
</template>
