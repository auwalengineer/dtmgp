<script setup lang="ts">
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, RefreshCw, Search } from "@lucide/vue";
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ReportActions from "@/components/ReportActions.vue";
import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";
import ItemTabs from "../shared/ItemTabs.vue";
import {
  HR_REPORTS, compareCells, formatCell, hrReportOptionsSchema, hrReportSchema, isNumeric, isoDate, startOfYear,
  type HrReport, type HrReportOptions, type ReportColumn,
} from "./hrReports";

const session = useSessionStore();
const route = useRoute();
const PAGE_SIZE = 100;

const byId = Object.fromEntries(HR_REPORTS.map((report) => [report.id, report]));
const activeId = ref(String(route.params.item || "") in byId ? String(route.params.item) : HR_REPORTS[0].id);
watch(() => route.params.item, (item) => { if (item && String(item) in byId) activeId.value = String(item); });
const definition = computed(() => byId[activeId.value]);

const params = reactive({ department: "", status: "Active", group_by: "department", dimension: "grade_level", leave_group: "leave_type", months: 24, from_date: startOfYear(), to_date: isoDate() });
const options = ref<HrReportOptions | null>(null);
const report = ref<HrReport | null>(null);
const loading = ref(false);
const error = ref("");
const search = ref("");
const page = ref(1);
const sort = ref<{ key: string; direction: "asc" | "desc" } | null>(null);
let requestNumber = 0;

/** The parameters this report actually uses, as sent to the API and the CSV export. */
const requestParams = computed(() => {
  const used = definition.value.filters;
  const values: Record<string, string> = {};
  if (used.includes("department") && params.department) values.department = params.department;
  if (used.includes("status")) values.status = params.status;
  if (used.includes("group_by")) values.group_by = params.group_by;
  if (used.includes("leave_group")) values.group_by = params.leave_group;
  if (used.includes("dimension")) values.dimension = params.dimension;
  if (used.includes("months")) values.months = String(params.months);
  if (used.includes("period")) { values.from_date = params.from_date; values.to_date = params.to_date; }
  return values;
});

async function loadOptions() {
  try {
    options.value = hrReportOptionsSchema.parse(await apiRequest(`/api/method/dtmgp.api.v1.hr.get_hr_report_options?company=${encodeURIComponent(session.activeLga)}`));
    params.group_by = options.value.is_statewide ? "lga" : "department";
    if (!options.value.departments.some((item) => item.value === params.department)) params.department = "";
  } catch { options.value = null; }
}

async function loadReport() {
  const current = ++requestNumber;
  loading.value = true;
  error.value = "";
  try {
    const query = new URLSearchParams({ report: definition.value.report, company: session.activeLga, ...requestParams.value });
    const result = hrReportSchema.parse(await apiRequest(`/api/method/dtmgp.api.v1.hr.get_hr_report?${query}`));
    if (current === requestNumber) { report.value = result; page.value = 1; }
  } catch (reason) {
    if (current === requestNumber) { report.value = null; error.value = reason instanceof Error ? reason.message : "Unable to load the report"; }
  } finally {
    if (current === requestNumber) loading.value = false;
  }
}

watch(() => session.activeLga, async () => { await loadOptions(); await loadReport(); }, { immediate: true });
watch([activeId, requestParams], () => { if (options.value) loadReport(); }, { deep: true });
watch(activeId, () => { search.value = ""; sort.value = null; });
watch(search, () => { page.value = 1; });

const filteredRows = computed(() => {
  const rows = report.value?.rows ?? [];
  const term = search.value.trim().toLowerCase();
  const matching = term ? rows.filter((row) => Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(term))) : rows;
  if (!sort.value) return matching;
  const { key, direction } = sort.value;
  return [...matching].sort((a, b) => (direction === "asc" ? 1 : -1) * compareCells(a[key], b[key]));
});
const pageCount = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / PAGE_SIZE)));
const visibleRows = computed(() => filteredRows.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE));

function toggleSort(column: ReportColumn) {
  const current = sort.value?.key === column.key ? sort.value.direction : null;
  // Numbers sort largest-first on the first click, text A-Z.
  const first = isNumeric(column.type) ? "desc" : "asc";
  sort.value = current === null ? { key: column.key, direction: first } : current === first ? { key: column.key, direction: first === "asc" ? "desc" : "asc" } : null;
}
function ariaSort(column: ReportColumn) {
  if (sort.value?.key !== column.key) return "none";
  return sort.value.direction === "asc" ? "ascending" : "descending";
}

