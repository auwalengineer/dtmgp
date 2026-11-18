<script setup lang="ts">
/**
 * 100%-stacked horizontal bars: the composition of each row (e.g. gender or grade
 * band mix per LGA), so LGAs of very different sizes compare fairly. Counts are
 * printed beside each bar and in tooltips, and a legend names every series, so
 * identity never depends on colour alone.
 */
const props = defineProps<{ series: string[]; rows: { label: string; values: number[] }[]; emptyText?: string }>();

// Fixed series order (never cycled): blue, gold, green.
const COLORS = ["var(--blue)", "var(--gold)", "var(--green-700)"];
function total(values: number[]) { return values.reduce((sum, value) => sum + value, 0); }
function share(value: number, values: number[]) { const sum = total(values); return sum ? (value / sum) * 100 : 0; }
function tooltip(row: { label: string; values: number[] }) {
  return `${row.label}: ` + props.series.map((name, index) => `${name} ${row.values[index]} (${Math.round(share(row.values[index], row.values))}%)`).join(" · ");
}
</script>

<template>
  <ul class="stacked-legend" aria-label="Legend">
    <li v-for="(name, index) in series" :key="name"><span :style="{ background: COLORS[index] }" aria-hidden="true" />{{ name }}</li>
  </ul>
  <p v-if="!rows.length" class="users-empty">{{ emptyText || "No records in scope yet." }}</p>
  <ol v-else class="stacked-list">
    <li v-for="row in rows" :key="row.label" :title="tooltip(row)">
      <span class="stacked-label">{{ row.label }}</span>
      <span class="stacked-track" aria-hidden="true">
        <template v-for="(value, index) in row.values" :key="index">
          <span v-if="value" class="stacked-segment" :style="{ width: `${share(value, row.values)}%`, background: COLORS[index] }" />
        </template>
        <span v-if="!total(row.values)" class="stacked-empty">No active staff</span>
      </span>
      <span class="stacked-values">{{ row.values.join(" / ") }}</span>
    </li>
  </ol>
</template>

<style scoped>
.stacked-legend { display: flex; flex-wrap: wrap; gap: 14px; list-style: none; margin: 0 0 10px; padding: 0; }
.stacked-legend li { align-items: center; color: var(--muted); display: flex; font-size: .72rem; gap: 6px; }
.stacked-legend span { display: inline-block; height: 10px; width: 14px; }
.stacked-list { display: grid; gap: 6px; list-style: none; margin: 0; padding: 0; }
.stacked-list li { align-items: center; display: grid; font-size: .78rem; gap: 10px; grid-template-columns: minmax(90px, 30%) 1fr auto; }
.stacked-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stacked-track { background: var(--line); display: flex; gap: 2px; height: 14px; overflow: hidden; position: relative; }
.stacked-segment { height: 100%; }
.stacked-segment:last-of-type { border-radius: 0 4px 4px 0; }
.stacked-empty { color: var(--muted); font-size: .64rem; left: 6px; line-height: 14px; position: absolute; }
.stacked-values { color: var(--muted); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
</style>
