<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Institution, Ruler } from "./types";

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "rulers-register": "Rulers Register", "current-rulers": "Current Rulers", "former-rulers": "Former Rulers", "vacant-stools": "Vacant Stools", "ruler-profiles": "Ruler Profiles" };
const DEFAULT_ITEM = "rulers-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const rulers = ref<Ruler[]>([]);
const institutions = ref<Institution[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [rulers.value, institutions.value] = await Promise.all([
      apiRequest<{ items: Ruler[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Ruler")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: Institution[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&company=${company}&page_size=100`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load rulers"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAll, { immediate: true });

const currentRulers = computed(() => rulers.value.filter((item) => item.status === "Reigning"));
const formerRulers = computed(() => rulers.value.filter((item) => item.status !== "Reigning"));
const vacantStools = computed(() => {
  const reigningInstitutions = new Set(currentRulers.value.map((item) => item.institution));
  return institutions.value.filter((item) => item.status === "Active" && !reigningInstitutions.has(item.name));
});

const selectedRuler = ref("");
const detail = ref<Ruler | null>(null);
const detailLoading = ref(false);
watch(selectedRuler, async (name) => {
  if (!name) { detail.value = null; return; }
  detailLoading.value = true;
  try { detail.value = await apiRequest<Ruler>(`/api/method/frappe.client.get?doctype=${encodeURIComponent("DTMGP Traditional Ruler")}&name=${encodeURIComponent(name)}`); }
  finally { detailLoading.value = false; }
});

const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string>>({});
function openCreate() { form.value = { ruler_name: "", institution: "", ruling_house: "", gender: "", date_of_birth: "", appointment_date: new Date().toISOString().slice(0, 10) }; showForm.value = true; }
async function saveRuler() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Ruler", values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the ruler"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>

  <template v-if="activeItem === 'rulers-register'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Rulers register</h3><button v-if="canManage" class="secondary-action" @click="openCreate"><FilePlus2 :size="15" /> New ruler</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Institution</th><th>Appointed</th><th>Status</th></tr></thead><tbody><tr v-for="item in rulers" :key="item.name"><td><strong>{{ item.ruler_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.appointment_date }}</td><td><span class="table-status" :class="item.status === 'Reigning' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading rulers...</p><p v-else-if="!rulers.length" class="users-empty">No rulers recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'current-rulers'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Institution</th><th>Appointed</th><th>Installed</th></tr></thead><tbody><tr v-for="item in currentRulers" :key="item.name"><td><strong>{{ item.ruler_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.appointment_date }}</td><td>{{ item.installation_date || '-' }}</td></tr></tbody></table><p v-if="!currentRulers.length" class="users-empty">No reigning rulers recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'former-rulers'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Institution</th><th>Status</th><th>Reign ended</th></tr></thead><tbody><tr v-for="item in formerRulers" :key="item.name"><td><strong>{{ item.ruler_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.status }}</td><td>{{ item.reign_end_date || '-' }}</td></tr></tbody></table><p v-if="!formerRulers.length" class="users-empty">No former rulers recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'vacant-stools'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Type</th><th>Rank / Class</th></tr></thead><tbody><tr v-for="item in vacantStools" :key="item.name"><td><strong>{{ item.institution_name }}</strong></td><td>{{ item.institution_type }}</td><td>{{ item.rank_class || '-' }}</td></tr></tbody></table><p v-if="!vacantStools.length" class="users-empty">No vacant stools among active institutions.</p></div>
  </template>

  <template v-else-if="activeItem === 'ruler-profiles'">
    <div class="directory-toolbar"><label style="flex:1;max-width:360px">Ruler<select v-model="selectedRuler"><option value="">Select a ruler</option><option v-for="item in rulers" :key="item.name" :value="item.name">{{ item.ruler_name }}</option></select></label></div>
    <p v-if="!selectedRuler" class="users-empty">Select a ruler above to view their profile.</p>
    <p v-else-if="detailLoading" class="users-empty">Loading...</p>
    <div v-else-if="detail" class="staff-table-wrap"><table class="staff-table"><tbody>
      <tr><td>Name</td><td>{{ detail.ruler_name }}</td></tr>
      <tr><td>Institution</td><td>{{ detail.institution }}</td></tr>
      <tr><td>Ruling house</td><td>{{ detail.ruling_house || '-' }}</td></tr>
      <tr><td>Appointment date</td><td>{{ detail.appointment_date }}</td></tr>
      <tr><td>Installation date</td><td>{{ detail.installation_date || '-' }}</td></tr>
      <tr><td>Status</td><td>{{ detail.status }}</td></tr>
      <tr v-if="detail.reign_end_date"><td>Reign ended</td><td>{{ detail.reign_end_date }}</td></tr>
    </tbody></table></div>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveRuler"><h2>New ruler</h2><div class="form-grid">
    <label class="full-field">Ruler name<input v-model="form.ruler_name" required /></label>
    <label>Institution<select v-model="form.institution" required><option value="" disabled>Select institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label>Appointment date<input v-model="form.appointment_date" type="date" required /></label>
  </div><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save ruler" }}</button></footer></form></div>
</template>
