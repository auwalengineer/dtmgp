<script setup lang="ts">
import { ArrowDown, ArrowUp, BadgeCheck, Briefcase, CalendarClock, CircleAlert, Fingerprint, Hourglass, RefreshCw, UsersRound, Venus } from "@lucide/vue";
import { computed, onMounted, ref } from "vue";

import ReportActions from "@/components/ReportActions.vue";
import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import BarList from "./BarList.vue";
import StackedBarList from "./StackedBarList.vue";
import {
  formatMetric, percent, scopeAverage, workforceSummarySchema,
  type BreakdownRow, type ComparisonMetric, type ComparisonRow, type MetricKey, type WorkforceSummary,
} from "./workforce";

const session = useSessionStore();
// "" = every LGA the caller may see; the server re-derives that scope (ADR-003).
const company = ref("");
const summary = ref<WorkforceSummary | null>(null);
const loading = ref(true);
const error = ref("");

// --- LGA comparison state
const compareMetric = ref<MetricKey>("active");
const hideEmpty = ref(false);
const sortKey = ref<MetricKey | "label">("active");
const sortDesc = ref(true);
const TABLE_COLUMNS: { key: MetricKey; label: string; unit: ComparisonMetric["unit"] }[] = [
  { key: "active", label: "Active", unit: "count" },
  { key: "share_pct", label: "Share", unit: "pct" },
  { key: "verified_pct", label: "Verified", unit: "pct" },
  { key: "female_pct", label: "Female", unit: "pct" },
  { key: "average_age", label: "Avg age", unit: "years" },
  { key: "average_service", label: "Avg service (yrs)", unit: "years" },
  { key: "management_pct", label: "GL 13+", unit: "pct" },
  { key: "retiring_12m", label: "Retiring 12m", unit: "count" },
  { key: "past_retirement", label: "Past retirement", unit: "count" },
  { key: "joined_this_year", label: "Appointed this yr", unit: "count" },
  { key: "bvn_pct", label: "BVN", unit: "pct" },
  { key: "nin_pct", label: "NIN", unit: "pct" },
  { key: "photo_pct", label: "Photo", unit: "pct" },
  { key: "bank_pct", label: "Bank", unit: "pct" },
];

const lgaChoices = computed(() => (session.canChangeLga ? session.allowedLgas : []));
const scopeLabel = computed(() => {
  if (company.value) return shortLga(company.value);
  if (summary.value?.scope.is_statewide) return `All ${summary.value.scope.companies} LGAs in your scope`;
  return session.activeLga ? shortLga(session.activeLga) : "Your LGA";
});
const totals = computed(() => summary.value?.totals);
const breakdowns = computed(() => summary.value?.breakdowns);
const comparison = computed(() => summary.value?.lga_comparison ?? []);
const showComparison = computed(() => comparison.value.length > 1);
const comparisonRows = computed(() => comparison.value.filter((row) => !hideEmpty.value || row.total > 0));
const lgasWithoutStaff = computed(() => comparison.value.filter((row) => !row.active).length);
const metric = computed(() => summary.value?.comparison_metrics.find((item) => item.key === compareMetric.value) ?? { key: "active", label: "Active staff", unit: "count" as const });
const metricAverage = computed(() => scopeAverage(comparison.value, compareMetric.value, metric.value.unit));
const rankedRows = computed(() => {
  const rows = comparisonRows.value.map((row) => ({ label: row.label, value: row[compareMetric.value] as number | null, hint: row.active ? "" : "no active staff" }));
  return rows.sort((a, b) => (b.value ?? -1) - (a.value ?? -1) || a.label.localeCompare(b.label));
});
const extremes = computed(() => {
  const rows = comparison.value.filter((row) => row.active && row[compareMetric.value] !== null);
  if (rows.length < 2) return null;
  const sorted = [...rows].sort((a, b) => Number(b[compareMetric.value]) - Number(a[compareMetric.value]));
  return { highest: sorted[0], lowest: sorted[sorted.length - 1] };
});
const sortedTable = computed(() => {
  const rows = [...comparisonRows.value];
  const direction = sortDesc.value ? -1 : 1;
  return rows.sort((a, b) => {
    if (sortKey.value === "label") return a.label.localeCompare(b.label) * direction;
    return ((Number(a[sortKey.value] ?? -1) - Number(b[sortKey.value] ?? -1)) || a.label.localeCompare(b.label)) * direction;
  });
});
const gradeSeries = computed(() => Object.keys(comparison.value[0]?.grade_bands ?? {}));
const genderMix = computed(() => comparisonRows.value.map((row) => ({ label: row.label, values: [row.male, row.female] })));
const gradeMix = computed(() => comparisonRows.value.map((row) => ({ label: row.label, values: gradeSeries.value.map((band) => row.grade_bands[band] ?? 0) })));
const comparisonExport = computed(() => ({
  columns: ["LGA", ...TABLE_COLUMNS.map((column) => column.label + (column.unit === "pct" ? " %" : ""))],
  rows: sortedTable.value.map((row) => [row.label, ...TABLE_COLUMNS.map((column) => row[column.key] ?? "")]),
}));
const completenessRows = computed(() => (breakdowns.value?.data_completeness ?? []).map((row) => ({ ...row, hint: `${row.count ?? 0} staff` })));

