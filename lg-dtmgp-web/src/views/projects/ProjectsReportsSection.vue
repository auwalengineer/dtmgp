<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ReportActions from "@/components/ReportActions.vue";
import { useSessionStore } from "@/stores/session";
import ItemTabs from "../shared/ItemTabs.vue";
import type { ReportsData } from "./types";

const props = defineProps<{ reports: ReportsData | null }>();
const session = useSessionStore();

const ITEM_LABELS: Record<string, string> = { "project-status-report": "Project Status Report", "project-performance-report": "Project Performance Report", "inspection-report": "Inspection Report", "asset-report": "Asset Report", "fleet-report": "Fleet Report" };
const DEFAULT_ITEM = "project-status-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
const exportData = computed(() => {
  const report = props.reports;
  if (!report) return { id: "projects.status", columns: ["Status", "Count"], rows: [] as unknown[][] };
  if (activeItem.value === "project-performance-report") return { id: "projects.performance", columns: ["Measure", "Value"], rows: [["Average physical progress (%)", report.project_performance.average_percent_complete], ["Delayed projects", report.project_performance.delayed]] };
  if (activeItem.value === "inspection-report") return { id: "projects.inspections", columns: ["Status", "Count"], rows: Object.entries(report.inspections) };
  if (activeItem.value === "asset-report") return { id: "projects.assets", columns: ["Status", "Count"], rows: Object.entries(report.assets) };
  if (activeItem.value === "fleet-report") return { id: "projects.fleet", columns: ["Measure", "Value"], rows: [["Vehicles", report.fleet.vehicle_count], ["Total fuel cost", report.fleet.total_fuel_cost]] };
  return { id: "projects.status", columns: ["Status", "Count"], rows: Object.entries(report.project_status).map(([status, count]) => [status, count]) };
});
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <ReportActions v-if="reports" :report-id="exportData.id" :title="ITEM_LABELS[activeItem]" :columns="exportData.columns" :rows="exportData.rows" :company="session.activeLga" />
  <p v-if="!reports" class="users-empty">Loading report data...</p>
  <template v-else>
    <template v-if="activeItem === 'project-status-report'">
      <div class="finance-metrics" aria-label="Project status report"><article><small>Total</small><strong>{{ reports.project_status.total }}</strong></article><article><small>Ongoing</small><strong>{{ reports.project_status.ongoing }}</strong></article><article><small>Delayed</small><strong>{{ reports.project_status.delayed }}</strong></article><article><small>Completed</small><strong>{{ reports.project_status.completed }}</strong></article><article><small>Suspended</small><strong>{{ reports.project_status.suspended }}</strong></article><article><small>Abandoned</small><strong>{{ reports.project_status.abandoned }}</strong></article></div>
    </template>

    <template v-else-if="activeItem === 'project-performance-report'">
      <div class="finance-metrics" aria-label="Project performance report"><article><small>Average physical progress</small><strong>{{ reports.project_performance.average_percent_complete }}%</strong></article><article><small>Delayed projects</small><strong>{{ reports.project_performance.delayed }}</strong></article></div>
    </template>

    <template v-else-if="activeItem === 'inspection-report'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody><tr v-for="(count, status) in reports.inspections" :key="status"><td>{{ status }}</td><td>{{ count }}</td></tr></tbody></table><p v-if="!Object.keys(reports.inspections).length" class="users-empty">No inspections recorded for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'asset-report'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody><tr v-for="(count, status) in reports.assets" :key="status"><td>{{ status }}</td><td>{{ count }}</td></tr></tbody></table><p v-if="!Object.keys(reports.assets).length" class="users-empty">No assets recorded for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'fleet-report'">
      <div class="finance-metrics" aria-label="Fleet report"><article><small>Vehicles</small><strong>{{ reports.fleet.vehicle_count }}</strong></article><article><small>Total fuel cost</small><strong>{{ reports.fleet.total_fuel_cost.toLocaleString() }}</strong></article></div>
    </template>
  </template>
</template>
