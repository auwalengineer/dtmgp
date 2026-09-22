<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Appointment } from "./types";

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "recognition-requests": "Recognition Requests", "recognition-approvals": "Recognition Approvals", "certificate-register": "Certificate Register", "issue-certificates": "Issue Certificates", "suspended-recognition": "Suspended Recognition", "withdrawn-recognition": "Withdrawn Recognition" };
const DEFAULT_ITEM = "recognition-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const appointments = ref<Appointment[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAppointments() {
  loading.value = true;
  error.value = "";
  try { appointments.value = (await apiRequest<{ items: Appointment[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Appointment")}&company=${encodeURIComponent(session.activeLga)}&page_size=100`)).items; }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load appointments"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAppointments, { immediate: true });

const recognitionRequests = computed(() => appointments.value.filter((a) => !["Gazetted", "Installed"].includes(a.status) && a.recognition_status === "Pending"));
const recognitionApprovals = computed(() => appointments.value.filter((a) => ["Gazetted", "Installed"].includes(a.status) && a.recognition_status === "Approved"));
const certificateRegister = computed(() => appointments.value.filter((a) => a.recognition_status === "Approved"));
const suspended = computed(() => appointments.value.filter((a) => a.recognition_status === "Suspended"));
const withdrawn = computed(() => appointments.value.filter((a) => a.recognition_status === "Withdrawn"));

async function setRecognitionStatus(name: string, status: "Suspended" | "Withdrawn") {
  const reason = window.prompt(`Reason for marking this recognition ${status}`);
  if (!reason) return;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.update_recognition", { method: "POST", body: JSON.stringify({ name, recognition_status: status, reason }) });
    await loadAppointments();
  } catch (reason_) { error.value = reason_ instanceof Error ? reason_.message : "Unable to update recognition status"; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p class="users-empty" style="text-align:left;padding:12px 20px 0">Recognition and certification share the same underlying appointment records as the Appointments tab — this view filters by recognition status instead of workflow stage.</p>

  <template v-if="activeItem === 'recognition-requests'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Stage</th></tr></thead><tbody><tr v-for="item in recognitionRequests" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><span class="table-status neutral">{{ item.status }}</span></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading...</p><p v-else-if="!recognitionRequests.length" class="users-empty">No appointments awaiting recognition.</p></div>
  </template>
  <template v-else-if="activeItem === 'recognition-approvals'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Gazette reference</th></tr></thead><tbody><tr v-for="item in recognitionApprovals" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.gazette_reference || '-' }}</td></tr></tbody></table><p v-if="!recognitionApprovals.length" class="users-empty">No approved and recognized appointments yet.</p></div>
  </template>
  <template v-else-if="activeItem === 'certificate-register' || activeItem === 'issue-certificates'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Gazette reference</th><th>Gazette date</th></tr></thead><tbody><tr v-for="item in certificateRegister" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.gazette_reference || '-' }}</td><td>{{ item.gazette_date || '-' }}</td></tr></tbody></table><p v-if="!certificateRegister.length" class="users-empty">No recognition certificates on file yet.</p></div>
  </template>
  <template v-else-if="activeItem === 'suspended-recognition'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th></tr></thead><tbody><tr v-for="item in suspended" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td></tr></tbody></table><p v-if="!suspended.length" class="users-empty">No suspended recognitions.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Suspend a recognized appointment</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th></th></tr></thead><tbody><tr v-for="item in recognitionApprovals" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="setRecognitionStatus(item.name, 'Suspended')">Suspend</button></td></tr></tbody></table></div>
  </template>
  <template v-else-if="activeItem === 'withdrawn-recognition'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th></tr></thead><tbody><tr v-for="item in withdrawn" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td></tr></tbody></table><p v-if="!withdrawn.length" class="users-empty">No withdrawn recognitions.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Withdraw a recognized appointment</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th></th></tr></thead><tbody><tr v-for="item in recognitionApprovals" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="setRecognitionStatus(item.name, 'Withdrawn')">Withdraw</button></td></tr></tbody></table></div>
  </template>
</template>
