<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Reports } from "./types";

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "traditional-institution-report": "Traditional Institution Report", "traditional-ruler-report": "Traditional Ruler Report", "appointment-report": "Appointment Report", "succession-report": "Succession Report", "petition-dispute-report": "Petition & Dispute Report" };
const DEFAULT_ITEM = "traditional-institution-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const reports = ref<Reports | null>(null);
const loading = ref(true);
const error = ref("");
async function loadReports() {
  loading.value = true;
  error.value = "";
  try { reports.value = await apiRequest<Reports>(`/api/method/dtmgp.api.v1.traditional.get_traditional_reports?company=${encodeURIComponent(session.activeLga)}`); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load reports"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadReports, { immediate: true });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading reports...</p>

  <template v-else-if="reports">
    <template v-if="activeItem === 'traditional-institution-report'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Institutions by type</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody><tr v-for="row in reports.institutions_by_type" :key="row.label"><td>{{ row.label }}</td><td>{{ row.count }}</td></tr></tbody></table><p v-if="!reports.institutions_by_type.length" class="users-empty">No institutions recorded for this LGA yet.</p></div>
    </template>
    <template v-else-if="activeItem === 'traditional-ruler-report'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Rulers by status</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody><tr v-for="row in reports.rulers_by_status" :key="row.label"><td>{{ row.label }}</td><td>{{ row.count }}</td></tr></tbody></table><p v-if="!reports.rulers_by_status.length" class="users-empty">No rulers recorded for this LGA yet.</p></div>
    </template>
    <template v-else-if="activeItem === 'appointment-report'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Appointments by stage</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Stage</th><th>Count</th></tr></thead><tbody><tr v-for="row in reports.appointments_by_stage" :key="row.label"><td>{{ row.label }}</td><td>{{ row.count }}</td></tr></tbody></table><p v-if="!reports.appointments_by_stage.length" class="users-empty">No appointments recorded for this LGA yet.</p></div>
    </template>
    <template v-else-if="activeItem === 'succession-report'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Succession cases by status</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody><tr v-for="row in reports.succession_by_status" :key="row.label"><td>{{ row.label }}</td><td>{{ row.count }}</td></tr></tbody></table><p v-if="!reports.succession_by_status.length" class="users-empty">No succession cases recorded for this LGA yet.</p></div>
    </template>
    <template v-else-if="activeItem === 'petition-dispute-report'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Petitions by status</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody><tr v-for="row in reports.petitions_by_status" :key="row.label"><td>{{ row.label }}</td><td>{{ row.count }}</td></tr></tbody></table><p v-if="!reports.petitions_by_status.length" class="users-empty">No petitions recorded for this LGA yet.</p></div>
    </template>
  </template>
</template>
