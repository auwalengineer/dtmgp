<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Institution, RulingHouse, SuccessionCase } from "./types";
import { nextInChain, SUCCESSION_CHAIN, today } from "./types";

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "succession-cases": "Succession Cases", "ruling-houses": "Ruling Houses", "eligible-candidates": "Eligible Candidates", "selection-records": "Selection Records", "succession-history": "Succession History" };
const DEFAULT_ITEM = "succession-cases";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const cases = ref<SuccessionCase[]>([]);
const institutions = ref<Institution[]>([]);
const rulingHouses = ref<RulingHouse[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [cases.value, institutions.value, rulingHouses.value] = await Promise.all([
      apiRequest<{ items: SuccessionCase[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Succession Case")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: Institution[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: RulingHouse[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Ruling House")}&company=${company}&page_size=100`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load succession records"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAll, { immediate: true });

const eligibleHouses = computed(() => [...rulingHouses.value].filter((h) => h.is_eligible).sort((a, b) => a.rotation_order - b.rotation_order));
const selectionRecords = computed(() => cases.value.filter((c) => c.status === "Kingmakers Deliberation"));
const history = computed(() => cases.value.filter((c) => c.status === "Closed"));

async function advanceCase(name: string) {
  const record = cases.value.find((c) => c.name === name);
  const target = record && nextInChain(SUCCESSION_CHAIN, record.status);
  if (!target) return;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Succession Case", name, target_status: target }) });
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the succession case"; }
}

const showCaseForm = ref(false);
const showHouseForm = ref(false);
const saving = ref(false);
const caseForm = ref<Record<string, string>>({});
const houseForm = ref<Record<string, string | number>>({});
function openCreateCase() { caseForm.value = { institution: "", vacancy_date: today(), vacancy_reason: "Death", eligible_ruling_house: "", candidates: "" }; showCaseForm.value = true; }
function openCreateHouse() { houseForm.value = { institution: "", house_name: "", rotation_order: 0 }; showHouseForm.value = true; }
async function saveCase() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Succession Case", values: { ...caseForm.value, company: session.activeLga } }) });
    showCaseForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the succession case"; }
  finally { saving.value = false; }
}
async function saveHouse() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Ruling House", values: { ...houseForm.value, company: session.activeLga } }) });
    showHouseForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the ruling house"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>

  <template v-if="activeItem === 'succession-cases'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Succession cases</h3><button v-if="canManage" class="secondary-action" @click="openCreateCase"><FilePlus2 :size="15" /> New case</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Vacancy date</th><th>Reason</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in cases" :key="item.name"><td><strong>{{ item.institution }}</strong></td><td>{{ item.vacancy_date }}</td><td>{{ item.vacancy_reason }}</td><td><span class="table-status" :class="item.status === 'Closed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && nextInChain(SUCCESSION_CHAIN, item.status) && item.status !== 'Selected'" class="secondary-action compact-action" @click="advanceCase(item.name)">Advance</button></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading...</p><p v-else-if="!cases.length" class="users-empty">No succession cases for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'ruling-houses'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Ruling houses</h3><button v-if="canManage" class="secondary-action" @click="openCreateHouse"><FilePlus2 :size="15" /> New ruling house</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>House</th><th>Institution</th><th>Rotation order</th><th>Eligible</th></tr></thead><tbody><tr v-for="item in rulingHouses" :key="item.name"><td><strong>{{ item.house_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.rotation_order }}</td><td><span class="table-status" :class="item.is_eligible ? 'success' : 'neutral'">{{ item.is_eligible ? 'Eligible' : 'Not eligible' }}</span></td></tr></tbody></table><p v-if="!rulingHouses.length" class="users-empty">No ruling houses registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'eligible-candidates'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>House</th><th>Institution</th><th>Rotation order</th></tr></thead><tbody><tr v-for="item in eligibleHouses" :key="item.name"><td><strong>{{ item.house_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.rotation_order }}</td></tr></tbody></table><p v-if="!eligibleHouses.length" class="users-empty">No ruling houses currently marked eligible.</p></div>
  </template>

  <template v-else-if="activeItem === 'selection-records'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Eligible house</th><th>Candidates</th><th></th></tr></thead><tbody><tr v-for="item in selectionRecords" :key="item.name"><td><strong>{{ item.institution }}</strong></td><td>{{ item.eligible_ruling_house || '-' }}</td><td>{{ item.candidates || '-' }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="advanceCase(item.name)">Advance</button></td></tr></tbody></table><p v-if="!selectionRecords.length" class="users-empty">No cases currently at Kingmakers Deliberation.</p></div>
  </template>

  <template v-else-if="activeItem === 'succession-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Selected candidate</th><th>Closed</th></tr></thead><tbody><tr v-for="item in history" :key="item.name"><td><strong>{{ item.institution }}</strong></td><td>{{ item.selected_candidate || '-' }}</td><td>{{ item.resulting_appointment || '-' }}</td></tr></tbody></table><p v-if="!history.length" class="users-empty">No closed succession cases yet.</p></div>
  </template>

  <div v-if="showCaseForm" class="modal-backdrop" @click.self="showCaseForm = false"><form class="user-modal" @submit.prevent="saveCase"><h2>New succession case</h2><div class="form-grid">
    <label>Institution<select v-model="caseForm.institution" required><option value="" disabled>Select institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label>Vacancy date<input v-model="caseForm.vacancy_date" type="date" required /></label>
    <label>Vacancy reason<select v-model="caseForm.vacancy_reason"><option>Death</option><option>Deposition</option><option>Abdication</option><option>Resignation</option></select></label>
    <label>Eligible ruling house<select v-model="caseForm.eligible_ruling_house"><option value="">Not yet determined</option><option v-for="item in rulingHouses.filter(h => h.institution === caseForm.institution)" :key="item.name" :value="item.name">{{ item.house_name }}</option></select></label>
    <label class="full-field">Nominated candidates<textarea v-model="caseForm.candidates" placeholder="One name per line"></textarea></label>
  </div><footer><button type="button" class="secondary-action" @click="showCaseForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save case" }}</button></footer></form></div>

  <div v-if="showHouseForm" class="modal-backdrop" @click.self="showHouseForm = false"><form class="user-modal" @submit.prevent="saveHouse"><h2>New ruling house</h2><div class="form-grid">
    <label>Institution<select v-model="houseForm.institution" required><option value="" disabled>Select institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label class="full-field">House name<input v-model="houseForm.house_name" required /></label>
    <label>Rotation order<input v-model.number="houseForm.rotation_order" type="number" min="0" /></label>
  </div><footer><button type="button" class="secondary-action" @click="showHouseForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save ruling house" }}</button></footer></form></div>
</template>
