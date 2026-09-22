<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { ReportsData } from "./types";

const props = defineProps<{ reports: ReportsData | null }>();

const ITEM_LABELS: Record<string, string> = { "project-status-report": "Project Status Report", "project-performance-report": "Project Performance Report", "inspection-report": "Inspection Report", "asset-report": "Asset Report", "fleet-report": "Fleet Report" };
const DEFAULT_ITEM = "project-status-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
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
