<script setup lang="ts">
import { ChartColumn, UserCheck } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { HRReports } from "./types";

defineProps<{ hrReports: HRReports | null }>();

const ITEM_LABELS: Record<string, string> = { "staff-strength-report": "Staff Strength Report", "staff-distribution-report": "Staff Distribution Report", "retirement-forecast": "Retirement Forecast", "leave-report": "Leave Report", "establishment-report": "Establishment Report" };
const DEFAULT_ITEM = "staff-strength-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'staff-strength-report' && hrReports">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Staff strength by department</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>Staff</th></tr></thead><tbody><tr v-for="row in hrReports.strength_by_department" :key="row.department || '-'"><td>{{ row.department || 'Unassigned' }}</td><td>{{ row.count }}</td></tr></tbody></table></div>
  </template>

  <template v-else-if="activeItem === 'staff-distribution-report' && hrReports">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Distribution by gender</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Gender</th><th>Staff</th></tr></thead><tbody><tr v-for="row in hrReports.distribution_by_gender" :key="row.gender || '-'"><td>{{ row.gender || 'Unspecified' }}</td><td>{{ row.count }}</td></tr></tbody></table></div>
    <p class="users-empty">Distribution is reported by gender only today; combined dimensions (department, grade, age) aren't available yet.</p>
  </template>

  <template v-else-if="activeItem === 'retirement-forecast' && hrReports">
    <section class="hr-metrics" aria-label="Retirement forecast">
      <article><span class="hr-metric-icon gold"><UserCheck :size="19" /></span><div><small>Retiring within 12 months</small><strong>{{ hrReports.retirement_forecast_12m }}</strong></div></article>
    </section>
    <p class="users-empty">See Upcoming Retirements under Retirement &amp; Exit for the named staff list behind this count.</p>
  </template>

  <template v-else-if="activeItem === 'leave-report' && hrReports">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Leave days by type</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Leave type</th><th>Days taken</th></tr></thead><tbody><tr v-for="row in hrReports.leave_by_type" :key="row.leave_type"><td>{{ row.leave_type }}</td><td>{{ row.days }}</td></tr></tbody></table><p v-if="!hrReports.leave_by_type.length" class="users-empty">No submitted leave in this LGA yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'establishment-report' && hrReports">
    <section class="hr-metrics" aria-label="Establishment summary">
      <article><span class="hr-metric-icon green"><ChartColumn :size="19" /></span><div><small>Approved establishment</small><strong>{{ hrReports.establishment.approved_total }}</strong><p>{{ hrReports.establishment.filled_total }} filled, {{ hrReports.establishment.vacant_count }} vacant</p></div></article>
    </section>
    <p class="users-empty">See Establishment Control for position-level detail behind this summary.</p>
  </template>
</template>