const exportColumns = computed(() => report.value?.columns.map((column) => column.label) ?? []);
const printRows = computed(() => {
  if (!report.value) return [];
  const format = (row: Record<string, unknown>) => report.value!.columns.map((column) => formatCell(row[column.key], column.type));
  return [...filteredRows.value.map(format), ...(report.value.totals ? [format(report.value.totals)] : [])];
});
const printFilters = computed(() => {
  const labels: Record<string, string | number> = {};
  const used = definition.value.filters;
  const find = (list: { value: string; label: string }[] | undefined, value: string) => list?.find((item) => item.value === value)?.label ?? value;
  if (used.includes("department")) labels.Department = params.department ? find(options.value?.departments, params.department) : "All departments";
  if (used.includes("status")) labels["Employment status"] = params.status === "All" ? "All statuses" : params.status;
  if (used.includes("group_by")) labels["Grouped by"] = find(options.value?.group_by, params.group_by);
  if (used.includes("leave_group")) labels["Grouped by"] = find(options.value?.leave_groups, params.leave_group);
  if (used.includes("dimension")) labels.Dimension = find(options.value?.dimensions, params.dimension);
  if (used.includes("months")) labels.Horizon = `${params.months} months`;
  if (used.includes("period")) labels.Period = `${formatCell(params.from_date, "date")} to ${formatCell(params.to_date, "date")}`;
  if (search.value.trim()) labels.Search = search.value.trim();
  return labels;
});
</script>

<template>
  <ItemTabs :items="HR_REPORTS.map(({ id, label }) => ({ id, label }))" :active-id="activeId" @select="activeId = $event" />

  <section class="hr-report" :aria-busy="loading">
    <header class="hr-report-header">
      <div>
        <h3>{{ definition.label }}</h3>
        <p>{{ definition.description }}</p>
      </div>
      <ReportActions v-if="report" :report-id="`hr.report.${definition.report}`" :title="definition.label" :columns="exportColumns" :rows="printRows" :company="session.activeLga" :filters="printFilters" :export-params="requestParams" />
    </header>

    <form class="hr-report-filters" aria-label="Report filters" @submit.prevent="loadReport">
      <label v-if="definition.filters.includes('group_by')">Group by
        <select v-model="params.group_by"><option v-for="item in options?.group_by" :key="item.value" :value="item.value">{{ item.label }}</option></select>
      </label>
      <label v-if="definition.filters.includes('leave_group')">Group by
        <select v-model="params.leave_group"><option v-for="item in options?.leave_groups" :key="item.value" :value="item.value">{{ item.label }}</option></select>
      </label>
      <label v-if="definition.filters.includes('dimension')">Distribution by
        <select v-model="params.dimension"><option v-for="item in options?.dimensions" :key="item.value" :value="item.value">{{ item.label }}</option></select>
      </label>
      <label v-if="definition.filters.includes('status')">Employment status
        <select v-model="params.status"><option v-for="item in options?.statuses" :key="item" :value="item">{{ item === "All" ? "All statuses" : item }}</option></select>
      </label>
      <label v-if="definition.filters.includes('months')">Horizon
        <select v-model.number="params.months"><option v-for="item in options?.retirement_horizons" :key="item" :value="item">Next {{ item }} months</option></select>
      </label>
      <template v-if="definition.filters.includes('period')">
        <label>From<input v-model="params.from_date" type="date" required :max="params.to_date" /></label>
        <label>To<input v-model="params.to_date" type="date" required :min="params.from_date" /></label>
      </template>
      <label v-if="definition.filters.includes('department')">Department
        <select v-model="params.department"><option value="">All departments</option><option v-for="item in options?.departments" :key="item.value" :value="item.value">{{ item.label }}</option></select>
      </label>
      <button type="submit" class="secondary-action hr-report-refresh" :disabled="loading"><RefreshCw :size="15" /> Refresh</button>
    </form>

    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <p v-else-if="loading && !report" class="users-empty" role="status">Loading report…</p>

    <template v-if="report">
      <section v-if="report.summary.length" class="hr-report-summary" aria-label="Summary">
        <article v-for="item in report.summary" :key="item.label" :class="{ danger: item.tone === 'danger' && Number(item.value) > 0 }">
          <small>{{ item.label }}</small>
          <strong>{{ typeof item.value === "number" ? formatCell(item.value, item.unit === "pct" ? "pct" : "years") : item.value }}</strong>
        </article>
      </section>
      <p v-if="report.note" class="hr-report-note">{{ report.note }}</p>

      <div v-if="definition.listing && report.rows.length > 10" class="hr-report-search">
        <label class="directory-search"><Search :size="16" /><input v-model="search" type="search" placeholder="Search this report" aria-label="Search this report" /></label>
        <span>{{ filteredRows.length.toLocaleString() }} of {{ report.rows.length.toLocaleString() }} rows</span>
      </div>

      <div class="staff-table-wrap">
        <table class="staff-table hr-report-table">
          <thead>
            <tr>
              <th v-for="column in report.columns" :key="column.key" :aria-sort="ariaSort(column)" :class="{ numeric: isNumeric(column.type) }">
                <button type="button" class="hr-report-sort" @click="toggleSort(column)">
                  {{ column.label }}
                  <ArrowUp v-if="sort?.key === column.key && sort.direction === 'asc'" :size="12" aria-hidden="true" />
                  <ArrowDown v-else-if="sort?.key === column.key" :size="12" aria-hidden="true" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in visibleRows" :key="String(row.name ?? row.group ?? index)">
              <td v-for="column in report.columns" :key="column.key" :class="{ numeric: isNumeric(column.type), overdue: column.key === 'timing' && row.timing === 'Overdue' }">{{ formatCell(row[column.key], column.type) }}</td>
            </tr>
          </tbody>
          <tfoot v-if="report.totals && filteredRows.length">
            <tr><td v-for="column in report.columns" :key="column.key" :class="{ numeric: isNumeric(column.type) }">{{ formatCell(report.totals[column.key], column.type) }}</td></tr>
          </tfoot>
        </table>
        <p v-if="!report.rows.length" class="users-empty">No records match this report's filters.</p>
        <p v-else-if="!filteredRows.length" class="users-empty">No rows match “{{ search }}”.</p>
        <footer v-if="pageCount > 1" class="table-footer">
          <span>Rows {{ ((page - 1) * PAGE_SIZE + 1).toLocaleString() }}–{{ Math.min(page * PAGE_SIZE, filteredRows.length).toLocaleString() }} of {{ filteredRows.length.toLocaleString() }}</span>
          <div><button :disabled="page === 1" @click="page -= 1"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }} / {{ pageCount }}</button><button :disabled="page >= pageCount" @click="page += 1">Next <ChevronRight :size="14" /></button></div>
        </footer>
      </div>
    </template>
  </section>
