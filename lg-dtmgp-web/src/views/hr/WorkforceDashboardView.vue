<script setup lang="ts">
import { BadgeCheck, CalendarClock, CircleAlert, Hourglass, RefreshCw, UsersRound } from "@lucide/vue";
import { computed, onMounted, ref } from "vue";

import ReportActions from "@/components/ReportActions.vue";
import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import BarList from "./BarList.vue";
import { percent, workforceSummarySchema, type BreakdownRow, type WorkforceSummary } from "./workforce";

const session = useSessionStore();
// "" = every LGA the caller may see; the server re-derives that scope (ADR-003).
const company = ref("");
const summary = ref<WorkforceSummary | null>(null);
const loading = ref(true);
const error = ref("");

const lgaChoices = computed(() => (session.canChangeLga ? session.allowedLgas : []));
const scopeLabel = computed(() => {
  if (company.value) return shortLga(company.value);
  if (summary.value?.scope.is_statewide) return `All ${summary.value.scope.companies} LGAs in your scope`;
  return session.activeLga ? shortLga(session.activeLga) : "Your LGA";
});
const totals = computed(() => summary.value?.totals);
const breakdowns = computed(() => summary.value?.breakdowns);
const lgaRows = computed(() => (breakdowns.value?.lga || []).map((row) => ({ label: row.label, value: row.value, secondary: row.verified })));
const lgaExport = computed(() => ({
  columns: ["LGA", "Active staff", "Verified", "Verified %"],
  rows: (breakdowns.value?.lga || []).map((row) => [row.label, row.value, row.verified, `${percent(row.verified, row.value)}%`]),
}));

function shortLga(name: string) { return name.replace(" Local Government Area", " LGA"); }
function columnHeight(rows: BreakdownRow[], value: number) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return `${Math.max((value / max) * 100, value ? 2 : 0)}%`;
}

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
    <section class="hr-metrics" aria-label="Workforce totals">
      <article>
        <span class="hr-metric-icon green"><UsersRound :size="19" /></span>
        <div><small>Active employees</small><strong>{{ totals.active.toLocaleString() }}</strong><p>{{ totals.total.toLocaleString() }} on record · {{ totals.left.toLocaleString() }} exited</p></div>
      </article>
      <article>
        <span class="hr-metric-icon blue"><BadgeCheck :size="19" /></span>
        <div><small>Verified (active)</small><strong>{{ percent(totals.verified, totals.active) }}%</strong><p>{{ totals.verified.toLocaleString() }} verified · {{ totals.pending_verification.toLocaleString() }} pending</p></div>
      </article>
      <article>
        <span class="hr-metric-icon gold"><Hourglass :size="19" /></span>
        <div><small>Retiring in 12 months</small><strong>{{ totals.retiring_12m.toLocaleString() }}</strong><p v-if="totals.past_retirement" class="workforce-flag"><CircleAlert :size="12" /> {{ totals.past_retirement }} active past retirement date</p><p v-else>None active past retirement date</p></div>
      </article>
      <article>
        <span class="hr-metric-icon red"><CalendarClock :size="19" /></span>
        <div><small>Average age (active)</small><strong>{{ totals.average_age ?? "—" }}</strong><p>{{ totals.joined_this_year.toLocaleString() }} appointed this year</p></div>
      </article>
    </section>

    <section class="workforce-grid">
      <article v-if="summary.scope.is_statewide || breakdowns.lga.length > 1" class="panel workforce-card wide">
        <header>
          <div><h2>Active staff by LGA</h2><p>Outer bar: active staff · inner bar: verified</p></div>
          <ReportActions report-id="hr.workforce-by-lga" title="Active staff by LGA" :columns="lgaExport.columns" :rows="lgaExport.rows" :company="company || undefined" />
        </header>
        <div class="workforce-legend" aria-hidden="true"><span class="swatch" /> Active <span class="swatch secondary" /> Verified</div>
        <BarList :rows="lgaRows" unit="active" secondary-label="verified" />
      </article>

      <article class="panel workforce-card"><header><div><h2>Staff by status</h2><p>All records</p></div></header><BarList :rows="breakdowns.status" unit="staff" /></article>
      <article class="panel workforce-card"><header><div><h2>Verification status</h2><p>Active staff</p></div></header><BarList :rows="breakdowns.verification" unit="staff" /></article>
      <article class="panel workforce-card"><header><div><h2>Gender</h2><p>Active staff</p></div></header><BarList :rows="breakdowns.gender" unit="staff" /></article>
      <article class="panel workforce-card"><header><div><h2>Age band</h2><p>Active staff with a date of birth</p></div></header><BarList :rows="breakdowns.age_band" unit="staff" /></article>
      <article class="panel workforce-card"><header><div><h2>Grade level</h2><p>Active staff</p></div></header><BarList :rows="breakdowns.grade_level" unit="staff" /></article>
      <article class="panel workforce-card"><header><div><h2>Departments</h2><p>Top departments by active staff</p></div></header><BarList :rows="breakdowns.department" unit="staff" /></article>

      <article v-for="series in [
        { key: 'retirements', title: 'Retirements due by year', note: 'Active staff, by date of retirement', rows: breakdowns.retirements_by_year },
        { key: 'appointments', title: 'Appointments by year', note: 'Date of first appointment, last 10 years', rows: breakdowns.appointments_by_year },
      ]" :key="series.key" class="panel workforce-card">
        <header><div><h2>{{ series.title }}</h2><p>{{ series.note }}</p></div></header>
        <ol class="year-columns" :aria-label="series.title">
          <li v-for="row in series.rows" :key="row.label" :title="`${row.label}: ${row.value}`" :class="{ overdue: row.label === 'Overdue' }">
            <span class="year-value">{{ row.value }}</span>
            <span class="year-track" aria-hidden="true"><span class="year-fill" :style="{ height: columnHeight(series.rows, row.value) }" /></span>
            <span class="year-label">{{ row.label }}</span>
          </li>
        </ol>
      </article>
    </section>
  </template>