function shortLga(name: string) { return name.replace(" Local Government Area", " LGA"); }
function columnHeight(rows: BreakdownRow[], value: number) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return `${Math.max((value / max) * 100, value ? 2 : 0)}%`;
}
function sortBy(key: MetricKey | "label") {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value;
  else { sortKey.value = key; sortDesc.value = key !== "label"; }
}
function ariaSort(key: MetricKey | "label") { return sortKey.value === key ? (sortDesc.value ? "descending" : "ascending") : "none"; }
function cell(row: ComparisonRow, column: { key: MetricKey; unit: ComparisonMetric["unit"] }) { return formatMetric(row[column.key] as number | null, column.unit); }

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const query = company.value ? `?company=${encodeURIComponent(company.value)}` : "";
    const data = await apiRequest<unknown>(`/api/method/dtmgp.api.v1.people.get_workforce_dashboard${query}`);
    summary.value = workforceSummarySchema.parse(data);
  } catch (err) {
    summary.value = null;
    error.value = err instanceof Error ? err.message : "Could not load the employee dashboard.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="hr-heading">
    <div>
      <h1>Employee Dashboard</h1>
      <p>Overall workforce picture · {{ scopeLabel }}</p>
    </div>
    <div class="workforce-controls">
      <label v-if="lgaChoices.length > 1" class="workforce-scope">
        <span>LGA</span>
        <select v-model="company" @change="load">
          <option value="">All permitted LGAs</option>
          <option v-for="lga in lgaChoices" :key="lga" :value="lga">{{ shortLga(lga) }}</option>
        </select>
      </label>
      <button class="secondary-action" type="button" :disabled="loading" @click="load"><RefreshCw :size="15" /> Refresh</button>
    </div>
  </section>

  <section v-if="loading && !summary" class="panel loading-panel">Loading workforce dashboard...</section>
  <section v-else-if="error" class="panel loading-panel" role="alert">{{ error }}</section>

  <template v-else-if="summary && totals && breakdowns">
    <section class="hr-metrics workforce-kpis" aria-label="Workforce totals">
      <article>
        <span class="hr-metric-icon green"><UsersRound :size="19" /></span>
        <div><small>Active employees</small><strong>{{ totals.active.toLocaleString() }}</strong><p>{{ totals.total.toLocaleString() }} on record · {{ totals.suspended_or_inactive }} suspended/inactive</p></div>
      </article>
      <article>
        <span class="hr-metric-icon blue"><BadgeCheck :size="19" /></span>
        <div><small>Verified (active)</small><strong>{{ percent(totals.verified, totals.active) }}%</strong><p>{{ totals.verified.toLocaleString() }} verified · {{ totals.pending_verification.toLocaleString() }} pending</p></div>
      </article>
      <article>
        <span class="hr-metric-icon blue"><Venus :size="19" /></span>
        <div><small>Female share (active)</small><strong>{{ percent(totals.female, totals.male + totals.female) }}%</strong><p>{{ totals.female.toLocaleString() }} female · {{ totals.male.toLocaleString() }} male</p></div>
      </article>
      <article>
        <span class="hr-metric-icon gold"><CalendarClock :size="19" /></span>
        <div><small>Average age (active)</small><strong>{{ totals.average_age ?? "—" }}</strong><p>Average service {{ totals.average_service ?? "—" }} years</p></div>
      </article>
      <article>
        <span class="hr-metric-icon gold"><Hourglass :size="19" /></span>
        <div><small>Retiring in 12 months</small><strong>{{ totals.retiring_12m.toLocaleString() }}</strong><p>{{ totals.retiring_5y.toLocaleString() }} within 5 years</p></div>
      </article>
      <article>
        <span class="hr-metric-icon red"><CircleAlert :size="19" /></span>
        <div><small>Active past retirement date</small><strong>{{ totals.past_retirement.toLocaleString() }}</strong><p>{{ totals.past_retirement ? "Review for exit processing" : "None outstanding" }}</p></div>
      </article>
      <article>
        <span class="hr-metric-icon green"><Fingerprint :size="19" /></span>
        <div><small>BVN / NIN captured</small><strong>{{ Math.round(totals.completeness.bvn ?? 0) }}% / {{ Math.round(totals.completeness.nin ?? 0) }}%</strong><p>Photo {{ Math.round(totals.completeness.photo ?? 0) }}% · bank {{ Math.round(totals.completeness.bank ?? 0) }}%</p></div>
      </article>
      <article>
        <span class="hr-metric-icon green"><Briefcase :size="19" /></span>
        <div><small>Appointed this year</small><strong>{{ totals.joined_this_year.toLocaleString() }}</strong><p>{{ totals.left.toLocaleString() }} exited in total</p></div>
      </article>
    </section>

    <!-- LGA comparison (only meaningful with more than one LGA in scope) -->
    <section v-if="showComparison" class="workforce-section" aria-labelledby="lga-comparison-title">
      <header class="workforce-section-header">
        <div>
          <h2 id="lga-comparison-title">LGA comparison</h2>
          <p>{{ comparison.length }} LGAs<template v-if="lgasWithoutStaff"> · <strong class="workforce-flag-text">{{ lgasWithoutStaff }} with no active staff records</strong></template></p>
        </div>
        <label class="workforce-toggle"><input v-model="hideEmpty" type="checkbox" /> Hide LGAs with no staff records</label>
      </header>

      <article class="panel workforce-card wide">
        <header>
          <div><h3>Compare LGAs by</h3><p>Dashed line: average across LGAs with staff{{ metric.unit === "count" ? "" : " (weighted by headcount)" }}</p></div>
          <label class="workforce-scope compact">
            <span class="visually-hidden">Comparison metric</span>
            <select v-model="compareMetric">
              <option v-for="item in summary.comparison_metrics" :key="item.key" :value="item.key">{{ item.label }}</option>
            </select>
          </label>
        </header>
        <p v-if="extremes" class="workforce-extremes">
          <span><ArrowUp :size="13" /> Highest: <strong>{{ extremes.highest.label }}</strong> {{ formatMetric(extremes.highest[compareMetric] as number, metric.unit) }}</span>
          <span><ArrowDown :size="13" /> Lowest: <strong>{{ extremes.lowest.label }}</strong> {{ formatMetric(extremes.lowest[compareMetric] as number, metric.unit) }}</span>
        </p>
        <BarList :rows="rankedRows" :percent="metric.unit === 'pct'" :decimals="metric.unit === 'count' ? undefined : 1" :unit="metric.label"
          :reference="metricAverage === null ? null : { value: metricAverage, label: 'Average' }" />
      </article>

      <article class="panel workforce-card wide">
        <header>
          <div><h3>LGA comparison table</h3><p>Select a column heading to sort. Percentages are of each LGA's active staff.</p></div>
          <ReportActions report-id="hr.lga-comparison" title="LGA workforce comparison" :columns="comparisonExport.columns" :rows="comparisonExport.rows" :company="company || undefined" />
        </header>
        <div class="staff-table-wrap">
          <table class="staff-table workforce-table">
            <thead>
              <tr>
                <th :aria-sort="ariaSort('label')"><button type="button" @click="sortBy('label')">LGA</button></th>
                <th v-for="column in TABLE_COLUMNS" :key="column.key" :aria-sort="ariaSort(column.key)">
                  <button type="button" @click="sortBy(column.key)">{{ column.label }}<template v-if="column.unit === 'pct'"> %</template><span v-if="sortKey === column.key" aria-hidden="true">{{ sortDesc ? " ▼" : " ▲" }}</span></button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in sortedTable" :key="row.company" :class="{ 'workforce-empty-row': !row.active }">
                <th scope="row">{{ row.label }}</th>
                <td v-for="column in TABLE_COLUMNS" :key="column.key" :class="{ 'workforce-alert-cell': column.key === 'past_retirement' && row.past_retirement > 0 }">{{ cell(row, column) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <div class="workforce-grid">
        <article class="panel workforce-card"><header><div><h3>Gender mix by LGA</h3><p>Active staff · male / female</p></div></header><StackedBarList :series="['Male', 'Female']" :rows="genderMix" /></article>
        <article class="panel workforce-card"><header><div><h3>Grade band mix by LGA</h3><p>Active staff · {{ gradeSeries.map((band) => band.split(' ')[0]).join(' / ') }}</p></div></header><StackedBarList :series="gradeSeries" :rows="gradeMix" /></article>
      </div>
    </section>

    <section class="workforce-section" aria-labelledby="distribution-title">
      <header class="workforce-section-header"><div><h2 id="distribution-title">Workforce distribution</h2><p>{{ scopeLabel }}</p></div></header>
      <div class="workforce-grid">
        <article v-if="!showComparison && breakdowns.lga.length" class="panel workforce-card"><header><div><h3>Active staff</h3><p>Outer bar: active · inner bar: verified</p></div></header><BarList :rows="breakdowns.lga.map((row) => ({ label: row.label, value: row.value, secondary: row.verified }))" unit="active" secondary-label="verified" /></article>
        <article class="panel workforce-card"><header><div><h3>Staff by status</h3><p>All records</p></div></header><BarList :rows="breakdowns.status" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Verification status</h3><p>Active staff</p></div></header><BarList :rows="breakdowns.verification" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Gender</h3><p>Active staff</p></div></header><BarList :rows="breakdowns.gender" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Grade band</h3><p>Active staff by cadre</p></div></header><BarList :rows="breakdowns.grade_band" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Age band</h3><p>Active staff with a date of birth</p></div></header><BarList :rows="breakdowns.age_band" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Years of service</h3><p>From date of 1st appointment (or date joined)</p></div></header><BarList :rows="breakdowns.service_band" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Records completeness</h3><p>% of active staff with each item captured</p></div></header><BarList :rows="completenessRows" percent :decimals="1" unit="of active staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Salary mode</h3><p>Active staff</p></div></header><BarList :rows="breakdowns.salary_mode" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Grade level</h3><p>Active staff</p></div></header><BarList :rows="breakdowns.grade_level" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Departments</h3><p>Top departments by active staff</p></div></header><BarList :rows="breakdowns.department" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Designations</h3><p>Top designations by active staff</p></div></header><BarList :rows="breakdowns.designation" unit="staff" /></article>
        <article class="panel workforce-card"><header><div><h3>Ranks</h3><p>Top ranks by active staff</p></div></header><BarList :rows="breakdowns.rank" unit="staff" /></article>

        <article v-for="series in [
          { key: 'retirements', title: 'Retirements due by year', note: 'Active staff, by date of retirement', rows: breakdowns.retirements_by_year },
          { key: 'appointments', title: 'Appointments by year', note: 'Date of first appointment, last 10 years', rows: breakdowns.appointments_by_year },
        ]" :key="series.key" class="panel workforce-card">
          <header><div><h3>{{ series.title }}</h3><p>{{ series.note }}</p></div></header>
          <ol class="year-columns" :aria-label="series.title">
            <li v-for="row in series.rows" :key="row.label" :title="`${row.label}: ${row.value}`" :class="{ overdue: row.label === 'Overdue' }">
              <span class="year-value">{{ row.value }}</span>
              <span class="year-track" aria-hidden="true"><span class="year-fill" :style="{ height: columnHeight(series.rows, row.value) }" /></span>
              <span class="year-label">{{ row.label }}</span>
            </li>
          </ol>
        </article>
      </div>
    </section>
  </template>
</template>

<style scoped>
.workforce-controls { align-items: flex-end; display: flex; gap: 10px; }
.workforce-scope { color: var(--muted); display: flex; flex-direction: column; font-size: .72rem; gap: 4px; }
.workforce-scope select { min-width: 220px; }
.workforce-scope.compact select { min-width: 200px; }
.workforce-controls .secondary-action { align-items: center; display: inline-flex; gap: 6px; }
.workforce-kpis { grid-template-columns: repeat(4, 1fr); }
.workforce-section { margin-bottom: 24px; }
.workforce-section-header { align-items: flex-end; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; margin-bottom: 12px; }
.workforce-section-header h2 { font-family: Georgia, serif; font-size: 1.35rem; font-weight: 500; margin: 0; }
.workforce-section-header p { color: var(--muted); font-size: .76rem; margin: 4px 0 0; }
.workforce-flag-text { color: var(--red); font-weight: 600; }
.workforce-toggle { align-items: center; color: var(--muted); display: inline-flex; font-size: .76rem; gap: 6px; }
.workforce-grid { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.workforce-card { margin-bottom: 16px; min-width: 0; padding: 18px 20px; }
.workforce-grid .workforce-card { margin-bottom: 0; }
.workforce-card header { align-items: flex-start; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; margin-bottom: 12px; }
.workforce-card h3 { font-size: 1rem; margin: 0; }
.workforce-card header p { color: var(--muted); font-size: .72rem; margin: 3px 0 0; }
.workforce-extremes { color: var(--muted); display: flex; flex-wrap: wrap; font-size: .76rem; gap: 18px; margin: 0 0 10px; }
.workforce-extremes span { align-items: center; display: inline-flex; gap: 4px; }
.workforce-extremes strong { color: var(--ink); }
.workforce-table th button { background: none; border: 0; color: inherit; cursor: pointer; font: inherit; font-weight: 600; padding: 0; text-align: left; white-space: nowrap; }
.workforce-table td, .workforce-table th { font-variant-numeric: tabular-nums; white-space: nowrap; }
.workforce-table tbody th { background: none; border-top: 1px solid var(--line); color: var(--ink); font-size: .8rem; font-weight: 600; letter-spacing: normal; text-align: left; text-transform: none; }
.workforce-empty-row { color: var(--muted); }
.workforce-alert-cell { color: var(--red); font-weight: 700; }
.visually-hidden { clip: rect(0 0 0 0); height: 1px; overflow: hidden; position: absolute; width: 1px; }
.year-columns { align-items: end; display: grid; gap: 4px; grid-auto-columns: minmax(0, 1fr); grid-auto-flow: column; height: 180px; list-style: none; margin: 0; padding: 0; }
.year-columns li { align-items: center; display: flex; flex-direction: column; gap: 4px; height: 100%; justify-content: flex-end; min-width: 0; }
.year-track { align-items: flex-end; display: flex; flex: 1; justify-content: center; width: 100%; }
.year-fill { background: var(--blue); border-radius: 4px 4px 0 0; max-width: 28px; width: 70%; }
.year-columns li.overdue .year-fill { background: var(--red); }
.year-columns li:hover .year-fill { filter: brightness(.85); }
.year-value { font-size: .7rem; font-variant-numeric: tabular-nums; }
.year-label { color: var(--muted); font-size: .66rem; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1100px) { .workforce-kpis { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 860px) {
  .workforce-grid { grid-template-columns: 1fr; }
  .workforce-kpis { grid-template-columns: 1fr; }
  .workforce-controls { flex-wrap: wrap; width: 100%; }
  .workforce-scope, .workforce-scope select { min-width: 0; width: 100%; }
  .year-label { font-size: .58rem; }
}
</style>