</template>

<style scoped>
.hr-report { display: flex; flex-direction: column; gap: 14px; padding: 16px 20px 20px; }
.hr-report-header { align-items: flex-start; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; }
.hr-report-header h3 { margin: 0; }
.hr-report-header p { color: var(--muted); font-size: .78rem; margin: 4px 0 0; }
.hr-report-filters { align-items: flex-end; display: flex; flex-wrap: wrap; gap: 10px; }
.hr-report-filters label { color: var(--muted); display: flex; flex-direction: column; font-size: .7rem; gap: 4px; }
.hr-report-filters select, .hr-report-filters input { background: #fff; border: 1px solid var(--line); color: var(--text, #1d2a23); font: inherit; font-size: .8rem; height: 38px; min-width: 160px; padding: 0 10px; }
.hr-report-refresh { align-items: center; display: inline-flex; gap: 6px; height: 38px; }
.hr-report-summary { background: var(--line); border: 1px solid var(--line); display: grid; gap: 1px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
.hr-report-summary article { background: #fff; display: flex; flex-direction: column; gap: 4px; padding: 14px 16px; }
.hr-report-summary small { color: var(--muted); font-size: .7rem; }
.hr-report-summary strong { font-family: Georgia, serif; font-size: 1.35rem; font-weight: 500; overflow-wrap: anywhere; }
.hr-report-summary article.danger strong { color: #a4262c; }
.hr-report-note { color: var(--muted); font-size: .74rem; margin: 0; }
.hr-report-search { align-items: center; display: flex; flex-wrap: wrap; gap: 12px; }
.hr-report-search span { color: var(--muted); font-size: .74rem; }
.hr-report-table th.numeric, .hr-report-table td.numeric { font-variant-numeric: tabular-nums; text-align: right; }
.hr-report-table th.numeric .hr-report-sort { justify-content: flex-end; }
.hr-report-sort { align-items: center; background: none; border: 0; color: inherit; cursor: pointer; display: inline-flex; font: inherit; gap: 4px; letter-spacing: inherit; padding: 0; text-align: inherit; text-transform: inherit; width: 100%; }
.hr-report-table td { white-space: nowrap; }
.hr-report-table td.overdue { color: #a4262c; font-weight: 700; }
.hr-report-table tfoot td { background: #f7f9f8; border-top: 2px solid var(--line); font-weight: 700; }
@media (max-width: 760px) {
  .hr-report { padding: 12px; }
  .hr-report-filters label, .hr-report-filters select, .hr-report-filters input { width: 100%; }
}
</style>