</template>

<style scoped>
.workforce-controls { align-items: flex-end; display: flex; gap: 10px; }
.workforce-scope { display: flex; flex-direction: column; font-size: .72rem; color: var(--muted); gap: 4px; }
.workforce-scope select { min-width: 220px; }
.workforce-controls .secondary-action { align-items: center; display: inline-flex; gap: 6px; }
.workforce-flag { align-items: center; color: var(--red) !important; display: inline-flex; gap: 4px; }
.workforce-grid { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.workforce-card { padding: 18px 20px; min-width: 0; }
.workforce-card.wide { grid-column: 1 / -1; }
.workforce-card header { align-items: flex-start; display: flex; gap: 12px; justify-content: space-between; margin-bottom: 12px; }
.workforce-card h2 { font-size: 1rem; margin: 0; }
.workforce-card header p { color: var(--muted); font-size: .72rem; margin: 3px 0 0; }
.workforce-legend { align-items: center; color: var(--muted); display: flex; font-size: .72rem; gap: 6px; margin-bottom: 8px; }
.workforce-legend .swatch { background: var(--green-100); border: 1px solid var(--green-700); display: inline-block; height: 10px; width: 14px; }
.workforce-legend .swatch.secondary { background: var(--green-700); margin-left: 8px; }
:deep(.bar-list) { display: grid; gap: 6px; list-style: none; margin: 0; padding: 0; }
:deep(.bar-list li) { align-items: center; display: grid; font-size: .78rem; gap: 10px; grid-template-columns: minmax(90px, 30%) 1fr auto; }
:deep(.bar-list-label) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
:deep(.bar-list-track) { height: 14px; position: relative; }
:deep(.bar-list-fill) { background: var(--green-100); border-radius: 0 4px 4px 0; box-shadow: inset 0 0 0 1px var(--green-700); height: 100%; left: 0; position: absolute; top: 0; }
:deep(.bar-list-fill.secondary) { background: var(--green-700); box-shadow: none; height: 60%; top: 20%; }
:deep(.bar-list-track:not(:has(.secondary)) .bar-list-fill) { background: var(--green-700); box-shadow: none; }
:deep(.bar-list li:hover .bar-list-label) { color: var(--green-900); font-weight: 600; }
:deep(.bar-list-value) { font-variant-numeric: tabular-nums; min-width: 3ch; text-align: right; }
:deep(.bar-list-value small) { color: var(--muted); }
.year-columns { align-items: end; display: grid; gap: 4px; grid-auto-columns: minmax(0, 1fr); grid-auto-flow: column; height: 180px; list-style: none; margin: 0; padding: 0; }
.year-columns li { align-items: center; display: flex; flex-direction: column; gap: 4px; height: 100%; justify-content: flex-end; min-width: 0; }
.year-track { align-items: flex-end; display: flex; flex: 1; justify-content: center; width: 100%; }
.year-fill { background: var(--blue); border-radius: 4px 4px 0 0; max-width: 28px; width: 70%; }
.year-columns li.overdue .year-fill { background: var(--red); }
.year-columns li:hover .year-fill { filter: brightness(.85); }
.year-value { font-size: .7rem; font-variant-numeric: tabular-nums; }
.year-label { color: var(--muted); font-size: .66rem; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 860px) {
  .workforce-grid { grid-template-columns: 1fr; }
  .workforce-controls { flex-wrap: wrap; width: 100%; }
  .workforce-scope, .workforce-scope select { min-width: 0; width: 100%; }
  .year-label { font-size: .58rem; }
}
</style>
