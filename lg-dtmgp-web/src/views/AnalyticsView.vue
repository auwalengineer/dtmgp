<script setup lang="ts">
import { Activity, AlertTriangle, BarChart3, CalendarRange, Database, Download, ExternalLink, MapPin, Printer, RefreshCw, ShieldCheck } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";
import { formatMetric, scoreLabel, type AlertItem, type Dashboard, type MapPoint, type Metric, type Scorecard, type TrendMonth } from "./analytics/types";

const route = useRoute();
const session = useSessionStore();
const dashboard = ref<Dashboard | null>(null);
const scorecards = ref<Scorecard[]>([]);
const trends = ref<TrendMonth[]>([]);
const alerts = ref<AlertItem[]>([]);
function printReport() { window.print(); }
const points = ref<MapPoint[]>([]);
const loading = ref(true);
const error = ref("");
const fromDate = ref(`${new Date().getFullYear()}-01-01`);
const toDate = ref(new Date().toISOString().slice(0, 10));
const exportOpen = ref(false);
const exportPurpose = ref("");
const exporting = ref(false);

const section = computed(() => String(route.params.section || "overview"));
const mode = computed(() => ({ "lga-performance": "performance", "domain-analytics": "domains", "geographic-view": "maps", "alerts-early-warnings": "alerts", "executive-reports": "reports", interoperability: "interoperability" }[section.value] || "overview"));
const title = computed(() => ({ overview: "Executive overview", performance: "LGA performance", domains: "Domain analytics", maps: "Geographic view", alerts: "Alerts & early warnings", reports: "Executive reports", interoperability: "Interoperability" }[mode.value]));
const domainGroups = computed(() => Object.entries((dashboard.value?.metrics || []).reduce<Record<string, Metric[]>>((groups, metric) => {
  (groups[metric.domain] ||= []).push(metric); return groups;
}, {})));
const maxTrend = computed(() => Math.max(1, ...trends.value.flatMap(item => [item.projects, item.returns])));
const scopeQuery = () => new URLSearchParams({ company: session.activeLga, from_date: fromDate.value, to_date: toDate.value });
const mapLink = (point: MapPoint) => `https://www.openstreetmap.org/?mlat=${point.latitude}&mlon=${point.longitude}#map=15/${point.latitude}/${point.longitude}`;
const shortLga = (company: string) => company.replace(" Local Government Area", " LGA");
const stamp = (value: string | null) => value ? new Date(value).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" }) : "No records";

