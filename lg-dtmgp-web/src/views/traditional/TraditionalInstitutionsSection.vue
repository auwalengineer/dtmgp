<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Institution } from "./types";

const COUNCIL_TYPES = new Set(["State Council of Chiefs", "Area Traditional Council", "LGA Traditional Council"]);
const DISTRICT_TYPES = new Set(["District Headship", "Clan/Ward Headship"]);
const INSTITUTION_TYPES = ["State Council of Chiefs", "Area Traditional Council", "LGA Traditional Council", "Paramount Stool", "First Class Stool", "Second Class Stool", "Third Class Stool", "District Headship", "Clan/Ward Headship"];

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "institution-register": "Institution Register", "traditional-councils": "Traditional Councils", "districts-chiefdoms": "Districts & Chiefdoms", "institutional-profiles": "Institutional Profiles", "historical-records": "Historical Records" };
const DEFAULT_ITEM = "institution-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const institutions = ref<Institution[]>([]);
const loading = ref(true);
const error = ref("");
async function loadInstitutions() {
  loading.value = true;
  error.value = "";
  try { institutions.value = (await apiRequest<{ items: Institution[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&company=${encodeURIComponent(session.activeLga)}&page_size=100`)).items; }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load institutions"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadInstitutions, { immediate: true });

const councils = computed(() => institutions.value.filter((item) => COUNCIL_TYPES.has(item.institution_type)));
const districts = computed(() => institutions.value.filter((item) => DISTRICT_TYPES.has(item.institution_type)));

const selectedInstitution = ref("");
const detail = ref<Institution | null>(null);
const detailLoading = ref(false);
async function loadDetail(name: string) {
  if (!name) { detail.value = null; return; }
  detailLoading.value = true;
  try { detail.value = await apiRequest<Institution>(`/api/method/frappe.client.get?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&name=${encodeURIComponent(name)}`); }
  finally { detailLoading.value = false; }
}
watch(selectedInstitution, loadDetail);

const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string>>({});
function openCreate() { form.value = { institution_name: "", institution_type: "District Headship", rank_class: "", parent_institution: "", seat_location: "", status: "Vacant" }; showForm.value = true; }
async function saveInstitution() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Institution", values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadInstitutions();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the institution"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>

  <template v-if="activeItem === 'institution-register'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Institution register</h3><button v-if="canManage" class="secondary-action" @click="openCreate"><FilePlus2 :size="15" /> New institution</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Type</th><th>Rank / Class</th><th>Seat</th><th>Status</th></tr></thead><tbody><tr v-for="item in institutions" :key="item.name"><td><strong>{{ item.institution_name }}</strong></td><td>{{ item.institution_type }}</td><td>{{ item.rank_class || '-' }}</td><td>{{ item.seat_location || '-' }}</td><td><span class="table-status" :class="item.status === 'Active' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading institutions...</p><p v-else-if="!institutions.length" class="users-empty">No traditional institutions registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'traditional-councils'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Council</th><th>Type</th><th>Seat</th><th>Status</th></tr></thead><tbody><tr v-for="item in councils" :key="item.name"><td><strong>{{ item.institution_name }}</strong></td><td>{{ item.institution_type }}</td><td>{{ item.seat_location || '-' }}</td><td><span class="table-status" :class="item.status === 'Active' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="!councils.length" class="users-empty">No traditional councils registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'districts-chiefdoms'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Institution</th><th>Type</th><th>Parent</th><th>Status</th></tr></thead><tbody><tr v-for="item in districts" :key="item.name"><td><strong>{{ item.institution_name }}</strong></td><td>{{ item.institution_type }}</td><td>{{ item.parent_institution || '-' }}</td><td><span class="table-status" :class="item.status === 'Active' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="!districts.length" class="users-empty">No districts or chiefdoms registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'institutional-profiles' || activeItem === 'historical-records'">
    <div class="directory-toolbar"><label style="flex:1;max-width:360px">Institution<select v-model="selectedInstitution"><option value="">Select an institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label></div>
    <p v-if="!selectedInstitution" class="users-empty">Select an institution above to view its {{ activeItem === 'historical-records' ? 'historical record' : 'profile' }}.</p>
    <p v-else-if="detailLoading" class="users-empty">Loading...</p>
    <template v-else-if="detail && activeItem === 'institutional-profiles'">
      <div class="staff-table-wrap"><table class="staff-table"><tbody>
        <tr><td>Name</td><td>{{ detail.institution_name }}</td></tr>
        <tr><td>Type</td><td>{{ detail.institution_type }}</td></tr>
        <tr><td>Rank / Class</td><td>{{ detail.rank_class || '-' }}</td></tr>
        <tr><td>Parent institution</td><td>{{ detail.parent_institution || '-' }}</td></tr>
        <tr><td>Seat location</td><td>{{ detail.seat_location || '-' }}</td></tr>
        <tr><td>Founding basis</td><td>{{ detail.founding_basis || '-' }}</td></tr>
        <tr><td>Status</td><td>{{ detail.status }}</td></tr>
      </tbody></table></div>
    </template>
    <template v-else-if="detail && activeItem === 'historical-records'">
      <div class="staff-table-wrap"><table class="staff-table"><tbody><tr><td style="white-space:pre-wrap">{{ detail.history || 'No historical record on file for this institution.' }}</td></tr></tbody></table></div>
    </template>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveInstitution"><h2>New institution</h2><div class="form-grid">
    <label class="full-field">Institution name<input v-model="form.institution_name" required /></label>
    <label>Type<select v-model="form.institution_type" required><option v-for="item in INSTITUTION_TYPES" :key="item">{{ item }}</option></select></label>
    <label>Rank / Class<select v-model="form.rank_class"><option value="">Not applicable</option><option>First Class</option><option>Second Class</option><option>Third Class</option></select></label>
    <label>Parent institution<select v-model="form.parent_institution"><option value="">None</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label>Seat location<input v-model="form.seat_location" /></label>
    <label>Status<select v-model="form.status"><option>Active</option><option>Vacant</option><option>Suspended</option><option>Dissolved</option></select></label>
  </div><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save institution" }}</button></footer></form></div>
</template>
