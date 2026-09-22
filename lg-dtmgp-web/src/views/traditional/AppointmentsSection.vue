<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Appointment, Institution, RulingHouse } from "./types";
import { APPOINTMENT_CHAIN, nextInChain, today } from "./types";

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "appointment-applications": "Appointment Applications", "selection-processes": "Selection Processes", "appointment-reviews": "Appointment Reviews", "pending-recognition": "Pending Recognition", "approved-appointments": "Approved Appointments", "installation-records": "Installation Records" };
const DEFAULT_ITEM = "appointment-applications";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const appointments = ref<Appointment[]>([]);
const institutions = ref<Institution[]>([]);
const rulingHouses = ref<RulingHouse[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [appointments.value, institutions.value, rulingHouses.value] = await Promise.all([
      apiRequest<{ items: Appointment[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Appointment")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: Institution[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: RulingHouse[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Ruling House")}&company=${company}&page_size=100`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load appointments"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAll, { immediate: true });

const applications = computed(() => appointments.value.filter((a) => a.status === "Nominated"));
const selectionProcesses = computed(() => appointments.value.filter((a) => ["Kingmakers Selection", "Council Endorsed"].includes(a.status)));
const reviews = computed(() => appointments.value.filter((a) => a.status === "Ministry Vetting"));
const pendingRecognition = computed(() => appointments.value.filter((a) => !["Gazetted", "Installed"].includes(a.status)));
const approved = computed(() => appointments.value.filter((a) => ["Gazetted", "Installed"].includes(a.status)));
const installed = computed(() => appointments.value.filter((a) => a.status === "Installed"));

async function advance(name: string) {
  const record = appointments.value.find((a) => a.name === name);
  const target = record && nextInChain(APPOINTMENT_CHAIN, record.status);
  if (!target) return;
  error.value = "";
  try {
    if (target === "Gazetted" && !record?.gazette_reference) {
      const reference = window.prompt("Gazette reference (required to advance to Gazetted)");
      if (!reference) return;
      await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Appointment", name, values: { gazette_reference: reference, gazette_date: today() } }) });
    }
    await apiRequest("/api/method/dtmgp.api.v1.traditional.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Appointment", name, target_status: target }) });
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the appointment"; }
}

const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string>>({});
function openCreate() { form.value = { institution: "", candidate_name: "", ruling_house: "", application_date: today() }; showForm.value = true; }
async function saveAppointment() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Appointment", values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the appointment"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <div class="directory-toolbar"><h3 style="margin:0;flex:1">{{ ITEM_LABELS[activeItem] }}</h3><button v-if="canManage" class="secondary-action" @click="openCreate"><FilePlus2 :size="15" /> New appointment</button></div>

  <template v-if="activeItem === 'appointment-applications'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Applied</th><th></th></tr></thead><tbody><tr v-for="item in applications" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.application_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading...</p><p v-else-if="!applications.length" class="users-empty">No appointment applications for this LGA.</p></div>
  </template>
  <template v-else-if="activeItem === 'selection-processes'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Stage</th><th></th></tr></thead><tbody><tr v-for="item in selectionProcesses" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="!selectionProcesses.length" class="users-empty">No appointments in a selection stage.</p></div>
  </template>
  <template v-else-if="activeItem === 'appointment-reviews'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th></th></tr></thead><tbody><tr v-for="item in reviews" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="!reviews.length" class="users-empty">No appointments under ministry review.</p></div>
  </template>
  <template v-else-if="activeItem === 'pending-recognition'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Stage</th><th></th></tr></thead><tbody><tr v-for="item in pendingRecognition" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="!pendingRecognition.length" class="users-empty">No appointments pending recognition.</p></div>
  </template>
  <template v-else-if="activeItem === 'approved-appointments'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Gazette reference</th></tr></thead><tbody><tr v-for="item in approved" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.gazette_reference || '-' }}</td></tr></tbody></table><p v-if="!approved.length" class="users-empty">No approved appointments yet.</p></div>
  </template>
  <template v-else-if="activeItem === 'installation-records'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Candidate</th><th>Institution</th><th>Installation date</th></tr></thead><tbody><tr v-for="item in installed" :key="item.name"><td><strong>{{ item.candidate_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.installation_date || '-' }}</td></tr></tbody></table><p v-if="!installed.length" class="users-empty">No installations recorded yet.</p></div>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveAppointment"><h2>New appointment</h2><div class="form-grid">
    <label>Institution<select v-model="form.institution" required><option value="" disabled>Select institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label class="full-field">Candidate name<input v-model="form.candidate_name" required /></label>
    <label>Ruling house<select v-model="form.ruling_house"><option value="">None</option><option v-for="item in rulingHouses.filter(h => h.institution === form.institution)" :key="item.name" :value="item.name">{{ item.house_name }}</option></select></label>
    <label>Application date<input v-model="form.application_date" type="date" required /></label>
  </div><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save appointment" }}</button></footer></form></div>
</template>
