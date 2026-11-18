<script setup lang="ts">
import { computed } from "vue";

/**
 * Horizontal bar list: one row per category, value always printed beside the bar,
 * so the list doubles as the accessible table view (no colour-only encoding).
 * Optional: `secondary` inner bar (e.g. verified within active), `percent` values on
 * a fixed 0-100 scale, and a `reference` marker (e.g. the state average).
 */
type Row = { label: string; value: number | null; secondary?: number; hint?: string; highlight?: boolean };
const props = defineProps<{
  rows: Row[];
  unit?: string;
  secondaryLabel?: string;
  emptyText?: string;
  percent?: boolean;
  decimals?: number;
  reference?: { value: number; label: string } | null;
}>();

const max = computed(() => (props.percent ? 100 : Math.max(1, ...props.rows.map((row) => row.value ?? 0), props.reference?.value ?? 0)));
function width(value: number | null) { return `${Math.max(((value ?? 0) / max.value) * 100, value ? 1.5 : 0)}%`; }
function format(value: number | null) {
  if (value === null) return "—";
  const text = props.decimals !== undefined ? value.toFixed(props.decimals) : value.toLocaleString();
  return props.percent ? `${text}%` : text;
}
// A reference (e.g. an average) is usually fractional even when the rows are counts.
function formatReference(value: number) {
  const text = Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1);
  return props.percent ? `${text}%` : text;
}
function tooltip(row: Row) {
  const base = `${row.label}: ${format(row.value)} ${props.unit || ""}`.trim();
  const secondary = row.secondary === undefined ? base : `${base} · ${row.secondary.toLocaleString()} ${props.secondaryLabel || ""}`.trim();
  return row.hint ? `${secondary} (${row.hint})` : secondary;
}
</script>

<template>
  <p v-if="!rows.length" class="users-empty">{{ emptyText || "No records in scope yet." }}</p>
  <template v-else>
    <p v-if="reference" class="bar-list-reference-note"><span class="bar-list-reference-swatch" aria-hidden="true" /> {{ reference.label }}: {{ formatReference(reference.value) }}</p>
    <ol class="bar-list">
      <li v-for="row in rows" :key="row.label" :title="tooltip(row)" :class="{ highlight: row.highlight }">
        <span class="bar-list-label">{{ row.label }}</span>
        <span class="bar-list-track" aria-hidden="true">
          <span class="bar-list-fill" :class="{ solid: row.secondary === undefined }" :style="{ width: width(row.value) }" />
          <span v-if="row.secondary !== undefined" class="bar-list-fill secondary" :style="{ width: width(row.secondary) }" />
          <span v-if="reference" class="bar-list-reference" :style="{ left: width(reference.value) }" />
        </span>
        <span class="bar-list-value">
          {{ format(row.value) }}<small v-if="row.secondary !== undefined"> / {{ row.secondary.toLocaleString() }}</small><small v-if="row.hint"> {{ row.hint }}</small>
        </span>
      </li>
    </ol>
  </template>
</template>

<style scoped>
.bar-list { display: grid; gap: 6px; list-style: none; margin: 0; padding: 0; }
.bar-list li { align-items: center; display: grid; font-size: .78rem; gap: 10px; grid-template-columns: minmax(90px, 30%) 1fr auto; }
.bar-list li.highlight .bar-list-label { color: var(--green-900); font-weight: 700; }
.bar-list-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-list-track { height: 14px; position: relative; }
.bar-list-fill { background: var(--green-100); border-radius: 0 4px 4px 0; box-shadow: inset 0 0 0 1px var(--green-700); height: 100%; left: 0; position: absolute; top: 0; }
.bar-list-fill.solid { background: var(--green-700); box-shadow: none; }
.bar-list-fill.secondary { background: var(--green-700); box-shadow: none; height: 60%; top: 20%; }
.bar-list-reference { border-left: 2px dashed var(--ink); bottom: -3px; position: absolute; top: -3px; }
.bar-list li:hover .bar-list-label { color: var(--green-900); font-weight: 600; }
.bar-list-value { font-variant-numeric: tabular-nums; min-width: 3ch; text-align: right; white-space: nowrap; }
.bar-list-value small { color: var(--muted); margin-left: 4px; }
.bar-list-reference-note { align-items: center; color: var(--muted); display: flex; font-size: .72rem; gap: 6px; margin: 0 0 8px; }
.bar-list-reference-swatch { border-left: 2px dashed var(--ink); display: inline-block; height: 12px; }
</style>