async function load() {
  if (!session.activeLga) return;
  loading.value = true; error.value = "";
  try {
    const query = scopeQuery();
    const calls: Promise<unknown>[] = [
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.analytics.get_dashboard?${query}`).then(value => { dashboard.value = value; }),
      apiRequest<{ months: TrendMonth[] }>(`/api/method/dtmgp.api.v1.analytics.get_trends?company=${encodeURIComponent(session.activeLga)}`).then(value => { trends.value = value.months; }),
      apiRequest<{ items: AlertItem[] }>(`/api/method/dtmgp.api.v1.analytics.get_alerts?company=${encodeURIComponent(session.activeLga)}`).then(value => { alerts.value = value.items; }),
      apiRequest<{ projects: MapPoint[]; inspections: MapPoint[] }>(`/api/method/dtmgp.api.v1.analytics.get_maps?company=${encodeURIComponent(session.activeLga)}`).then(value => { points.value = [...value.projects, ...value.inspections]; }),
    ];
    if (session.canCompareLgas) calls.push(apiRequest<{ rows: Scorecard[] }>(`/api/method/dtmgp.api.v1.analytics.get_scorecards?from_date=${fromDate.value}&to_date=${toDate.value}`).then(value => { scorecards.value = value.rows; }));
    await Promise.all(calls);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load executive analytics"; }
  finally { loading.value = false; }
}

async function exportSummary() {
  exporting.value = true; error.value = "";
  try {
    const result = await apiRequest<{ filename: string; content: string }>("/api/method/dtmgp.api.v1.analytics.export_executive_summary", { method: "POST", body: JSON.stringify({ purpose: exportPurpose.value, company: session.activeLga, from_date: fromDate.value, to_date: toDate.value }) });
    const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([result.content], { type: "text/csv;charset=utf-8" })); link.download = result.filename; link.click(); URL.revokeObjectURL(link.href);
    exportOpen.value = false; exportPurpose.value = "";
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to export summary"; }
  finally { exporting.value = false; }
}

watch([() => session.activeLga, () => route.fullPath], load, { immediate: true });
</script>

<template>
  <section class="analytics-heading"><div><p class="eyebrow">{{ dashboard?.scope || session.activeLga }}</p><h1>{{ title }}</h1><p v-if="dashboard">{{ dashboard.period.label }} · refreshed {{ stamp(dashboard.generated_at) }}</p></div><div class="analytics-heading-actions"><button class="secondary-action" @click="load"><RefreshCw :size="16" /> Refresh</button><button class="secondary-action" @click="printReport"><Printer :size="16" /> Print</button><button class="primary-action" @click="exportOpen = true"><Download :size="16" /> Export</button></div></section>
  <form class="analytics-period panel" @submit.prevent="load"><label><CalendarRange :size="16" /> From<input v-model="fromDate" type="date" required /></label><label>To<input v-model="toDate" type="date" required /></label><button class="secondary-action">Apply period</button><span v-if="dashboard" class="analytics-completeness" :class="dashboard.completeness.percent === 100 ? 'complete' : 'incomplete'"><Database :size="15" /> {{ dashboard.completeness.percent }}% data complete</span></form>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Preparing authorized analytics...</section>
  <template v-else-if="dashboard">
    <section v-if="mode === 'overview'" class="analytics-overview">
      <div class="analytics-kpis"><RouterLink v-for="metric in dashboard.metrics" :key="metric.key" :to="metric.drilldown" class="analytics-kpi"><span>{{ metric.label }}</span><strong>{{ formatMetric(metric) }}</strong><small :class="`freshness-${metric.freshness.status}`">{{ metric.source }} · {{ metric.freshness.status }}</small></RouterLink></div>
      <div class="analytics-grid"><section class="panel"><header class="panel-header"><div><h2>Six-month activity</h2><p>Operational volume, not a performance ranking</p></div><BarChart3 :size="19" /></header><div class="trend-chart"><div v-for="month in trends" :key="month.key" class="trend-column"><div class="trend-bars"><span class="projects" :style="{ height: `${Math.max(4, month.projects / maxTrend * 100)}%` }" :title="`${month.projects} projects`"></span><span class="returns" :style="{ height: `${Math.max(4, month.returns / maxTrend * 100)}%` }" :title="`${month.returns} returns`"></span></div><small>{{ month.label.split(' ')[0] }}</small></div></div><footer class="chart-legend"><span><i class="projects"></i>Projects opened</span><span><i class="returns"></i>Returns submitted</span></footer></section><section class="panel"><header class="panel-header"><div><h2>Priority alerts</h2><p>{{ alerts.length }} active signals in scope</p></div><AlertTriangle :size="19" /></header><div class="analytics-alert-list"><RouterLink v-for="alert in alerts.slice(0, 6)" :key="`${alert.type}-${alert.company}-${alert.title}`" :to="alert.to"><span :class="`alert-severity ${alert.severity.toLowerCase()}`">{{ alert.severity }}</span><div><strong>{{ alert.type }}</strong><small>{{ shortLga(alert.company) }}<template v-if="alert.age_days !== null"> · {{ alert.age_days }} days overdue</template></small></div></RouterLink><p v-if="!alerts.length" class="users-empty">No active alerts in this scope.</p></div></section></div>
    </section>

    <section v-else-if="mode === 'performance'" class="panel"><header class="panel-header"><div><h2>{{ session.canCompareLgas ? 'Statewide comparison' : 'LGA scorecard' }}</h2><p>Incomplete or stale LGAs are explicitly excluded from ranking</p></div><ShieldCheck :size="19" /></header><div v-if="session.canCompareLgas" class="staff-table-wrap"><table class="staff-table analytics-score-table"><thead><tr><th>Rank</th><th>LGA</th><th>Score</th><th>Completeness</th><th>Returns</th><th>Actions</th><th>Projects</th><th>Workforce</th><th>Revenue</th></tr></thead><tbody><tr v-for="row in scorecards" :key="row.company"><td>{{ row.rank || '—' }}</td><td><strong>{{ shortLga(row.company) }}</strong></td><td><span :class="row.score === null ? 'score-unranked' : 'score-ranked'">{{ scoreLabel(row) }}</span></td><td>{{ row.completeness }}%</td><td v-for="key in ['returns','actions','projects','workforce','revenue']" :key="key">{{ row.metrics[key] === null ? 'Missing' : `${row.metrics[key]}%` }}</td></tr></tbody></table></div><div v-else class="analytics-kpis"><RouterLink v-for="metric in dashboard.metrics" :key="metric.key" :to="metric.drilldown" class="analytics-kpi"><span>{{ metric.label }}</span><strong>{{ formatMetric(metric) }}</strong><small>{{ metric.source }}</small></RouterLink></div></section>

    <section v-else-if="mode === 'domains'" class="domain-analytics-grid"><article v-for="[domain, metrics] in domainGroups" :key="domain" class="panel"><header class="panel-header"><div><h2>{{ domain }}</h2><p>Authorized indicators for this period</p></div><Activity :size="18" /></header><RouterLink v-for="metric in metrics" :key="metric.key" :to="metric.drilldown" class="domain-metric"><span>{{ metric.label }}<small>{{ metric.source }}</small></span><strong>{{ formatMetric(metric) }}</strong></RouterLink></article></section>

    <section v-else-if="mode === 'maps'" class="panel"><header class="panel-header"><div><h2>Geocoded operations</h2><p>Projects and inspections with approved coordinates</p></div><MapPin :size="19" /></header><div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Record</th><th>LGA</th><th>Status</th><th>Coordinates</th><th></th></tr></thead><tbody><tr v-for="point in points" :key="point.name"><td><strong>{{ point.label || point.name }}</strong></td><td>{{ shortLga(point.company) }}</td><td>{{ point.status }}</td><td>{{ Number(point.latitude).toFixed(5) }}, {{ Number(point.longitude).toFixed(5) }}</td><td><a class="text-action" :href="mapLink(point)" target="_blank" rel="noreferrer">Map <ExternalLink :size="14" /></a></td></tr></tbody></table><p v-if="!points.length" class="users-empty">No geocoded records are available in this scope.</p></div></section>

    <section v-else-if="mode === 'alerts'" class="panel"><header class="panel-header"><div><h2>Active alerts</h2><p>Prioritized operational exceptions without restricted details</p></div><AlertTriangle :size="19" /></header><div class="analytics-alert-list full"><RouterLink v-for="alert in alerts" :key="`${alert.type}-${alert.company}-${alert.title}`" :to="alert.to"><span :class="`alert-severity ${alert.severity.toLowerCase()}`">{{ alert.severity }}</span><div><strong>{{ alert.type }}</strong><small>{{ alert.title }} · {{ shortLga(alert.company) }}<template v-if="alert.age_days !== null"> · {{ alert.age_days }} days overdue</template></small></div></RouterLink><p v-if="!alerts.length" class="users-empty">No active alerts in this scope.</p></div></section>

    <section v-else-if="mode === 'reports'" class="analytics-grid"><article class="panel executive-summary"><header class="panel-header"><div><h2>Executive summary</h2><p>{{ dashboard.period.label }}</p></div><Download :size="19" /></header><div><p><strong>{{ dashboard.metrics.length }}</strong> authorized KPIs</p><p><strong>{{ alerts.length }}</strong> active alerts</p><p><strong>{{ dashboard.completeness.percent }}%</strong> data completeness</p><button class="primary-action" @click="exportOpen = true"><Download :size="16" /> Export marked CSV</button></div></article><article class="panel"><header class="panel-header"><div><h2>Data quality</h2><p>Sources affecting executive interpretation</p></div><Database :size="19" /></header><div class="data-quality-list"><p v-for="source in dashboard.completeness.sources" :key="source.source"><span>{{ source.source }}</span><strong :class="`freshness-${source.status}`">{{ source.status }}</strong><small>{{ stamp(source.last_updated) }}</small></p></div></article></section>

    <section v-else class="panel"><header class="panel-header"><div><h2>Interoperability status</h2><p>External connections remain disabled pending approved data-sharing agreements</p></div><ShieldCheck :size="19" /></header><div class="integration-status"><Database :size="34" /><strong>No external analytics connections configured</strong><p>API clients, webhooks and synchronization monitoring will be enabled per integration after security review and sandbox acceptance.</p></div></section>
  </template>

  <div v-if="exportOpen" class="modal-backdrop" @click.self="exportOpen = false"><form class="user-modal" @submit.prevent="exportSummary"><h2>Export executive summary</h2><p class="modal-copy">The CSV is marked Internal and the purpose, filters, actor and row count are recorded.</p><label>Purpose<textarea v-model="exportPurpose" minlength="10" required placeholder="Quarterly management review"></textarea></label><footer><button type="button" class="secondary-action" @click="exportOpen = false">Cancel</button><button class="primary-action" :disabled="exporting">{{ exporting ? 'Preparing...' : 'Export CSV' }}</button></footer></form></div>
</template>
